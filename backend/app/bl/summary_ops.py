from __future__ import annotations

import numpy as np
import spacy
import torch
from sklearn.cluster import KMeans
from spacy.language import Language
from transformers import AutoModel, AutoTokenizer


class SummaryOps:
    """
    Extractive summarizer: spaCy sentencizer → IndicBERT embeddings → KMeans → pick closest to centroids.
    Construct once (via lifespan), call summarize() per request.
    """

    def __init__(
        self,
        nlp: Language,
        model_name: str = "ai4bharat/IndicBERTv2-MLM-only",
        num_sentences: int = 3,
    ):
        self.num_sentences = num_sentences
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # use passed-in NLP for sentence splitting if it has a sentence detector;
        # otherwise attach a lightweight sentencizer to a blank pipeline
        if any(p in nlp.pipe_names for p in ("sentencizer", "senter", "parser")):
            self._sent_nlp = nlp
        else:
            self._sent_nlp = spacy.blank("en")
            self._sent_nlp.add_pipe("sentencizer")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize(self, text: str, n: int | None = None) -> dict:
        k = n or self.num_sentences
        sentences = self._split_sentences(text)
        if len(sentences) <= k:
            return {"summary": " ".join(sentences)}
        embeddings = self._embed(sentences)
        indices = self._cluster_pick(embeddings, k)
        return {"summary": " ".join(sentences[i] for i in sorted(indices))}

    # ------------------------------------------------------------------
    # Private stages
    # ------------------------------------------------------------------

    def _split_sentences(self, text: str) -> list[str]:
        text = " ".join(text.split())
        doc = self._sent_nlp(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    def _embed(self, sentences: list[str]) -> np.ndarray:
        all_embeddings = []
        batch_size = 16
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i: i + batch_size]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                output = self.model(**encoded)
            cls = output.last_hidden_state[:, 0, :].cpu().numpy()
            all_embeddings.append(cls)
        return np.vstack(all_embeddings)

    def _cluster_pick(self, embeddings: np.ndarray, k: int) -> list[int]:
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        km.fit(embeddings)
        picked = []
        for cluster_idx in range(k):
            members = np.where(km.labels_ == cluster_idx)[0]
            centroid = km.cluster_centers_[cluster_idx]
            distances = np.linalg.norm(embeddings[members] - centroid, axis=1)
            closest = members[np.argmin(distances)]
            picked.append(int(closest))
        return picked
