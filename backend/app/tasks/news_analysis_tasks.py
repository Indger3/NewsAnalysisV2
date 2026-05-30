
import celery


@celery.Task
def summarize():
    return NotImplemented()