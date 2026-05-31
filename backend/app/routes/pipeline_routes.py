import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.celery_main import celery_app
from app.dal.app_db import get_db
from app.dal.db_models import (
    Articles,
    ArticleSummary,
    ArticleWorkflowRuns,
    Entities,
    Relationships,
    WorkflowStepExecutions,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

WORKFLOW_CONFIG_PATH = Path(__file__).parent.parent / "config" / "workflow.json"


def _load_workflow() -> dict:
    return json.loads(WORKFLOW_CONFIG_PATH.read_text())


def _step_dict(s: WorkflowStepExecutions) -> dict:
    return {
        "step_exec_id": s.step_exec_id,
        "step_order": s.step_order,
        "step_name": s.step_name,
        "celery_task_name": s.celery_task_name,
        "status": s.status,
        "error_message": s.error_message,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
    }


def _run_dict(run: ArticleWorkflowRuns) -> dict:
    return {
        "run_id": run.run_id,
        "workflow_name": run.workflow_name,
        "workflow_version": run.workflow_version,
        "status": run.status,
        "triggered_at": run.triggered_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "steps": [_step_dict(s) for s in sorted(run.workflow_step_executions, key=lambda x: x.step_order)],
    }


# ---------------------------------------------------------------------------
# List all articles with latest run status
# ---------------------------------------------------------------------------

@router.get("/articles")
def list_articles(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    articles = (
        db.query(Articles)
        .order_by(Articles.ingested_at.desc())
        .all()
    )

    article_ids = [a.article_id for a in articles]
    latest_runs: dict[int, ArticleWorkflowRuns] = {}

    if article_ids:
        runs = (
            db.query(ArticleWorkflowRuns)
            .filter(ArticleWorkflowRuns.article_id.in_(article_ids))
            .order_by(ArticleWorkflowRuns.triggered_at.desc())
            .options(selectinload(ArticleWorkflowRuns.workflow_step_executions))
            .all()
        )
        for run in runs:
            if run.article_id not in latest_runs:
                latest_runs[run.article_id] = run

    result = []
    for a in articles:
        run = latest_runs.get(a.article_id)
        result.append({
            "article_id": a.article_id,
            "title": a.title,
            "source": a.source,
            "url": a.url,
            "word_count": a.word_count,
            "language": a.language,
            "ingested_at": a.ingested_at.isoformat(),
            "pipeline_status": a.pipeline_status,
            "latest_run": _run_dict(run) if run else None,
        })

    return {"articles": result}


# ---------------------------------------------------------------------------
# Trigger pipeline for an article
# ---------------------------------------------------------------------------

@router.post("/articles/{article_id}/trigger")
def trigger_pipeline(
    article_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    article = db.get(Articles, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.pipeline_status == "running":
        raise HTTPException(status_code=409, detail="Pipeline already running for this article")

    workflow = _load_workflow()

    # clear prior analysis results (cascade deletes relationships via entities FK)
    db.query(ArticleSummary).filter(ArticleSummary.article_id == article_id).delete()
    db.query(Entities).filter(Entities.article_id == article_id).delete()

    article.pipeline_status = "running"

    run = ArticleWorkflowRuns(
        article_id=article_id,
        workflow_name=workflow["name"],
        workflow_version=workflow["version"],
        workflow_snapshot=workflow,
        status="running",
    )
    db.add(run)
    db.flush()  # populate run.run_id

    steps = []
    for step_def in sorted(workflow["steps"], key=lambda s: s["order"]):
        step = WorkflowStepExecutions(
            run_id=run.run_id,
            article_id=article_id,
            step_order=step_def["order"],
            step_name=step_def["name"],
            celery_task_name=step_def["task"],
            status="pending",
            config_snapshot=step_def.get("config"),
        )
        db.add(step)
        steps.append(step)

    db.flush()  # populate step_exec_ids

    # dispatch first step
    first = steps[0]
    task_result = celery_app.send_task(
        first.celery_task_name,
        args=[run.run_id, first.step_exec_id],
    )
    first.celery_task_id = task_result.id

    db.commit()

    return {
        "article_id": article_id,
        "run_id": run.run_id,
        "status": "running",
        "steps_queued": len(steps),
    }


# ---------------------------------------------------------------------------
# Poll status for a single article
# ---------------------------------------------------------------------------

@router.get("/articles/{article_id}/status")
def get_article_status(
    article_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    article = db.get(Articles, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    latest_run = (
        db.query(ArticleWorkflowRuns)
        .filter(ArticleWorkflowRuns.article_id == article_id)
        .order_by(ArticleWorkflowRuns.triggered_at.desc())
        .options(selectinload(ArticleWorkflowRuns.workflow_step_executions))
        .first()
    )

    return {
        "article_id": article_id,
        "pipeline_status": article.pipeline_status,
        "latest_run": _run_dict(latest_run) if latest_run else None,
    }


# ---------------------------------------------------------------------------
# Get article body
# ---------------------------------------------------------------------------

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    article = db.get(Articles, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "article_id": article.article_id,
        "title": article.title,
        "source": article.source,
        "url": article.url,
        "body": article.body,
        "authors": article.authors,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "word_count": article.word_count,
        "language": article.language,
    }


# ---------------------------------------------------------------------------
# Get persisted analysis results
# ---------------------------------------------------------------------------

@router.get("/articles/{article_id}/results")
def get_article_results(
    article_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    article = db.get(Articles, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    summary_row = (
        db.query(ArticleSummary)
        .filter(
            ArticleSummary.article_id == article_id,
            ArticleSummary.prop_name == "extractive_summary",
        )
        .first()
    )

    entities = (
        db.query(Entities)
        .filter(Entities.article_id == article_id)
        .all()
    )

    relationships = (
        db.query(Relationships)
        .filter(Relationships.article_id == article_id)
        .options(
            selectinload(Relationships.subject_entity),
            selectinload(Relationships.object_entity),
        )
        .all()
    )

    return {
        "article_id": article_id,
        "summary": summary_row.prop_value if summary_row else None,
        "entities": [
            {"entity": e.entity_name, "label": e.entity_type}
            for e in entities
        ],
        "relationships": [
            {
                "subj": r.subject_entity.entity_name,
                "verb": r.predicate,
                "obj": r.object_entity.entity_name,
                "confidence": r.confidence,
                "evidence_span": r.evidence_span,
            }
            for r in relationships
        ],
    }
