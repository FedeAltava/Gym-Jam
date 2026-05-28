import { useParams, Link } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { useWorkout } from '../hooks/useWorkouts';

const DAY_LABELS: Record<string, string> = {
  MONDAY: 'Monday', TUESDAY: 'Tuesday', WEDNESDAY: 'Wednesday',
  THURSDAY: 'Thursday', FRIDAY: 'Friday', SATURDAY: 'Saturday', SUNDAY: 'Sunday',
};

export function WorkoutDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: workout, isLoading, isError, error } = useWorkout(id ?? '');

  if (isLoading) return <p className="text-gray-500">Loading workout…</p>;
  if (isError) return <p className="text-red-500">Error: {(error as Error).message}</p>;
  if (!workout) return null;

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="sm" asChild>
          <Link to="/dashboard">← Back</Link>
        </Button>
        <h1 className="text-2xl font-bold">{workout.name}</h1>
        {workout.is_active && <Badge>Active</Badge>}
      </div>

      {workout.description && (
        <p className="text-gray-600 mb-6">{workout.description}</p>
      )}

      {workout.training_days.length === 0 ? (
        <p className="text-gray-400 italic">No training days configured.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {workout.training_days.map((day) => (
            <Card key={day.day_of_week}>
              <CardHeader>
                <CardTitle className="text-base">
                  {DAY_LABELS[day.day_of_week] ?? day.day_of_week}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {day.exercises.length === 0 ? (
                  <p className="text-sm text-gray-400">No exercises</p>
                ) : (
                  <ol className="space-y-1">
                    {day.exercises.map((ex) => (
                      <li key={ex.id} className="text-sm flex items-center gap-2">
                        <span className="text-gray-400 w-5 text-right">{ex.order}.</span>
                        <span className="font-mono text-xs bg-gray-100 rounded px-2 py-0.5">
                          {ex.exercise_id.slice(0, 8)}…
                        </span>
                      </li>
                    ))}
                  </ol>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
