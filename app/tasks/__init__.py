"""
Celery tasks para processamento assíncrono.
"""

from celery import Celery

from app.config import settings

# Criar aplicação Celery
celery_app = Celery(
    "biofouling_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configurações
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutos
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Auto-descoberta de tasks
celery_app.autodiscover_tasks([
    "app.tasks.ais_processor",
    "app.tasks.index_calculator",
    "app.tasks.alert_checker",
    "app.tasks.report_generator",
])

# Schedules para Celery Beat
celery_app.conf.beat_schedule = {
    "check-fleet-alerts-hourly": {
        "task": "app.tasks.alert_checker.check_fleet_alerts",
        "schedule": 3600.0,  # 1 hora
    },
    "calculate-fleet-indices-daily": {
        "task": "app.tasks.index_calculator.calculate_fleet_indices",
        "schedule": 86400.0,  # 24 horas
    },
    "update-environmental-metrics-hourly": {
        "task": "app.tasks.ais_processor.update_all_environmental_metrics",
        "schedule": 3600.0,  # 1 hora
    },
}
