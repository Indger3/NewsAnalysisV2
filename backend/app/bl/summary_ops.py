# from __future__ import annotations

# import numpy as np
# import spacy
# import torch
# from sklearn.cluster import KMeans
# from spacy.language import Language
# from transformers import AutoModel, AutoTokenizer


# class SummaryOps:
#     """
#     Extractive summarizer: spaCy sentencizer → IndicBERT embeddings → KMeans → pick closest to centroids.
#     Construct once (via lifespan), call summarize() per request.
#     """

#     def __init__(
#         self,
#         nlp: Language,
#         model_name: str = "ai4bharat/IndicBERTv2-MLM-only",
#         num_sentences: int = 3,
#     ):
#         self.num_sentences = num_sentences
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#         # use passed-in NLP for sentence splitting if it has a sentence detector;
#         # otherwise attach a lightweight sentencizer to a blank pipeline
#         if any(p in nlp.pipe_names for p in ("sentencizer", "senter", "parser")):
#             self._sent_nlp = nlp
#         else:
#             self._sent_nlp = spacy.blank("en")
#             self._sent_nlp.add_pipe("sentencizer")

#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#         self.model = AutoModel.from_pretrained(model_name).to(self.device)
#         self.model.eval()

#     # ------------------------------------------------------------------
#     # Public API
#     # ------------------------------------------------------------------

#     def summarize(self, text: str, n: int | None = None) -> dict:
#         k = n or self.num_sentences
#         sentences = self._split_sentences(text)
#         if len(sentences) <= k:
#             return {"summary": " ".join(sentences)}
#         embeddings = self._embed(sentences)
#         indices = self._cluster_pick(embeddings, k)
#         return {"summary": " ".join(sentences[i] for i in sorted(indices))}

#     # ------------------------------------------------------------------
#     # Private stages
#     # ------------------------------------------------------------------

#     def _split_sentences(self, text: str) -> list[str]:
#         text = " ".join(text.split())
#         doc = self._sent_nlp(text)
#         return [s.text.strip() for s in doc.sents if s.text.strip()]

#     def _embed(self, sentences: list[str]) -> np.ndarray:
#         all_embeddings = []
#         batch_size = 16
#         for i in range(0, len(sentences), batch_size):
#             batch = sentences[i: i + batch_size]
#             encoded = self.tokenizer(
#                 batch,
#                 padding=True,
#                 truncation=True,
#                 max_length=512,
#                 return_tensors="pt",
#             ).to(self.device)
#             with torch.no_grad():
#                 output = self.model(**encoded)
#             cls = output.last_hidden_state[:, 0, :].cpu().numpy()
#             all_embeddings.append(cls)
#         return np.vstack(all_embeddings)

#     def _cluster_pick(self, embeddings: np.ndarray, k: int) -> list[int]:
#         km = KMeans(n_clusters=k, random_state=42, n_init="auto")
#         km.fit(embeddings)
#         picked = []
#         for cluster_idx in range(k):
#             members = np.where(km.labels_ == cluster_idx)[0]
#             centroid = km.cluster_centers_[cluster_idx]
#             distances = np.linalg.norm(embeddings[members] - centroid, axis=1)
#             closest = members[np.argmin(distances)]
#             picked.append(int(closest))
#         return picked


from __future__ import annotations

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from spacy.language import Language


class SummaryOps:
    """
    Abstractive summarizer using Google FLAN-T5 Base.

    Public API remains identical:
        summarize(text) -> {"summary": "..."}
    """

    def __init__(
        self,
        nlp: Language,   # kept only for compatibility with your project
        model_name: str = "facebook/bart-large-cnn", #model_name: str = "google/pegasus-cnn_dailymail", facebook/bart-large-cnn, "google/flan-t5-base"
    ):
        # self.device = torch.device(
        #     "cuda" if torch.cuda.is_available() else "cpu"
        # )
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = (
            AutoModelForSeq2SeqLM
            .from_pretrained(model_name)
            .to(self.device)
        )

        self.model.eval()

    def summarize(
        self,
        text: str,
        n: int | None = None,
    ) -> dict:

        if not text.strip():
            return {"summary": ""}

#         prompt = f"""

# Write a concise news summary of the following article.

# The summary should:

# • be between 4 and 6 sentences

# • mention the main event

# • identify the key people

# • mention the location

# • include the most important statements

# • avoid opinions

# • do not use bullet points

# Article:

# {text}

# Summary:

# """

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(self.device)
        # inputs = self.tokenizer(
        #     prompt,
        #     return_tensors="pt",
        #     truncation=True,
        #     max_length=1024,
        # ).to(self.device)

        # with torch.no_grad():
        with torch.inference_mode():

            summary_ids = self.model.generate(
                **inputs,
                max_new_tokens=150,
                min_new_tokens=40,
                num_beams=2,
                early_stopping=True,
                no_repeat_ngram_size=3,
                length_penalty=1.0,
            )

        summary = self.tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True,
        )

        return {"summary": summary}