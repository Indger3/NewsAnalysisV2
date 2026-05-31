from celery import Celery

import app.settings as settings

# RabbitMQ as the Broker
broker_url = "amqp://guest:guest@localhost:5672//"

# PostgreSQL as the Result Backend
# Format: db+postgresql://user:password@localhost:port/dbname
result_backend = settings.APP_DB_CONN

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.pipeline_tasks",
        "app.tasks.news_analysis_tasks",
    ],
)

celery_app.conf.update(
    database_table_names={
        'task': 'celery_taskmeta',
        'group': 'celery_groupmeta',
    },
    # RabbitMQ 4.x rejects transient non-exclusive queues by default. The
    # remote-control (pidbox) consumer declares exactly such a queue at startup,
    # so disable it to keep the worker bootable. Disables `celery inspect/control`.
    worker_enable_remote_control=False,
)