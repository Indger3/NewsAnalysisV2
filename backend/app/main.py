import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app import settings
from app.bl.relation_ops import RelationOps
from app.bl.summary_ops import SummaryOps
from app.routes import auth_routes, nlp_routes
from app.utils.app_logger import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug(settings.NLP.meta)
    logger.info("spaCy model loaded")
    app.state.summary_ops = SummaryOps(settings.NLP)
    logger.info("SummaryOps loaded")
    app.state.relation_ops = RelationOps(settings.NLP)
    logger.info("RelationOps loaded")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/v1")
app.include_router(nlp_routes.router, prefix="/v1")


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Completed: {request.method} {request.url.path} "
            f"| Status: {response.status_code} "
            f"| Time: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.exception(f"Request failed: {request.method} {request.url.path} | Error: {str(e)}")
        raise e


@app.get("/")
def root():
    return {"response": "Welcome!"}
