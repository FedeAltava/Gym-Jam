from __future__ import annotations
from datetime import datetime, UTC
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, UniqueConstraint, Index, DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Python-side default fills ORM instances pre-commit; server_default covers
    # rows inserted without the column (e.g. metadata.create_all test seeds).
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90, server_default="90")
    units: Mapped[str] = mapped_column(String(2), nullable=False, default="kg", server_default="kg")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Set when the token was revoked by rotation (id of the replacing token).
    # NULL on logout revocation — the reuse grace window only applies to rotation.
    replaced_by_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ExerciseModel(Base):
    __tablename__ = "exercises"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(50), nullable=False)
    is_bodyweight: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WorkoutModel(Base):
    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    training_days: Mapped[list[TrainingDayModel]] = relationship(
        "TrainingDayModel", back_populates="workout", cascade="all, delete-orphan", lazy="selectin"
    )


class TrainingDayModel(Base):
    __tablename__ = "training_days"
    __table_args__ = (UniqueConstraint("workout_id", "day_of_week"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workout_id: Mapped[str] = mapped_column(String(36), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    workout: Mapped[WorkoutModel] = relationship("WorkoutModel", back_populates="training_days")
    exercises: Mapped[list[WorkoutExerciseModel]] = relationship(
        "WorkoutExerciseModel", back_populates="training_day", cascade="all, delete-orphan", lazy="selectin"
    )


class WorkoutExerciseModel(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("training_day_id", "order_in_day"),
        Index("ix_workout_exercises_exercise_id", "exercise_id"),
        Index("ix_workout_exercises_workout_id", "workout_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workout_id: Mapped[str] = mapped_column(String(36), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    training_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_days.id", ondelete="CASCADE"), nullable=False)
    # Deliberate soft reference (no FK to exercises): legacy rows hold free-text
    # ids that predate the catalog. Integrity is enforced in the use case layer
    # (AddExerciseToWorkoutUseCase validates against the catalog).
    exercise_id: Mapped[str] = mapped_column(String(255), nullable=False)
    order_in_day: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    reps_per_set: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    training_day: Mapped[TrainingDayModel] = relationship("TrainingDayModel", back_populates="exercises")


class WorkoutSessionModel(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (
        Index("ix_workout_sessions_user_id", "user_id"),
        Index("ix_workout_sessions_workout_id", "workout_id"),
        Index("ix_workout_sessions_training_day_id", "training_day_id"),
        # Serves GET /sessions history: filter by user + ORDER BY started_at.
        # Kept in sync with migration 009.
        Index("ix_workout_sessions_user_started", "user_id", "started_at"),
        # Prevents two concurrent POST /sessions from creating two in-progress
        # sessions for the same (user, training_day). Partial index: only one
        # NULL completed_at row per (user_id, training_day_id) is allowed.
        # Kept in sync with migration 014.
        Index(
            "uix_one_inprogress_per_day",
            "user_id",
            "training_day_id",
            unique=True,
            postgresql_where=text("completed_at IS NULL"),
            sqlite_where=text("completed_at IS NULL"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    workout_id: Mapped[str] = mapped_column(String(36), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    training_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_days.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    logs: Mapped[list["WorkoutLogModel"]] = relationship(
        "WorkoutLogModel", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class WorkoutLogModel(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (
        UniqueConstraint("session_id", "workout_exercise_id", "set_number"),
        Index("ix_workout_logs_session_id", "session_id"),
        Index("ix_workout_logs_workout_exercise_id", "workout_exercise_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False)
    workout_exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    session: Mapped["WorkoutSessionModel"] = relationship("WorkoutSessionModel", back_populates="logs")


class PersonalRecordModel(Base):
    __tablename__ = "personal_records"
    __table_args__ = (
        # One row per (user, catalog exercise): the heaviest weight ever
        # logged. Upserted in Python (SELECT-then-INSERT, ADR 4) — the UNIQUE
        # constraint is the backstop.
        UniqueConstraint("user_id", "exercise_id", name="uq_personal_records_user_exercise"),
        Index("ix_personal_records_user", "user_id"),
        # Serves the pr_count LEFT JOIN in session history.
        Index("ix_personal_records_session_id", "session_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Soft reference to the exercise catalog, same rationale as
    # workout_exercises.exercise_id (legacy free-text ids, no FK).
    exercise_id: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False
    )


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
