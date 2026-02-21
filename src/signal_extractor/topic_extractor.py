"""
Signal Extractor — Topic & Domain Extractor
=============================================
Extracts topics, entities, and life domains from sentence text.
Runs after TAS, before signal assembly.

Responsibilities:
  1. Keyword extraction — pull meaningful terms from text
  2. Domain classification — map keywords → SignalDomain
  3. Concept normalization — "my job", "work", "career" → "career.job"
  4. Identity statement detection — "I am a...", "I'm the kind of person..."
  5. Emotional intensity scoring — how emotionally charged is this sentence?

Design principle: Fast, rule-based, no LLM calls in hot path.
Operates on a single sentence at a time.
All heavy lifting (spaCy NLP) is done once and the Doc is passed in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from models import SignalDomain


# =============================================================================
# DOMAIN KEYWORD LEXICONS
# =============================================================================
# Each domain has a set of trigger keywords.
# Order matters: more specific domains listed first to avoid broad matches.

DOMAIN_LEXICONS: dict[SignalDomain, set[str]] = {

    SignalDomain.CAREER: {
        "job", "work", "career", "profession", "startup", "company", "business",
        "office", "boss", "colleague", "promotion", "salary", "interview",
        "hired", "fired", "quit", "resign", "employment", "unemployed",
        "freelance", "client", "project", "deadline", "meeting", "team",
        "manager", "leadership", "entrepreneur", "launch", "product",
        "revenue", "investor", "funding", "market", "industry", "role",
        "position", "title", "workplace", "remote", "commute",
    },

    SignalDomain.HEALTH: {
        "health", "fitness", "exercise", "workout", "gym", "run", "running",
        "sleep", "diet", "eating", "food", "weight", "body", "pain",
        "sick", "illness", "doctor", "hospital", "therapy", "meditation",
        "mental health", "anxiety", "depression", "stress", "burnout",
        "energy", "tired", "exhausted", "recover", "injury", "medicine",
        "symptoms", "diagnosis", "treatment", "wellbeing", "healthy",
        "marathon", "training", "yoga", "nutrition", "calories", "rest",
    },

    SignalDomain.RELATIONSHIPS: {
        "relationship", "partner", "spouse", "husband", "wife", "girlfriend",
        "boyfriend", "family", "parent", "mother", "father", "mom", "dad",
        "sister", "brother", "friend", "friendship", "social", "dating",
        "love", "breakup", "divorce", "marriage", "wedding", "lonely",
        "connection", "trust", "conflict", "argument", "communication",
        "support", "together", "apart", "meet", "bond", "attachment",
        "children", "kids", "baby", "grandparent",
    },

    SignalDomain.FINANCES: {
        "money", "finances", "financial", "debt", "loan", "credit", "savings",
        "invest", "investment", "budget", "spend", "spending", "income",
        "salary", "rent", "mortgage", "bills", "afford", "expensive",
        "cheap", "broke", "rich", "wealthy", "poverty", "bank", "account",
        "stock", "crypto", "fund", "retirement", "tax", "insurance",
        "cost", "price", "pay", "payment", "earning",
    },

    SignalDomain.CREATIVITY: {
        "creative", "creativity", "art", "music", "writing", "design",
        "painting", "drawing", "photography", "film", "video", "content",
        "build", "make", "create", "craft", "code", "coding", "program",
        "develop", "project", "side project", "blog", "podcast", "book",
        "novel", "song", "compose", "perform", "publish", "expression",
        "artist", "maker", "creator", "invention",
    },

    SignalDomain.LEARNING: {
        "learn", "learning", "study", "course", "degree", "university",
        "college", "school", "education", "skill", "knowledge", "read",
        "reading", "book", "research", "understand", "practice", "improve",
        "develop", "grow", "certify", "certification", "class", "lecture",
        "teach", "mentor", "tutor", "exam", "test", "grade",
    },

    SignalDomain.IDENTITY: {
        "i am", "i'm a", "i see myself", "my identity", "who i am",
        "i believe in", "my values", "what i stand for", "i define",
        "i consider myself", "i'm the kind of person", "true to myself",
        "authentic", "integrity", "purpose", "meaning", "values",
        "principles", "philosophy", "worldview", "spirituality", "faith",
        "culture", "heritage", "background", "personality",
    },
}

# =============================================================================
# CONCEPT NORMALIZATION MAP
# Raw keyword → canonical concept label used as node_id component
# =============================================================================

CONCEPT_NORMALIZER: dict[str, str] = {
    # Career
    "job": "job", "work": "job", "employment": "job", "hired": "job",
    "startup": "startup", "business": "startup", "entrepreneur": "startup",
    "boss": "management", "manager": "management", "leadership": "management",
    "promotion": "advancement", "salary": "compensation", "income": "compensation",
    "interview": "job_search", "unemployed": "job_search",
    "client": "client_work", "freelance": "client_work",
    "career": "career_general",

    # Health
    "exercise": "fitness", "workout": "fitness", "gym": "fitness",
    "run": "fitness", "running": "fitness", "marathon": "fitness",
    "training": "fitness", "yoga": "fitness",
    "sleep": "sleep", "rest": "sleep",
    "diet": "nutrition", "eating": "nutrition", "food": "nutrition",
    "weight": "body_image", "body": "body_image",
    "anxiety": "mental_health", "depression": "mental_health",
    "stress": "mental_health", "burnout": "mental_health",
    "therapy": "mental_health",
    "sick": "illness", "illness": "illness", "pain": "illness",

    # Relationships
    "partner": "romantic", "spouse": "romantic", "husband": "romantic",
    "wife": "romantic", "girlfriend": "romantic", "boyfriend": "romantic",
    "dating": "romantic", "love": "romantic",
    "family": "family", "parent": "family", "mother": "family",
    "father": "family", "children": "family", "kids": "family",
    "friend": "friendship", "friendship": "friendship",
    "lonely": "loneliness", "connection": "belonging",

    # Finances
    "money": "finances_general", "finances": "finances_general",
    "debt": "debt", "loan": "debt", "credit": "debt",
    "savings": "savings", "invest": "investing", "investment": "investing",
    "budget": "budgeting", "spending": "spending", "spend": "spending",
    "rent": "housing_cost", "mortgage": "housing_cost",

    # Creativity
    "writing": "writing", "book": "writing", "novel": "writing", "blog": "writing",
    "music": "music", "song": "music", "compose": "music",
    "art": "visual_art", "painting": "visual_art", "drawing": "visual_art",
    "code": "coding", "coding": "coding", "program": "coding",
    "side project": "side_project", "create": "creating_general",

    # Learning
    "learn": "learning_general", "study": "studying", "course": "studying",
    "degree": "education", "university": "education", "college": "education",
    "skill": "skill_building", "practice": "skill_building",
    "read": "reading", "reading": "reading",

    # Identity
    "values": "values", "beliefs": "values", "principles": "values",
    "purpose": "life_purpose", "meaning": "life_purpose",
    "identity": "self_concept", "authentic": "self_concept",
}

# =============================================================================
# EMOTIONAL INTENSITY LEXICONS
# =============================================================================

HIGH_INTENSITY_WORDS = {
    "love", "hate", "terrified", "devastated", "thrilled", "obsessed",
    "desperate", "furious", "ecstatic", "heartbroken", "passionate",
    "disgusted", "overwhelmed", "exhausted", "exhilarated", "crushed",
    "elated", "horrified", "adore", "despise", "burning", "dying",
}

MEDIUM_INTENSITY_WORDS = {
    "excited", "worried", "scared", "happy", "sad", "angry", "frustrated",
    "proud", "ashamed", "anxious", "nervous", "motivated", "discouraged",
    "hopeful", "confused", "stressed", "relieved", "disappointed", "jealous",
    "grateful", "annoyed", "surprised", "inspired", "hurt", "lonely",
}

LOW_INTENSITY_WORDS = {
    "like", "enjoy", "prefer", "want", "wish", "hope", "think", "feel",
    "believe", "notice", "wonder", "consider", "appreciate", "dislike",
}

# =============================================================================
# IDENTITY STATEMENT PATTERNS
# =============================================================================

IDENTITY_PATTERNS = [
    r"\bi am\s+a\b",
    r"\bi'm\s+a\b",
    r"\bi'm\s+the\s+kind\s+of\s+person\b",
    r"\bi\s+consider\s+myself\b",
    r"\bi\s+see\s+myself\s+as\b",
    r"\bthat's\s+who\s+i\s+am\b",
    r"\bi've\s+always\s+been\b",
    r"\bat\s+my\s+core\b",
    r"\bwhat\s+i\s+stand\s+for\b",
    r"\bmy\s+identity\s+is\b",
]

COMPILED_IDENTITY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in IDENTITY_PATTERNS]


# =============================================================================
# EXTRACTION RESULT
# =============================================================================

@dataclass
class TopicExtractionResult:
    """
    Result of topic extraction for a single sentence.

    Passed to SignalAssembler to build ExplicitSignal objects.
    """
    sentence_text: str
    detected_keywords: list[str] = field(default_factory=list)
    domain_matches: list[tuple[SignalDomain, list[str]]] = field(default_factory=list)
    # [(domain, [matched_keywords]), ...]  — sorted by match count descending

    normalized_concepts: list[str] = field(default_factory=list)
    # Canonical concept labels, e.g. ["fitness", "mental_health"]

    is_identity_statement: bool = False
    emotional_intensity: float = 0.0      # 0.0–1.0
    is_self_referential: bool = False


# =============================================================================
# TOPIC EXTRACTOR
# =============================================================================

class TopicExtractor:
    """
    Extracts topics, domains, and concepts from a single sentence.

    Does NOT use spaCy directly — receives pre-tokenized text.
    Designed to be fast: pure Python string operations only.

    Usage:
        extractor = TopicExtractor()
        result = extractor.extract("I've been training for a marathon every day")
        # result.domain_matches → [(SignalDomain.HEALTH, ['training', 'marathon'])]
        # result.normalized_concepts → ['fitness']
        # result.emotional_intensity → 0.2
    """

    def extract(self, sentence_text: str, is_self_referential: bool = True) -> TopicExtractionResult:
        """
        Extract topics and domains from a single sentence.

        Args:
            sentence_text: The sentence to analyze
            is_self_referential: Whether sentence is about the speaker (from TAS)

        Returns:
            TopicExtractionResult with all extracted information
        """
        text_lower = sentence_text.lower()
        tokens = self._tokenize(text_lower)

        # Step 1: Detect keywords from each domain
        domain_matches: dict[SignalDomain, list[str]] = {}

        for domain, keywords in DOMAIN_LEXICONS.items():
            matched = []
            for keyword in keywords:
                if " " in keyword:
                    # Multi-word: check as substring
                    if keyword in text_lower:
                        matched.append(keyword)
                else:
                    # Single word: check in token set
                    if keyword in tokens:
                        matched.append(keyword)
            if matched:
                domain_matches[domain] = matched

        # Step 2: Sort domains by match count
        sorted_domains = sorted(
            domain_matches.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        # Step 3: Normalize concepts
        all_matched_keywords = [kw for _, kws in sorted_domains for kw in kws]
        normalized = self._normalize_concepts(all_matched_keywords, text_lower)

        # Step 4: Identity statement detection
        is_identity = self._is_identity_statement(text_lower)

        # Step 5: Emotional intensity
        intensity = self._score_emotional_intensity(tokens)

        return TopicExtractionResult(
            sentence_text=sentence_text,
            detected_keywords=all_matched_keywords,
            domain_matches=sorted_domains,
            normalized_concepts=normalized,
            is_identity_statement=is_identity,
            emotional_intensity=intensity,
            is_self_referential=is_self_referential,
        )

    # ── Private helpers ────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> set[str]:
        """Simple whitespace + punctuation tokenizer."""
        tokens = re.findall(r"\b[a-z]+\b", text)
        return set(tokens)

    def _normalize_concepts(self, keywords: list[str], text_lower: str) -> list[str]:
        """Map keywords to canonical concept labels, deduplicating."""
        concepts = []
        seen = set()

        for keyword in keywords:
            # Try exact match first
            concept = CONCEPT_NORMALIZER.get(keyword)

            # Try partial match (keyword contained in a normalizer key)
            if concept is None:
                for norm_key, norm_val in CONCEPT_NORMALIZER.items():
                    if norm_key in text_lower and norm_key not in seen:
                        concept = norm_val
                        break

            if concept and concept not in seen:
                concepts.append(concept)
                seen.add(concept)

        return concepts

    def _is_identity_statement(self, text_lower: str) -> bool:
        """Detect if sentence contains an identity-anchoring statement."""
        for pattern in COMPILED_IDENTITY_PATTERNS:
            if pattern.search(text_lower):
                return True
        return False

    def _score_emotional_intensity(self, tokens: set[str]) -> float:
        """
        Score emotional intensity from 0.0 to 1.0.

        High intensity words = 1.0 each (capped)
        Medium intensity = 0.5 each
        Low intensity = 0.2 each
        """
        score = 0.0

        for token in tokens:
            if token in HIGH_INTENSITY_WORDS:
                score += 1.0
            elif token in MEDIUM_INTENSITY_WORDS:
                score += 0.5
            elif token in LOW_INTENSITY_WORDS:
                score += 0.2

        # Normalize to 0.0–1.0 (cap at 2 high-intensity words = 1.0)
        return min(1.0, score / 2.0)

    def get_primary_domain(self, result: TopicExtractionResult) -> SignalDomain:
        """
        Return the single most likely domain for a sentence.

        Used when a sentence clearly belongs to one domain.
        Falls back to UNKNOWN if no domains detected.
        """
        if not result.domain_matches:
            return SignalDomain.UNKNOWN
        return result.domain_matches[0][0]