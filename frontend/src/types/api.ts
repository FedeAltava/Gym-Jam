export interface UserResponse {
  id: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface WorkoutExerciseResponse {
  id: string;
  exercise_id: string;
  order: number;
}

export interface TrainingDayResponse {
  day_of_week: string;
  exercises: WorkoutExerciseResponse[];
}

export interface WorkoutResponse {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  training_days: TrainingDayResponse[];
}

export interface ApiError {
  detail: string;
}
