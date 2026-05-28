from __future__ import annotations
from datetime import datetime, UTC
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
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
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workout_id: Mapped[str] = mapped_column(String(36), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    training_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_days.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[str] = mapped_column(String(255), nullable=False)
    order_in_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    training_day: Mapped[TrainingDayModel] = relationship("TrainingDayModel", back_populates="exercises")


class WorkoutSessionModel(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (Index("ix_workout_sessions_user_id", "user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    workout_id: Mapped[str] = mapped_column(String(36), ForeignKey("workouts.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WorkoutLogModel(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (Index("ix_workout_logs_session_id", "session_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_sessions.id"), nullable=False)
    workout_exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_exercises.id"), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
