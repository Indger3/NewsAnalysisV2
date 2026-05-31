import os
import spacy

APP_DB_CONN = os.environ.get("APP_DB_CONN")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "password")

NLP = spacy.load("app/static/improved_modelv2")