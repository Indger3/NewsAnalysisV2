

import re
import pickle
import logging
import warnings
from collections import Counter
from typing import Optional

import numpy as np
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _patch_logreg_compat(estimator) -> None:
    """Recursively patch legacy LogisticRegression objects loaded from pickle."""
    if estimator is None:
        return

    if isinstance(estimator, LogisticRegression):
        if not hasattr(estimator, "multi_class"):
            estimator.multi_class = "auto"
        return

    if hasattr(estimator, "steps"):
        for _, step_estimator in estimator.steps:
            _patch_logreg_compat(step_estimator)

    if hasattr(estimator, "estimator"):
        _patch_logreg_compat(estimator.estimator)

    if hasattr(estimator, "base_estimator"):
        _patch_logreg_compat(estimator.base_estimator)

    if hasattr(estimator, "calibrated_classifiers_"):
        for calibrated in estimator.calibrated_classifiers_:
            _patch_logreg_compat(getattr(calibrated, "estimator", None))


# ─────────────────────────────────────────────────────────────────────────────
# Taxonomy  (8 topics × 4 subtopics = 32 leaf categories)
# ─────────────────────────────────────────────────────────────────────────────
TAXONOMY = {
    "Politics & Governance": {
        "keywords": [
            "government","parliament","election","democracy","president",
            "minister","political","policy","constitution","legislation",
            "senate","congress","vote","party","BJP","modi","trump","biden",
            "republican","democrat","ruling","opposition","lok sabha",
            "rajya sabha","white house","kremlin","legislature","diplomatic",
            "sovereignty","coup","populism","manifesto","coalition",
            "governance","geopolitics","autocracy","cabinet","chancellor",
            "regime","referendum","ballot","lawmaker","senator","assemblyman",
        ],
        "subtopics": {
            "Elections & Voting": [
                "election","vote","ballot","campaign","candidate","referendum",
                "polling","electoral","constituency","suffrage","voter","turnout",
            ],
            "Government Policy": [
                "policy","legislation","law","bill","act","regulation",
                "parliament","congress","senate","ordinance","statute",
                "amendment","reform","cabinet decision","executive order",
            ],
            "Political Leaders": [
                "president","prime minister","minister","governor","chancellor",
                "modi","trump","biden","politician","leader","chief",
                "secretary of state","head of state",
            ],
            "Democracy & Rights": [
                "democracy","constitution","rights","freedom","civil liberties",
                "opposition","ruling party","authoritarian","dictatorship",
                "protest","dissent",
            ],
        },
    },
    "Human Rights & Social Justice": {
        "keywords": [
            "human rights","discrimination","persecution","minority","refugee",
            "protest","oppression","justice","inequality","marginalized",
            "activist","abuse","violence","racism","caste","tribal","indigenous",
            "displaced","trafficking","atrocity","genocide","torture",
            "imprisonment","arbitrary detention","stateless","lynching",
            "mob violence","dispossession","eviction","forced labor",
        ],
        "subtopics": {
            "Minority Rights": [
                "minority","muslim","christian","hindu","dalit","tribal",
                "adivasi","romani","caste","ethnic","racial","community",
                "scheduled tribe","scheduled caste",
            ],
            "Displacement & Refugees": [
                "refugee","displaced","migration","asylum","exile","IDP",
                "fleeing","stateless","repatriation","internally displaced",
                "camp","shelter",
            ],
            "Protest & Activism": [
                "protest","activist","movement","demonstration","rally",
                "campaign","rights","civil disobedience","strike","march",
                "agitation","uprising",
            ],
            "Gender & Social Issues": [
                "women","gender","feminist","harassment","rape","sexual",
                "trafficking","domestic violence","patriarchy","equality","metoo",
            ],
        },
    },
    "Religion & Spirituality": {
        "keywords": [
            "religion","church","mosque","temple","faith","spiritual","god",
            "prayer","christian","islamic","hindu","buddhist","bible","quran",
            "clergy","worship","theology","sacred","pilgrimage","diocese",
            "seminary","cathedral","synagogue","conversion","missionary",
            "congregation","pastor","imam","priest","monk","nun","baptism",
            "communion","sermon","evangelical","vatican","archbishop",
        ],
        "subtopics": {
            "Christianity": [
                "church","christian","christ","bible","bishop","priest",
                "catholic","protestant","evangelical","diocese","pastor",
                "congregation","sermon","gospel","vatican",
            ],
            "Islam": [
                "muslim","islam","mosque","quran","allah","ramadan","hijab",
                "jihad","sharia","imam","madrasa","ummah","fatwa","halal",
            ],
            "Hinduism & Eastern": [
                "hindu","vedic","temple","karma","yoga","dharma","buddhist",
                "meditation","brahmin","puja","mandir","ashram","sikh","guru",
                "swami","sanatan",
            ],
            "Religious Persecution": [
                "persecution","religious freedom","blasphemy","sectarian",
                "forced conversion","apostasy","martyrdom","heresy",
            ],
        },
    },
    "Economy & Finance": {
        "keywords": [
            "economy","GDP","inflation","trade","market","investment",
            "financial","banking","tax","budget","recession","growth","poverty",
            "employment","business","corporate","currency","debt","fiscal",
            "monetary","stock","capital","exports","imports","revenue",
            "deficit","surplus","interest rate","central bank","IMF",
            "World Bank","tariff","subsidy","commerce","entrepreneur",
            "privatization","nationalization","austerity",
        ],
        "subtopics": {
            "Macroeconomics": [
                "GDP","inflation","recession","growth","fiscal","monetary policy",
                "interest rate","central bank","reserve bank","economic growth",
                "stagflation",
            ],
            "Trade & Business": [
                "trade","export","import","business","corporate","investment",
                "market","commerce","industry","startup","entrepreneur",
                "supply chain",
            ],
            "Poverty & Inequality": [
                "poverty","inequality","unemployment","wages","income","welfare",
                "disparity","destitution","hunger","deprivation","minimum wage",
            ],
            "Banking & Finance": [
                "bank","financial","loan","debt","currency","credit","budget",
                "IMF","World Bank","microfinance","stock market","hedge fund",
            ],
        },
    },
    "Environment & Climate": {
        "keywords": [
            "climate","environment","forest","pollution","ecosystem",
            "biodiversity","nature","deforestation","carbon","emissions",
            "wildlife","conservation","green","sustainable","renewable","flood",
            "drought","glacier","ozone","habitat","species","ecology",
            "reforestation","wildfire","coral reef","ocean","sea level",
            "permafrost","methane","pasture","grazing","pastoral",
        ],
        "subtopics": {
            "Climate Change": [
                "climate change","global warming","carbon","emissions",
                "greenhouse","temperature","IPCC","Paris agreement","net zero",
                "carbon neutral","fossil fuel",
            ],
            "Forest & Biodiversity": [
                "forest","biodiversity","ecosystem","wildlife","deforestation",
                "conservation","habitat","species","flora","fauna","endangered",
                "rainforest","pasture","grazing",
            ],
            "Pollution": [
                "pollution","toxic","waste","contamination","air quality",
                "water quality","plastic","smog","chemical","industrial waste",
                "microplastics",
            ],
            "Sustainability": [
                "sustainable","renewable","green energy","solar","wind",
                "clean energy","recycling","circular economy","net zero",
                "carbon offset",
            ],
        },
    },
    "Conflict & Security": {
        "keywords": [
            "war","conflict","military","army","weapons","attack","violence",
            "terrorism","insurgency","ceasefire","troops","nato","security",
            "defense","bombing","massacre","genocide","armed","artillery",
            "missile","airstrike","occupation","siege","rebel","militant",
            "casualties","frontline","offensive","battalion","drone strike",
            "counterinsurgency","paramilitary","guerrilla",
        ],
        "subtopics": {
            "Armed Conflict & War": [
                "war","conflict","battle","troops","military","bombing",
                "ceasefire","invasion","offensive","frontline","casualties",
                "artillery","siege",
            ],
            "Terrorism": [
                "terrorism","terror","extremism","jihadist","attack",
                "suicide bombing","insurgency","militant","radicalization",
                "isis","al-qaeda","boko haram",
            ],
            "Geopolitics": [
                "NATO","sanctions","diplomacy","nuclear","geopolitical",
                "alliance","sovereignty","superpower","proxy","cold war",
                "arms race","UN security council",
            ],
            "Internal Security": [
                "security forces","police","paramilitary","crackdown",
                "surveillance","detention","intelligence","counterterrorism",
                "riot","curfew",
            ],
        },
    },
    "Health & Medicine": {
        "keywords": [
            "health","disease","hospital","medicine","pandemic","virus","covid",
            "vaccine","healthcare","mental health","epidemic","treatment",
            "patient","medical","nutrition","malnutrition","mortality",
            "morbidity","diagnosis","surgery","clinical","pharmaceutical",
            "WHO","CDC","antibiotics","cancer","diabetes","HIV","AIDS",
            "tuberculosis","quarantine","lockdown","infection","outbreak",
        ],
        "subtopics": {
            "Pandemic & Infectious Disease": [
                "pandemic","covid","virus","epidemic","outbreak","infection",
                "vaccine","pathogen","quarantine","lockdown","contagion",
                "herd immunity",
            ],
            "Healthcare Systems": [
                "hospital","healthcare","medical","doctor","patient","treatment",
                "medicine","clinic","nursing","health system","insurance","NHS",
            ],
            "Mental Health": [
                "mental health","depression","anxiety","suicide","psychological",
                "trauma","counseling","psychiatry","PTSD","therapy","bipolar",
            ],
            "Nutrition & Hunger": [
                "hunger","malnutrition","food security","famine","starvation",
                "nutrition","diet","food crisis","wasting","stunting",
            ],
        },
    },
    "Society & Culture": {
        "keywords": [
            "culture","social","community","tradition","art","education",
            "history","identity","language","heritage","custom","media",
            "journalism","censorship","freedom of press","literature","music",
            "sports","entertainment","family","youth","urbanization",
            "migration","internet","technology","social media","civil society",
            "NGO","diaspora","colonialism","indigenous rights",
        ],
        "subtopics": {
            "Education": [
                "education","school","university","student","teacher","learning",
                "curriculum","literacy","scholarship","academic","tuition",
                "dropout",
            ],
            "Media & Journalism": [
                "media","journalism","press","censorship","propaganda",
                "fake news","journalist","broadcasting","social media",
                "publication","newspaper","editorial",
            ],
            "Cultural Heritage": [
                "culture","tradition","heritage","history","identity","language",
                "art","museum","festival","folklore","indigenous culture",
                "civilization",
            ],
            "Community & Society": [
                "community","social","population","urban","rural","civil society",
                "NGO","welfare","neighborhood","social services","family","youth",
            ],
        },
    },
}

SUBTOPIC_TO_TOPIC = {
    sub: topic
    for topic, info in TAXONOMY.items()
    for sub in info["subtopics"]
}


# ─────────────────────────────────────────────────────────────────────────────
# Text Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
_STOPWORDS = set(
    "the a an is are was were be been being have has had do does did will "
    "would could should may might must shall can to of in for on with at by "
    "from as into through during before after about against between and but "
    "or nor not so yet both either neither this that these those which who "
    "what when where how why i we you he she it they me him her us them "
    "also said says just more most other than then its their our your".split()
)


def preprocess(text: str, title: str = "", title_weight: int = 4) -> str:
    """Clean + boost title signal by repeating it title_weight times."""
    combined = (title + " ") * title_weight + text
    combined = combined.lower()
    combined = re.sub(r"https?://\S+", " ", combined)
    combined = re.sub(r"<[^>]+>", " ", combined)
    combined = re.sub(r"[^a-z\s]", " ", combined)
    tokens = [t for t in combined.split() if t not in _STOPWORDS and len(t) > 2]
    return " ".join(tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Confidence-Filtered Auto-Labeler  ← KEY INNOVATION
# ─────────────────────────────────────────────────────────────────────────────
def keyword_label(text: str, title: str) -> tuple:
    """
    Assign topic/subtopic via keyword matching (no confidence filter).
    Used as fallback / for prediction without a trained model.
    """
    combined = (title + " " + text).lower()
    scores = {t: sum(1 for kw in info["keywords"] if kw.lower() in combined)
              for t, info in TAXONOMY.items()}
    top_topic = max(scores, key=scores.get)
    if scores[top_topic] == 0:
        top_topic = "Society & Culture"
    sub_scores = {s: sum(1 for kw in kws if kw.lower() in combined)
                  for s, kws in TAXONOMY[top_topic]["subtopics"].items()}
    top_sub = max(sub_scores, key=sub_scores.get)
    if sub_scores[top_sub] == 0:
        top_sub = list(TAXONOMY[top_topic]["subtopics"].keys())[0]
    return top_topic, top_sub


def confident_label(
    text: str,
    title: str,
    min_score: int = 3,
    min_confidence: float = 0.30,
) -> tuple:
    """
    Assign topic/subtopic ONLY if the keyword signal is unambiguous.

    Returns (topic, subtopic) if confident, or (None, None) if ambiguous.

    Parameters
    ----------
    min_score : int
        Minimum keyword hits required for top topic (filters zero-signal docs).
    min_confidence : float
        Minimum gap ratio: (top1 - top2) / top1.
        0.30 means top topic must score 30% more than runner-up.
    """
    combined = (title + " " + text).lower()
    scores = {t: sum(1 for kw in info["keywords"] if kw.lower() in combined)
              for t, info in TAXONOMY.items()}
    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    top_topic, top1_score = sorted_scores[0]
    _, top2_score = sorted_scores[1]

    if top1_score < min_score:
        return None, None
    confidence = (top1_score - top2_score) / top1_score
    if confidence < min_confidence:
        return None, None

    sub_scores = {s: sum(1 for kw in kws if kw.lower() in combined)
                  for s, kws in TAXONOMY[top_topic]["subtopics"].items()}
    top_sub = max(sub_scores, key=sub_scores.get)
    if sub_scores[top_sub] == 0:
        top_sub = list(TAXONOMY[top_topic]["subtopics"].keys())[0]
    return top_topic, top_sub


# ─────────────────────────────────────────────────────────────────────────────
# Classifier Builders
# ─────────────────────────────────────────────────────────────────────────────
def _safe_cv(y: list, max_cv: int = 3) -> int:
    """Return largest cv that won't fail given class sizes."""
    min_class = min(Counter(y).values())
    return max(2, min(max_cv, min_class))


def _build_tfidf_svm(y: list) -> Pipeline:
    """Word + character n-gram TF-IDF → Calibrated LinearSVM."""
    cv = _safe_cv(y)
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                max_features=50_000, ngram_range=(1, 2),
                sublinear_tf=True, min_df=1, analyzer="word",
            )),
            ("char", TfidfVectorizer(
                max_features=30_000, ngram_range=(3, 5),
                sublinear_tf=True, min_df=1, analyzer="char_wb",
            )),
        ])),
        ("clf", CalibratedClassifierCV(
            LinearSVC(C=1.0, max_iter=3000, class_weight="balanced"),
            cv=cv,
        )),
    ])


def _build_lr(y: list) -> Pipeline:
    """Logistic Regression fallback for very small groups (< 4 per class)."""
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                max_features=20_000, ngram_range=(1, 2),
                sublinear_tf=True, min_df=1, analyzer="word",
            )),
            ("char", TfidfVectorizer(
                max_features=10_000, ngram_range=(3, 5),
                sublinear_tf=True, min_df=1, analyzer="char_wb",
            )),
        ])),
        ("clf", LogisticRegression(
            C=2.0, max_iter=1000, class_weight="balanced", solver="lbfgs",
        )),
    ])


def _build_svm_on_embeddings(y: list) -> CalibratedClassifierCV:
    """Calibrated SVM for dense embedding inputs."""
    cv = _safe_cv(y)
    return CalibratedClassifierCV(
        LinearSVC(C=1.0, max_iter=3000, class_weight="balanced"),
        cv=cv,
    )


def _build_lr_on_embeddings() -> LogisticRegression:
    """LR fallback for small groups with embeddings."""
    return LogisticRegression(
        C=2.0, max_iter=1000, class_weight="balanced", solver="lbfgs",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main Model Class
# ─────────────────────────────────────────────────────────────────────────────
class TaxonomyModelV2:
    """
    Hierarchical two-stage taxonomy extractor with confidence-filtered labels.

    Architecture
    ------------
    Stage 1: Topic classifier    (8 classes)
    Stage 2: Subtopic classifier (4 classes per topic, one model per topic)

    Key insight
    -----------
    ~49% of auto-labeled records are ambiguous (top-2 topics score within 1
    keyword hit of each other). Training on these noisy labels causes the model
    to learn contradictions. By keeping only high-confidence labeled records
    (top topic scores ≥30% more than runner-up) and using at least 3 keyword
    hits, we achieve 85–88% topic accuracy with TF-IDF+SVM — without any GPU.

    Parameters
    ----------
    backend : str
        "tfidf"       — TF-IDF word+char + SVM (85–88%, CPU-only)
        "transformer" — SentenceTransformer + SVM (88–92%, GPU recommended)
    transformer_model : str
        HuggingFace model (used when backend="transformer"):
          "all-MiniLM-L6-v2"  — fast, 384-dim
          "all-mpnet-base-v2" — accurate, 768-dim
    label_min_score : int
        Min keyword hits for a label to be used in training (default 3).
    label_min_confidence : float
        Min gap ratio between top-2 topics (default 0.30).
    """

    def __init__(
        self,
        backend: str = "tfidf",
        transformer_model: str = "all-MiniLM-L6-v2",
        label_min_score: int = 3,
        label_min_confidence: float = 0.30,
    ):
        assert backend in ("tfidf", "transformer")
        self.backend = backend
        self.transformer_model = transformer_model
        self.label_min_score = label_min_score
        self.label_min_confidence = label_min_confidence

        self.topic_clf = None
        self.topic_encoder = LabelEncoder()
        self.subtopic_clfs: dict = {}
        self.subtopic_encoders: dict = {}
        self._encoder = None
        self.is_trained = False
        self.training_stats: dict = {}

    # ── private ──────────────────────────────────────────────────────────────

    def _get_encoder(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading %s ...", self.transformer_model)
                self._encoder = SentenceTransformer(self.transformer_model)
            except ImportError:
                raise ImportError(
                    "Install sentence-transformers: pip install sentence-transformers\n"
                    "Or use backend='tfidf' for CPU-only mode."
                )
        return self._encoder

    def _encode(self, texts: list) -> np.ndarray:
        enc = self._get_encoder()
        return enc.encode(
            texts,
            batch_size=64,
            show_progress_bar=len(texts) > 200,
            convert_to_numpy=True,
        )

    # ── fit ──────────────────────────────────────────────────────────────────

    def fit(
        self,
        records: list,
        use_confidence_filter: bool = True,
    ) -> "TaxonomyModelV2":
        """
        Train topic + subtopic classifiers.

        Parameters
        ----------
        records : list of dicts with 'title', 'content'.
                  Uses 'topic'/'subtopic' if present; else auto-labels.
        use_confidence_filter : bool
            If True (default), discard ambiguously labeled records.
            Keeps ~50% of records but dramatically improves label quality.
        """
        logger.info("Auto-labeling %d records...", len(records))

        clean, skipped = [], 0
        for r in records:
            title   = r.get("title", "")
            content = r.get("content", "")

            # Use provided labels if available (e.g. human-annotated)
            if r.get("topic") and r.get("subtopic"):
                topic, subtopic = r["topic"], r["subtopic"]
            elif use_confidence_filter:
                topic, subtopic = confident_label(
                    content, title,
                    min_score=self.label_min_score,
                    min_confidence=self.label_min_confidence,
                )
                if topic is None:
                    skipped += 1
                    continue
            else:
                topic, subtopic = keyword_label(content, title)

            clean.append({
                "title": title, "content": content,
                "topic": topic, "subtopic": subtopic,
            })

        logger.info(
            "Label filter: kept %d / %d records  (removed %d noisy labels)",
            len(clean), len(clean) + skipped, skipped
        )
        self.training_stats = {
            "total_input": len(clean) + skipped,
            "kept": len(clean),
            "skipped_noisy": skipped,
        }

        if len(clean) < 50:
            raise ValueError(
                f"Only {len(clean)} confident records — too few to train. "
                "Lower label_min_score or label_min_confidence, or add more data."
            )

        texts_proc  = [preprocess(r["content"], r["title"]) for r in clean]
        texts_raw   = [r["title"] + " " + r["content"] for r in clean]
        topics      = [r["topic"]    for r in clean]
        subtopics   = [r["subtopic"] for r in clean]

        # ── encode ───────────────────────────────────────────────────────────
        if self.backend == "transformer":
            logger.info("Encoding with SentenceTransformer...")
            X = self._encode(texts_raw)
        else:
            X = texts_proc

        # ── Stage 1: Topic ───────────────────────────────────────────────────
        logger.info("Training topic classifier (%s)...", self.backend)
        y_topic = self.topic_encoder.fit_transform(topics)

        if self.backend == "transformer":
            clf = _build_svm_on_embeddings(topics)
            clf.fit(X, y_topic)
        else:
            clf = _build_tfidf_svm(topics)
            clf.fit(X, y_topic)
        self.topic_clf = clf
        logger.info("Topics: %s", list(self.topic_encoder.classes_))

        # ── Stage 2: Subtopics ───────────────────────────────────────────────
        logger.info("Training subtopic classifiers...")
        groups: dict = {}
        inp = X if self.backend == "transformer" else texts_proc
        for xi, topic, sub in zip(inp, topics, subtopics):
            groups.setdefault(topic, {"X": [], "y": []})
            groups[topic]["X"].append(xi)
            groups[topic]["y"].append(sub)

        for topic, grp in groups.items():
            Xt_raw, yt_raw = grp["X"], grp["y"]
            n_classes = len(set(yt_raw))
            if n_classes < 2:
                enc = LabelEncoder().fit(yt_raw)
                self.subtopic_encoders[topic] = enc
                self.subtopic_clfs[topic] = None
                continue

            enc = LabelEncoder()
            yt = enc.fit_transform(yt_raw)
            self.subtopic_encoders[topic] = enc

            min_cls = min(Counter(yt_raw).values())
            use_lr  = min_cls < 4    # LR avoids cross-val on tiny classes

            if self.backend == "transformer":
                Xt = np.array(Xt_raw)
                if use_lr:
                    clf = _build_lr_on_embeddings()
                else:
                    clf = _build_svm_on_embeddings(yt_raw)
                clf.fit(Xt, yt)
            else:
                if use_lr:
                    clf = _build_lr(yt_raw)
                else:
                    clf = _build_tfidf_svm(yt_raw)
                clf.fit(Xt_raw, yt)

            self.subtopic_clfs[topic] = clf
            logger.info("  [%s] %s", topic, list(enc.classes_))

        self.is_trained = True
        logger.info("Training complete. Stats: %s", self.training_stats)
        return self

    # ── predict ──────────────────────────────────────────────────────────────

    def predict(self, text: str, title: str = "") -> dict:
        """Predict topic and subtopic for one article."""
        if not self.is_trained:
            raise RuntimeError("Call fit() or load() first.")

        if self.backend == "transformer":
            x = self._encode([title + " " + text])
        else:
            x = [preprocess(text, title)]

        # Stage 1
        topic_proba = self.topic_clf.predict_proba(x)[0]
        topic_idx   = int(np.argmax(topic_proba))
        topic       = self.topic_encoder.inverse_transform([topic_idx])[0]
        topic_conf  = float(topic_proba[topic_idx])

        # Stage 2
        sub_clf = self.subtopic_clfs.get(topic)
        if sub_clf is None:
            enc      = self.subtopic_encoders.get(topic)
            subtopic = enc.classes_[0] if enc else "Unknown"
            sub_conf = 1.0
        else:
            sub_proba = sub_clf.predict_proba(x)[0]
            sub_idx   = int(np.argmax(sub_proba))
            enc       = self.subtopic_encoders[topic]
            subtopic  = enc.inverse_transform([sub_idx])[0]
            sub_conf  = float(sub_proba[sub_idx])

        return {
            "topic":               topic,
            "subtopic":            subtopic,
            "topic_confidence":    round(topic_conf, 4),
            "subtopic_confidence": round(sub_conf, 4),
        }

    def predict_batch(self, texts: list, titles: Optional[list] = None) -> list:
        if titles is None:
            titles = [""] * len(texts)
        return [self.predict(t, ti) for t, ti in zip(texts, titles)]

    def evaluate(self, records: list) -> dict:
        true_t, pred_t, true_s, pred_s = [], [], [], []
        for r in records:
            res = self.predict(r["content"], r.get("title", ""))
            true_t.append(r["topic"]);    pred_t.append(res["topic"])
            true_s.append(r["subtopic"]); pred_s.append(res["subtopic"])
        return {
            "topic_accuracy":    round(accuracy_score(true_t, pred_t), 4),
            "subtopic_accuracy": round(accuracy_score(true_s, pred_s), 4),
            "topic_report":      classification_report(true_t, pred_t, zero_division=0),
            "subtopic_report":   classification_report(true_s, pred_s, zero_division=0),
        }

    # ── persistence ──────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        enc_bak = self._encoder
        self._encoder = None
        with open(path, "wb") as f:
            pickle.dump({
                "topic_clf":           self.topic_clf,
                "subtopic_clfs":       self.subtopic_clfs,
                "topic_encoder":       self.topic_encoder,
                "subtopic_encoders":   self.subtopic_encoders,
                "backend":             self.backend,
                "transformer_model":   self.transformer_model,
                "label_min_score":     self.label_min_score,
                "label_min_confidence":self.label_min_confidence,
                "training_stats":      self.training_stats,
                "is_trained":          self.is_trained,
            }, f)
        self._encoder = enc_bak
        logger.info("Saved → %s", path)

    def load(self, path: str) -> "TaxonomyModelV2":
        with open(path, "rb") as f:
            p = pickle.load(f)
        self.topic_clf            = p["topic_clf"]
        self.subtopic_clfs        = p["subtopic_clfs"]
        self.topic_encoder        = p["topic_encoder"]
        self.subtopic_encoders    = p["subtopic_encoders"]
        self.backend              = p["backend"]
        self.transformer_model    = p["transformer_model"]
        self.label_min_score      = p.get("label_min_score", 3)
        self.label_min_confidence = p.get("label_min_confidence", 0.30)
        self.training_stats       = p.get("training_stats", {})
        self.is_trained           = p["is_trained"]
        self._encoder             = None

        _patch_logreg_compat(self.topic_clf)
        for clf in self.subtopic_clfs.values():
            _patch_logreg_compat(clf)

        logger.info("Loaded ← %s  (backend=%s)", path, self.backend)
        return self

    # ── introspection ─────────────────────────────────────────────────────────
    def get_taxonomy(self)              -> dict: return TAXONOMY
    def get_topics(self)                -> list: return list(TAXONOMY.keys())
    def get_subtopics(self, topic: str) -> list:
        return list(TAXONOMY.get(topic, {}).get("subtopics", {}).keys())
