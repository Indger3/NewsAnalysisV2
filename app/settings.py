import os
import spacy


APP_DB_CONN = os.environ.get("APP_DB_CONN")

NLP = spacy.load("app/static/improved_modelv2") #for loading once in app lifecycle