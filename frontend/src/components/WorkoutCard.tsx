import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import type { WorkoutResponse } from '../types/api';

const DAY_LABELS: Record<string, string> = {
  MONDAY: 'Mon', TUESDAY: 'Tue', WEDNESDAY: 'Wed',
  THURSDAY: 'Thu', FRIDAY: 'Fri', SATURDAY: 'Sat', SUNDAY: 'Sun',
};

export function WorkoutCard({ workout }: { workout: WorkoutResponse }) {
  return (
    <Link to={`/workouts/${workout.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader>
          <CardTitle className="text-lg">{workout.name}</CardTitle>
        </CardHeader>
        <CardContent>
          {workout.description && (
            <p className="text-sm text-gray-500 mb-3">{workout.description}</p>
          )}
          <div className="flex flex-wrap gap-2">
            {workout.training_days.map((d) => (
              <Badge key={d.day_of_week} variant="secondary">
                {DAY_LABELS[d.day_of_week] ?? d.day_of_week}
              </Badge>
            ))}
            {workout.training_days.length === 0 && (
              <span className="text-xs text-gray-400">No training days yet</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
