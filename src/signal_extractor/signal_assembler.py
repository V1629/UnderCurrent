"""
Signal Extractor — Signal Assembler
=====================================
Assembles ExplicitSignal and NodeUpdate objects from:
  - TAS sentence analysis (tense, hedge, graph_operation, self_referential)
  - TopicExtractionResult (domain, concept, emotional_intensity)

This is the core integration layer between TAS and the Graph Engine.
It bridges the HOW (tense) with the WHAT (topic) to produce
a fully-resolved, ready-to-execute NodeUpdate.

Pipeline position:
  TASOutput → [TopicExtractor] → [SignalAssembler] → [NodeUpdate] → Graph Engine

Key logic:
  1. Determine SignalLayer from TenseClass + content
  2. Determine SignalStrength from hedge_score + emotional_intensity + confidence
  3. Build node_id: "{domain}.{concept}"
  4. Pass through graph_operation and weight_modifier from TAS
  5. Flag identity statements for low-decay treatment
"""

from __future__ import annotations

from models import (
    SignalDomain,
    SignalLayer,
    SignalStrength,
    ExplicitSignal,
    NodeUpdate,
)
from topic_extractor import TopicExtractionResult


# =============================================================================
# TENSE → EFIB LAYER MAPPING
# =============================================================================
# Each TenseClass maps to a most-likely EFIB layer.
# This is a default — content can override it.

TENSE_TO_LAYER: dict[str, SignalLayer] = {
    "T1":  SignalLayer.BEHAVIOUR,   # Active Present: doing something now
    "T2":  SignalLayer.BEHAVIOUR,   # Habitual Present: recurring behaviour
    "T3":  SignalLayer.INTENTION,   # Stable Belief: values driving intentions
    "T4":  SignalLayer.BEHAVIOUR,   # Historical Past: past behaviour
    "T5":  SignalLayer.FEELING,     # Experiential Past: lived feeling
    "T6":  SignalLayer.EMOTION,     # Narrative Present: emotionally vivid recall
    "T7":  SignalLayer.INTENTION,   # Declared Future: strong intention
    "T8":  SignalLayer.INTENTION,   # Hedged Future: weak intention
    "T9":  SignalLayer.INTENTION,   # Conditional: desire-level intention
    "T10": SignalLayer.EMOTION,     # Counterfactual Past: regret = raw emotion
    "T11": SignalLayer.FEELING,     # Present Fatalistic: named helplessness
    "T12": SignalLayer.EMOTION,     # Future Anxious: raw fear about future
}

# Content-level overrides: if these keywords appear, layer shifts
EMOTION_KEYWORDS = {
    "feel", "felt", "scared", "afraid", "angry", "sad", "happy",
    "fear", "joy", "rage", "grief", "excited", "ashamed", "embarrassed",
}

FEELING_KEYWORDS = {
    "anxiety", "anxious", "proud", "pride", "lonely", "loneliness",
    "resentment", "nostalgia", "guilt", "shame", "excited", "worried",
    "hopeful", "hopeless", "frustrated", "grateful",
}

INTENTION_KEYWORDS = {
    "want", "plan", "goal", "aim", "intend", "trying", "hoping",
    "will", "going to", "decide", "decided", "commit", "committed",
}

BEHAVIOUR_KEYWORDS = {
    "do", "doing", "did", "working", "running", "building", "training",
    "studying", "practicing", "applying", "avoiding", "started", "stopped",
}


# =============================================================================
# STRENGTH THRESHOLDS
# =============================================================================

def compute_strength(
    hedge_score: float,
    emotional_intensity: float,
    confidence: float,
) -> SignalStrength:
    """
    Compute SignalStrength from three contributing factors.

    Formula:
        composite = (hedge_score * 0.5) + (emotional_intensity * 0.3) + (confidence * 0.2)
        STRONG  ≥ 0.65
        MEDIUM  ≥ 0.35
        WEAK    < 0.35

    Args:
        hedge_score:        From TAS (1.0=certain, 0.0=maximally hedged)
        emotional_intensity: From TopicExtractor (0.0–1.0)
        confidence:         From TAS classifier (0.0–1.0)

    Returns:
        SignalStrength enum value
    """
    composite = (hedge_score * 0.5) + (emotional_intensity * 0.3) + (confidence * 0.2)

    if composite >= 0.65:
        return SignalStrength.STRONG
    elif composite >= 0.35:
        return SignalStrength.MEDIUM
    else:
        return SignalStrength.WEAK


def resolve_layer(tense_class: str, extracted_keywords: list[str]) -> SignalLayer:
    """
    Resolve the EFIB layer for a signal.

    Starts with tense-class default, then checks content keywords
    for override. Content overrides tense when both are present,
    because what was said is more specific than how it was framed.

    Args:
        tense_class:        TenseClass value string, e.g. "T1"
        extracted_keywords: Keywords from TopicExtractor

    Returns:
        SignalLayer enum value
    """
    default_layer = TENSE_TO_LAYER.get(tense_class, SignalLayer.BEHAVIOUR)

    keyword_set = set(k.lower() for k in extracted_keywords)

    # Content override: check most specific first
    if keyword_set & EMOTION_KEYWORDS:
        return SignalLayer.EMOTION
    if keyword_set & FEELING_KEYWORDS:
        return SignalLayer.FEELING
    if keyword_set & INTENTION_KEYWORDS:
        return SignalLayer.INTENTION
    if keyword_set & BEHAVIOUR_KEYWORDS:
        return SignalLayer.BEHAVIOUR

    return default_layer


def build_node_id(domain: SignalDomain, concept: str) -> str:
    """
    Build canonical node_id for the graph engine.

    Format: "{domain_value}.{concept}"
    Example: "health.fitness", "career.startup", "identity.values"

    Args:
        domain:  SignalDomain enum member
        concept: Normalized concept string from TopicExtractor

    Returns:
        String node_id
    """
    clean_concept = concept.strip().lower().replace(" ", "_")
    return f"{domain.value}.{clean_concept}"


# =============================================================================
# SIGNAL ASSEMBLER
# =============================================================================

class SignalAssembler:
    """
    Assembles ExplicitSignal and NodeUpdate objects.

    Takes one sentence's TAS analysis + TopicExtractionResult
    and produces a list of NodeUpdates (one per detected domain/concept).

    A single sentence can produce multiple NodeUpdates if it spans
    multiple domains. Example:
      "I've been training but I'm worried about my job"
      → NodeUpdate(health.fitness, INCREMENT)
      → NodeUpdate(career.job, FLAG)

    Usage:
        assembler = SignalAssembler()
        updates = assembler.assemble(tas_sentence_dict, topic_result)
    """

    def assemble(
        self,
        tas_sentence: dict,
        topic_result: TopicExtractionResult,
    ) -> list[NodeUpdate]:
        """
        Assemble NodeUpdates from TAS sentence dict + topic extraction.

        Args:
            tas_sentence:   One SentenceAnalysis serialized as dict
                            (from TASOutput.sentences[i])
            topic_result:   TopicExtractionResult for the same sentence

        Returns:
            List of NodeUpdate objects (may be empty if no domain detected)
        """

        # Skip non-self-referential sentences — they don't update user's graph
        if not tas_sentence.get("self_referential", True):
            return []

        # Skip if no domain detected
        if not topic_result.domain_matches:
            return []

        tense_class    = tas_sentence.get("tense_class", "T1")
        graph_op       = tas_sentence.get("graph_operation", "INCREMENT")
        weight_mod     = float(tas_sentence.get("weight_modifier", 1.0))
        hedge_score    = float(tas_sentence.get("hedge_score", 1.0))
        confidence     = float(tas_sentence.get("confidence", 0.8))
        source_text    = tas_sentence.get("text", "")

        updates: list[NodeUpdate] = []

        # Build one NodeUpdate per detected domain
        # (cap at 3 domains per sentence to avoid over-signaling)
        for domain, matched_keywords in topic_result.domain_matches[:3]:

            # Get concepts for this domain
            domain_concepts = self._get_domain_concepts(
                domain, matched_keywords, topic_result.normalized_concepts
            )

            # Use "general" if no specific concept resolved
            if not domain_concepts:
                domain_concepts = [f"{domain.value}_general"]

            for concept in domain_concepts[:2]:  # Max 2 concepts per domain per sentence

                layer = resolve_layer(tense_class, matched_keywords)
                strength = compute_strength(
                    hedge_score,
                    topic_result.emotional_intensity,
                    confidence,
                )
                node_id = build_node_id(domain, concept)

                # Identity statements get very low decay — flag them
                is_identity = (
                    topic_result.is_identity_statement
                    or domain == SignalDomain.IDENTITY
                )

                updates.append(NodeUpdate(
                    node_id=node_id,
                    domain=domain,
                    concept=concept,
                    graph_operation=graph_op,
                    weight_modifier=weight_mod,
                    layer=layer,
                    signal_source="explicit",
                    strength=strength,
                    tense_class=tense_class,
                    is_identity_anchored=is_identity,
                    emotional_intensity=topic_result.emotional_intensity,
                    source_text=source_text,
                    confidence=confidence,
                ))

        return updates

    def _get_domain_concepts(
        self,
        domain: SignalDomain,
        matched_keywords: list[str],
        all_normalized: list[str],
    ) -> list[str]:
        """
        Filter normalized concepts that belong to this specific domain.

        Prevents concepts from one domain being attached to a different domain's
        NodeUpdate when a sentence spans multiple domains.
        """
        # Domain-to-concept prefix mapping for filtering
        domain_concept_prefixes: dict[SignalDomain, set[str]] = {
            SignalDomain.CAREER:        {"job", "startup", "career", "management", "advancement", "compensation", "job_search", "client_work"},
            SignalDomain.HEALTH:        {"fitness", "sleep", "nutrition", "body_image", "mental_health", "illness"},
            SignalDomain.RELATIONSHIPS: {"romantic", "family", "friendship", "loneliness", "belonging"},
            SignalDomain.FINANCES:      {"finances", "debt", "savings", "investing", "budgeting", "spending", "housing_cost"},
            SignalDomain.CREATIVITY:    {"writing", "music", "visual_art", "coding", "side_project", "creating"},
            SignalDomain.LEARNING:      {"learning", "studying", "education", "skill_building", "reading"},
            SignalDomain.IDENTITY:      {"values", "life_purpose", "self_concept"},
        }

        valid_prefixes = domain_concept_prefixes.get(domain, set())

        matched_concepts = [
            c for c in all_normalized
            if any(c.startswith(prefix) or c == prefix for prefix in valid_prefixes)
        ]

        return matched_concepts if matched_concepts else []