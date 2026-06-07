# class TaxonomyOps:

#     def __init__(self, nlp):

#         self.nlp = nlp

#         self.model = ...  # load your taxonomy model

#     def get_taxonomy(self, text: str):

#         result = self.model.predict(text)

#         return {

#             "categories": result

#         }
from app import settings
from app.static.taxonomy_model.taxonomy_model_v2 import TaxonomyModelV2


class TaxonomyOps:

    def __init__(self, nlp):
        self.nlp = nlp

        self.model = TaxonomyModelV2()
        self.model.load(settings.TAX)

    def get_taxonomy(self, text: str):
        return self.model.predict(text)