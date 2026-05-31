import os
from pathlib import Path

import spacy
from dotenv import load_dotenv

# load .env from project root (one level above backend/)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

APP_DB_CONN = os.environ.get("APP_DB_CONN")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

NLP = spacy.load("app/static/improved_modelv2")