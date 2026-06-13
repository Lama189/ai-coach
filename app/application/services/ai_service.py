import time
import logging
from typing import Annotated, TypedDict, Callable, AsyncContextManager
from uuid import UUID

from langchain_core.messages import (
    AIMessage, 
    BaseMessage, 
    HumanMessage, 
    SystemMessage, 
    ToolMessage
)
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.core.metrics import llm_requests_total, llm_tokens_used, llm_request_duration
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
    GenerateProgram
)
from app.domain.enums import MuscleGroup
from app.domain.training.exercise import Exercise
from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService


logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: UUID
    program: WorkoutProgramAI | None


class AIService:
    def __init__(self, 
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]],
        embedder: SentenceTransformerEmbeddingService, 
        api_key: str
    ):
        self._uow_factory = uow_factory
        self._embedder = embedder
        self._llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        self._tools = self._build_tools()
        self._graph = self._build_graph()


    async def _build_prompt(self, dto: GenerateProgram) -> str:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by(id=dto.user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            profile = user.profile
            if profile is None:
                raise ValueError("Профиль пользователя отсутствует")
            
            if profile.is_complete:
                assert profile.gender is not None
                assert profile.goal is not None
                assert profile.experience_level is not None

                username = user.username
                gender_val = profile.gender.value
                age = profile.age
                height = profile.height_cm
                weight = profile.weight_kg
                goal_val = profile.goal.value
                exp_val = profile.experience_level.value
            else:
                raise ValueError("Профиль полностью не заполнен")

        prompt = f"""
                Ты элитный персональный фитнес-тренер.

                Профиль клиента:
                Имя: {username}
                Пол: {gender_val}
                Возраст: {age}
                Рост: {height}
                Вес: {weight}
                Цель: {goal_val}
                Уровень подготовки: {exp_val}

                Правила работы:
                1. Используй только упражнения, полученные из инструментов.
                2. Перед составлением программы вызови search_exercises_batch со списком всех нужных упражнений сразу.
                3. Если каких-то упражнений нет — вызови create_exercises_batch со списком всех недостающих упражнений сразу.
                4. Используй UUID только из результатов инструментов.
                5. Никогда не придумывай UUID самостоятельно.
                6. Группируй упражнения в один вызов инструмента, не вызывай инструменты по одному.
                7. Когда все упражнения найдены — заверши работу с инструментами и составь программу.

                Правила именования упражнений:
                - Только английский язык
                - Title Case: каждое слово с заглавной буквы (Bench Press, Pull Up, Bicep Curl)
                - Без дефисов: "Pull Up" не "Pull-ups", "Push Up" не "Push-up"
                - Без множественного числа: "Pull Up" не "Pull Ups", "Squat" не "Squats"
                - Без лишних слов: "Bench Press" не "Barbell Flat Bench Press"

                Название дня должно отражать группы мышц: "Legs and Back", "Chest and Triceps", не "Day 1"

                Количество тренировочных дней в неделю:
                - beginner:     3 дня
                - intermediate: 3-4 дня  
                - advanced:     4-5 дней

                Правила составления программы:
                - beginner:     3-4 упражнения в день
                - intermediate: 4-5 упражнений в день
                - advanced:     5-6 упражнений в день
                - Минимум упражнений в день — 3, исключений нет

                Если пользователь указал на боль или дискомфорт в суставе/мышце —
                ИСКЛЮЧИ упражнения на эту группу полностью.
                Боль — это не "меньше нагрузки", это "не трогать вообще".

                Не повторяй одинаковые упражнения в разные дни одной недели.
                Каждое упражнение должно встречаться максимум один раз в программе.

                Допустимые значения muscle_group (строго lowercase):
                chest, back, legs, shoulders, biceps, triceps, core, full_body, cardio
                """
        
        if dto.content:
            importance_map = {
                "low": "Прими во внимание, но не обязательно строго следуй",
                "medium": "Старайся учитывать при составлении программы",
                "high": "Обязательно учти, это приоритет при составлении",
            }
            instruction = importance_map.get(dto.importance, importance_map["medium"])

            prompt += f"""
                        Пожелания клиента ({instruction}):
                        {dto.content}   
                        """
        return prompt
    

    def _build_tools(self):
        @tool(args_schema=SearchExercisesBatchInput, description="Найти несколько упражнений в базе данных за один вызов.")
        async def search_exercises_batch(queries: list[str]) -> str:
            lines = []

            async with self._uow_factory() as uow:
                for query in queries:
                    exercises = await uow.exercises.search(query=query, limit=5)
                    if not exercises:
                        lines.append(f"[{query}] не найдено")
                        continue
                    for e in exercises:
                        lines.append(f"[{query}] id={e.id} | name={e.name} | muscle_group={e.muscle_group.value}")
            return "\n".join(lines) if lines else "Ничего не найдено"

        @tool(args_schema=CreateExercisesBatchInput, description="Создать несколько упражнений за один вызов. UUID генерируются автоматически.")
        async def create_exercises_batch(exercises: list[CreateExerciseInput]) -> str:
            results = []

            async with self._uow_factory() as uow:
                for ex in exercises:
                    existing = await uow.exercises.get_by(name=ex.name)
                    if existing:
                        results.append(f"id={existing.id} | name={existing.name}")
                        continue

                    embedding = await self._embedder.get_embedding(f"{ex.name} {ex.muscle_group}")
                    similar = await uow.exercises.find_familiar(embedding)
                    if similar:
                        results.append(f"id={similar.id} | name={similar.name}")
                        continue

                    exercise = Exercise(
                        name=ex.name,
                        muscle_group=MuscleGroup(ex.muscle_group.lower()),
                        description=ex.description,
                    )
                    await uow.exercises.save_exercise(exercise, embedding)
                    results.append(f"id={exercise.id} | name={exercise.name}")

                await uow.commit()
            return "\n".join(results)

        return [search_exercises_batch, create_exercises_batch]


    async def _agent_node(self, state: AgentState) -> dict:
        start = time.time()
        llm_with_tools = self._llm.bind_tools(self._tools)
        try:
            response = await llm_with_tools.ainvoke(state["messages"])

            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.get("input_tokens", 0)
                output_tokens = response.usage_metadata.get("output_tokens", 0)
                llm_tokens_used.labels(node="agent").inc(input_tokens + output_tokens)
                logger.debug(f"[agent_node] input={input_tokens} output={output_tokens}")

            llm_requests_total.labels(node="agent", status="success").inc()
            return {"messages": [response]}
        
        except Exception as e:
            llm_requests_total.labels(node="agent", status="error").inc()
            raise
        finally:
            llm_request_duration.labels(node="agent").observe(time.time() - start)


    async def _generate_node(self, state: AgentState) -> dict:
        start = time.time()
        structured_llm = self._llm.with_structured_output(WorkoutProgramAI, method="json_mode")
        try:
            system_msg = state["messages"][0]
            raw_results = "\n".join(
                msg.content if isinstance(msg.content, str) else str(msg.content)
                for msg in state["messages"]
                if isinstance(msg, ToolMessage) and msg.content
            )

            clean_messages = [
                system_msg,
                HumanMessage(content=(
                    f"Доступные упражнения для программы:\n"
                    f"{raw_results}\n\n"
                    "Правила финальной генерации:\n"
                    "1. Используй ТОЛЬКО UUID из списка выше в поле exercise_id\n"
                    "2. Каждый день минимум 4-5 упражнений (для advanced)\n"
                    "3. rest_seconds обязателен:\n"
                    "   - lose_weight: 30-45 сек\n"
                    "   - gain_muscle: 60-90 сек\n"
                    "   - endurance: 20-30 сек\n"
                    "   - maintenance: 45-60 сек\n"
                    "4. Строго следуй пожеланиям клиента из системного промпта\n"
                    "5. Не повторяй одинаковые упражнения в разные дни\n\n"
                    "Верни ответ строго в формате JSON со следующей структурой:\n"
                    "{\n"
                    '  "name": "название программы",\n'
                    '  "description": "описание программы",\n'
                    '  "workout_days": [\n'
                    "    {\n"
                    '      "day_number": 1,\n'
                    '      "title": "Legs and Back",\n'
                    '      "exercises": [\n'
                    "        {\n"
                    '          "exercise_id": "uuid-из-списка-выше",\n'
                    '          "sets": 4,\n'
                    '          "reps": 8,\n'
                    '          "rest_seconds": 90\n'
                    "        }\n"
                    "      ]\n"
                    "    }\n"
                    "  ]\n"
                    "}"
                )),
            ]

            program = await structured_llm.ainvoke(clean_messages)

            estimated_tokens = sum(len(str(m.content)) for m in clean_messages) // 4
            llm_tokens_used.labels(node="generate").inc(estimated_tokens)
            logger.debug(f"[generate_node] estimated_tokens={estimated_tokens}")

            llm_requests_total.labels(node="generate", status="success").inc()
            return {"program": program}
        
        except Exception as e:
            llm_requests_total.labels(node="generate", status="error").inc()
            raise
        finally:
            llm_request_duration.labels(node="generate").observe(time.time() - start)


    def _should_continue(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "generate"


    async def _sequential_tool_node(self, state: AgentState) -> dict:
        last_message = state["messages"][-1]
        
    
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            logger.warning(f"[_sequential_tool_node] Получено сообщение без tool_calls: {type(last_message)}")
            return {"messages": []}

        outputs = []
        tools_map = {tool.name: tool for tool in self._tools}
        
        for tool_call in last_message.tool_calls:
            tool_obj = tools_map[tool_call["name"]]
            tool_output = await tool_obj.ainvoke(tool_call)
            outputs.append(tool_output)
            
        return {"messages": outputs}


    def _build_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self._sequential_tool_node)  
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


    async def generate_workout(self, dto: GenerateProgram, task_id: UUID | None = None) -> WorkoutProgramResponse:
        system_prompt = await self._build_prompt(dto)

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
            "user_id": dto.user_id,
            "program": None,
        }

        result = await self._graph.ainvoke(initial_state)

        program: WorkoutProgramAI = result["program"]
        if program is None:
            raise ValueError("Модель не вернула программу")

        domain_program = self._map_to_domain(dto.user_id, program)

        async with self._uow_factory() as uow:
            await uow.programs.deactivate_all_for_user(dto.user_id)
            await uow.programs.save(domain_program, task_id)
            
            for day in domain_program.workout_days:
                await uow.workout_days.save(day, domain_program.id)

                for ex in day.exercises:
                    await uow.workout_days_exercise.save(ex, day.id)

            await uow.commit()
            
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