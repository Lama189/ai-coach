from app.application.interfaces.identity import IUserRepository
from app.application.interfaces.exercises import IExerciseRepository
from app.application.interfaces.program import IWorkoutProgramRepository
from app.application.interfaces.workout_day import IWorkoutDayRepository
from app.application.interfaces.workout_day_exercise import IWorkoutDayExerciseRepository
from app.application.interfaces.insights import IUserInsightRepository
from app.application.interfaces.intents import IUserIntentRepository
from app.application.interfaces.knowledge_document import IKnowledgeDocumentRepository
from app.application.interfaces.knowledge_chunk import IKnowledgeChunkRepository


class IUnitOfWork:
    users: IUserRepository
    exercises: IExerciseRepository
    programs: IWorkoutProgramRepository
    workout_days: IWorkoutDayRepository
    workout_days_exercise: IWorkoutDayExerciseRepository
    insights: IUserInsightRepository
    intents: IUserIntentRepository
    knowledge_documents: IKnowledgeDocumentRepository
    knowledge_chunks: IKnowledgeChunkRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
