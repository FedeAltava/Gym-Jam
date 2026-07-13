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
  const avatarLetter = firstName ? firstName[0].toUpperCase() : '?';

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
          <StreakCard
            streak={stats?.streak ?? 0}
            planDays={planDays}
            completedDays={completedDays}
          />
          <WeeklyChart volumes={volumes} todayIndex={todayIdx} sessionsThisWeek={thisWeekSessions.length} planDaysCount={planDays.size} />
          <NextWorkoutCard workout={activeWorkout} />
          <RecentActivityList sessions={recentSessions} />
        </div>
      )}
    </div>
  );
}
