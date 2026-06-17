from celery import Celery

celery_app = Celery('ai_coach_workers', broker="amqp://guest:123@rabbitmq:5672//")