"""
News Summarizer — Custom Extractive Implementation
===================================================
No dependency on bert-extractive-summarizer.
Works with transformers>=5.0.

Stack: spaCy sentencizer → BERT/IndicBERT embeddings → KMeans → pick closest to centroids

Install:
    pip install torch transformers sentencepiece spacy scikit-learn numpy
    python -m spacy download en_core_web_trf
"""

import numpy as np
import spacy
import torch
from sklearn.cluster import KMeans
from transformers import AutoModel, AutoTokenizer


class NewsSummarizer:
    """
    Extractive news summarizer using BERT-family encoder + KMeans clustering.

    Construct once, call summarize() per article.

    Args:
        model_name: Any HuggingFace encoder model. Defaults to IndicBERT (Indian
                    English + Indic languages). Use 'distilbert-base-uncased' for
                    a lighter English-only alternative.
        spacy_model: spaCy model for sentence splitting. 'en_core_web_trf' is fine
                     for Indian English news.
        num_sentences: Default number of sentences to extract.
        device: 'cpu' or 'cuda'. Auto-detects GPU if available when set to None.
    """

    def __init__(
        self,
        model_name: str = "ai4bharat/IndicBERTv2-MLM-only",
        spacy_model: str = "en_core_web_trf",
        num_sentences: int = 3,
        device: str | None = None,
    ):
        # device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # sentence splitter — disable everything except sentencizer (fast)
        self.nlp = spacy.load(spacy_model, disable=["ner", "parser", "lemmatizer"])
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

        # encoder
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

        self.num_sentences = num_sentences

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize(self, text: str, n: int | None = None) -> str:
        """
        Summarize a single article.

        Args:
            text: Raw article text.
            n: Number of sentences to extract. Overrides the instance default.

        Returns:
            Summary string — selected sentences joined in original order.
        """
        k = n or self.num_sentences
        sentences = self._split_sentences(text)

        # short article — return as-is
        if len(sentences) <= k:
            return " ".join(sentences)

        embeddings = self._embed(sentences)
        indices = self._cluster_pick(embeddings, k)
        return " ".join(sentences[i] for i in sorted(indices))

    def summarize_many(self, texts: list[str], n: int | None = None) -> list[str]:
        """Summarize a list of articles. Returns a list of summary strings."""
        return [self.summarize(t, n) for t in texts]

    def summarize_cluster(self, docs: list[str], n: int | None = None) -> str:
        """
        Multi-document summary (e.g. same story across outlets).
        Concatenates docs, deduplicates near-identical sentences, then summarizes.

        Args:
            docs: List of article texts covering the same story.
            n: Number of sentences to extract from the combined pool.

        Returns:
            Summary string.
        """
        combined = " ".join(docs)
        sentences = self._split_sentences(combined)
        sentences = self._dedup(sentences)

        k = n or self.num_sentences
        if len(sentences) <= k:
            return " ".join(sentences)

        embeddings = self._embed(sentences)
        indices = self._cluster_pick(embeddings, k)
        return " ".join(sentences[i] for i in sorted(indices))

    # ------------------------------------------------------------------
    # Private stages
    # ------------------------------------------------------------------

    def _split_sentences(self, text: str) -> list[str]:
        """Clean and split text into sentences using spaCy sentencizer."""
        # basic cleanup
        text = " ".join(text.split())
        doc = self.nlp(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    def _embed(self, sentences: list[str]) -> np.ndarray:
        """
        Embed sentences using the BERT encoder.
        Uses CLS token pooling — standard for sentence-level classification.
        Batches to avoid OOM on longer articles.
        """
        all_embeddings = []
        batch_size = 16

        for i in range(0, len(sentences), batch_size):
            batch = sentences[i : i + batch_size]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                output = self.model(**encoded)

            # CLS token — first token of last hidden state
            cls = output.last_hidden_state[:, 0, :].cpu().numpy()
            all_embeddings.append(cls)

        return np.vstack(all_embeddings)

    def _cluster_pick(self, embeddings: np.ndarray, k: int) -> list[int]:
        """
        KMeans cluster the sentence embeddings into k clusters.
        Pick the sentence closest to each centroid — those are the most
        representative sentences.
        """
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        km.fit(embeddings)

        picked = []
        for cluster_idx in range(k):
            # sentences belonging to this cluster
            members = np.where(km.labels_ == cluster_idx)[0]
            centroid = km.cluster_centers_[cluster_idx]
            # sentence closest to the centroid
            distances = np.linalg.norm(embeddings[members] - centroid, axis=1)
            closest = members[np.argmin(distances)]
            picked.append(int(closest))

        return picked

    def _dedup(self, sentences: list[str], threshold: float = 0.92) -> list[str]:
        """
        Remove near-duplicate sentences (e.g. wire-copy republished across outlets).
        Compares via embedding cosine similarity; drops a sentence if it's above
        the threshold with an already-kept sentence.
        Only runs on multi-doc input (_cluster_pick handles single-doc fine without it).
        """
        if len(sentences) <= 1:
            return sentences

        embeddings = self._embed(sentences)
        # L2-normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normed = embeddings / np.where(norms == 0, 1, norms)

        kept = []
        kept_emb = []

        for i, sent in enumerate(sentences):
            if not kept_emb:
                kept.append(sent)
                kept_emb.append(normed[i])
                continue
            sims = np.array(kept_emb) @ normed[i]
            if sims.max() < threshold:
                kept.append(sent)
                kept_emb.append(normed[i])

        return kept


# ------------------------------------------------------------------
# Quick smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    sample = """
    The Reserve Bank of India kept its benchmark interest rate unchanged at 6.5 percent
    on Friday, as widely expected, while maintaining its stance focused on withdrawal
    of accommodation to ensure that inflation progressively aligns with the target.
    Governor Shaktikanta Das said the Monetary Policy Committee voted unanimously to
    hold rates. Consumer price inflation eased to 4.75 percent in May, down from
    5.1 percent in April, giving the central bank room to pause. Analysts at HDFC Bank
    said they now expect a rate cut of 25 basis points in the October policy meeting.
    The Indian rupee strengthened marginally against the US dollar following the
    announcement. Equity markets rose half a percent, with the Sensex gaining around
    350 points in afternoon trade in Mumbai.
    """

    # Default: IndicBERT
    summ = NewsSummarizer(num_sentences=2)
    print("=== IndicBERT ===")
    print(summ.summarize(sample))

    # Swap to distilBERT — one constructor arg, nothing else changes
    summ_dist = NewsSummarizer(
        model_name="distilbert-base-uncased", num_sentences=2
    )
    print("\n=== distilBERT ===")
    print(summ_dist.summarize(sample))