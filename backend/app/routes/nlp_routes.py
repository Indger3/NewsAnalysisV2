from fastapi import APIRouter, Depends, Request
import json
from pydantic import BaseModel
from app import settings
from app.bl.entity_ops import EntityOps
from app.bl.metadata_ops import MetadataOps
from app.bl.taxonomy_ops import TaxonomyOps
from app.utils.auth import get_current_user
from app.bl.normalization_ops import NormalizationOps
from fastapi import (

    APIRouter,

    Depends,

    Request,

    UploadFile,

    File,

    HTTPException

)

router = APIRouter()

entity_ops = EntityOps(settings.NLP)
taxonomy_ops = TaxonomyOps(settings.NLP)
normalization_ops = NormalizationOps()
metadata_ops = MetadataOps(settings.NLP)


class TextInput(BaseModel):
    text: str


class SummaryInput(BaseModel):
    text: str
    n: int | None = None


class RelationsInput(BaseModel):
    text: str
    confidence: float = 0.6

class NormalizationInput(BaseModel):
    text: str

class BatchAnalysisRequest(BaseModel):
    input_file: str
    output_file: str

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

@router.post("/taxonomy")
def get_taxonomy(
    body: TextInput,
    _: dict = Depends(get_current_user)
):
    return taxonomy_ops.get_taxonomy(body.text)

@router.post("/normalize")
def normalize_entities(
    request: Request,
    body: NormalizationInput,
    _: dict = Depends(get_current_user)
):

    entities = entity_ops.get_entities(body.text)

    relation_result = request.app.state.relation_ops.get_relations(
        body.text
    )

    return {
        "normalized_entities":
            normalization_ops.normalize_entities(
                entities=entities,
                text=body.text,
                relations=relation_result.get(
                    "relationships",
                    []
                )
            )
    }

@router.post("/batch-analysis")
async def batch_analysis(
    request: Request,
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user)
):
    try:

        contents = await file.read()

        articles = json.loads(
            contents.decode("utf-8")
        )

        if not isinstance(articles, list):

            raise HTTPException(
                status_code=400,
                detail="JSON file must contain a list of articles"
            )

        results = (
            request.app.state.batch_analysis_ops.process_batch(
                articles
            )
        )

        return {
            "total_articles": len(results),
            "results": results
        }

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON file"
        )
    
@router.post("/metadata")
def get_metadata(
    body: TextInput,
    _: dict = Depends(get_current_user)
):
    return metadata_ops.extract(body.text)