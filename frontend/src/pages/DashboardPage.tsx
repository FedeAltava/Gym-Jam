import { Spinner } from '../components/Spinner';
import { StreakCard } from '../components/dashboard/StreakCard';
import { WeeklyChart } from '../components/dashboard/WeeklyChart';
import { NextWorkoutCard } from '../components/dashboard/NextWorkoutCard';
import { RecentActivityList } from '../components/dashboard/RecentActivityList';
import { useAuthStore } from '../store/authStore';
import { useUserStats } from '../hooks/useStats';
import { useActiveWorkout } from '../hooks/useActiveWorkout';
import { useSessionHistory } from '../hooks/useSessionHistory';
import { DAYS, mondayFirstIndex, type DayKey } from '../lib/days';
import type { SessionHistoryItemResponse } from '../types/api';

function firstNameFromEmail(email: string): string {
  const prefix = email.split('@')[0];
  return prefix.charAt(0).toUpperCase() + prefix.slice(1);
}

function greetingForHour(hour: number): string {
  if (hour < 12) return 'Buenos días';
  if (hour < 20) return 'Buenas tardes';
  return 'Buenas noches';
}

const subtitleFormat = new Intl.DateTimeFormat('es-ES', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
});

/** Start of the current week: Monday 00:00 local time. */
function currentWeekStart(now: Date): Date {
  const start = new Date(now);
  start.setDate(now.getDate() - mondayFirstIndex(now));
  start.setHours(0, 0, 0, 0);
  return start;
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
  const { data: historyData, isLoading: historyLoading } = useSessionHistory({
    status: 'completed',
  });

  const now = new Date();
  const todayIdx = mondayFirstIndex(now);
  const firstName = user ? firstNameFromEmail(user.email) : '';

  // Offset pagination can repeat items between pages — dedupe by id.
  const completedSessions = historyData
    ? Array.from(new Map(historyData.pages.flat().map((s) => [s.id, s])).values())
    : [];
  const recentSessions = completedSessions.slice(0, 2);

  const weekStart = currentWeekStart(now);
  const thisWeekSessions = completedSessions.filter(
    (s) => new Date(s.started_at) >= weekStart,
  );

  const completedDays = new Set(
    thisWeekSessions.map((s) => mondayFirstIndex(new Date(s.started_at))),
  );
  const volumes = Array.from({ length: 7 }, () => 0);
  for (const session of thisWeekSessions) {
    volumes[mondayFirstIndex(new Date(session.started_at))] += sessionVolumeKg(session);
  }

  const planDays = new Set(
    (activeWorkout?.training_days ?? [])
      .map((td) => DAYS.indexOf(td.day_of_week as DayKey))
      .filter((idx) => idx >= 0),
  );

  const isLoading = statsLoading || workoutsLoading || historyLoading;
  const isFullyEmpty = !activeWorkout && completedSessions.length === 0;

  return (
    <div>
      <header className="mb-6">
        <h1 className="font-condensed font-bold text-2xl text-text">
          {greetingForHour(now.getHours())}, {firstName}
        </h1>
        <p className="text-sm mt-0.5 text-muted">Hoy, {subtitleFormat.format(now)}</p>
      </header>

      {isLoading ? (
        <Spinner />
      ) : isFullyEmpty ? (
        <div className="max-w-md mx-auto mt-10">
          <NextWorkoutCard workout={undefined} />
        </div>
      ) : (
        <div className="grid gap-4">
          <StreakCard
            streak={stats?.streak ?? 0}
            planDays={planDays}
            completedDays={completedDays}
          />
          <WeeklyChart volumes={volumes} todayIndex={todayIdx} />
          <NextWorkoutCard workout={activeWorkout} />
          <RecentActivityList sessions={recentSessions} />
        </div>
      )}
    </div>
  );
}
