import { Spinner } from '../components/Spinner';
import { WeeklyChart } from '../components/dashboard/WeeklyChart';
import { MuscleSetsCard, type MuscleSets } from '../components/dashboard/MuscleSetsCard';
import { NextWorkoutCard } from '../components/dashboard/NextWorkoutCard';
import { WeeklyConsistencyCard, type WeekSessions } from '../components/dashboard/WeeklyConsistencyCard';
import { useAuthStore } from '../store/authStore';
import { useUserStats } from '../hooks/useStats';
import { useActiveWorkout } from '../hooks/useActiveWorkout';
import { useExercises } from '../hooks/useExercises';
import { useCompletedSessionsSince } from '../hooks/useSessionHistory';
import { DAYS, type DayKey } from '../lib/days';
import type { ExerciseResponse, SessionHistoryItemResponse, WorkoutResponse } from '../types/api';

const CONSISTENCY_WEEKS = 8;
const WEEK_MS = 7 * 86_400_000;
// Muscle groups in display order; anything else follows alphabetically.
const MUSCLE_ORDER = ['Pecho', 'Espalda', 'Hombros', 'Piernas', 'Brazos', 'Core'];

function firstNameFromEmail(email: string): string {
  const prefix = email.split('@')[0];
  return prefix.charAt(0).toUpperCase() + prefix.slice(1);
}

/**
 * Start of the current week: Monday 00:00 UTC.
 *
 * The backend computes streak/weekly stats on UTC week boundaries, so the
 * dashboard MUST bucket sessions the same way — otherwise users at non-UTC
 * offsets see dashboard segments that disagree with the backend streak.
 */
function currentWeekStartUTC(now: Date): Date {
  const dayOfWeek = now.getUTCDay(); // 0 = Sunday … 6 = Saturday
  const daysFromMonday = (dayOfWeek + 6) % 7; // Mon=0 … Sun=6
  return new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - daysFromMonday),
  );
}

/** Monday-first (Mon=0 … Sun=6) day index of a date, computed in UTC. */
function mondayFirstIndexUTC(date: Date): number {
  return (date.getUTCDay() + 6) % 7;
}

/** This week's logged sets per muscle group against the routine's weekly plan. */
function muscleSets(
  workout: WorkoutResponse | undefined,
  catalog: ExerciseResponse[] | undefined,
  thisWeekSessions: SessionHistoryItemResponse[],
): MuscleSets[] {
  const muscleById = new Map((catalog ?? []).map((e) => [e.id, e.muscle_group]));
  const byMuscle = new Map<string, MuscleSets>();
  const row = (muscle: string) => {
    const existing = byMuscle.get(muscle) ?? { muscle, done: 0, planned: 0 };
    byMuscle.set(muscle, existing);
    return existing;
  };
  for (const day of workout?.training_days ?? []) {
    for (const exercise of day.exercises) {
      const muscle = muscleById.get(exercise.exercise_id);
      if (muscle) row(muscle).planned += exercise.sets;
    }
  }
  // History logs carry the muscle of the exercise actually done (swaps included).
  for (const session of thisWeekSessions) {
    for (const log of session.logs) {
      if (log.muscle_group) row(log.muscle_group).done += 1;
    }
  }
  const rank = (muscle: string) => {
    const i = MUSCLE_ORDER.indexOf(muscle);
    return i < 0 ? MUSCLE_ORDER.length : i;
  };
  return [...byMuscle.values()].sort((a, b) => rank(a.muscle) - rank(b.muscle) || a.muscle.localeCompare(b.muscle));
}

/** Completed sessions in each of the last CONSISTENCY_WEEKS UTC weeks, oldest first. */
function weeklySessions(sessions: SessionHistoryItemResponse[], weekStart: Date): WeekSessions[] {
  return Array.from({ length: CONSISTENCY_WEEKS }, (_, i) => {
    const start = new Date(weekStart.getTime() - (CONSISTENCY_WEEKS - 1 - i) * WEEK_MS);
    const end = start.getTime() + WEEK_MS;
    const count = sessions.filter((s) => {
      const t = new Date(s.started_at).getTime();
      return t >= start.getTime() && t < end;
    }).length;
    return { start, sessions: count };
  });
}

function sessionVolumeKg(session: SessionHistoryItemResponse): number {
  return session.logs.reduce(
    (total, log) => total + log.reps_completed * (log.weight_kg ?? 0),
    0,
  );
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data: stats, isLoading: statsLoading } = useUserStats();
  const { activeWorkout, isLoading: workoutsLoading } = useActiveWorkout();
  const { data: catalog } = useExercises();

  const now = new Date();
  const todayIdx = mondayFirstIndexUTC(now);
  const firstName = user ? firstNameFromEmail(user.email) : '';
  const avatarLetter = firstName ? firstName[0].toUpperCase() : '?';

  const weekStart = currentWeekStartUTC(now);
  const firstWeekStart = new Date(weekStart.getTime() - (CONSISTENCY_WEEKS - 1) * WEEK_MS);
  const { data: historyData, isLoading: historyLoading } = useCompletedSessionsSince(
    firstWeekStart.toISOString().slice(0, 10),
  );
  const completedSessions = historyData?.items ?? [];
  const thisWeekSessions = completedSessions.filter(
    (s) => new Date(s.started_at) >= weekStart,
  );

  const volumes = Array.from({ length: 7 }, () => 0);
  for (const session of thisWeekSessions) {
    volumes[mondayFirstIndexUTC(new Date(session.started_at))] += sessionVolumeKg(session);
  }

  const planDays = new Set(
    (activeWorkout?.training_days ?? [])
      .map((td) => DAYS.indexOf(td.day_of_week as DayKey))
      .filter((idx) => idx >= 0),
  );

  const isLoading = statsLoading || workoutsLoading || historyLoading;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '22px' }}>
        <div>
          <div style={{ fontSize: '14px', color: '#7E8A7E', fontWeight: 500 }}>Buenas, {firstName}</div>
          <div style={{ fontSize: '27px', fontWeight: 700, color: '#EAF0EA', fontFamily: "'Barlow Semi Condensed', sans-serif", letterSpacing: '-0.3px' }}>¿Listo para romperla?</div>
        </div>
        <div style={{ width: '42px', height: '42px', borderRadius: '14px', background: '#151A15', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#EAF0EA', fontWeight: 700 }}>
          {avatarLetter}
        </div>
      </div>

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="grid gap-4">
          <WeeklyChart
            streak={stats?.streak ?? 0}
            volumes={volumes}
            todayIndex={todayIdx}
            sessionsThisWeek={thisWeekSessions.length}
            planDaysCount={planDays.size}
          />
          <MuscleSetsCard rows={muscleSets(activeWorkout, catalog, thisWeekSessions)} />
          <NextWorkoutCard
            workout={activeWorkout}
            trainedDays={new Set(thisWeekSessions.map((session) => session.day_of_week))}
          />
          <WeeklyConsistencyCard weeks={weeklySessions(completedSessions, weekStart)} planDaysCount={planDays.size} />
        </div>
      )}
    </div>
  );
}
