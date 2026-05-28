import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { WorkoutCard } from '../components/WorkoutCard';
import { useWorkouts } from '../hooks/useWorkouts';

export function DashboardPage() {
  const { data: workouts, isLoading, isError, error } = useWorkouts();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Workouts</h1>
        <Button asChild>
          <Link to="/workouts/new">+ New Workout</Link>
        </Button>
      </div>

      {isLoading && <p className="text-gray-500">Loading workouts…</p>}
      {isError && <p className="text-red-500">Error: {(error as Error).message}</p>}

      {workouts && workouts.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg mb-2">No workouts yet.</p>
          <p className="text-sm">Create your first workout to get started!</p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {workouts?.map((w) => <WorkoutCard key={w.id} workout={w} />)}
      </div>
    </div>
  );
}
