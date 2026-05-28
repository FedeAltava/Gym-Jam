import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent } from '../components/ui/card';
import { useCreateWorkout } from '../hooks/useWorkouts';

const DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'];
const DAY_LABELS: Record<string, string> = {
  MONDAY: 'Monday', TUESDAY: 'Tuesday', WEDNESDAY: 'Wednesday',
  THURSDAY: 'Thursday', FRIDAY: 'Friday', SATURDAY: 'Saturday', SUNDAY: 'Sunday',
};

const createWorkoutSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().max(500).optional(),
  training_days: z.array(z.string()),
});
type CreateWorkoutForm = z.infer<typeof createWorkoutSchema>;

export function NewWorkoutPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, control, formState: { errors } } = useForm<CreateWorkoutForm>({
    resolver: zodResolver(createWorkoutSchema),
    defaultValues: { training_days: [] },
  });
  const createMutation = useCreateWorkout();

  function onSubmit(data: CreateWorkoutForm) {
    createMutation.mutate(
      { name: data.name, description: data.description, training_days: data.training_days },
      { onSuccess: (w) => navigate(`/workouts/${w.id}`) }
    );
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">New Workout</h1>
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <Label htmlFor="name">Workout name *</Label>
              <Input id="name" {...register('name')} placeholder="e.g. Push Day" />
              {errors.name && <p className="text-sm text-red-500 mt-1">{errors.name.message}</p>}
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" {...register('description')} placeholder="Optional description…" />
            </div>
            <div>
              <Label className="mb-2 block">Training days</Label>
              <Controller
                name="training_days"
                control={control}
                render={({ field }) => (
                  <div className="grid grid-cols-2 gap-2">
                    {DAYS.map((day) => (
                      <label key={day} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={field.value.includes(day)}
                          onChange={(e) => {
                            if (e.target.checked) field.onChange([...field.value, day]);
                            else field.onChange(field.value.filter((d: string) => d !== day));
                          }}
                          className="rounded"
                        />
                        <span className="text-sm">{DAY_LABELS[day]}</span>
                      </label>
                    ))}
                  </div>
                )}
              />
            </div>
            {createMutation.isError && (
              <p className="text-sm text-red-500">{(createMutation.error as Error).message}</p>
            )}
            <div className="flex gap-3">
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating…' : 'Create Workout'}
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate('/dashboard')}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
