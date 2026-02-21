"""
Signal Extractor — SE Orchestrator
=====================================
Main entry point for the Signal Extractor submodule.
Ties together: TopicExtractor, SignalAssembler, ImplicitSignalDetector.

This is what the rest of the Psynapse system calls.
Receives TASOutput, returns SEOutput.

Pipeline:
    TASOutput (from TAS submodule)
        ↓
    [1] Parse TASOutput sentences
        ↓
    [2] TopicExtractor.extract()  — per sentence
        ↓
    [3] SignalAssembler.assemble() — per sentence
        ↓
    [4] ImplicitSignalDetector.detect() — per full message
        ↓
    [5] Aggregate → SEOutput
        ↓
    NodeUpdates → Graph Engine (Submodule 3)

Design constraints (matching TAS):
  - No LLM calls in hot path
  - Target: < 80ms per message
  - Stateless per call (state lives in topic_history passed in)
  - Pure Python + rule-based (spaCy optional future enhancement)
"""

from __future__ import annotations

import time
import logging
from dataclasses import asdict
from typing import Optional

from models import (
    SEOutput,
    SEInput,
    NodeUpdate,
    SignalDomain,
    SignalLayer,
    SignalStrength,
    ImplicitSignal,
)
from topic_extractor import TopicExtractor
from signal_assembler import SignalAssembler
from implicit_detector import ImplicitSignalDetector


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# SE ORCHESTRATOR
# =============================================================================

class SEOrchestrator:
    """
    Main Signal Extractor orchestrator.

    Accepts TASOutput (as dict or SEInput) and returns SEOutput
    containing all NodeUpdates for the Graph Engine.

    Usage:
        se = SEOrchestrator()
        se_output = se.extract(
            tas_output_dict=tas_result.model_dump(),
            user_id="user_123",
            session_id="session_456",
            topic_frequency_history={"health.fitness": 5, "career.job": 3},
            previously_discussed_domains=["health", "career"],
        )
    """

    def __init__(self):
        logger.info("Initializing SEOrchestrator...")
        self.topic_extractor    = TopicExtractor()
        self.signal_assembler   = SignalAssembler()
        self.implicit_detector  = ImplicitSignalDetector()
        logger.info("SEOrchestrator ready.")

    def extract(
        self,
        tas_output_dict: dict,
        user_id: str = "anonymous",
        session_id: str = "default",
        topic_frequency_history: Optional[dict[str, int]] = None,
        previously_discussed_domains: Optional[list[str]] = None,
    ) -> SEOutput:
        """
        Full Signal Extractor pipeline for one message.

        Args:
            tas_output_dict:              Serialized TASOutput from TAS submodule
            user_id:                      User identifier
            session_id:                   Session identifier
            topic_frequency_history:      Historical mention counts per node_id
            previously_discussed_domains: Domain names from prior sessions

        Returns:
            SEOutput with NodeUpdates for Graph Engine and implicit signals
        """
        start_time = time.time()

        topic_history = topic_frequency_history or {}
        prior_domains = previously_discussed_domains or []
        original_text = tas_output_dict.get("original_text", "")

        logger.info(f"SE extracting signals for user={user_id} session={session_id}")

        # ── Step 1: Parse TAS sentences ───────────────────────────────────
        tas_sentences: list[dict] = tas_output_dict.get("sentences", [])

        if not tas_sentences:
            logger.warning("No sentences in TASOutput — returning empty SEOutput")
            return self._empty_output(original_text, user_id, session_id, start_time)

        # ── Step 2: Topic extraction + signal assembly per sentence ────────
        all_node_updates: list[NodeUpdate] = []
        all_sentence_texts: list[str] = []
        current_message_node_ids: list[str] = []

        for tas_sent in tas_sentences:
            sentence_text = tas_sent.get("text", "")
            if not sentence_text.strip():
                continue

            all_sentence_texts.append(sentence_text)
            is_self_ref = tas_sent.get("self_referential", True)

            # Extract topics
            topic_result = self.topic_extractor.extract(sentence_text, is_self_ref)

            # Assemble NodeUpdates
            updates = self.signal_assembler.assemble(tas_sent, topic_result)
            all_node_updates.extend(updates)

            # Collect node_ids for implicit detection
            for upd in updates:
                current_message_node_ids.append(upd.node_id)

        # ── Step 3: Implicit signal detection ─────────────────────────────
        implicit_signals: list[ImplicitSignal] = self.implicit_detector.detect(
            message=original_text,
            sentences=all_sentence_texts,
            topic_history=topic_history,
            current_sentence_topics=current_message_node_ids,
            previously_discussed_domains=prior_domains,
        )

        # ── Step 4: Aggregate metadata ─────────────────────────────────────
        active_domains = list({upd.domain for upd in all_node_updates})
        identity_signals = [
            upd.node_id for upd in all_node_updates if upd.is_identity_anchored
        ]

        # EFIB layer distribution
        layer_dist: dict[str, int] = {}
        for upd in all_node_updates:
            layer_dist[upd.layer.value] = layer_dist.get(upd.layer.value, 0) + 1

        # Flags
        flags: list[str] = []
        if identity_signals:
            flags.append("identity_statement_detected")
        if len(active_domains) >= 3:
            flags.append("multi_domain_message")
        if any(s.concept in {"rationalization_pattern", "dissatisfaction_pattern"}
               for s in implicit_signals):
            flags.append("asymmetric_elaboration_detected")
        if any(s.signal_type.value == "repeated_topic_return" for s in implicit_signals):
            flags.append("high_salience_topic_confirmed")

        # Serialize implicit signals (ImplicitSignal is a dataclass, not Pydantic)
        implicit_dicts = [
            {
                "signal_type": s.signal_type.value,
                "domain":      s.domain.value,
                "concept":     s.concept,
                "evidence":    s.evidence,
                "confidence":  s.confidence,
                "weight_modifier": s.weight_modifier,
            }
            for s in implicit_signals
        ]

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"SE complete: {len(all_node_updates)} node updates, "
            f"{len(implicit_signals)} implicit signals, "
            f"{processing_time_ms:.1f}ms"
        )

        return SEOutput(
            original_text=original_text,
            user_id=user_id,
            session_id=session_id,
            node_updates=all_node_updates,
            implicit_signals=implicit_dicts,
            active_domains=active_domains,
            identity_signals=identity_signals,
            layer_distribution=layer_dist,
            flags=flags,
            processing_time_ms=processing_time_ms,
        )

    def _empty_output(
        self, original_text: str, user_id: str, session_id: str, start_time: float
    ) -> SEOutput:
        """Return an empty SEOutput when no sentences are available."""
        return SEOutput(
            original_text=original_text,
            user_id=user_id,
            session_id=session_id,
            node_updates=[],
            implicit_signals=[],
            active_domains=[],
            identity_signals=[],
            layer_distribution={},
            flags=["no_sentences_detected"],
            processing_time_ms=(time.time() - start_time) * 1000,
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

_default_orchestrator: Optional[SEOrchestrator] = None


def get_se() -> SEOrchestrator:
    """Get or create the singleton SEOrchestrator."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = SEOrchestrator()
    return _default_orchestrator


def extract_signals(
    tas_output_dict: dict,
    user_id: str = "anonymous",
    session_id: str = "default",
    topic_frequency_history: Optional[dict[str, int]] = None,
    previously_discussed_domains: Optional[list[str]] = None,
) -> SEOutput:
    """
    Module-level convenience function for signal extraction.

    Args:
        tas_output_dict:  Serialized TASOutput from TAS submodule
        user_id:          User identifier
        session_id:       Session identifier
        topic_frequency_history:      Historical mention counts per node_id
        previously_discussed_domains: Domain names from prior sessions

    Returns:
        SEOutput with NodeUpdates for Graph Engine

    Example:
        from se_orchestrator import extract_signals

        se_result = extract_signals(
            tas_output_dict=tas_output.model_dump(),
            user_id="user_42",
            topic_frequency_history={"health.fitness": 6},
        )
        for update in se_result.node_updates:
            print(update.node_id, update.graph_operation, update.weight_modifier)
    """
    return get_se().extract(
        tas_output_dict=tas_output_dict,
        user_id=user_id,
        session_id=session_id,
        topic_frequency_history=topic_frequency_history,
        previously_discussed_domains=previously_discussed_domains,
    )


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    """
    Run SE submodule tests against mock TASOutput.

    These tests use synthetic TAS output since TAS requires spaCy
    which may not be available in all environments.
    """
    print("\n" + "=" * 70)
    print("SIGNAL EXTRACTOR — TESTS")
    print("=" * 70 + "\n")

    se = SEOrchestrator()

    # ── Mock TASOutput dicts ───────────────────────────────────────────────
    test_cases = [
        {
            "label": "Active career + health sentence",
            "tas_output": {
                "original_text": "I've been training for a marathon every day and it's helping my focus at work.",
                "sentences": [
                    {
                        "text": "I've been training for a marathon every day and it's helping my focus at work.",
                        "tense_class": "T1",
                        "graph_operation": "INCREMENT",
                        "weight_modifier": 0.85,
                        "hedge_score": 0.85,
                        "confidence": 0.88,
                        "self_referential": True,
                        "temporal_orientation": "present",
                        "flags": [],
                    }
                ],
                "sentence_level_events": [],
                "contrast_markers_detected": [],
                "session_zimbardo_delta": {},
                "processing_time_ms": 22.4,
            },
            "topic_history": {"health.fitness": 2},
            "prior_domains": ["career"],
        },
        {
            "label": "Historical + hedged future (behavioral shift)",
            "tas_output": {
                "original_text": "I used to run every day, but lately I've been thinking maybe I'll get back into it.",
                "sentences": [
                    {
                        "text": "I used to run every day",
                        "tense_class": "T4",
                        "graph_operation": "DECREMENT",
                        "weight_modifier": 0.90,
                        "hedge_score": 0.90,
                        "confidence": 0.91,
                        "self_referential": True,
                        "temporal_orientation": "past",
                        "flags": [],
                    },
                    {
                        "text": "lately I've been thinking maybe I'll get back into it",
                        "tense_class": "T8",
                        "graph_operation": "INCREMENT",
                        "weight_modifier": 0.35,
                        "hedge_score": 0.35,
                        "confidence": 0.76,
                        "self_referential": True,
                        "temporal_orientation": "future",
                        "flags": ["heavily_hedged"],
                    },
                ],
                "sentence_level_events": ["TENSE_MIGRATION: T4→T8 on topic:fitness"],
                "contrast_markers_detected": ["but", "lately"],
                "session_zimbardo_delta": {"past_positive": 0.02},
                "processing_time_ms": 31.1,
            },
            "topic_history": {"health.fitness": 4},
            "prior_domains": ["health"],
        },
        {
            "label": "Identity statement",
            "tas_output": {
                "original_text": "I'm a builder at heart. I've always been obsessed with making things.",
                "sentences": [
                    {
                        "text": "I'm a builder at heart.",
                        "tense_class": "T3",
                        "graph_operation": "INCREMENT",
                        "weight_modifier": 0.95,
                        "hedge_score": 0.95,
                        "confidence": 0.90,
                        "self_referential": True,
                        "temporal_orientation": "present",
                        "flags": [],
                    },
                    {
                        "text": "I've always been obsessed with making things.",
                        "tense_class": "T2",
                        "graph_operation": "INCREMENT",
                        "weight_modifier": 0.92,
                        "hedge_score": 0.92,
                        "confidence": 0.87,
                        "self_referential": True,
                        "temporal_orientation": "present",
                        "flags": [],
                    },
                ],
                "sentence_level_events": [],
                "contrast_markers_detected": [],
                "session_zimbardo_delta": {},
                "processing_time_ms": 18.6,
            },
            "topic_history": {},
            "prior_domains": [],
        },
        {
            "label": "Validation-seeking question (implicit signal)",
            "tas_output": {
                "original_text": "Is it weird that I don't want to go back to work after my break?",
                "sentences": [
                    {
                        "text": "Is it weird that I don't want to go back to work after my break?",
                        "tense_class": "T12",
                        "graph_operation": "FLAG",
                        "weight_modifier": 0.70,
                        "hedge_score": 0.70,
                        "confidence": 0.72,
                        "self_referential": True,
                        "temporal_orientation": "present",
                        "flags": [],
                    }
                ],
                "sentence_level_events": [],
                "contrast_markers_detected": [],
                "session_zimbardo_delta": {},
                "processing_time_ms": 14.2,
            },
            "topic_history": {"career.job": 5},
            "prior_domains": ["career"],
        },
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"[Test {i}] {tc['label']}")
        print("-" * 70)

        result = se.extract(
            tas_output_dict=tc["tas_output"],
            topic_frequency_history=tc["topic_history"],
            previously_discussed_domains=tc["prior_domains"],
        )

        print(f"  Node Updates ({len(result.node_updates)}):")
        for upd in result.node_updates:
            print(f"    → {upd.node_id:<35} {upd.graph_operation:<12} "
                  f"weight={upd.weight_modifier:.2f}  layer={upd.layer.value:<10} "
                  f"strength={upd.strength.value}")
            if upd.is_identity_anchored:
                print(f"       ★ IDENTITY ANCHORED")

        if result.implicit_signals:
            print(f"\n  Implicit Signals ({len(result.implicit_signals)}):")
            for sig in result.implicit_signals:
                print(f"    ⚑ [{sig['signal_type']}] {sig['concept']} "
                      f"(conf={sig['confidence']:.2f})")
                print(f"      {sig['evidence'][:80]}...")

        print(f"\n  Active domains: {[d.value for d in result.active_domains]}")
        print(f"  EFIB layers:    {result.layer_distribution}")
        if result.flags:
            print(f"  Flags:          {result.flags}")
        print(f"  Time:           {result.processing_time_ms:.1f}ms")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    run_tests()