from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import settings
from app.bl.entity_ops import EntityOps
from app.utils.auth import get_current_user

router = APIRouter()

entity_ops = EntityOps(settings.NLP)


class TextInput(BaseModel):
    text: str


@router.post("/entities")
def get_entities(body: TextInput, _: dict = Depends(get_current_user)):
    entities = entity_ops.get_entities(body.text)
    return {"entities": entities}
