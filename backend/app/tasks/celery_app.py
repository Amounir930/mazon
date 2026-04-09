"""
Celery Application Configuration
Sets up Celery worker and task routing
"""
from celery import Celery
from kombu import Queue
from app.config import get_settings

settings = get_settings()

# Create Celery application
celery_app = Celery(
    "crazy_lister",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.listing_tasks",
    ],
)

# Task routing configuration
celery_app.conf.task_routes = {
    "app.tasks.listing_tasks.submit_listing_task": {"queue": "listings"},
    "app.tasks.listing_tasks.check_feed_status_task": {"queue": "feeds"},
    "app.tasks.listing_tasks.sync_inventory_task": {"queue": "inventory"},
}

# Queue definitions
celery_app.conf.task_queues = (
    Queue("listings", routing_key="listing.#"),
    Queue("feeds", routing_key="feed.#"),
    Queue("inventory", routing_key="inventory.#"),
    Queue("default", routing_key="default.#"),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "main"
celery_app.conf.task_default_routing_key = "default.#"

# Worker configuration
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_max_tasks_per_child = 1000
celery_app.conf.worker_max_memory_per_child = 2000000  # 2GB

# Task execution settings
celery_app.conf.task_acks_late = True  # Acknowledge after task completion
celery_app.conf.task_reject_on_worker_lost = True  # Requeue on worker loss

# Retry settings
celery_app.conf.task_default_retry_delay = 60  # 1 minute
celery_app.conf.task_default_max_retries = 3

# Serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# Timezone
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# Task tracking
celery_app.conf.task_track_started = True

# Logging
celery_app.conf.worker_log_color = True
celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
