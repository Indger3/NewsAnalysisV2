"""
Relation Extractor Pipeline
============================
Stack: spaCy NER → alias-based mention unification → candidates →
       IndicBERT + entity markers → linear head → triples

Coreference: uses alias/substring matching (no external coref library).
All current coref libraries conflict with spaCy 3.8. This is a POC-adequate
substitute; upgrade path is noted in _coref().

Install:
    pip install torch transformers sentencepiece spacy pyyaml numpy
    python -m spacy download en_core_web_sm

Relations config: config/relations.yaml

Usage:
    rex = RelationExtractor(
        spacy_model="en_core_web_sm",
        re_model_path="path/to/finetuned",
        relations_config="config/relations.yaml",
    )
    triples = rex.extract(article_text, article_id="article_001")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import spacy
import torch
import torch.nn as nn
import yaml
from transformers import AutoModel, AutoTokenizer


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

@dataclass
class Mention:
    text: str
    start: int                      # char offset in article
    end: int
    type: str | None = None         # canonical entity type
    is_pronoun: bool = False
    cluster_id: int | None = None


@dataclass
class Cluster:
    cluster_id: int
    canonical_name: str             # longest proper-noun mention
    type: str                       # propagated from NER members


@dataclass
class Triple:
    subject_id: int
    predicate: str
    object_id: int
    subject_name: str
    object_name: str
    confidence: float
    negated: bool = False
    modality: str = "asserted"      # asserted | reported | planned
    source_sentence: str = ""
    article_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Ontology loader
# ---------------------------------------------------------------------------

class Ontology:
    """Loads relations.yaml and exposes label set + type-constraint lookup."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        self.spacy_label_map: dict[str, str] = cfg.get("spacy_label_map", {})

        # relations: list of {name, subject, object}
        self.relations: list[dict] = cfg.get("relations", [])

        # label list for classifier: index 0 = no_relation, 1..N = relations
        self.labels: list[str] = ["no_relation"] + [r["name"] for r in self.relations]
        self.label2id: dict[str, int] = {l: i for i, l in enumerate(self.labels)}
        self.id2label: dict[int, str] = {i: l for l, i in self.label2id.items()}

        # type-pair → allowed relation names (for candidate filtering)
        self._type_pairs: dict[tuple[str, str], list[str]] = {}
        for r in self.relations:
            key = (r["subject"], r["object"])
            self._type_pairs.setdefault(key, []).append(r["name"])

    def allows(self, subj_type: str, obj_type: str) -> bool:
        """True if any relation allows this (subject_type, object_type) pair."""
        return (subj_type, obj_type) in self._type_pairs

    @property
    def num_labels(self) -> int:
        return len(self.labels)

    def describe(self) -> None:
        """Print a readable summary of what got loaded."""
        print(f"Ontology — {self.num_labels} labels "
              f"({self.num_labels - 1} relations + no_relation)\n")

        print("  spacy_label_map:")
        for spacy_label, canonical in self.spacy_label_map.items():
            print(f"    {spacy_label:<15} -> {canonical}")

        print("\n  relations:")
        for r in self.relations:
            print(f"    [{self.label2id[r['name']]}] {r['name']:<25} "
                  f"subject={r['subject']}  object={r['object']}")

        print("\n  type pairs allowed (candidate filter):")
        for (subj, obj), rels in self._type_pairs.items():
            print(f"    ({subj}, {obj}) -> {rels}")

    def __repr__(self) -> str:
        rel_names = [r["name"] for r in self.relations]
        return (f"Ontology(relations={rel_names}, "
                f"label_map_keys={list(self.spacy_label_map.keys())})")


# ---------------------------------------------------------------------------
# RE model: IndicBERT encoder + linear classification head
# ---------------------------------------------------------------------------

class REModel(nn.Module):
    """
    Entity-marker relation classification model.
    Architecture: IndicBERT encoder → pool [E1] and [E2] start tokens
                  → concatenate → linear → logits
    """

    def __init__(self, encoder_name: str, num_labels: int):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(encoder_name)
        hidden = self.encoder.config.hidden_size
        self.classifier = nn.Linear(hidden * 2, num_labels)  # E1 + E2 concatenated
        self.dropout = nn.Dropout(0.1)

    def forward(self, input_ids, attention_mask,
                e1_pos: list[int], e2_pos: list[int]) -> torch.Tensor:
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        hidden = out.last_hidden_state  # (batch, seq_len, hidden)

        # pool the start-marker token of each entity for each item in batch
        e1_vecs = torch.stack([hidden[i, e1_pos[i], :] for i in range(len(e1_pos))])
        e2_vecs = torch.stack([hidden[i, e2_pos[i], :] for i in range(len(e2_pos))])

        combined = torch.cat([e1_vecs, e2_vecs], dim=-1)   # (batch, hidden*2)
        return self.classifier(self.dropout(combined))      # (batch, num_labels)


def load_re_model(
    model_path: str,
    num_labels: int,
    tokenizer_name: str,
    device: str,
    e1_token: str = "[E1]",
    e2_token: str = "[E2]",
    e1_end_token: str = "[/E1]",
    e2_end_token: str = "[/E2]",
) -> tuple[AutoTokenizer, REModel]:
    """
    Load tokenizer and RE model. Adds entity marker special tokens.
    If model_path is a HuggingFace base model (no saved head), the linear
    head is randomly initialized — useful for dev/POC before fine-tuning.
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    special_tokens = [e1_token, e2_token, e1_end_token, e2_end_token]
    tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})

    model = REModel(model_path, num_labels)
    model.encoder.resize_token_embeddings(len(tokenizer))  # account for new tokens

    saved_head = Path(model_path) / "re_head.pt"
    if saved_head.exists():
        model.classifier.load_state_dict(
            torch.load(saved_head, map_location=device)
        )

    model.to(device)
    model.eval()
    return tokenizer, model


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "without", "n't"}
HEDGE_WORDS = {"allegedly", "reportedly", "apparently", "claimed", "accused",
               "said", "told", "according"}
PLAN_WORDS = {"plans", "planning", "intends", "intending", "aims", "aiming",
              "expected", "seeking"}


class RelationExtractor:
    """
    Single-class relation extraction pipeline.

    Construct once (loads spaCy + coreferee + IndicBERT), call extract() per article.

    Args:
        spacy_model:       spaCy model path. Swap to any custom NER model here.
        re_model_path:     Path to fine-tuned weights, or a HuggingFace base
                           encoder name for dev (head will be random until trained).
        relations_config:  Path to config/relations.yaml.
        encoder_name:      HuggingFace encoder for the RE head. Defaults to IndicBERT.
                           Must match the model the head was trained with.
        threshold:         Minimum confidence to emit a triple (vs. review queue).
        device:            'cpu' | 'cuda'. Auto-detected when None.
    """

    E1 = "[E1]"; E1_END = "[/E1]"
    E2 = "[E2]"; E2_END = "[/E2]"

    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        re_model_path: str = "ai4bharat/IndicBERTv2-MLM-only",
        relations_config: str = "config/relations.yaml",
        encoder_name: str = "ai4bharat/IndicBERTv2-MLM-only",
        threshold: float = 0.6,
        device: str | None = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.threshold = threshold

        # ontology (labels + type rules)
        self.ontology = Ontology(relations_config)

        # NER — spaCy only (swap model via spacy_model arg)
        self.nlp = spacy.load(spacy_model)

        # RE model + tokenizer
        self.tokenizer, self.re_model = load_re_model(
            re_model_path,
            self.ontology.num_labels,
            encoder_name,
            self.device,
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def extract(self, text: str, article_id: str = "") -> list[Triple]:
        """
        Run the full pipeline on one article.

        Returns:
            List of Triple objects above the confidence threshold.
        """
        text = self._clean(text)
        mentions = self._ner(text)
        clusters = self._coref(text, mentions)
        candidates = self._candidates(text, mentions)
        triples = []
        for cand in candidates:
            triple = self._classify(cand, clusters, article_id)
            if triple:
                triples.append(triple)
        return triples

    def extract_many(
        self, texts: list[str], ids: list[str] | None = None
    ) -> list[list[Triple]]:
        """Batch convenience wrapper."""
        ids = ids or [""] * len(texts)
        return [self.extract(t, i) for t, i in zip(texts, ids)]

    # -----------------------------------------------------------------------
    # Private stages
    # -----------------------------------------------------------------------

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return (
            text.replace("\u2019", "'")
                .replace("\u201c", '"')
                .replace("\u201d", '"')
        )

    def _ner(self, text: str) -> list[Mention]:
        """
        Run spaCy NER, map entity labels to canonical types via ontology.
        Unmapped labels are dropped.

        Also merges adjacent mis-split entities — en_core_web_sm occasionally
        splits a single entity across two spans with different labels
        (e.g. "Cornwall Fire and" PERSON + "Rescue Service" ORG).
        Adjacent spans within 3 chars of each other and where one is ORG
        are merged into one ORG mention.
        """
        doc = self.nlp(text)
        raw = [(ent.text, ent.start_char, ent.end_char, ent.label_)
               for ent in doc.ents]

        # merge adjacent spans that are likely one split entity
        merged = []
        skip = set()
        for i, (text_i, start_i, end_i, label_i) in enumerate(raw):
            if i in skip:
                continue
            if i + 1 < len(raw):
                text_j, start_j, end_j, label_j = raw[i + 1]
                gap = start_j - end_i
                # merge if adjacent (gap <= 3 chars) and at least one is ORG
                if gap <= 3 and (label_i == "ORG" or label_j == "ORG"):
                    merged_text = text[start_i:end_j]
                    merged.append((merged_text, start_i, end_j, "ORG"))
                    skip.add(i + 1)
                    continue
            merged.append((text_i, start_i, end_i, label_i))

        mentions = []
        for (ent_text, start, end, label) in merged:
            canonical = self.ontology.spacy_label_map.get(label)
            if canonical is None:
                continue
            mentions.append(Mention(
                text=ent_text,
                start=start,
                end=end,
                type=canonical,
            ))
        return mentions

    def _coref(self, text: str, mentions: list[Mention]) -> list[Cluster]:
        """
        Alias-based mention unification.

        No external coref library — all current options (coreferee, fastcoref,
        en_coreference_web_trf) conflict with spaCy 3.8. This method handles
        the repeated-entity problem (the original requirement) via string
        normalisation: mentions that resolve to the same canonical name are
        grouped into one cluster. Good enough for a POC; swap for a proper
        coref model when the ecosystem catches up.

        Algorithm:
          1. Normalise each mention surface form (strip titles/suffixes, lower).
          2. Group mentions that share a normalised form OR where one is a
             substring of another (handles "Mukesh Ambani" vs "Ambani").
          3. Assign a cluster_id; canonical_name = longest mention in the group.
          4. Each mention gets its cluster_id in-place.
        """
        if not mentions:
            return []

        # --- normalise ---
        def _norm(s: str) -> str:
            s = s.lower().strip()
            for prefix in ("shri ", "smt. ", "smt ", "dr. ", "dr ", "mr. ",
                           "mr ", "ms. ", "ms ", "prof. ", "prof ", "justice ",
                           "lt. gen. ", "adv. ", "ca "):
                if s.startswith(prefix):
                    s = s[len(prefix):]
            return s.rstrip(" ji").strip()

        norms = [_norm(m.text) for m in mentions]

        # --- union-find for grouping ---
        parent = list(range(len(mentions)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            parent[find(a)] = find(b)

        for i in range(len(mentions)):
            for j in range(i + 1, len(mentions)):
                if mentions[i].type != mentions[j].type:
                    continue
                ni, nj = norms[i], norms[j]
                # exact match always links
                if ni == nj:
                    union(i, j)
                # substring match: only if the shorter form is at least 4 chars
                # (avoids linking short common words like "he", "it", "Inc")
                elif len(ni) >= 4 and len(nj) >= 4 and (ni in nj or nj in ni):
                    union(i, j)

        # --- build clusters ---
        from collections import defaultdict
        groups: dict[int, list[int]] = defaultdict(list)
        for i in range(len(mentions)):
            groups[find(i)].append(i)

        clusters: list[Cluster] = []
        for cluster_id, (root, idxs) in enumerate(groups.items()):
            canonical_idx = max(idxs, key=lambda i: len(mentions[i].text))
            canonical_name = mentions[canonical_idx].text
            cluster_type = mentions[canonical_idx].type or ""
            clusters.append(Cluster(
                cluster_id=cluster_id,
                canonical_name=canonical_name,
                type=cluster_type,
            ))
            for i in idxs:
                mentions[i].cluster_id = cluster_id

        return clusters

    def _candidates(
        self, text: str, mentions: list[Mention]
    ) -> list[tuple[str, Mention, Mention]]:
        """
        Generate (sentence, subject_mention, object_mention) candidates.
        Sentence-level only — both mentions must appear in the same sentence.
        Filtered by the ontology type-constraint (reduces IndicBERT calls).
        """
        doc = self.nlp(text)
        candidates = []

        for sent in doc.sents:
            s_start, s_end = sent.start_char, sent.end_char
            sent_text = sent.text

            # mentions in this sentence
            in_sent = [
                m for m in mentions
                if m.start >= s_start and m.end <= s_end and m.type
            ]

            # ordered pairs, subject ≠ object, type-filtered
            for i, subj in enumerate(in_sent):
                for obj in in_sent:
                    if subj is obj:
                        continue
                    if subj.type and obj.type and self.ontology.allows(subj.type, obj.type):
                        candidates.append((sent_text, subj, obj))

        return candidates

    def _classify(
        self,
        candidate: tuple[str, Mention, Mention],
        clusters: list[Cluster],
        article_id: str,
    ) -> Optional[Triple]:
        """
        Insert entity markers → encode with IndicBERT → classify relation.
        Returns a Triple if confidence >= threshold and predicate != no_relation.
        """
        sent_text, subj, obj = candidate

        # --- build marked sentence ---
        # locate entity spans within the sentence string (not article offsets)
        subj_in_sent = sent_text.find(subj.text)
        obj_in_sent = sent_text.find(obj.text)

        if subj_in_sent == -1 or obj_in_sent == -1:
            return None  # can't locate span in sentence — skip

        # insert markers without rewriting sentence words
        marked = self._insert_markers(sent_text, subj.text, obj.text,
                                      subj_in_sent, obj_in_sent)

        # --- tokenize ---
        encoded = self.tokenizer(
            marked,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)

        input_ids = encoded["input_ids"][0].tolist()

        e1_id = self.tokenizer.convert_tokens_to_ids(self.E1)
        e2_id = self.tokenizer.convert_tokens_to_ids(self.E2)

        try:
            e1_pos = input_ids.index(e1_id)
            e2_pos = input_ids.index(e2_id)
        except ValueError:
            return None  # marker not found after truncation — skip

        # --- forward pass ---
        with torch.no_grad():
            logits = self.re_model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                e1_pos=[e1_pos],
                e2_pos=[e2_pos],
            )

        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        pred_id = int(np.argmax(probs))
        confidence = float(probs[pred_id])
        predicate = self.ontology.id2label[pred_id]

        if predicate == "no_relation" or confidence < self.threshold:
            return None

        # --- postprocess ---
        negated, modality = self._validate(sent_text)

        subj_cluster = next((c for c in clusters if c.cluster_id == subj.cluster_id), None)
        obj_cluster  = next((c for c in clusters if c.cluster_id == obj.cluster_id), None)

        # drop triple if either endpoint has no cluster — unresolved entity,
        # not safe to emit
        if subj.cluster_id is None or obj.cluster_id is None:
            return None

        return Triple(
            subject_id=subj.cluster_id,
            predicate=predicate,
            object_id=obj.cluster_id,
            subject_name=subj_cluster.canonical_name if subj_cluster else subj.text,
            object_name=obj_cluster.canonical_name if obj_cluster else obj.text,
            confidence=round(confidence, 4),
            negated=negated,
            modality=modality,
            source_sentence=sent_text,
            article_id=article_id,
        )

    def _insert_markers(
        self,
        sentence: str,
        subj_text: str,
        obj_text: str,
        subj_pos: int,
        obj_pos: int,
    ) -> str:
        """
        Wrap subject and object in [E1]/[E2] markers in place.
        Handles both orderings (subject before object and vice versa).
        Never rewrites the entity text — markers are inserted around it.
        """
        subj_end = subj_pos + len(subj_text)
        obj_end = obj_pos + len(obj_text)

        if subj_pos < obj_pos:
            # subject comes first in the sentence
            marked = (
                sentence[:subj_pos]
                + f"{self.E1} {subj_text} {self.E1_END}"
                + sentence[subj_end:obj_pos]
                + f"{self.E2} {obj_text} {self.E2_END}"
                + sentence[obj_end:]
            )
        else:
            # object comes first
            marked = (
                sentence[:obj_pos]
                + f"{self.E2} {obj_text} {self.E2_END}"
                + sentence[obj_end:subj_pos]
                + f"{self.E1} {subj_text} {self.E1_END}"
                + sentence[subj_end:]
            )
        return marked

    def _validate(self, sentence: str) -> tuple[bool, str]:
        """
        Cheap negation and modality check on the sentence.
        Returns: (negated: bool, modality: str)
        """
        tokens = set(sentence.lower().split())
        negated = bool(tokens & NEGATION_WORDS)
        if tokens & PLAN_WORDS:
            modality = "planned"
        elif tokens & HEDGE_WORDS:
            modality = "reported"
        else:
            modality = "asserted"
        return negated, modality


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, textwrap

    # Minimal inline config — normally lives in config/relations.yaml
    import tempfile, os

    config_yaml = textwrap.dedent("""
        spacy_label_map:
          PERSON: PERSON
          ORG: ORG
          GPE: GPE
          NORP: POLITICAL_PARTY

        relations:
          - {name: acquired,         subject: ORG,    object: ORG}
          - {name: headquartered_in, subject: ORG,    object: GPE}
          - {name: party_member_of,  subject: PERSON, object: POLITICAL_PARTY}
    """)

    # write a temp config for the smoke test
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        tmp_cfg = f.name

    sample = (
        "Reliance Industries, headquartered in Mumbai, announced that it has "
        "acquired a majority stake in Network18. Mukesh Ambani, the chairman of "
        "Reliance, said the deal would strengthen the company's media presence."
    )

    print("Loading models (first run downloads from HuggingFace)...")
    rex = RelationExtractor(
        spacy_model="en_core_web_sm",
        re_model_path="ai4bharat/IndicBERTv2-MLM-only",  # base model, head is random
        relations_config=tmp_cfg,
        threshold=0.3,   # low threshold for smoke test (head is untrained)
    )

    triples = rex.extract(sample, article_id="smoke_test_001")
    print(f"\nFound {len(triples)} triple(s):\n")
    for t in triples:
        print(json.dumps(t.to_dict(), indent=2))

    os.unlink(tmp_cfg)