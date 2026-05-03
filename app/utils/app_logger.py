import logging
import sys
from loguru import logger

def setup_logging():
    # 1. Remove default handlers
    logging.getLogger().handlers = []
    logger.remove()

    # 2. Add custom Loguru handler
    # level can be "DEBUG", "INFO", etc.
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # 3. Intercept standard logging (Optional but recommended for Uvicorn)
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)