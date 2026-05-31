from app.celery_main import celery_app
from app import settings
from app.bl.entity_ops import EntityOps
from app.bl.summary_ops import SummaryOps
from app.bl.relation_ops import RelationOps

# initialized once per worker process — not per task call
_entity_ops = EntityOps(settings.NLP)
_summary_ops = SummaryOps(settings.NLP)
_relation_ops = RelationOps(settings.NLP)


@celery_app.task(name="news_analysis.get_entities")
def get_entities(text: str) -> dict:
    return {"entities": _entity_ops.get_entities(text)}


@celery_app.task(name="news_analysis.summarize")
def summarize(text: str, n: int | None = None) -> dict:
    return _summary_ops.summarize(text, n=n)


@celery_app.task(name="news_analysis.get_relations")
def get_relations(text: str, confidence: float = 0.6) -> dict:
    return _relation_ops.get_relations(text, confidence=confidence)
