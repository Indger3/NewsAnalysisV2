from datetime import time
from fastapi import FastAPI, Request
from loguru import logger
from app.utils.app_logger import setup_logging

app = FastAPI()
setup_logging()

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request start
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log request completion
        logger.info(
            f"Completed: {request.method} {request.url.path} "
            f"| Status: {response.status_code} "
            f"| Time: {process_time:.2f}ms"
        )
        return response
        
    except Exception as e:
        # Log unhandled exceptions
        process_time = (time.time() - start_time) * 1000
        logger.exception(f"Request failed: {request.method} {request.url.path} | Error: {str(e)}")
        raise e


@app.get("/")
def root():
    return {"response":"Welcome!"}
