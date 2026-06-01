from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.training.workout_day_exercise import WorkoutDayExercise
        

@dataclass
class WorkoutDay:
    day_number: int
    title: str
    id: UUID = field(default_factory=uuid4)
    exercises: list[WorkoutDayExercise] = field(default_factory=list)

    def add_exercise(self, exercise: WorkoutDayExercise) -> None:
        if any(e.exercise_id == exercise.exercise_id for e in self.exercises):
            raise ValueError(f"Упражнение {exercise.exercise_id} уже добавлено в этот день")
        self.exercises.append(exercise)

    def remove_exercise(self, exercise_id: UUID) -> None:
        initial_len = len(self.exercises)
        self.exercises = [e for e in self.exercises if e.exercise_id != exercise_id]
        if len(self.exercises) == initial_len:
            raise ValueError("Упражнение не найдено в этом дне")
        

