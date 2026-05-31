from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app import settings
from app.bl.entity_ops import EntityOps
from app.utils.auth import get_current_user

router = APIRouter()

entity_ops = EntityOps(settings.NLP)


class TextInput(BaseModel):
    text: str


class SummaryInput(BaseModel):
    text: str
    n: int | None = None


class RelationsInput(BaseModel):
    text: str
    confidence: float = 0.6


@router.post("/entities")
def get_entities(body: TextInput, _: dict = Depends(get_current_user)):
    entities = entity_ops.get_entities(body.text)
    return {"entities": entities}


@router.post("/summarize")
def get_summary(request: Request, body: SummaryInput, _: dict = Depends(get_current_user)):
    return request.app.state.summary_ops.summarize(body.text, n=body.n)


@router.post("/relations")
def get_relations(request: Request, body: RelationsInput, _: dict = Depends(get_current_user)):
    return request.app.state.relation_ops.get_relations(body.text, confidence=body.confidence)
