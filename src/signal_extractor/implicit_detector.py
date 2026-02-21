"""
Signal Extractor — Implicit Signal Detector
=============================================
Detects behavioral signals that the user never stated directly.
These emerge from PATTERNS across a conversation, not from content.

The four implicit signal types detected here:

1. REPEATED_TOPIC_RETURN
   A topic the user keeps bringing up unprompted. High cognitive salience.
   The signal is what they return to, not what they say about it.

2. UNPROMPTED_ELABORATION
   A user who elaborates on a topic more than the conversation requires.
   Over-explanation signals that this topic is occupying mental real estate.

3. ASYMMETRIC_ELABORATION
   One side of a stated trade-off gets significantly more words than the other.
   "My job is great — creative, flexible, well-paid, amazing team. But the hours
   are long." → Over-elaborated positive = rationalization pattern.

4. QUESTION_TYPE
   What someone ASKS reveals what they're worried about or seeking.
   "How do you stay motivated when nothing is working?" → fatalism signal.
   "What's the fastest way to make a lot of money?" → financial anxiety signal.
   "Is it weird that I...?" → social validation seeking = potential shame signal.

Research basis:
- Implicit signals are often MORE revealing than explicit statements
- Behavioral revealed preference: what people DO (ask, return to, elaborate on)
  tells more than what they SAY they want
- Asymmetric elaboration is a well-documented rationalization marker in therapy
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from models import (
    SignalDomain,
    ImplicitSignal,
    ImplicitSignalType,
)


# =============================================================================
# QUESTION TYPE PATTERNS
# =============================================================================
# Questions reveal internal state. Classify them into signal types.

@dataclass
class QuestionSignalPattern:
    """A pattern that detects a question type and its implied signal."""
    pattern: re.Pattern
    signal_domain: SignalDomain
    concept: str
    evidence_template: str
    confidence: float


QUESTION_PATTERNS: list[QuestionSignalPattern] = [

    # Validation-seeking questions → shame / social anxiety signal
    QuestionSignalPattern(
        pattern=re.compile(r"\bis it (weird|normal|okay|ok|bad|wrong)\s+(that|if|when)\s+i\b", re.I),
        signal_domain=SignalDomain.IDENTITY,
        concept="self_acceptance",
        evidence_template="Validation-seeking question detected: '{text}' — signals self-doubt or shame",
        confidence=0.75,
    ),

    # Motivation questions → fatalism or present-fatalistic signal
    QuestionSignalPattern(
        pattern=re.compile(r"\bhow (do|can|do you) (stay|keep|get|find)\s+(motivated|going|inspired)\b", re.I),
        signal_domain=SignalDomain.IDENTITY,
        concept="motivation",
        evidence_template="Motivation-seeking question: '{text}' — suggests active struggle with motivation",
        confidence=0.70,
    ),

    # Fast-money questions → financial anxiety
    QuestionSignalPattern(
        pattern=re.compile(r"\b(fastest|quickest|easiest)\s+way\s+to\s+(make|earn|get)\s+(money|cash|income)\b", re.I),
        signal_domain=SignalDomain.FINANCES,
        concept="financial_anxiety",
        evidence_template="Urgency-framed financial question: '{text}' — signals financial pressure",
        confidence=0.72,
    ),

    # Career escape questions → job dissatisfaction
    QuestionSignalPattern(
        pattern=re.compile(r"\bhow (do|can)\s+(i|you)\s+(quit|leave|escape|get out of)\s+(my|a|the)\s+job\b", re.I),
        signal_domain=SignalDomain.CAREER,
        concept="job_dissatisfaction",
        evidence_template="Job-escape question: '{text}' — signals dissatisfaction with current role",
        confidence=0.80,
    ),

    # Relationship fixing questions → relationship strain
    QuestionSignalPattern(
        pattern=re.compile(r"\bhow (do|can)\s+(i|you)\s+(fix|save|repair|improve)\s+(my|a|the)\s+(relationship|marriage|friendship)\b", re.I),
        signal_domain=SignalDomain.RELATIONSHIPS,
        concept="relationship_strain",
        evidence_template="Relationship-repair question: '{text}' — signals active relationship difficulty",
        confidence=0.78,
    ),

    # Burnout questions → health/mental health signal
    QuestionSignalPattern(
        pattern=re.compile(r"\b(burnout|burned out|exhausted|drained|no energy)\b", re.I),
        signal_domain=SignalDomain.HEALTH,
        concept="burnout",
        evidence_template="Burnout-adjacent language: '{text}' — signals health/energy concern",
        confidence=0.68,
    ),

    # Starting-from-scratch questions → transition signal
    QuestionSignalPattern(
        pattern=re.compile(r"\bhow (do|can)\s+(i|you)\s+(start over|start fresh|begin again|restart)\b", re.I),
        signal_domain=SignalDomain.IDENTITY,
        concept="life_transition",
        evidence_template="Starting-over question: '{text}' — signals major life transition underway",
        confidence=0.72,
    ),
]


# =============================================================================
# ELABORATION ANALYSIS
# =============================================================================

def measure_elaboration_asymmetry(sentence: str) -> Optional[tuple[str, str, float]]:
    """
    Detect asymmetric elaboration around contrast markers.

    When a sentence has a contrast marker (but, however, although),
    measure whether one side is significantly longer than the other.

    Returns:
        Tuple of (dominant_side, weak_side, asymmetry_ratio) if asymmetric,
        None if balanced or no contrast marker found.

    Asymmetry is significant when ratio > 2.5 (one side 2.5x longer than other).

    Example:
        "I love my job, it's creative and flexible and I learn every day,
         but the pay is low."
        dominant_side = "positive" (before 'but')
        asymmetry_ratio = 4.2
        Interpretation: Over-elaborated positive = possible rationalization
    """
    contrast_markers = ["but", "however", "although", "though", "yet", "whereas"]

    for marker in contrast_markers:
        pattern = re.compile(r"(.+?)\b" + marker + r"\b(.+)", re.IGNORECASE | re.DOTALL)
        match = pattern.search(sentence)
        if match:
            before = match.group(1).strip()
            after  = match.group(2).strip()

            before_words = len(before.split())
            after_words  = len(after.split())

            if before_words == 0 or after_words == 0:
                continue

            ratio = max(before_words, after_words) / min(before_words, after_words)

            if ratio >= 2.5:
                dominant = "before_contrast" if before_words > after_words else "after_contrast"
                weak     = "after_contrast"  if before_words > after_words else "before_contrast"
                return (dominant, weak, ratio)

    return None


import spacy
_elab_nlp = spacy.load("en_core_web_sm")

def score_elaboration_depth(sentence: str) -> float:
    """
    Improved elaboration scoring using linguistic features:
    - Word count
    - Adjective/adverb density
    - Named entity count (specificity)
    - Clause count (complexity)
    Returns a score between 0.0 and 1.0.
    """
    doc = _elab_nlp(sentence)
    word_count = len([t for t in doc if t.is_alpha])
    adj_adv_count = sum(1 for t in doc if t.pos_ in {"ADJ", "ADV"})
    entity_count = len(doc.ents)
    clause_count = sum(1 for t in doc if t.dep_ in {"ROOT", "conj", "ccomp", "advcl", "acl"})

    # Normalize features
    word_score = min(1.0, word_count / 25.0)
    adj_adv_score = min(0.3, adj_adv_count / max(1, word_count) * 3)
    entity_score = min(0.2, entity_count / 5)
    clause_score = min(0.2, clause_count / 4)

    # Combine with weighted sum
    elaboration_score = word_score + adj_adv_score + entity_score + clause_score
    return min(1.0, elaboration_score)


# =============================================================================
# IMPLICIT SIGNAL DETECTOR
# =============================================================================

class ImplicitSignalDetector:
    """
    Detects implicit behavioral signals from conversational patterns.

    Operates at two levels:
    1. Single-message level: question type, elaboration asymmetry
    2. Session level: repeated topic return (requires topic history)

    Usage:
        detector = ImplicitSignalDetector()
        signals = detector.detect(
            message="Is it weird that I don't want to go back to work?",
            topic_history={"career.job": 4, "identity.self_concept": 2},
            current_sentence_topics=["career.job"]
        )
    """

    REPETITION_THRESHOLD = 3   # Topic mentioned 3+ times = repetition signal
    HIGH_ELABORATION_THRESHOLD = 0.70  # Elaboration score above this = implicit signal

    def detect(
        self,
        message: str,
        sentences: list[str],
        topic_history: dict[str, int],
        current_sentence_topics: list[str],
        previously_discussed_domains: list[str],
    ) -> list[ImplicitSignal]:
        """
        Detect all implicit signals for a message.

        Args:
            message:                    Full original message text
            sentences:                  List of sentence strings from this message
            topic_history:              {concept_node_id: total_mention_count}
            current_sentence_topics:    Node IDs mentioned in current message
            previously_discussed_domains: Domain names from prior sessions

        Returns:
            List of ImplicitSignal objects
        """
        signals: list[ImplicitSignal] = []

        # 1. Question type signals (per sentence)
        for sentence in sentences:
            q_signals = self._detect_question_signals(sentence)
            signals.extend(q_signals)

        # 2. Elaboration asymmetry (per sentence)
        for sentence in sentences:
            asym = self._detect_elaboration_asymmetry(sentence)
            if asym:
                signals.append(asym)

        # 3. Unprompted elaboration (per sentence)
        for sentence in sentences:
            elab = self._detect_unprompted_elaboration(sentence)
            if elab:
                signals.append(elab)

        # 4. Repeated topic return (session-level)
        rep_signals = self._detect_repeated_topics(
            current_sentence_topics, topic_history
        )
        signals.extend(rep_signals)

        return signals

    # ── Private detection methods ──────────────────────────────────────────

    def _detect_question_signals(self, sentence: str) -> list[ImplicitSignal]:
        """Detect implicit signals from question type."""
        found = []
        for qp in QUESTION_PATTERNS:
            if qp.pattern.search(sentence):
                found.append(ImplicitSignal(
                    signal_type=ImplicitSignalType.QUESTION_TYPE,
                    domain=qp.signal_domain,
                    concept=qp.concept,
                    evidence=qp.evidence_template.format(text=sentence[:80]),
                    confidence=qp.confidence,
                    weight_modifier=qp.confidence * 0.7,  # Implicit = lower weight
                ))
        return found

    def _detect_elaboration_asymmetry(self, sentence: str) -> Optional[ImplicitSignal]:
        """Detect asymmetric elaboration around contrast markers."""
        asym = measure_elaboration_asymmetry(sentence)
        if asym is None:
            return None

        dominant_side, _, ratio = asym

        # Determine what the asymmetry means
        if dominant_side == "before_contrast":
            # More words before "but" → over-elaborating positives
            concept = "rationalization_pattern"
            evidence = (
                f"Asymmetric elaboration detected (ratio={ratio:.1f}x): "
                f"Over-elaborated positive side before contrast marker. "
                f"Possible rationalization of dissatisfaction."
            )
        else:
            # More words after "but" → complaints get more space than positives
            concept = "dissatisfaction_pattern"
            evidence = (
                f"Asymmetric elaboration detected (ratio={ratio:.1f}x): "
                f"Over-elaborated negative side after contrast marker. "
                f"Suppressed dissatisfaction signal."
            )

        confidence = min(0.85, 0.50 + (ratio - 2.5) * 0.08)

        return ImplicitSignal(
            signal_type=ImplicitSignalType.ASYMMETRIC_ELABORATION,
            domain=SignalDomain.IDENTITY,
            concept=concept,
            evidence=evidence,
            confidence=confidence,
            weight_modifier=confidence * 0.6,
        )

    def _detect_unprompted_elaboration(self, sentence: str) -> Optional[ImplicitSignal]:
        """Detect when a sentence is unusually long and detailed unprompted."""
        elab_score = score_elaboration_depth(sentence)

        if elab_score < self.HIGH_ELABORATION_THRESHOLD:
            return None

        return ImplicitSignal(
            signal_type=ImplicitSignalType.UNPROMPTED_ELABORATION,
            domain=SignalDomain.UNKNOWN,  # Domain resolved by topic extractor
            concept="high_salience_topic",
            evidence=(
                f"High elaboration depth (score={elab_score:.2f}): "
                f"'{sentence[:60]}...' — topic occupies significant cognitive space."
            ),
            confidence=0.55,
            weight_modifier=0.40,
        )

    def _detect_repeated_topics(
        self,
        current_topics: list[str],
        topic_history: dict[str, int],
    ) -> list[ImplicitSignal]:
        """Detect topics the user keeps returning to across sessions."""
        signals = []

        for node_id in current_topics:
            historical_count = topic_history.get(node_id, 0)

            if historical_count >= self.REPETITION_THRESHOLD:
                # Parse domain and concept from node_id
                parts = node_id.split(".", 1)
                domain_str = parts[0] if parts else "unknown"
                concept    = parts[1] if len(parts) > 1 else node_id

                # Map domain string back to enum
                try:
                    domain = SignalDomain(domain_str)
                except ValueError:
                    domain = SignalDomain.UNKNOWN

                confidence = min(0.90, 0.60 + (historical_count - 3) * 0.05)

                signals.append(ImplicitSignal(
                    signal_type=ImplicitSignalType.REPEATED_TOPIC_RETURN,
                    domain=domain,
                    concept=concept,
                    evidence=(
                        f"Topic '{node_id}' mentioned {historical_count + 1} times "
                        f"across sessions — high cognitive salience confirmed."
                    ),
                    confidence=confidence,
                    weight_modifier=confidence * 0.85,
                ))

        return signals