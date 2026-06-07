from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import settings
from app.bl.entity_ops import EntityOps
from app.bl.relation_ops import RelationOps
from app.bl.summary_ops import SummaryOps
from app.celery_main import celery_app
from app.dal.app_db import SessionLocal
from app.dal.db_models import (
    Articles,
    ArticleSummary,
    ArticleWorkflowRuns,
    Entities,
    Relationships,
    WorkflowStepExecutions,
)

# initialized once per worker process
_entity_ops = EntityOps(settings.NLP)
_summary_ops = SummaryOps(settings.NLP)
_relation_ops = RelationOps(settings.NLP)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mark_running(db, step_exec_id: int, celery_task_id: str) -> WorkflowStepExecutions:
    step = db.get(WorkflowStepExecutions, step_exec_id)
    step.status = "running"
    step.celery_task_id = celery_task_id
    step.started_at = _now()
    db.flush()
    return step


def _mark_completed(db, step_exec_id: int) -> None:
    step = db.get(WorkflowStepExecutions, step_exec_id)
    step.status = "completed"
    step.completed_at = _now()
    db.flush()


def _mark_failed_and_skip_rest(db, run_id: int, step_exec_id: int, error: str) -> None:
    step = db.get(WorkflowStepExecutions, step_exec_id)
    step.status = "failed"
    step.error_message = error
    step.completed_at = _now()

    # skip all subsequent steps
    remaining = (
        db.query(WorkflowStepExecutions)
        .filter(
            WorkflowStepExecutions.run_id == run_id,
            WorkflowStepExecutions.step_order > step.step_order,
        )
        .all()
    )
    for s in remaining:
        s.status = "skipped"

    run = db.get(ArticleWorkflowRuns, run_id)
    run.status = "failed"
    run.completed_at = _now()

    article = db.get(Articles, run.article_id)
    article.pipeline_status = "failed"
    db.flush()


def _advance_workflow(db, run_id: int, current_step_order: int) -> None:
    """Dispatch next step or mark run complete — called after a step succeeds."""
    next_step = (
        db.query(WorkflowStepExecutions)
        .filter(
            WorkflowStepExecutions.run_id == run_id,
            WorkflowStepExecutions.step_order == current_step_order + 1,
        )
        .first()
    )

    if next_step:
        result = celery_app.send_task(
            next_step.celery_task_name,
            args=[run_id, next_step.step_exec_id],
        )
        next_step.celery_task_id = result.id
        db.flush()
    else:
        run = db.get(ArticleWorkflowRuns, run_id)
        run.status = "completed"
        run.completed_at = _now()
        article = db.get(Articles, run.article_id)
        article.pipeline_status = "completed"
        db.flush()


# ---------------------------------------------------------------------------
# Task 1: Summarize
# ---------------------------------------------------------------------------

@celery_app.task(name="pipeline.summarize", bind=True)
def pipeline_summarize(self, run_id: int, step_exec_id: int) -> None:
    db = SessionLocal()
    try:
        step = _mark_running(db, step_exec_id, self.request.id)
        config = step.config_snapshot or {}

        article = db.get(Articles, step.article_id)
        result = _summary_ops.summarize(article.body, n=config.get("n_sentences"))

        stmt = (
            pg_insert(ArticleSummary)
            .values(
                article_id=step.article_id,
                prop_name="extractive_summary",
                prop_value=result["summary"],
            )
            .on_conflict_do_update(
                constraint="article_summary_article_id_prop_name_key",
                set_={"prop_value": result["summary"], "updated_at": _now()},
            )
        )
        db.execute(stmt)

        _mark_completed(db, step_exec_id)
        _advance_workflow(db, run_id, step.step_order)
        db.commit()
        logger.info(f"[pipeline.summarize] article={step.article_id} run={run_id} done")
    except Exception as exc:
        db.rollback()
        _mark_failed_and_skip_rest(db, run_id, step_exec_id, str(exc))
        db.commit()
        logger.exception(f"[pipeline.summarize] article={step.article_id} run={run_id} failed")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 2: Entities
# ---------------------------------------------------------------------------

@celery_app.task(name="pipeline.entities", bind=True)
def pipeline_entities(self, run_id: int, step_exec_id: int) -> None:
    db = SessionLocal()
    try:
        step = _mark_running(db, step_exec_id, self.request.id)

        article = db.get(Articles, step.article_id)
        entities = _entity_ops.get_entities(article.body)

        for e in entities:
            stmt = (
                pg_insert(Entities)
                .values(
                    article_id=step.article_id,
                    entity_name=e["entity"],
                    entity_type=e["label"],
                )
                .on_conflict_do_update(
                    constraint="entities_article_id_entity_name_entity_type_key",
                    set_={"updated_at": _now()},
                )
            )
            db.execute(stmt)

        _mark_completed(db, step_exec_id)
        _advance_workflow(db, run_id, step.step_order)
        db.commit()
        logger.info(f"[pipeline.entities] article={step.article_id} run={run_id} saved {len(entities)} entities")
    except Exception as exc:
        db.rollback()
        _mark_failed_and_skip_rest(db, run_id, step_exec_id, str(exc))
        db.commit()
        logger.exception(f"[pipeline.entities] article={step.article_id} run={run_id} failed")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 3: Relations
# ---------------------------------------------------------------------------

@celery_app.task(name="pipeline.relations", bind=True)
def pipeline_relations(self, run_id: int, step_exec_id: int) -> None:
    db = SessionLocal()
    try:
        step = _mark_running(db, step_exec_id, self.request.id)
        config = step.config_snapshot or {}

        article = db.get(Articles, step.article_id)

        # build entity name → id map from what was persisted by the entities step
        entity_rows = (
            db.query(Entities)
            .filter(Entities.article_id == step.article_id)
            .all()
        )
        entity_map: dict[str, int] = {e.entity_name.lower(): e.entity_id for e in entity_rows}

        result = _relation_ops.get_relations(
            article.body,
            confidence=config.get("confidence_threshold", 0.6),
        )

        saved = 0
        for rel in result.get("relationships", []):
            subj_id = entity_map.get(rel["subj"].lower())
            obj_id = entity_map.get(rel["obj"].lower())
            if subj_id is None or obj_id is None:
                logger.warning(
                    f"[pipeline.relations] skipping triple ({rel['subj']} → {rel['obj']}): entity not in DB"
                )
                continue
            db.add(
                Relationships(
                    article_id=step.article_id,
                    subject_entity_id=subj_id,
                    object_entity_id=obj_id,
                    predicate=rel["verb"],
                    confidence=rel.get("confidence"),
                    evidence_span=rel.get("evidence_span"),
                )
            )
            saved += 1

        _mark_completed(db, step_exec_id)
        _advance_workflow(db, run_id, step.step_order)
        db.commit()
        logger.info(f"[pipeline.relations] article={step.article_id} run={run_id} saved {saved} relationships")
    except Exception as exc:
        db.rollback()
        _mark_failed_and_skip_rest(db, run_id, step_exec_id, str(exc))
        db.commit()
        logger.exception(f"[pipeline.relations] article={step.article_id} run={run_id} failed")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 4: Taxonomy
# ---------------------------------------------------------------------------

@celery_app.task(name="pipeline.taxonomy", bind=True)
def pipeline_taxonomy(self, run_id: int, step_exec_id: int) -> None:
    db = SessionLocal()

    try:
        step = _mark_running(db, step_exec_id, self.request.id)

        article = db.get(Articles, step.article_id)

        result = _taxonomy_ops.get_taxonomy(article.body)

        logger.info(
            f"[pipeline.taxonomy] "
            f"article={step.article_id} "
            f"result={result}"
        )

        # TODO:
        # Save taxonomy result to DB here

        _mark_completed(db, step_exec_id)
        _advance_workflow(db, run_id, step.step_order)

        db.commit()

    except Exception as exc:
        db.rollback()
        _mark_failed_and_skip_rest(
            db,
            run_id,
            step_exec_id,
            str(exc)
        )
        db.commit()

        logger.exception(
            f"[pipeline.taxonomy] article={step.article_id} run={run_id} failed"
        )

        raise

    finally:
        db.close()