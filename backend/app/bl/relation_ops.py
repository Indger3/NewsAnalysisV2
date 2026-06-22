# from __future__ import annotations

# import re
# from collections import defaultdict
# from dataclasses import dataclass, asdict
# from pathlib import Path
# from typing import Optional

# import numpy as np
# import spacy
# import torch
# import torch.nn as nn
# import yaml
# from spacy.language import Language
# from transformers import AutoModel, AutoTokenizer


# # ---------------------------------------------------------------------------
# # Schemas
# # ---------------------------------------------------------------------------

# @dataclass
# class Mention:
#     text: str
#     start: int
#     end: int
#     type: str | None = None
#     is_pronoun: bool = False
#     cluster_id: int | None = None


# @dataclass
# class Cluster:
#     cluster_id: int
#     canonical_name: str
#     type: str


# @dataclass
# class Triple:
#     subject_id: int
#     predicate: str
#     object_id: int
#     subject_name: str
#     object_name: str
#     confidence: float
#     negated: bool = False
#     modality: str = "asserted"
#     source_sentence: str = ""

#     def to_dict(self) -> dict:
#         return asdict(self)


# # ---------------------------------------------------------------------------
# # Ontology loader
# # ---------------------------------------------------------------------------

# class Ontology:
#     def __init__(self, config_path: str):
#         with open(config_path) as f:
#             cfg = yaml.safe_load(f)

#         self.spacy_label_map: dict[str, str] = cfg.get("spacy_label_map", {})
#         self.relations: list[dict] = cfg.get("relations", [])
#         self.labels: list[str] = ["no_relation"] + [r["name"] for r in self.relations]
#         self.label2id: dict[str, int] = {l: i for i, l in enumerate(self.labels)}
#         self.id2label: dict[int, str] = {i: l for l, i in self.label2id.items()}

#         self._type_pairs: dict[tuple[str, str], list[str]] = {}
#         for r in self.relations:
#             key = (r["subject"], r["object"])
#             self._type_pairs.setdefault(key, []).append(r["name"])

#     def allows(self, subj_type: str, obj_type: str) -> bool:
#         return (subj_type, obj_type) in self._type_pairs

#     @property
#     def num_labels(self) -> int:
#         return len(self.labels)


# # ---------------------------------------------------------------------------
# # RE model
# # ---------------------------------------------------------------------------

# class REModel(nn.Module):
#     def __init__(self, encoder_name: str, num_labels: int):
#         super().__init__()
#         self.encoder = AutoModel.from_pretrained(encoder_name)
#         hidden = self.encoder.config.hidden_size
#         self.classifier = nn.Linear(hidden * 2, num_labels)
#         self.dropout = nn.Dropout(0.1)

#     def forward(self, input_ids, attention_mask,
#                 e1_pos: list[int], e2_pos: list[int]) -> torch.Tensor:
#         out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
#         hidden = out.last_hidden_state
#         e1_vecs = torch.stack([hidden[i, e1_pos[i], :] for i in range(len(e1_pos))])
#         e2_vecs = torch.stack([hidden[i, e2_pos[i], :] for i in range(len(e2_pos))])
#         combined = torch.cat([e1_vecs, e2_vecs], dim=-1)
#         return self.classifier(self.dropout(combined))


# def _load_re_model(
#     model_name: str,
#     num_labels: int,
#     device: str,
#     e1_token: str = "[E1]",
#     e2_token: str = "[E2]",
#     e1_end_token: str = "[/E1]",
#     e2_end_token: str = "[/E2]",
# ) -> tuple[AutoTokenizer, REModel]:
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     tokenizer.add_special_tokens(
#         {"additional_special_tokens": [e1_token, e2_token, e1_end_token, e2_end_token]}
#     )
#     model = REModel(model_name, num_labels)
#     model.encoder.resize_token_embeddings(len(tokenizer))
#     # load saved head weights if available
#     saved_head = Path(model_name) / "re_head.pt"
#     if saved_head.exists():
#         model.classifier.load_state_dict(torch.load(saved_head, map_location=device))
#     model.to(device)
#     model.eval()
#     return tokenizer, model


# # ---------------------------------------------------------------------------
# # Constants
# # ---------------------------------------------------------------------------

# NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "without", "n't"}
# HEDGE_WORDS = {"allegedly", "reportedly", "apparently", "claimed", "accused",
#                "said", "told", "according"}
# PLAN_WORDS = {"plans", "planning", "intends", "intending", "aims", "aiming",
#               "expected", "seeking"}


# # ---------------------------------------------------------------------------
# # Main BL class
# # ---------------------------------------------------------------------------

# class RelationOps:
#     """
#     Relation extraction pipeline: NER → coref → candidates → IndicBERT classify → triples.
#     Construct once (via lifespan), call get_relations() per request.
#     """

#     E1 = "[E1]"; E1_END = "[/E1]"
#     E2 = "[E2]"; E2_END = "[/E2]"

#     def __init__(
#         self,
#         nlp: Language,
#         model_name: str = "ai4bharat/IndicBERTv2-MLM-only",
#         relations_config: str = "app/config/relations.yaml",
#     ):
#         self.device = "cuda" if torch.cuda.is_available() else "cpu"
#         self.nlp = nlp  # settings.NLP — used for entity extraction in _ner()
#         self.ontology = Ontology(relations_config)

#         # lightweight sentencizer for sentence-level candidate generation
#         if any(p in nlp.pipe_names for p in ("sentencizer", "senter", "parser")):
#             self._sent_nlp = nlp
#         else:
#             self._sent_nlp = spacy.blank("en")
#             self._sent_nlp.add_pipe("sentencizer")

#         self.tokenizer, self.re_model = _load_re_model(
#             model_name, self.ontology.num_labels, self.device
#         )

#     # ------------------------------------------------------------------
#     # Public API
#     # ------------------------------------------------------------------

#     def get_relations(self, text: str, confidence: float = 0.6) -> dict:
#         text = self._clean(text)
#         mentions = self._ner(text)
#         clusters = self._coref(mentions)
#         candidates = self._candidates(text, mentions)
#         triples = []
#         for cand in candidates:
#             triple = self._classify(cand, clusters, confidence)
#             if triple:
#                 triples.append(triple)
#         return {
#             "relationships": [
#                 {"subj": t.subject_name, "verb": t.predicate, "obj": t.object_name}
#                 for t in triples
#             ]
#         }

#     # ------------------------------------------------------------------
#     # Private pipeline stages
#     # ------------------------------------------------------------------

#     @staticmethod
#     def _clean(text: str) -> str:
#         text = re.sub(r"\s+", " ", text).strip()
#         return (
#             text.replace("’", "'")
#                 .replace("“", '"')
#                 .replace("”", '"')
#         )

#     def _ner(self, text: str) -> list[Mention]:
#         doc = self.nlp(text)
#         raw = [(ent.text, ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]

#         merged = []
#         skip = set()
#         for i, (text_i, start_i, end_i, label_i) in enumerate(raw):
#             if i in skip:
#                 continue
#             if i + 1 < len(raw):
#                 text_j, start_j, end_j, label_j = raw[i + 1]
#                 if start_j - end_i <= 3 and (label_i == "ORG" or label_j == "ORG"):
#                     merged.append((text[start_i:end_j], start_i, end_j, "ORG"))
#                     skip.add(i + 1)
#                     continue
#             merged.append((text_i, start_i, end_i, label_i))

#         mentions = []
#         for (ent_text, start, end, label) in merged:
#             canonical = self.ontology.spacy_label_map.get(label)
#             if canonical is None:
#                 continue
#             mentions.append(Mention(text=ent_text, start=start, end=end, type=canonical))
#         return mentions

#     def _coref(self, mentions: list[Mention]) -> list[Cluster]:
#         if not mentions:
#             return []

#         def _norm(s: str) -> str:
#             s = s.lower().strip()
#             for prefix in ("shri ", "smt. ", "smt ", "dr. ", "dr ", "mr. ",
#                            "mr ", "ms. ", "ms ", "prof. ", "prof ", "justice ",
#                            "lt. gen. ", "adv. ", "ca "):
#                 if s.startswith(prefix):
#                     s = s[len(prefix):]
#             return s.rstrip(" ji").strip()

#         norms = [_norm(m.text) for m in mentions]
#         parent = list(range(len(mentions)))

#         def find(x):
#             while parent[x] != x:
#                 parent[x] = parent[parent[x]]
#                 x = parent[x]
#             return x

#         def union(a, b):
#             parent[find(a)] = find(b)

#         for i in range(len(mentions)):
#             for j in range(i + 1, len(mentions)):
#                 if mentions[i].type != mentions[j].type:
#                     continue
#                 ni, nj = norms[i], norms[j]
#                 if ni == nj:
#                     union(i, j)
#                 elif len(ni) >= 4 and len(nj) >= 4 and (ni in nj or nj in ni):
#                     union(i, j)

#         groups: dict[int, list[int]] = defaultdict(list)
#         for i in range(len(mentions)):
#             groups[find(i)].append(i)

#         clusters: list[Cluster] = []
#         for cluster_id, idxs in enumerate(groups.values()):
#             canonical_idx = max(idxs, key=lambda i: len(mentions[i].text))
#             clusters.append(Cluster(
#                 cluster_id=cluster_id,
#                 canonical_name=mentions[canonical_idx].text,
#                 type=mentions[canonical_idx].type or "",
#             ))
#             for i in idxs:
#                 mentions[i].cluster_id = cluster_id

#         return clusters

#     def _candidates(self, text: str, mentions: list[Mention]) -> list[tuple]:
#         doc = self._sent_nlp(text)
#         candidates = []
#         for sent in doc.sents:
#             s_start, s_end = sent.start_char, sent.end_char
#             sent_text = sent.text
#             in_sent = [
#                 m for m in mentions
#                 if m.start >= s_start and m.end <= s_end and m.type
#             ]
#             for subj in in_sent:
#                 for obj in in_sent:
#                     if subj is obj:
#                         continue
#                     if subj.type and obj.type and self.ontology.allows(subj.type, obj.type):
#                         candidates.append((sent_text, subj, obj))
#         return candidates

#     def _classify(
#         self,
#         candidate: tuple,
#         clusters: list[Cluster],
#         confidence: float,
#     ) -> Optional[Triple]:
#         sent_text, subj, obj = candidate
#         subj_in_sent = sent_text.find(subj.text)
#         obj_in_sent = sent_text.find(obj.text)
#         if subj_in_sent == -1 or obj_in_sent == -1:
#             return None

#         marked = self._insert_markers(sent_text, subj.text, obj.text,
#                                       subj_in_sent, obj_in_sent)
#         encoded = self.tokenizer(
#             marked,
#             return_tensors="pt",
#             truncation=True,
#             max_length=512,
#         ).to(self.device)

#         input_ids = encoded["input_ids"][0].tolist()
#         e1_id = self.tokenizer.convert_tokens_to_ids(self.E1)
#         e2_id = self.tokenizer.convert_tokens_to_ids(self.E2)

#         try:
#             e1_pos = input_ids.index(e1_id)
#             e2_pos = input_ids.index(e2_id)
#         except ValueError:
#             return None

#         with torch.no_grad():
#             logits = self.re_model(
#                 input_ids=encoded["input_ids"],
#                 attention_mask=encoded["attention_mask"],
#                 e1_pos=[e1_pos],
#                 e2_pos=[e2_pos],
#             )

#         probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
#         pred_id = int(np.argmax(probs))
#         conf = float(probs[pred_id])
#         predicate = self.ontology.id2label[pred_id]

#         if predicate == "no_relation" or conf < confidence:
#             return None

#         negated, modality = self._validate(sent_text)

#         if subj.cluster_id is None or obj.cluster_id is None:
#             return None

#         subj_cluster = next((c for c in clusters if c.cluster_id == subj.cluster_id), None)
#         obj_cluster = next((c for c in clusters if c.cluster_id == obj.cluster_id), None)

#         return Triple(
#             subject_id=subj.cluster_id,
#             predicate=predicate,
#             object_id=obj.cluster_id,
#             subject_name=subj_cluster.canonical_name if subj_cluster else subj.text,
#             object_name=obj_cluster.canonical_name if obj_cluster else obj.text,
#             confidence=round(conf, 4),
#             negated=negated,
#             modality=modality,
#             source_sentence=sent_text,
#         )

#     def _insert_markers(
#         self,
#         sentence: str,
#         subj_text: str,
#         obj_text: str,
#         subj_pos: int,
#         obj_pos: int,
#     ) -> str:
#         subj_end = subj_pos + len(subj_text)
#         obj_end = obj_pos + len(obj_text)
#         if subj_pos < obj_pos:
#             return (
#                 sentence[:subj_pos]
#                 + f"{self.E1} {subj_text} {self.E1_END}"
#                 + sentence[subj_end:obj_pos]
#                 + f"{self.E2} {obj_text} {self.E2_END}"
#                 + sentence[obj_end:]
#             )
#         return (
#             sentence[:obj_pos]
#             + f"{self.E2} {obj_text} {self.E2_END}"
#             + sentence[obj_end:subj_pos]
#             + f"{self.E1} {subj_text} {self.E1_END}"
#             + sentence[subj_end:]
#         )

#     @staticmethod
#     def _validate(sentence: str) -> tuple[bool, str]:
#         tokens = set(sentence.lower().split())
#         negated = bool(tokens & NEGATION_WORDS)
#         if tokens & PLAN_WORDS:
#             modality = "planned"
#         elif tokens & HEDGE_WORDS:
#             modality = "reported"
#         else:
#             modality = "asserted"
#         return negated, modality

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Optional

import spacy
import yaml
import json
from google import genai
from spacy.language import Language


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

@dataclass
class Mention:
    text: str
    start: int
    end: int
    type: str | None = None
    is_pronoun: bool = False
    cluster_id: int | None = None


@dataclass
class Cluster:
    cluster_id: int
    canonical_name: str
    type: str


@dataclass
class Triple:
    subject_id: int
    predicate: str
    object_id: int
    subject_name: str
    object_name: str
    confidence: float
    negated: bool = False
    modality: str = "asserted"
    source_sentence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Ontology loader
# ---------------------------------------------------------------------------

class Ontology:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        self.spacy_label_map: dict[str, str] = cfg.get("spacy_label_map", {})
        self.relations: list[dict] = cfg.get("relations", [])
        self.labels: list[str] = ["no_relation"] + [r["name"] for r in self.relations]
        self.label2id: dict[str, int] = {l: i for i, l in enumerate(self.labels)}
        self.id2label: dict[int, str] = {i: l for l, i in self.label2id.items()}

        self._type_pairs: dict[tuple[str, str], list[str]] = {}
        for r in self.relations:
            key = (r["subject"], r["object"])
            self._type_pairs.setdefault(key, []).append(r["name"])

    def allows(self, subj_type: str, obj_type: str) -> bool:
        return (subj_type, obj_type) in self._type_pairs

    @property
    def num_labels(self) -> int:
        return len(self.labels)


# ---------------------------------------------------------------------------
# RE model
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "without", "n't"}
HEDGE_WORDS = {"allegedly", "reportedly", "apparently", "claimed", "accused",
               "said", "told", "according"}
PLAN_WORDS = {"plans", "planning", "intends", "intending", "aims", "aiming",
              "expected", "seeking"}


# ---------------------------------------------------------------------------
# Main BL class
# ---------------------------------------------------------------------------

class RelationOps:
    """
    Relation extraction pipeline: NER → coref → candidates → IndicBERT classify → triples.
    Construct once (via lifespan), call get_relations() per request.
    """

    E1 = "[E1]"; E1_END = "[/E1]"
    E2 = "[E2]"; E2_END = "[/E2]"

    def __init__(
        self,
        nlp: Language,
        model_name: str = "ai4bharat/IndicBERTv2-MLM-only",
        relations_config: str = "app/config/relations.yaml",
    ):
       # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.nlp = nlp  # settings.NLP — used for entity extraction in _ner()
        self.ontology = Ontology(relations_config)

        # lightweight sentencizer for sentence-level candidate generation
        if any(p in nlp.pipe_names for p in ("sentencizer", "senter", "parser")):
            self._sent_nlp = nlp
        else:
            self._sent_nlp = spacy.blank("en")
            self._sent_nlp.add_pipe("sentencizer")

        self.gemini_client = genai.Client(api_key="#")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_relations(self, text: str, confidence: float = 0.6) -> dict:
        text = self._clean(text)

        mentions = self._ner(text)
        clusters = self._coref(mentions)

        entity_list = [{"entity": m.text, "type": m.type} for m in mentions]

        prompt = f"""
Extract relationships from the text.

TEXT:
{text}

ENTITIES:
{json.dumps(entity_list, indent=2)}

RULES:
- Only use the given entities
- No hallucination
- Extract clear relationships only
- Ignore invalid entities if necessary

Return STRICT JSON:

{{
  "relations": [
    {{
      "subject": "...",
      "relation": "...",
      "object": "..."
    }}
  ]
}}
"""

        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            output_text = response.text.strip()
            match = re.search(r"\{.*\}", output_text, re.DOTALL)

            if not match:
                return {"relationships": []}

            parsed = json.loads(match.group())
            relations = parsed.get("relations", [])

        except Exception as e:
            print("Gemini RE Error:", e)
            return {"relationships": []}

        # return {
        #     "relationships": [
        #         {
        #             "subj": r["subject"],
        #             "verb": r["relation"],
        #             "obj": r["object"]
        #         }
        #         for r in relations
        #     ]
            
        # }
        relationships = [

            {

                "subj": r["subject"],

                "verb": r["relation"],

                "obj": r["object"]

            }

            for r in relations

        ]

        nodes = {}

        edges = []

        for rel in relationships:

            nodes[rel["subj"]] = {

                "id": rel["subj"]

            }

            nodes[rel["obj"]] = {

                "id": rel["obj"]

            }

            edges.append({

                "from": rel["subj"],

                "to": rel["obj"],

                "label": rel["verb"]

            })

        return {

            "relationships": relationships,

            "graph": {

             "nodes": list(nodes.values()),

            "edges": edges

    }

}

    # ------------------------------------------------------------------
    # Private pipeline stages
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return (
            text.replace("’", "'")
                .replace("“", '"')
                .replace("”", '"')
        )

    def _ner(self, text: str) -> list[Mention]:
        doc = self.nlp(text)
        raw = [(ent.text, ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]

        merged = []
        skip = set()
        for i, (text_i, start_i, end_i, label_i) in enumerate(raw):
            if i in skip:
                continue
            if i + 1 < len(raw):
                text_j, start_j, end_j, label_j = raw[i + 1]
                if start_j - end_i <= 3 and (label_i == "ORG" or label_j == "ORG"):
                    merged.append((text[start_i:end_j], start_i, end_j, "ORG"))
                    skip.add(i + 1)
                    continue
            merged.append((text_i, start_i, end_i, label_i))

        mentions = []
        for (ent_text, start, end, label) in merged:
            canonical = self.ontology.spacy_label_map.get(label)
            if canonical is None:
                continue
            mentions.append(Mention(text=ent_text, start=start, end=end, type=canonical))
        return mentions

    def _coref(self, mentions: list[Mention]) -> list[Cluster]:
        if not mentions:
            return []

        def _norm(s: str) -> str:
            s = s.lower().strip()
            for prefix in ("shri ", "smt. ", "smt ", "dr. ", "dr ", "mr. ",
                           "mr ", "ms. ", "ms ", "prof. ", "prof ", "justice ",
                           "lt. gen. ", "adv. ", "ca "):
                if s.startswith(prefix):
                    s = s[len(prefix):]
            return s.rstrip(" ji").strip()

        norms = [_norm(m.text) for m in mentions]
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
                if ni == nj:
                    union(i, j)
                elif len(ni) >= 4 and len(nj) >= 4 and (ni in nj or nj in ni):
                    union(i, j)

        groups: dict[int, list[int]] = defaultdict(list)
        for i in range(len(mentions)):
            groups[find(i)].append(i)

        clusters: list[Cluster] = []
        for cluster_id, idxs in enumerate(groups.values()):
            canonical_idx = max(idxs, key=lambda i: len(mentions[i].text))
            clusters.append(Cluster(
                cluster_id=cluster_id,
                canonical_name=mentions[canonical_idx].text,
                type=mentions[canonical_idx].type or "",
            ))
            for i in idxs:
                mentions[i].cluster_id = cluster_id

        return clusters

    def _candidates(self, text: str, mentions: list[Mention]) -> list[tuple]:
        doc = self._sent_nlp(text)
        candidates = []
        for sent in doc.sents:
            s_start, s_end = sent.start_char, sent.end_char
            sent_text = sent.text
            in_sent = [
                m for m in mentions
                if m.start >= s_start and m.end <= s_end and m.type
            ]
            for subj in in_sent:
                for obj in in_sent:
                    if subj is obj:
                        continue
                    if subj.type and obj.type and self.ontology.allows(subj.type, obj.type):
                        candidates.append((sent_text, subj, obj))
        return candidates

    def _classify(
        self,
        candidate: tuple,
        clusters: list[Cluster],
        confidence: float,
    ) -> Optional[Triple]:
        sent_text, subj, obj = candidate
        subj_in_sent = sent_text.find(subj.text)
        obj_in_sent = sent_text.find(obj.text)
        if subj_in_sent == -1 or obj_in_sent == -1:
            return None

        marked = self._insert_markers(sent_text, subj.text, obj.text,
                                      subj_in_sent, obj_in_sent)
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
            return None

        with torch.no_grad():
            logits = self.re_model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                e1_pos=[e1_pos],
                e2_pos=[e2_pos],
            )

        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        pred_id = int(np.argmax(probs))
        conf = float(probs[pred_id])
        predicate = self.ontology.id2label[pred_id]

        if predicate == "no_relation" or conf < confidence:
            return None

        negated, modality = self._validate(sent_text)

        if subj.cluster_id is None or obj.cluster_id is None:
            return None

        subj_cluster = next((c for c in clusters if c.cluster_id == subj.cluster_id), None)
        obj_cluster = next((c for c in clusters if c.cluster_id == obj.cluster_id), None)

        return Triple(
            subject_id=subj.cluster_id,
            predicate=predicate,
            object_id=obj.cluster_id,
            subject_name=subj_cluster.canonical_name if subj_cluster else subj.text,
            object_name=obj_cluster.canonical_name if obj_cluster else obj.text,
            confidence=round(conf, 4),
            negated=negated,
            modality=modality,
            source_sentence=sent_text,
        )

    def _insert_markers(
        self,
        sentence: str,
        subj_text: str,
        obj_text: str,
        subj_pos: int,
        obj_pos: int,
    ) -> str:
        subj_end = subj_pos + len(subj_text)
        obj_end = obj_pos + len(obj_text)
        if subj_pos < obj_pos:
            return (
                sentence[:subj_pos]
                + f"{self.E1} {subj_text} {self.E1_END}"
                + sentence[subj_end:obj_pos]
                + f"{self.E2} {obj_text} {self.E2_END}"
                + sentence[obj_end:]
            )
        return (
            sentence[:obj_pos]
            + f"{self.E2} {obj_text} {self.E2_END}"
            + sentence[obj_end:subj_pos]
            + f"{self.E1} {subj_text} {self.E1_END}"
            + sentence[subj_end:]
        )

    @staticmethod
    def _validate(sentence: str) -> tuple[bool, str]:
        tokens = set(sentence.lower().split())
        negated = bool(tokens & NEGATION_WORDS)
        if tokens & PLAN_WORDS:
            modality = "planned"
        elif tokens & HEDGE_WORDS:
            modality = "reported"
        else:
            modality = "asserted"
        return negated, modality
