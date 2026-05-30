from fastapi import APIRouter
from pydantic import BaseModel
from app import settings
from app.bl.entity_ops import EntityOps

router = APIRouter()

entity_ops = EntityOps(settings.NLP)


class TextInput(BaseModel):
    text: str


@router.post("/entities")
def get_entities(body: TextInput):
    entities = entity_ops.get_entities(body.text)
    return {"entities": entities}
