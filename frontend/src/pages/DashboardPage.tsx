import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { WorkoutCard } from '../components/WorkoutCard';
import { Spinner } from '../components/Spinner';
import { useWorkouts } from '../hooks/useWorkouts';

export function DashboardPage() {
  const { data: workouts, isLoading, isError, error } = useWorkouts();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-bold text-2xl text-text">Mis Entrenamientos</h1>
          <p className="text-sm mt-0.5 text-muted">Gestiona y sigue tus planes</p>
        </div>
        <Link
          to="/workouts/new"
          className="flex items-center gap-1.5 font-semibold no-underline rounded-btn bg-accent text-bg text-sm"
          style={{
            height: '40px',
            padding: '0 16px',
            boxShadow: '0 0 12px rgba(0, 255, 135, 0.35)',
          }}
        >
          <Plus size={16} />
          Nuevo
        </Link>
      </div>

      {isLoading && <Spinner />}
      {isError && (
        <p className="text-sm text-danger">
          Error: {(error as Error).message}
        </p>
      )}

      {workouts?.length === 0 && (
        <div className="text-center py-16 rounded-card border-2 border-dashed border-border">
          <p className="text-3xl mb-3">💪</p>
          <p className="font-semibold mb-1 text-text">Sin entrenamientos aún</p>
          <p className="text-sm text-muted">Crea tu primer entrenamiento para empezar</p>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {workouts?.map((w) => <WorkoutCard key={w.id} workout={w} />)}
      </div>
    </div>
  );
}
