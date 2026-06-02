import logging
from typing import Annotated, TypedDict
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.application.dto.for_ai import (
    SearchExercisesBatchInput,
    CreateExercisesBatchInput,
    CreateExerciseInput,
    WorkoutProgramAI,
)
from app.application.dto.program import (
    WorkoutProgramResponse,
    WorkoutDayResponse,
    WorkoutDayExerciseResponse,
)
from app.domain.enums import MuscleGroup
from app.domain.training.exercise import Exercise
from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.infrastructure.postgres.unit_of_work import IUnitOfWork


logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: UUID
    program: WorkoutProgramAI | None


class AIService:
    def __init__(self, uow: IUnitOfWork, api_key: str):
        self._uow = uow
        self._llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        self._tools = self._build_tools()
        self._llm_with_tools = self._llm.bind_tools(self._tools)
        self._structured_llm = self._llm.with_structured_output(WorkoutProgramAI)
        self._graph = self._build_graph()


    async def _build_prompt(self, user_id: UUID) -> str:
        user = await self._uow.users.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        profile = user.profile
        if profile is None:
            raise ValueError("Профиль пользователя отсутствует")

        return f"""
                Ты элитный персональный фитнес-тренер.

                Профиль клиента:

                Имя: {user.username}
                Пол: {profile.gender.value}
                Возраст: {profile.age}
                Рост: {profile.height_cm}
                Вес: {profile.weight_kg}
                Цель: {profile.goal.value}
                Уровень подготовки: {profile.experience_level.value}

                Правила работы:

                1. Используй только упражнения, полученные из инструментов.
                2. Перед составлением программы вызови search_exercises_batch со списком всех нужных упражнений сразу.
                3. Если каких-то упражнений нет — вызови create_exercises_batch со списком всех недостающих упражнений сразу.
                4. Используй UUID только из результатов инструментов.
                5. Никогда не придумывай UUID самостоятельно.
                6. Группируй упражнения в один вызов инструмента, не вызывай инструменты по одному.
                7. Когда все упражнения найдены — заверши работу с инструментами и составь программу.

                Допустимые значения muscle_group (строго lowercase):
                chest, back, legs, shoulders, biceps, triceps, core, full_body, cardio
                """


    def _build_tools(self):
        @tool(args_schema=SearchExercisesBatchInput, description="Найти несколько упражнений в базе данных за один вызов.")
        async def search_exercises_batch(queries: list[str]) -> str:
            lines = []

            for query in queries:
                exercises = await self._uow.exercises.search(query=query, limit=5)
                if not exercises:
                    lines.append(f"[{query}] не найдено")
                    continue
                for e in exercises:
                    lines.append(f"[{query}] id={e.id} | name={e.name} | muscle_group={e.muscle_group.value}")
            return "\n".join(lines) if lines else "Ничего не найдено"

        @tool(args_schema=CreateExercisesBatchInput, description="Создать несколько упражнений за один вызов. UUID генерируются автоматически.")
        async def create_exercises_batch(exercises: list[CreateExerciseInput]) -> str:
            results = []

            for ex in exercises:
                existing = await self._uow.exercises.get_by_name(ex.name)
                if existing:
                    results.append(f"id={existing.id} | name={existing.name}")
                    continue

                exercise = Exercise(
                    name=ex.name,
                    muscle_group=MuscleGroup(ex.muscle_group.lower()),
                    description=ex.description,
                )
                await self._uow.exercises.save_exercise(exercise)
                results.append(f"id={exercise.id} | name={exercise.name}")

            await self._uow.commit()
            return "\n".join(results)

        return [search_exercises_batch, create_exercises_batch]


    async def _agent_node(self, state: AgentState) -> dict:
        response = await self._llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}


    async def _generate_node(self, state: AgentState) -> dict:
        program = await self._structured_llm.ainvoke(state["messages"])
        return {"program": program}


    def _should_continue(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "generate"


    def _build_graph(self):
        tool_node = ToolNode(self._tools)

        graph = StateGraph(AgentState)

        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", tool_node)
        graph.add_node("generate", self._generate_node)

        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "generate": "generate",
            },
        )
        graph.add_edge("tools", "agent")
        graph.add_edge("generate", END)

        return graph.compile()


    async def generate_workout(self, user_id: UUID) -> WorkoutProgramResponse:
        system_prompt = await self._build_prompt(user_id)

        initial_state: AgentState = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=(
                    "Составь программу тренировок. "
                    "Сначала найди все нужные упражнения одним вызовом search_exercises_batch. "
                    "Недостающие создай одним вызовом create_exercises_batch. "
                    "Затем составь программу используя реальные UUID."
                )),
            ],
            "user_id": user_id,
            "program": None,
        }

        result = await self._graph.ainvoke(initial_state)

        program: WorkoutProgramAI = result["program"]
        if program is None:
            raise ValueError("Модель не вернула программу")

        domain_program = self._map_to_domain(user_id, program)

        await self._uow.programs.save(domain_program)
        await self._uow.commit()

        return self._map_to_response(domain_program)


    def _map_to_domain(self, user_id: UUID, response: WorkoutProgramAI) -> WorkoutProgram:
        program = WorkoutProgram(
            user_id=user_id,
            name=response.name,
            description=response.description,
            is_active=True,
        )

        for day_dto in response.workout_days:
            day = WorkoutDay(
                day_number=day_dto.day_number,
                title=day_dto.title,
            )
            for exercise_dto in day_dto.exercises:
                exercise = WorkoutDayExercise(
                    exercise_id=exercise_dto.exercise_id,
                    sets=exercise_dto.sets,
                    reps=exercise_dto.reps,
                    rest_seconds=exercise_dto.rest_seconds,
                )
                day.add_exercise(exercise)
            program.add_day(day)

        return program


    def _map_to_response(self, program: WorkoutProgram) -> WorkoutProgramResponse:
        return WorkoutProgramResponse(
            id=program.id,
            user_id=program.user_id,
            name=program.name,
            description=program.description,
            is_active=program.is_active,
            workout_days=[
                WorkoutDayResponse(
                    id=day.id,
                    day_number=day.day_number,
                    title=day.title,
                    exercises=[
                        WorkoutDayExerciseResponse(
                            id=exercise.id,
                            exercise_id=exercise.exercise_id,
                            sets=exercise.sets,
                            reps=exercise.reps,
                            rest_seconds=exercise.rest_seconds,
                        )
                        for exercise in day.exercises
                    ],
                )
                for day in program.workout_days
            ],
        )