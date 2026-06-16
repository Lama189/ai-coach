import logging
from uuid import UUID
from typing import List
from pydantic import BaseModel


from app.application.dto.for_ai import (
    PlanningContext,
    ExerciseBundle,
    WorkoutProgramAI,
)

logger = logging.getLogger(__name__)


class ValidationError(BaseModel):
    code: str
    message: str


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationError]


class WorkoutProgramValidator:
    def __init__(self) -> None:
        pass


    def validate(
        self,
        program: WorkoutProgramAI,
        context: PlanningContext,
        exercises: ExerciseBundle
    ) -> ValidationResult:

        errors: list[ValidationError] = []

        allowed_ids = {ex.id for ex in exercises.exercises}

        errors += self._validate_uuid(allowed_ids, program)
        errors += self._check_duplicates(program)
        errors += self._check_days(context.experience_level, program)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
   

    def _validate_uuid(
        self,
        allowed_ids: set[UUID],
        program: WorkoutProgramAI
    ) -> list[ValidationError]:

        errors = []

        for d_i, day in enumerate(program.workout_days):
            for ex in day.exercises:
                if ex.exercise_id not in allowed_ids:
                    errors.append(
                        ValidationError(
                            code="INVALID_EXERCISE_ID",
                            message=f"Day {d_i}: exercise {ex.exercise_id} not in allowed set"
                        )
                    )

        return errors


    def _check_duplicates(self, program: WorkoutProgramAI) -> list[ValidationError]:
        errors = []
        used = set()

        for d_i, day in enumerate(program.workout_days):
            for ex in day.exercises:
                if ex.exercise_id in used:
                    errors.append(
                        ValidationError(
                            code="DUPLICATE_EXERCISE",
                            message=f"Duplicate exercise {ex.exercise_id}"
                        )
                    )
                used.add(ex.exercise_id)

        return errors


    def _check_days(
        self,
        level: str,
        program: WorkoutProgramAI
    ) -> list[ValidationError]:

        count = len(program.workout_days)

        allowed = {
            "beginner": {3},
            "intermediate": {3, 4},
            "advanced": {4, 5},
        }.get(level, set())

        if count not in allowed:
            return [
                ValidationError(
                    code="INVALID_DAYS_COUNT",
                    message=f"{level} must have {allowed}, got {count}"
                )
            ]

        return []