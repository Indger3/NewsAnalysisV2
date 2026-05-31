from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dal.app_db import get_db
from app.dal.db_models import Articles
from app.utils.auth import get_current_user

router = APIRouter()


class ArticleIngestRequest(BaseModel):
    source: str
    url: str
    body: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    authors: Optional[list[str]] = None


@router.post("/ingest/article")
def ingest_article(
    body: ArticleIngestRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    words = len(body.body.split())
    article = Articles(
        source=body.source,
        url=body.url,
        body=body.body,
        title=body.title,
        published_at=body.published_at,
        language=body.language,
        authors=body.authors,
        word_count=words,
        reading_time_seconds=round(words / 3),  # ~200 wpm average reading speed
    )
    try:
        db.add(article)
        db.commit()
        db.refresh(article)
    except IntegrityError:
        db.rollback()
        return {"error": "article with this URL already exists"}

    return {"article_id": article.article_id, "word_count": article.word_count}
