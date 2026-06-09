class BatchAnalysisOps:

    def __init__(
        self,
        entity_ops,
        relation_ops,
        taxonomy_ops,
        normalization_ops,
        #local_relation_ops,
        summary_ops=None
    ):
        self.entity_ops = entity_ops
        self.relation_ops = relation_ops
        self.taxonomy_ops = taxonomy_ops
        self.normalization_ops = normalization_ops
        self.summary_ops = summary_ops
        #self.local_relation_ops = local_relation_ops

    def process_article(self, article):

        text = article.get("content", "")

        if not text.strip():

            return {
                **article,
                "analysis": {
                    "error": "No content found"
                }
            }

        entities = self.entity_ops.get_entities(text)

        relations_result = self.relation_ops.get_relations(text)

        relations = relations_result.get(
            "relationships",
            []
        )

        taxonomy = self.taxonomy_ops.get_taxonomy(text)

        normalized_entities = (
            self.normalization_ops.normalize_entities(
                entities,
                text,
                relations
            )
        )

        result = {
            **article,
            "analysis": {
                "entities": entities,
                "normalized_entities": normalized_entities,
                "relations": relations,
                "taxonomy": taxonomy
            }
        }

        if self.summary_ops:

            result["analysis"]["summary"] = (
                self.summary_ops.summarize(text)
            )

        return result

    def process_batch(self, articles):

        return [
            self.process_article(article)
            for article in articles
        ]