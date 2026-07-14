export interface UserResponse {
  id: string;
  email: string;
  created_at: string;
  rest_seconds: number;
  units: 'kg' | 'lb';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ExerciseResponse {
  id: string;
  name: string;
  muscle_group: string;
  is_bodyweight: boolean;
}

export interface WorkoutExerciseResponse {
  id: string;
  exercise_id: string;
  order: number;
  sets: number;
  reps_per_set: number;
  weight_kg: number | null;
}

export interface TrainingDayResponse {
  id: string;
  day_of_week: string;
  order: number;
  exercises: WorkoutExerciseResponse[];
}

export interface ExerciseLogResponse {
  id: string;
  session_id: string;
  workout_exercise_id: string;
  set_number: number;
  reps_completed: number;
  weight_kg: number | null;
}

export interface WorkoutSessionResponse {
  id: string;
  workout_id: string;
  training_day_id: string;
  started_at: string;
  status: 'in_progress' | 'completed';
  completed_at: string | null;
  logs: ExerciseLogResponse[];
}

export interface WorkoutResponse {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  training_days: TrainingDayResponse[];
}

export interface ApiError {
  detail: string;
}

export interface UserStats {
  total_sessions: number;
  streak: number;
  total_prs: number;
  weekly_volume_kg: number;
  weekly_sessions: number;
  weekly_prs: number;
}

export interface SessionHistoryLogResponse {
  id: string;
  workout_exercise_id: string;
  exercise_name: string;
  muscle_group: string | null;
  set_number: number;
  reps_completed: number;
  weight_kg: number | null;
}

export interface SessionHistoryItemResponse {
  id: string;
  workout_id: string;
  training_day_id: string;
  workout_name: string;
  day_of_week: string;
  started_at: string;
  completed_at: string | null;
  status: 'completed' | 'in_progress';
  duration_seconds: number | null;
  pr_count: number;
  logs: SessionHistoryLogResponse[];
}
