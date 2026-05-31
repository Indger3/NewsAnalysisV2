import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.utils.app_logger import setup_logging
from app import settings
from app.routes import nlp_routes, auth_routes

app = FastAPI()
setup_logging()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    logger.debug(settings.NLP.meta)
    logger.info("Spacy model loaded")
except Exception as e:
    print(str(e))

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
