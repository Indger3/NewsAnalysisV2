import json
import re
from difflib import SequenceMatcher


class NormalizationOps:

    def __init__(self):

        with open(
            "app/config/normalization_config.json",
            "r",
            encoding="utf-8"
        ) as f:
            config = json.load(f)

        self.TITLES = set(config["titles"])
        self.STRICT_SUFFIXES = set(config["strict_suffixes"])
        self.AMBIGUOUS_SUFFIXES = set(config["ambiguous_suffixes"])
        self.ORG_SUFFIXES = set(config.get("org_suffixes", []))

        abbreviations = config.get("abbreviations", {})

        self.ABBR_GENERAL = abbreviations.get("general", {})
        self.ABBR_ORG = abbreviations.get("organization", {})
        self.ABBR_LEGAL = abbreviations.get("legal", {})

    def extract_entity_texts(self, entities):

        clean_list = []

        for e in entities:

            if isinstance(e, dict):

                label = e.get("label")

                if label not in {"PERSON", "ORG"}:
                    continue

                clean_list.append(e.get("entity", ""))

            else:

                clean_list.append(e)

        return clean_list

    def expand_abbreviations(self, entity):

        words = entity.split()
        lower_words = [w.lower() for w in words]

        expanded = []

        for i, (w, lw) in enumerate(zip(words, lower_words)):

            if lw == "inc":

                if len(words) == 1:
                    expanded.append("indian national congress")
                    continue

                if entity.strip().upper() == entity.strip():
                    expanded.append("indian national congress")
                    continue

                if i == len(words) - 1:
                    expanded.append("incorporated")
                    continue

                expanded.append("inc")
                continue

            if lw in self.ABBR_GENERAL:
                expanded.append(self.ABBR_GENERAL[lw])
                continue

            if lw in self.ABBR_ORG:
                expanded.append(self.ABBR_ORG[lw])
                continue

            if lw in self.ABBR_LEGAL:
                expanded.append(self.ABBR_LEGAL[lw])
                continue

            expanded.append(lw)

        return " ".join(expanded)

    def clean_entity(self, entity):

        entity = entity.lower()

        entity = re.sub(r"(?:'|’)s\b", "", entity, flags=re.IGNORECASE)

        entity = re.sub(r"[^\w\s]", "", entity)

        entity = self.expand_abbreviations(entity)

        words = entity.split()

        words = [w for w in words if w not in self.TITLES]

        if not words:
            return ""

        if len(words) > 1 and words[-1] in self.STRICT_SUFFIXES:
            words = words[:-1]

        if len(words) > 1 and words[-1] in self.AMBIGUOUS_SUFFIXES:

            last = words[-1]

            if len(words) == 2:
                pass

            elif len(words) >= 3:
                words = words[:-1]

            if words.count(last) > 1:
                words = [w for w in words if w != last]

        return " ".join(words).strip()

    def expand_initials(self, entity):

        words = entity.split()

        words = [w for w in words if len(w) > 1]

        return " ".join(words)

    def indian_soundex(self, name):

        name = name.lower()

        name = name.replace("ch", "2")

        mapping = {
            "a": "0",
            "e": "0",
            "i": "0",
            "o": "0",
            "u": "0",
            "v": "0",
            "y": "0",
            "h": "0",
            "w": "0",
            "k": "1",
            "g": "1",
            "q": "1",
            "c": "1",
            "j": "2",
            "t": "3",
            "d": "3",
            "z": "4",
            "x": "4",
            "m": "5",
            "p": "6",
            "f": "6",
            "b": "6",
            "l": "7",
            "s": "8",
            "r": "9",
            "n": "!"
        }

        encoded = []

        for ch in name:

            if ch in mapping:
                encoded.append(mapping[ch])

            elif ch.isdigit():
                encoded.append(ch)

        result = []
        prev = None

        for c in encoded:

            if c != prev:
                result.append(c)

            prev = c

        return "".join(result)

    def similarity(self, a, b):

        lev = SequenceMatcher(None, a, b).ratio()

        jw = lev

        sx_score = (
            1.0
            if self.indian_soundex(a)
            == self.indian_soundex(b)
            else 0.0
        )

        base = 0.5 * lev + 0.3 * jw + 0.2 * sx_score

        if a in b or b in a:
            base = max(base, 0.9)

        if a.split()[-1] == b.split()[-1]:
            base = max(base, 0.88)

        return base

    def context_score(self, e1, e2, text):

        text = text.lower()

        window = 40

        def get_context(entity):

            positions = [
                m.start()
                for m in re.finditer(entity, text)
            ]

            contexts = []

            for pos in positions:

                contexts.append(
                    text[max(0, pos - window):pos + window]
                )

            return contexts

        for x in get_context(e1):
            for y in get_context(e2):

                if SequenceMatcher(None, x, y).ratio() > 0.75:
                    return 1.0

        return 0.0

    def relation_score(self, e1, e2, relations):

        if not relations:
            return 0.0

        score = 0.0

        for relation in relations:

            subj = relation.get("subj", "").lower()
            obj = relation.get("obj", "").lower()
            verb = relation.get("verb", "").lower()

            e1_lower = e1.lower()
            e2_lower = e2.lower()

            #
            # Direct relation overlap
            #
            if (
                (e1_lower in subj or e1_lower in obj)
                and
                (e2_lower in subj or e2_lower in obj)
            ):
                score += 0.30

            #
            # Same object + same relation
            #
            if (
                e1_lower in subj
                and
                e2_lower in subj
            ):
                score += 0.20

            #
            # Same target
            #
            if (
                e1_lower in subj
                and
                e2_lower in subj
                and
                obj
            ):
                score += 0.20

            return min(score, 0.60)

    def choose_canonical(self, cluster):

        cleaned_pairs = [
            (e, self.clean_entity(e))
            for e in cluster
        ]

        groups = {}

        for orig, clean in cleaned_pairs:
            groups.setdefault(clean, []).append(orig)

        best_clean = sorted(
            groups.keys(),
            key=lambda x: (
                -len(x.split()),
                -len(x)
            )
        )[0]

        return best_clean

    def normalize_entities(
        self,
        entities,
        text,
        relations=None,
        threshold=0.85
    ):

        entities = self.extract_entity_texts(entities)

        processed = []

        for e in entities:

            clean = self.clean_entity(e)

            clean = self.expand_initials(clean)

            if clean:
                processed.append((e, clean))

        clusters = []

        used = set()

        for i, (orig1, e1) in enumerate(processed):

            if i in used:
                continue

            cluster = [orig1]

            used.add(i)

            for j, (orig2, e2) in enumerate(processed):

                if j in used:
                    continue

                sim = self.similarity(e1, e2)

                sim += (
                    0.15
                    * self.context_score(
                        e1,
                        e2,
                        text
                    )
                )

                sim += self.relation_score(
                    e1,
                    e2,
                    relations
                )

                if (
                    len(e1.split()) == 1
                    or
                    len(e2.split()) == 1
                ):
                    if sim < 0.9:
                        continue

                if sim >= threshold:

                    cluster.append(orig2)

                    used.add(j)

            clusters.append(cluster)

        mapping = {}

        for cluster in clusters:

            canonical = self.choose_canonical(cluster)

            for e in cluster:
                mapping[e] = canonical

        return mapping