from spacy.language import Language


class EntityOps:
    def __init__(self, nlp: Language):
        self.nlp = nlp

    def get_entities(self, text: str):
        doc = self.nlp(text)
        seen = set()
        entities = []
        for ent in doc.ents:
            key = (ent.text, ent.label_)
            if key not in seen:
                seen.add(key)
                entities.append({
                    "entity": ent.text,
                    "label": ent.label_
                })
        return entities