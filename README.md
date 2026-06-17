# AI Coach

Персональный фитнес-тренер на базе ИИ. Генерирует индивидуальные программы тренировок с учётом профиля пользователя, его состояния и ограничений. Работает через REST API и Telegram-бот.

---

## Содержание

- [Описание](#описание)
- [Возможности](#возможности)
- [Стек технологий](#стек-технологий)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [API Endpoints](#api-endpoints)
- [База данных](#база-данных)
- [AI-пайплайн](#ai-пайплайн)
- [Telegram-бот](#telegram-бот)
- [Фоновые задачи](#фоновые-задачи)
- [Мониторинг](#мониторинг)
- [Тестирование](#тестирование)
- [Структура проекта](#структура-проекта)

---

## Описание

AI Coach — платформа для персонализированных тренировок. Система анализирует профиль пользователя (пол, возраст, вес, цель, уровень подготовки), его замечания и ограничения (травмы, усталость, предпочтения), а затем с помощью LLM генерирует структурированную программу тренировок с конкретными упражнениями, подходами и повторениями.

Для семантического поиска упражнений и пользовательских инсайтов используется pgvector + Sentence Transformers (all-MiniLM-L6-v2). Фоновая обработка (генерация программ, загрузка PDF, пакетное создание упражнений) выполняется через Celery + RabbitMQ.

---

## Возможности

- **Регистрация и авторизация** — JWT (access + refresh токены), валидация узбекских номеров (+998XXXXXXXXX)
- **Профиль пользователя** — пол, возраст, рост, вес, цель, уровень подготовки, локация (зал/дом/улица)
- **Управление упражнениями** — CRUD с векторными эмбеддингами для семантического поиска
- **Пользовательские инсайты** — тегированные заметки (травма, прогресс, усталость, предпочтение, расписание, питание, техника, ментальное состояние) с векторными эмбеддингами
- **Генерация программ ИИ** — персональная программа тренировок на основе профиля, инсайтов и ограничений пользователя
- **Ограничения пользователя** — автоматическое исключение упражнений по медицинским ограничениям (без нагрузки на плечо/колено, без становой, без штанги и др.)
- **Семантический поиск** — поиск похожих упражнений и инсайтов через векторное сходство
- **Загрузка базы знаний** — загрузка PDF с автоматическим разбиением на чанки, созданием эмбеддингов и хранением в PostgreSQL (RAG-подобный подход)
- **Telegram-бот** — регистрация, авторизация, создание инсайтов прямо из Telegram
- **Мониторинг** — Prometheus метрики, Grafana дашборды, Loki + Promtail для логов

---

## Стек технологий

| Компонент         | Технология                                              |
| ----------------- | ------------------------------------------------------- |
| Язык              | Python 3.12                                             |
| Web-фреймворк     | FastAPI                                                 |
| ORM               | SQLAlchemy (async)                                      |
| БД                | PostgreSQL 15 + pgvector                                |
| Кэширование       | Redis 7                                                 |
| Очередь задач     | Celery + RabbitMQ                                       |
| LLM               | Google Gemini (gemini-3.5-flash, gemini-3.1-flash-lite) |
| Эмбеддинги        | Sentence Transformers (all-MiniLM-L6-v2, 384d)          |
| Хранилище файлов  | MinIO (S3-совместимый)                                  |
| Telegram-бот      | aiogram 3                                               |
| Миграции          | Alembic                                                 |
| Мониторинг        | Prometheus + Grafana                                    |
| Логирование       | Loki + Promtail (JSON structured logging)               |
| PDF-парсинг       | PyPDF + langchain-text-splitters                        |
| Токенизация       | tiktoken                                                |
| Пакетный менеджер | uv                                                      |
| Контейнеризация   | Docker + Docker Compose                                 |

---

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Ключ API Google Gemini

### Запуск

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd ai-coach

# 2. Создать .env файл
cp .env.example .env
# Заполнить переменные (см. Конфигурация)

# 3. Запустить все сервисы
docker compose up -d

# 4. Проверить статус
docker compose ps
```

Сервисы:

- **API**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs
- **RabbitMQ UI**: http://localhost:15672 (guest/guest)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (admin/admin123456)

### Локальная разработка

```bash
# Установить зависимости
uv sync

# Запустить миграции
alembic upgrade head

# Запустить API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запустить Celery worker
celery -A app.application.workers.tasks.celery_app worker --loglevel=info

# Запустить Telegram-бота
python bot/main.py
```

---

## Конфигурация

### Переменные окружения (.env)

| Переменная         | Описание                     | Пример                                                          |
| ------------------ | ---------------------------- | --------------------------------------------------------------- |
| `DATABASE_URL`     | URL подключения к PostgreSQL | `postgresql+asyncpg://postgres:postgres@postgres:5432/ai_coach` |
| `REDIS_URL`        | URL подключения к Redis      | `redis://redis:6379/0`                                          |
| `SECRET_KEY`       | Секретный ключ для JWT       | `your-secret-key`                                               |
| `LLM_API_KEY`      | API ключ Google Gemini       | `your-gemini-api-key`                                           |
| `MINIO_ENDPOINT`   | Адрес MinIO                  | `minio:9000`                                                    |
| `MINIO_ACCESS_KEY` | Логин MinIO                  | `admin`                                                         |
| `MINIO_SECRET_KEY` | Пароль MinIO                 | `admin123456`                                                   |
| `MINIO_BUCKET`     | Имя бакета для файлов        | `knowledge`                                                     |
| `BOT_TOKEN`        | Токен Telegram-бота          | `your-telegram-bot-token`                                       |
| `DEBUG`            | Режим отладки                | `false`                                                         |

---

## API Endpoints

### Авторизация и профиль (`/api/v1/users`)

| Метод   | Путь                      | Описание                                         |
| ------- | ------------------------- | ------------------------------------------------ |
| `POST`  | `/register`               | Регистрация нового пользователя                  |
| `POST`  | `/login`                  | Авторизация (phone + password)                   |
| `POST`  | `/refresh`                | Обновление access токена                         |
| `POST`  | `/logout`                 | Выход (инвалидация токенов)                      |
| `GET`   | `/telegram/{telegram_id}` | Получить пользователя по Telegram ID             |
| `GET`   | `/exists/phone/{phone}`   | Проверить существование номера                   |
| `GET`   | `/{user_id}`              | Получить пользователя по UUID                    |
| `PATCH` | `/profile`                | Обновить профиль (пол, возраст, вес, цель и др.) |

### Упражнения (`/api/v1/exercises`)

| Метод    | Путь             | Описание                                           |
| -------- | ---------------- | -------------------------------------------------- |
| `POST`   | `/`              | Создать упражнение (с генерацией эмбеддинга)       |
| `DELETE` | `/{exercise_id}` | Удалить упражнение                                 |
| `POST`   | `/batch`         | Пакетное создание упражнений (async, через Celery) |

### Программы (`/api/v1/programs`)

| Метод  | Путь         | Описание                                                     |
| ------ | ------------ | ------------------------------------------------------------ |
| `POST` | `/`          | Создать программу вручную                                    |
| `POST` | `/generate`  | Сгенерировать программу через ИИ (async, возвращает task_id) |
| `GET`  | `/{user_id}` | Получить активную программу пользователя                     |

### Инсайты (`/api/v1/insights`)

| Метод  | Путь | Описание                                                                                        |
| ------ | ---- | ----------------------------------------------------------------------------------------------- |
| `POST` | `/`  | Создать инсайт с тегом (injury/progress/fatigue/preference/schedule/nutrition/technique/mental) |

### База знаний (`/api/v1/knowledge`)

| Метод  | Путь      | Описание                                                         |
| ------ | --------- | ---------------------------------------------------------------- |
| `POST` | `/upload` | Загрузить PDF (async: парсинг → чанкинг → эмбеддинги → хранение) |

### Системные

| Метод | Путь       | Описание           |
| ----- | ---------- | ------------------ |
| `GET` | `/`        | Health check       |
| `GET` | `/metrics` | Prometheus метрики |
| `GET` | `/docs`    | Swagger UI         |

---

## База данных

### Модели

| Модель               | Таблица                 | Описание                                                                 |
| -------------------- | ----------------------- | ------------------------------------------------------------------------ |
| `User`               | `users`                 | Пользователь (id, telegram_id, username, phone, password_hash)           |
| `UserProfile`        | `user_profiles`         | Профиль (gender, age, height, weight, goal, experience_level, location)  |
| `Exercise`           | `exercises`             | Упражнение (name, muscle_group, equipment, movement_patterns, embedding) |
| `WorkoutProgram`     | `workout_programs`      | Программа тренировок                                                     |
| `WorkoutDay`         | `workout_days`          | День тренировки                                                          |
| `WorkoutDayExercise` | `workout_day_exercises` | Упражнение в дне (sets, reps, rest)                                      |
| `Session`            | `sessions`              | Сессия тренировки                                                        |
| `ExerciseSet`        | `exercise_sets`         | Подход (weight, reps, rpe)                                               |
| `UserInsight`        | `user_insights`         | Инсайт пользователя (content, tag, embedding)                            |
| `UserIntentModel`    | `user_intents`          | Извлечённое намерение (goal, constraints, focus_areas)                   |
| `KnowledgeDocument`  | `knowledge_documents`   | Загруженный документ                                                     |
| `KnowledgeChunk`     | `knowledge_chunks`      | Чанк документа (content, embedding, token_count)                         |

### Связи

```
User 1──1 UserProfile
User 1──N WorkoutProgram
User 1──N Session
User 1──N UserInsight
User 1──N UserIntent
WorkoutProgram 1──N WorkoutDay
WorkoutDay 1──N WorkoutDayExercise ──N──1 Exercise
Session 1──N ExerciseSet ──N──1 Exercise
KnowledgeDocument 1──N KnowledgeChunk
```

---

## AI-пайплайн

### Генерация программы

```
Запрос пользователя
        │
        ▼
┌─────────────────────┐
│  Извлечение Intent   │  Gemini flash-lite → goal, constraints, focus_areas, location
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Контекст пользователя│  Профиль + инсайты (hard/context/preferences/semantic)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Поиск упражнений    │  По muscle_group + исключение по constraints + cosine similarity
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Генерация программы │  Gemini flash → WorkoutProgramAI (structured JSON)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Валидация           │  UUID проверка, дубликаты, количество дней по уровню
└──────────┬──────────┘
           │
           ▼
       Сохранение
```

### Инсайты и семантический поиск

- Каждый инсайт получает векторный эмбеддинг (384d)
- При генерации программы инсайты категоризируются:
  - **Hard** — injury, fatigue (обязательные ограничения)
  - **Context** — schedule, mental (контекстные)
  - **Preferences** — preference, technique (предпочтения)
  - **Semantic** — cosine similarity поиск похожих инсайтов

### Ограничения

| Ограничение           | Исключённые паттерны         |
| --------------------- | ---------------------------- |
| `no_overhead`         | push_vertical                |
| `no_shoulder_load`    | push_vertical, pull_vertical |
| `no_knee_load`        | squat, lunge                 |
| `no_hinge`            | hinge                        |
| `no_horizontal_press` | push_horizontal              |
| `no_carry`            | carry                        |
| `no_barbell`          | barbell equipment            |

### База знаний (RAG)

1. PDF загружается в MinIO
2. Извлекается текст через PyPDF
3. Разбивается на чанки (500 символов, 200 перекрытие)
4. Генерируются эмбеддинги для каждого чанка
5. Сохраняется документ + чанки в PostgreSQL с pgvector

---

## Telegram-бот

| Команда    | Описание                                          |
| ---------- | ------------------------------------------------- |
| `/start`   | Приветственное сообщение                          |
| `/auth`    | Авторизация/регистрация (номер телефона → пароль) |
| `/insight` | Создание инсайта (выбор тега → ввод текста)       |

Особенности:

- FSM (машина состояний) через Redis
- Автоматическая нормализация номеров (+998XXXXXXXXX)
- HTTP-клиент с retry-логикой (3 попытки при 5xx/timeout)
- Автообновление токена при 401

---

## Фоновые задачи

| Задача                  | Описание                                                 |
| ----------------------- | -------------------------------------------------------- |
| `add_exercises_batch`   | Пакетное создание упражнений с эмбеддингами              |
| `generate_workout_task` | Полный AI-пайплайн генерации программы                   |
| `upload_pdf_task`       | Обработка PDF: парсинг → чанкинг → эмбеддинги → хранение |

---

## Мониторинг

### Метрики (Prometheus)

| Метрика                         | Тип       | Описание                  |
| ------------------------------- | --------- | ------------------------- |
| `http_requests_total`           | Counter   | Количество HTTP-запросов  |
| `http_request_duration_seconds` | Histogram | Время обработки запросов  |
| `llm_tokens_used_total`         | Counter   | Использованные токены LLM |
| `llm_requests_total`            | Counter   | Запросы к LLM             |
| `llm_request_duration_seconds`  | Histogram | Время ответа LLM          |

### Стек

- **Prometheus** — сбор метрик (скрейпинг каждые 15 сек)
- **Grafana** — дашборды и алерты
- **Loki** — агрегация логов
- **Promtail** — доставка логов из Docker-контейнеров

---

## Тестирование

```bash
# Все тесты
pytest

# Только unit-тесты
pytest tests/backend/unit/

# Только integration-тесты
pytest tests/backend/integration/

# С coverage
pytest --cov=app --cov-report=html
```

### Структура тестов

```
tests/backend/
├── conftest.py                    # Фикстуры (sample_user, mock_uow и др.)
├── unit/services/                 # Unit-тесты сервисов (mock UoW)
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_exercise_service.py
│   ├── test_program_service.py
│   ├── test_insight_service.py
│   └── test_intent_service.py
└── integration/
    ├── api/                       # Интеграционные тесты роутеров
    │   ├── test_users_router.py
    │   ├── test_exercises_router.py
    │   ├── test_programs_router.py
    │   └── test_insights_router.py
    └── repos/                     # Интеграционные тесты репозиториев
        ├── test_user_repository.py
        ├── test_exercise_repository.py
        ├── test_program_repository.py
        ├── test_workout_day_repository.py
        ├── test_workout_day_exercise_repository.py
        ├── test_insight_repository.py
        ├── test_intent_repository.py
        └── test_session_repository.py
```

---

## Структура проекта

```
ai-coach/
├── alembic/                       # Миграции БД
├── app/                           # FastAPI приложение
│   ├── main.py                    # Точка входа, lifespan, роутеры
│   ├── api/v1/
│   │   ├── middlewares/           # Middleware (request-id)
│   │   └── routes/               # API эндпоинты
│   ├── application/
│   │   ├── ai/                   # AI-компоненты (генератор, валидатор, контекст)
│   │   ├── dependencies.py       # DI-контейнер
│   │   ├── dto/                  # Data Transfer Objects
│   │   ├── interfaces/           # Абстракции репозиториев и сервисов
│   │   ├── policies/             # Бизнес-политики (ограничения упражнений)
│   │   ├── services/             # Бизнес-логика
│   │   ├── use_cases/            # Use cases (загрузка документов)
│   │   └── workers/              # Celery-задачи и пайплайны
│   ├── core/                     # Конфигурация, безопасность, логирование, метрики
│   ├── domain/                   # Доменные модели и enum'ы
│   │   ├── enums.py
│   │   ├── identity/             # User, UserProfile, Insight, Intent
│   │   ├── training/             # Exercise, Program, Session, WorkoutDay
│   │   └── knowledge/            # Document, Chunk
│   └── infrastructure/           # Реализации инфраструктуры
│       ├── ai/                   # Embedding service
│       ├── postgres/             # SQLAlchemy модели, репозитории, UoW
│       ├── redis/                # Кэширование, токены
│       ├── storage/              # MinIO клиент
│       └── logging/              # Декораторы логирования
├── bot/                           # Telegram-бот
│   ├── main.py                   # Точка входа бота
│   ├── api/                      # HTTP-клиент к API
│   ├── routers/                  # Хэндлеры команд
│   ├── states/                   # FSM состояния
│   ├── keyboards/                # Клавиатуры
│   └── usecases/                 # Use cases бота
├── data/
│   └── exercises.json            # Seed-данные (~100+ упражнений)
├── monitoring/                    # Конфиги Prometheus, Loki, Promtail
├── tests/                         # Unit и integration тесты
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

---

## Лицензия

Proprietary — All rights reserved.
