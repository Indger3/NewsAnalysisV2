from celery import Celery

import settings

# RabbitMQ as the Broker
broker_url = "amqp://guest:guest@localhost:5672//"

# PostgreSQL as the Result Backend
# Format: db+postgresql://user:password@localhost:port/dbname
result_backend = settings.APP_DB_CONN

celery_app = Celery(
    "worker", 
    broker=broker_url, 
    backend=result_backend
)

celery_app.conf.update(
    # Optional: If you want Celery to create the tables automatically
    database_table_names={
        'task': 'celery_taskmeta',
        'group': 'celery_groupmeta',
    },
)