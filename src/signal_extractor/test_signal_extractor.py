"""
Signal Extractor — Full Test Suite
====================================
Tests all 5 SE files using a single realistic chat conversation as input.

Simulated user: "Arjun" — a software engineer, mid-career, feeling stuck,
thinking about a startup, dealing with relationship strain and fitness neglect.

Files tested:
  1. se_models.py         — enum instantiation, dataclass creation
  2. topic_extractor.py   — keyword extraction, domain classification,
                            concept normalization, identity detection,
                            emotional intensity scoring
  3. signal_assembler.py  — compute_strength, resolve_layer, build_node_id,
                            SignalAssembler.assemble()
  4. implicit_detector.py — question signals, asymmetric elaboration,
                            unprompted elaboration, repeated topic return
  5. se_orchestrator.py   — full end-to-end pipeline, SEOrchestrator.extract()

Run with:
    python test_signal_extractor.py
"""

import sys
import traceback
from typing import Any


# ── colour helpers (no deps) ──────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗ FAIL — {msg}{RESET}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET}  {msg}")
def section(title):
    print(f"\n{BOLD}{'─'*68}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─'*68}{RESET}")

PASS_COUNT = 0
FAIL_COUNT = 0

def assert_true(condition: bool, description: str, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        ok(description)
        PASS_COUNT += 1
    else:
        fail(f"{description}  {DIM}{detail}{RESET}")
        FAIL_COUNT += 1

def assert_equal(actual: Any, expected: Any, description: str):
    assert_true(actual == expected, description, f"got={actual!r}  expected={expected!r}")

def assert_in(value: Any, container: Any, description: str):
    assert_true(value in container, description, f"{value!r} not in {container!r}")

def assert_not_empty(container: Any, description: str):
    assert_true(bool(container), description, f"container was empty: {container!r}")

def assert_range(value: float, lo: float, hi: float, description: str):
    assert_true(lo <= value <= hi, description, f"{value} not in [{lo}, {hi}]")


# =============================================================================
# SIMULATED CHAT — Arjun's conversation
# =============================================================================
# This is the single chat input driving ALL tests.
# Each message is one turn from the user.

CHAT = [
    # Turn 1 — identity statement + career domain
    {
        "turn": 1,
        "text": "I'm a builder at heart. I've always been obsessed with making things and solving hard problems.",
        "mock_tas": {
            "original_text": "I'm a builder at heart. I've always been obsessed with making things and solving hard problems.",
            "sentences": [
                {
                    "text": "I'm a builder at heart.",
                    "tense_class": "T3",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.95,
                    "hedge_score": 0.95,
                    "confidence": 0.91,
                    "self_referential": True,
                    "temporal_orientation": "present",
                    "flags": [],
                },
                {
                    "text": "I've always been obsessed with making things and solving hard problems.",
                    "tense_class": "T2",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.92,
                    "hedge_score": 0.92,
                    "confidence": 0.88,
                    "self_referential": True,
                    "temporal_orientation": "present",
                    "flags": [],
                },
            ],
            "sentence_level_events": [],
            "contrast_markers_detected": [],
            "session_zimbardo_delta": {},
            "processing_time_ms": 19.3,
        },
    },

    # Turn 2 — career dissatisfaction + hedged future startup intention
    {
        "turn": 2,
        "text": "My job is fine I guess — stable salary, decent team, good manager. But honestly I feel stuck. I've been thinking maybe I should start my own startup someday.",
        "mock_tas": {
            "original_text": "My job is fine I guess — stable salary, decent team, good manager. But honestly I feel stuck. I've been thinking maybe I should start my own startup someday.",
            "sentences": [
                {
                    "text": "My job is fine I guess — stable salary, decent team, good manager.",
                    "tense_class": "T3",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.40,
                    "hedge_score": 0.40,
                    "confidence": 0.78,
                    "self_referential": True,
                    "temporal_orientation": "present",
                    "flags": ["heavily_hedged"],
                },
                {
                    "text": "But honestly I feel stuck.",
                    "tense_class": "T11",
                    "graph_operation": "FLAG",
                    "weight_modifier": 0.85,
                    "hedge_score": 0.85,
                    "confidence": 0.82,
                    "self_referential": True,
                    "temporal_orientation": "present",
                    "flags": ["fatalism_marker"],
                },
                {
                    "text": "I've been thinking maybe I should start my own startup someday.",
                    "tense_class": "T8",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.18,
                    "hedge_score": 0.18,
                    "confidence": 0.74,
                    "self_referential": True,
                    "temporal_orientation": "future",
                    "flags": ["heavily_hedged"],
                },
            ],
            "sentence_level_events": ["CONTRAST_DETECTED: but, honestly"],
            "contrast_markers_detected": ["but"],
            "session_zimbardo_delta": {"present_fatalistic": 0.05},
            "processing_time_ms": 28.7,
        },
    },

    # Turn 3 — historical health + hedged reactivation
    {
        "turn": 3,
        "text": "I used to run every morning, like 5km before work. Haven't touched it in months. Maybe I'll get back into it.",
        "mock_tas": {
            "original_text": "I used to run every morning, like 5km before work. Haven't touched it in months. Maybe I'll get back into it.",
            "sentences": [
                {
                    "text": "I used to run every morning, like 5km before work.",
                    "tense_class": "T4",
                    "graph_operation": "DECREMENT",
                    "weight_modifier": 0.90,
                    "hedge_score": 0.90,
                    "confidence": 0.89,
                    "self_referential": True,
                    "temporal_orientation": "past",
                    "flags": [],
                },
                {
                    "text": "Haven't touched it in months.",
                    "tense_class": "T4",
                    "graph_operation": "DECREMENT",
                    "weight_modifier": 0.88,
                    "hedge_score": 0.88,
                    "confidence": 0.85,
                    "self_referential": True,
                    "temporal_orientation": "past",
                    "flags": [],
                },
                {
                    "text": "Maybe I'll get back into it.",
                    "tense_class": "T8",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.20,
                    "hedge_score": 0.20,
                    "confidence": 0.71,
                    "self_referential": True,
                    "temporal_orientation": "future",
                    "flags": ["heavily_hedged"],
                },
            ],
            "sentence_level_events": ["TENSE_MIGRATION: T4→T8 on topic:fitness"],
            "contrast_markers_detected": [],
            "session_zimbardo_delta": {"past_positive": 0.03},
            "processing_time_ms": 24.1,
        },
    },

    # Turn 4 — relationship strain + regret + validation-seeking question
    {
        "turn": 4,
        "text": "My girlfriend says I don't give her enough time. She's probably right. I should have prioritised our relationship more. Is it weird that I feel relieved when she cancels plans?",
        "mock_tas": {
            "original_text": "My girlfriend says I don't give her enough time. She's probably right. I should have prioritised our relationship more. Is it weird that I feel relieved when she cancels plans?",
            "sentences": [
                {
                    "text": "My girlfriend says I don't give her enough time.",
                    "tense_class": "T1",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.80,
                    "hedge_score": 0.80,
                    "confidence": 0.83,
                    "self_referential": True,
                    "temporal_orientation": "present",
                    "flags": [],
                },
                {
                    "text": "She's probably right.",
                    "tense_class": "T3",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.60,
                    "hedge_score": 0.60,
                    "confidence": 0.72,
                    "self_referential": False,
                    "temporal_orientation": "present",
                    "flags": [],
                },
                {
                    "text": "I should have prioritised our relationship more.",
                    "tense_class": "T10",
                    "graph_operation": "TRIGGER",
                    "weight_modifier": 0.88,
                    "hedge_score": 0.88,
                    "confidence": 0.90,
                    "self_referential": True,
                    "temporal_orientation": "past",
                    "flags": ["regret_marker"],
                },
                {
                    "text": "Is it weird that I feel relieved when she cancels plans?",
                    "tense_class": "T12",
                    "graph_operation": "FLAG",
                    "weight_modifier": 0.72,
                    "hedge_score": 0.72,
                    "confidence": 0.75,
                    "self_referential": True,
                    "temporal_orientation": "future",
                    "flags": [],
                },
            ],
            "sentence_level_events": [],
            "contrast_markers_detected": [],
            "session_zimbardo_delta": {"past_negative": 0.05},
            "processing_time_ms": 31.2,
        },
    },

    # Turn 5 — declared financial goal + declared learning intention
    {
        "turn": 5,
        "text": "I will save 20% of my salary starting this month. I'm also going to learn Python properly — I know I keep saying it but this time I'm committed.",
        "mock_tas": {
            "original_text": "I will save 20% of my salary starting this month. I'm also going to learn Python properly — I know I keep saying it but this time I'm committed.",
            "sentences": [
                {
                    "text": "I will save 20% of my salary starting this month.",
                    "tense_class": "T7",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.95,
                    "hedge_score": 0.95,
                    "confidence": 0.93,
                    "self_referential": True,
                    "temporal_orientation": "future",
                    "flags": [],
                },
                {
                    "text": "I'm also going to learn Python properly — I know I keep saying it but this time I'm committed.",
                    "tense_class": "T7",
                    "graph_operation": "INCREMENT",
                    "weight_modifier": 0.88,
                    "hedge_score": 0.88,
                    "confidence": 0.86,
                    "self_referential": True,
                    "temporal_orientation": "future",
                    "flags": [],
                },
            ],
            "sentence_level_events": [],
            "contrast_markers_detected": ["but"],
            "session_zimbardo_delta": {"future_oriented": 0.08},
            "processing_time_ms": 22.5,
        },
    },
]

# Simulated topic history — what Arjun has mentioned across past sessions
TOPIC_HISTORY = {
    "career.job":          6,   # keeps coming back to this
    "career.startup":      4,
    "health.fitness":      5,
    "relationships.romantic": 3,
    "identity.self_concept": 2,
}

PRIOR_DOMAINS = ["career", "health", "identity"]


# =============================================================================
# TEST SUITE
# =============================================================================

def test_se_models():
    section("FILE 1 — se_models.py  (Enums + Dataclasses)")

    from models import (
        SignalDomain, SignalLayer, SignalStrength, ImplicitSignalType,
        ExplicitSignal, ImplicitSignal, NodeUpdate, SEOutput, SEInput,
    )

    # ── Enum values ──────────────────────────────────────────────────────────
    assert_equal(SignalDomain.CAREER.value,   "career",   "SignalDomain.CAREER = 'career'")
    assert_equal(SignalDomain.HEALTH.value,   "health",   "SignalDomain.HEALTH = 'health'")
    assert_equal(SignalDomain.IDENTITY.value, "identity", "SignalDomain.IDENTITY = 'identity'")
    assert_equal(SignalLayer.BEHAVIOUR.value, "behaviour","SignalLayer.BEHAVIOUR = 'behaviour'")
    assert_equal(SignalLayer.INTENTION.value, "intention","SignalLayer.INTENTION = 'intention'")
    assert_equal(SignalLayer.EMOTION.value,   "emotion",  "SignalLayer.EMOTION = 'emotion'")
    assert_equal(SignalStrength.STRONG.value, "strong",   "SignalStrength.STRONG = 'strong'")
    assert_equal(SignalStrength.WEAK.value,   "weak",     "SignalStrength.WEAK = 'weak'")
    assert_equal(ImplicitSignalType.QUESTION_TYPE.value, "question_type", "ImplicitSignalType.QUESTION_TYPE")
    assert_equal(ImplicitSignalType.ASYMMETRIC_ELABORATION.value, "asymmetric_elaboration", "ImplicitSignalType.ASYMMETRIC_ELABORATION")

    # ── Enum membership ──────────────────────────────────────────────────────
    all_domains = [d.value for d in SignalDomain]
    for d in ["career", "health", "relationships", "finances", "creativity", "identity", "learning", "unknown"]:
        assert_in(d, all_domains, f"SignalDomain contains '{d}'")

    # ── NodeUpdate instantiation ─────────────────────────────────────────────
    nu = NodeUpdate(
        node_id="career.startup",
        domain=SignalDomain.CAREER,
        concept="startup",
        graph_operation="INCREMENT",
        weight_modifier=0.85,
        layer=SignalLayer.INTENTION,
        signal_source="explicit",
        strength=SignalStrength.STRONG,
        tense_class="T7",
        is_identity_anchored=False,
        emotional_intensity=0.3,
        source_text="I will launch my startup next month.",
        confidence=0.92,
    )
    assert_equal(nu.node_id, "career.startup", "NodeUpdate.node_id set correctly")
    assert_equal(nu.graph_operation, "INCREMENT", "NodeUpdate.graph_operation set correctly")
    assert_equal(nu.is_identity_anchored, False, "NodeUpdate.is_identity_anchored defaults False")

    # ── SEOutput instantiation ──────────────────────────────────────────────
    out = SEOutput(original_text="Hello", user_id="u1", session_id="s1")
    assert_equal(out.node_updates, [], "SEOutput.node_updates defaults to []")
    assert_equal(out.flags, [],        "SEOutput.flags defaults to []")
    assert_equal(out.processing_time_ms, 0.0, "SEOutput.processing_time_ms defaults to 0.0")

    # ── ImplicitSignal instantiation ─────────────────────────────────────────
    imp = ImplicitSignal(
        signal_type=ImplicitSignalType.REPEATED_TOPIC_RETURN,
        domain=SignalDomain.CAREER,
        concept="job",
        evidence="mentioned 6 times",
        confidence=0.80,
        weight_modifier=0.68,
    )
    assert_equal(imp.signal_type, ImplicitSignalType.REPEATED_TOPIC_RETURN, "ImplicitSignal.signal_type correct")
    assert_range(imp.confidence, 0.0, 1.0, "ImplicitSignal.confidence in range")

    # ── SEInput instantiation ────────────────────────────────────────────────
    inp = SEInput(tas_output={"original_text": "test"})
    assert_equal(inp.user_id, "anonymous", "SEInput.user_id defaults to 'anonymous'")
    assert_equal(inp.topic_frequency_history, {}, "SEInput.topic_frequency_history defaults to {}")


def test_topic_extractor():
    section("FILE 2 — topic_extractor.py  (Keyword + Domain + Concept)")

    from topic_extractor import TopicExtractor, TopicExtractionResult, CONCEPT_NORMALIZER, DOMAIN_LEXICONS
    from models import SignalDomain

    ex = TopicExtractor()

    # ── Turn 1: identity + creativity ────────────────────────────────────────
    r1 = ex.extract("I'm a builder at heart. I've always been obsessed with making things.", True)
    info(f"Turn 1 → domains: {[d.value for d, _ in r1.domain_matches]}")
    assert_not_empty(r1.domain_matches, "Turn 1: at least one domain detected")
    assert_true(r1.is_identity_statement, "Turn 1: identity pattern detected (i'm a builder)")
    assert_range(r1.emotional_intensity, 0.0, 1.0, "Turn 1: emotional_intensity in range")

    # ── Turn 2: career + fatalism ────────────────────────────────────────────
    r2 = ex.extract("My job is fine I guess — stable salary, decent team, good manager.", True)
    info(f"Turn 2a → domains: {[d.value for d, _ in r2.domain_matches]}")
    domain_vals_2 = [d.value for d, _ in r2.domain_matches]
    assert_in("career", domain_vals_2, "Turn 2: career domain detected (job, salary)")
    assert_not_empty(r2.normalized_concepts, "Turn 2: at least one concept normalized")

    r2b = ex.extract("I've been thinking maybe I should start my own startup someday.", True)
    info(f"Turn 2b → domains: {[d.value for d, _ in r2b.domain_matches]}")
    domain_vals_2b = [d.value for d, _ in r2b.domain_matches]
    assert_in("career", domain_vals_2b, "Turn 2b: career domain detected (startup)")

    # ── Turn 3: health ───────────────────────────────────────────────────────
    r3 = ex.extract("I used to run every morning, like 5km before work.", True)
    info(f"Turn 3 → domains: {[d.value for d, _ in r3.domain_matches]}")
    domain_vals_3 = [d.value for d, _ in r3.domain_matches]
    assert_in("health", domain_vals_3, "Turn 3: health domain detected (run)")
    assert_in("fitness", r3.normalized_concepts, "Turn 3: 'run' normalized to 'fitness'")

    # ── Turn 4: relationships + regret ──────────────────────────────────────
    r4 = ex.extract("My girlfriend says I don't give her enough time.", True)
    info(f"Turn 4 → domains: {[d.value for d, _ in r4.domain_matches]}")
    domain_vals_4 = [d.value for d, _ in r4.domain_matches]
    assert_in("relationships", domain_vals_4, "Turn 4: relationships domain detected (girlfriend)")

    r4b = ex.extract("I feel relieved when she cancels plans.", True)
    info(f"Turn 4b → emotional_intensity: {r4b.emotional_intensity:.2f}")
    assert_range(r4b.emotional_intensity, 0.0, 1.0, "Turn 4b: emotional_intensity in valid range")

    # ── Turn 5: finances + learning ─────────────────────────────────────────
    r5a = ex.extract("I will save 20% of my salary starting this month.", True)
    info(f"Turn 5a → domains: {[d.value for d, _ in r5a.domain_matches]}")
    domain_vals_5a = [d.value for d, _ in r5a.domain_matches]
    assert_in("finances", domain_vals_5a, "Turn 5a: finances domain detected (salary, save)")

    r5b = ex.extract("I'm also going to learn Python properly.", True)
    info(f"Turn 5b → domains: {[d.value for d, _ in r5b.domain_matches]}")
    domain_vals_5b = [d.value for d, _ in r5b.domain_matches]
    assert_in("learning", domain_vals_5b, "Turn 5b: learning domain detected (learn)")

    # ── Non-self-referential sentence ────────────────────────────────────────
    r_ns = ex.extract("She's probably right.", is_self_referential=False)
    assert_equal(r_ns.is_self_referential, False, "Non-self-referential flag preserved correctly")

    # ── Empty sentence ───────────────────────────────────────────────────────
    r_empty = ex.extract("")
    assert_equal(r_empty.domain_matches, [], "Empty sentence → no domain matches")

    health_in_matches = any(d == SignalDomain.HEALTH for d, _ in r3.domain_matches)
    assert_true(health_in_matches, "health domain present in domain_matches for run sentence")
    primary_empty = ex.get_primary_domain(r_empty)




    assert_equal(primary_empty, SignalDomain.UNKNOWN, "get_primary_domain returns UNKNOWN for empty")

    # ── Identity patterns ────────────────────────────────────────────────────
    r_id1 = ex.extract("I am a software engineer.", True)
    assert_true(r_id1.is_identity_statement, "'I am a...' triggers identity detection")
    r_id2 = ex.extract("I consider myself a creative person.", True)
    assert_true(r_id2.is_identity_statement, "'I consider myself' triggers identity detection")
    r_id3 = ex.extract("I went to the gym yesterday.", True)
    assert_true(not r_id3.is_identity_statement, "Gym sentence is NOT an identity statement")

    # ── Emotional intensity scoring ──────────────────────────────────────────
    r_hi = ex.extract("I am absolutely devastated and overwhelmed.", True)
    r_lo = ex.extract("I think I might like running a bit.", True)
    assert_true(r_hi.emotional_intensity > r_lo.emotional_intensity,
                "High-intensity sentence scores higher than low-intensity sentence")


def test_signal_assembler():
    section("FILE 3 — signal_assembler.py  (Strength, Layer, NodeUpdate assembly)")

    from signal_assembler import (
        compute_strength, resolve_layer, build_node_id, SignalAssembler,
        TENSE_TO_LAYER,
    )
    from topic_extractor import TopicExtractor
    from models import SignalDomain, SignalLayer, SignalStrength

    ex = TopicExtractor()
    sa = SignalAssembler()

    # ── compute_strength ─────────────────────────────────────────────────────
    s_strong = compute_strength(hedge_score=0.95, emotional_intensity=0.8, confidence=0.92)
    s_medium = compute_strength(hedge_score=0.55, emotional_intensity=0.3, confidence=0.70)
    s_weak   = compute_strength(hedge_score=0.15, emotional_intensity=0.1, confidence=0.50)
    assert_equal(s_strong, SignalStrength.STRONG, "compute_strength: high inputs → STRONG")
    assert_equal(s_medium, SignalStrength.MEDIUM, "compute_strength: medium inputs → MEDIUM")
    assert_equal(s_weak,   SignalStrength.WEAK,   "compute_strength: low inputs → WEAK")

    # ── resolve_layer — tense defaults ───────────────────────────────────────
    assert_equal(resolve_layer("T1", []),  SignalLayer.BEHAVIOUR,  "T1 → BEHAVIOUR (no keywords)")
    assert_equal(resolve_layer("T7", []),  SignalLayer.INTENTION,  "T7 → INTENTION (no keywords)")
    assert_equal(resolve_layer("T10", []), SignalLayer.EMOTION,    "T10 → EMOTION (no keywords)")
    assert_equal(resolve_layer("T6", []),  SignalLayer.EMOTION,    "T6 → EMOTION (no keywords)")
    assert_equal(resolve_layer("T11", []), SignalLayer.FEELING,    "T11 → FEELING (no keywords)")

    # ── resolve_layer — content overrides ────────────────────────────────────
    assert_equal(resolve_layer("T1", ["scared"]),    SignalLayer.EMOTION,    "T1 + 'scared' → EMOTION override")
    assert_equal(resolve_layer("T1", ["anxious"]),   SignalLayer.FEELING,    "T1 + 'anxious' → FEELING override")
    assert_equal(resolve_layer("T4", ["want"]),      SignalLayer.INTENTION,  "T4 + 'want' → INTENTION override")
    assert_equal(resolve_layer("T7", ["training"]),  SignalLayer.BEHAVIOUR,  "T7 + 'training' → BEHAVIOUR override")

    # ── build_node_id ─────────────────────────────────────────────────────────
    assert_equal(build_node_id(SignalDomain.HEALTH,  "fitness"),  "health.fitness",  "build_node_id: health.fitness")
    assert_equal(build_node_id(SignalDomain.CAREER,  "startup"),  "career.startup",  "build_node_id: career.startup")
    assert_equal(build_node_id(SignalDomain.IDENTITY,"self_concept"), "identity.self_concept", "build_node_id: identity.self_concept")
    assert_equal(build_node_id(SignalDomain.FINANCES,"finances_general"), "finances.finances_general", "build_node_id with underscore concept")
    # Spaces should become underscores
    assert_equal(build_node_id(SignalDomain.CREATIVITY,"side project"), "creativity.side_project", "build_node_id: space→underscore")

    # ── assemble — Turn 1 identity sentence ─────────────────────────────────
    tas_s1 = CHAT[0]["mock_tas"]["sentences"][0]
    topic_r1 = ex.extract(tas_s1["text"], tas_s1["self_referential"])
    updates_1 = sa.assemble(tas_s1, topic_r1)
    info(f"Turn 1 sentence 1 → {len(updates_1)} NodeUpdate(s): {[u.node_id for u in updates_1]}")
    assert_not_empty(updates_1, "Turn 1 s1: at least one NodeUpdate produced")
    assert_true(any(u.is_identity_anchored for u in updates_1),
                "Turn 1 s1: identity statement → is_identity_anchored=True")

    # ── assemble — Turn 2 fatalism sentence ──────────────────────────────────
    tas_s2_stuck = CHAT[1]["mock_tas"]["sentences"][1]
    topic_r2 = ex.extract(tas_s2_stuck["text"], tas_s2_stuck["self_referential"])
    updates_stuck = sa.assemble(tas_s2_stuck, topic_r2)
    info(f"Turn 2 'stuck' → {len(updates_stuck)} NodeUpdate(s): {[u.node_id for u in updates_stuck]}")
    # 'stuck' has no clear domain keyword — may produce 0 updates, which is correct
    for u in updates_stuck:
        assert_equal(u.graph_operation, "FLAG", f"Fatalism sentence graph_op = FLAG for {u.node_id}")

    # ── assemble — Turn 2 heavily hedged startup ─────────────────────────────
    tas_s2_startup = CHAT[1]["mock_tas"]["sentences"][2]
    topic_r2s = ex.extract(tas_s2_startup["text"], tas_s2_startup["self_referential"])
    updates_startup = sa.assemble(tas_s2_startup, topic_r2s)
    info(f"Turn 2 startup → {len(updates_startup)} NodeUpdate(s): {[u.node_id for u in updates_startup]}")
    if updates_startup:
        u = updates_startup[0]
        assert_true(u.weight_modifier < 0.5,
                    f"Heavily hedged startup → weight_modifier < 0.5 (got {u.weight_modifier:.2f})")
        assert_equal(u.strength, SignalStrength.WEAK,
                     "Heavily hedged startup → strength=WEAK")

    # ── assemble — Turn 3 historical fitness (DECREMENT) ─────────────────────
    tas_s3 = CHAT[2]["mock_tas"]["sentences"][0]
    topic_r3 = ex.extract(tas_s3["text"], tas_s3["self_referential"])
    updates_3 = sa.assemble(tas_s3, topic_r3)
    info(f"Turn 3 historical → {len(updates_3)} NodeUpdate(s): {[u.node_id for u in updates_3]}")
    assert_not_empty(updates_3, "Turn 3 historical: at least one NodeUpdate produced")
    assert_true(any(u.graph_operation == "DECREMENT" for u in updates_3),
                "Turn 3 historical: DECREMENT operation present")
    assert_true(any("fitness" in u.node_id for u in updates_3),
                "Turn 3 historical: fitness node targeted")

    # ── assemble — Turn 4 counterfactual regret (TRIGGER) ────────────────────
    tas_s4_regret = CHAT[3]["mock_tas"]["sentences"][2]
    topic_r4 = ex.extract(tas_s4_regret["text"], tas_s4_regret["self_referential"])
    updates_4 = sa.assemble(tas_s4_regret, topic_r4)
    info(f"Turn 4 regret → {len(updates_4)} NodeUpdate(s): {[u.node_id for u in updates_4]}")
    if updates_4:
        assert_true(any(u.graph_operation == "TRIGGER" for u in updates_4),
                    "Turn 4 regret: TRIGGER operation present")

    # ── assemble — Turn 4 non-self-referential (should be skipped) ───────────
    tas_s4_ns = CHAT[3]["mock_tas"]["sentences"][1]
    topic_r4ns = ex.extract(tas_s4_ns["text"], tas_s4_ns["self_referential"])
    updates_ns = sa.assemble(tas_s4_ns, topic_r4ns)
    assert_equal(updates_ns, [], "Non-self-referential sentence → 0 NodeUpdates (skipped)")

    # ── assemble — Turn 5 declared finance goal (STRONG) ─────────────────────
    tas_s5 = CHAT[4]["mock_tas"]["sentences"][0]
    topic_r5 = ex.extract(tas_s5["text"], tas_s5["self_referential"])
    updates_5 = sa.assemble(tas_s5, topic_r5)
    info(f"Turn 5 finance → {len(updates_5)} NodeUpdate(s): {[u.node_id for u in updates_5]}")
    if updates_5:
        finance_updates = [u for u in updates_5 if u.domain.value == "finances"]
        if finance_updates:
            assert_equal(finance_updates[0].strength, SignalStrength.STRONG,
                         "Turn 5 declared finance goal → STRONG signal")


def test_implicit_detector():
    section("FILE 4 — implicit_detector.py  (Implicit Pattern Detection)")

    from implicit_detector import (
        ImplicitSignalDetector,
        measure_elaboration_asymmetry,
        score_elaboration_depth,
        QUESTION_PATTERNS,
    )
    from models import ImplicitSignalType, SignalDomain

    det = ImplicitSignalDetector()

    # ── score_elaboration_depth ───────────────────────────────────────────────
    long_s  = "I've been working really hard every single day specifically on this startup idea that I'm incredibly passionate about."
    short_s = "I run sometimes."
    long_score  = score_elaboration_depth(long_s)
    short_score = score_elaboration_depth(short_s)
    assert_true(long_score > short_score,
                f"Long sentence scores higher elaboration ({long_score:.2f} > {short_score:.2f})")
    assert_range(long_score,  0.0, 1.0, "Elaboration score capped at 1.0")
    assert_range(short_score, 0.0, 1.0, "Short elaboration score in range")

    # ── measure_elaboration_asymmetry ────────────────────────────────────────
    # Asymmetric: lots before 'but', little after
    asym_sentence = (
        "My job is creative, flexible, well-paid, has an amazing team, "
        "great benefits, and interesting projects. But the hours are long."
    )
    asym = measure_elaboration_asymmetry(asym_sentence)
    assert_true(asym is not None, "Asymmetric sentence → asymmetry detected")
    if asym:
        dominant, weak, ratio = asym
        assert_true(ratio >= 2.5, f"Asymmetry ratio ≥ 2.5 (got {ratio:.1f})")
        assert_equal(dominant, "before_contrast", "Dominant side is before 'but'")

    # Balanced sentence → no asymmetry
    balanced = "The job is good but the commute is terrible."
    bal = measure_elaboration_asymmetry(balanced)
    assert_true(bal is None, "Balanced sentence → no asymmetry detected")

    # No contrast marker → no asymmetry
    no_marker = "I love my job it is the best thing ever."
    assert_true(measure_elaboration_asymmetry(no_marker) is None,
                "No contrast marker → no asymmetry")

    # ── Question signal detection ─────────────────────────────────────────────
    # Validation-seeking
    q_valid = "Is it weird that I feel relieved when she cancels plans?"
    sigs_valid = det._detect_question_signals(q_valid)
    assert_not_empty(sigs_valid, "Validation-seeking question → at least 1 implicit signal")
    assert_equal(sigs_valid[0].signal_type, ImplicitSignalType.QUESTION_TYPE,
                 "Validation question signal_type = QUESTION_TYPE")
    assert_equal(sigs_valid[0].domain, SignalDomain.IDENTITY,
                 "Validation question domain = IDENTITY")

    # Motivation question
    q_motiv = "How do you stay motivated when nothing is working?"
    sigs_motiv = det._detect_question_signals(q_motiv)
    assert_not_empty(sigs_motiv, "Motivation question → at least 1 implicit signal")

    # Non-question sentence → no signals
    sigs_none = det._detect_question_signals("I went for a run this morning.")
    assert_equal(sigs_none, [], "Non-question sentence → 0 question signals")

    # ── Unprompted elaboration ────────────────────────────────────────────────
    long_sent = (
        "I've specifically been thinking every single day about definitely "
        "committing to my fitness routine and absolutely making it happen consistently."
    )
    elab = det._detect_unprompted_elaboration(long_sent)
    assert_true(elab is not None, "Long/detailed sentence → unprompted elaboration detected")
    if elab:
        assert_equal(elab.signal_type, ImplicitSignalType.UNPROMPTED_ELABORATION,
                     "Elaboration signal_type = UNPROMPTED_ELABORATION")

    short_sent = "I run."
    elab_short = det._detect_unprompted_elaboration(short_sent)
    assert_true(elab_short is None, "Short sentence → no unprompted elaboration")

    # ── Repeated topic return ─────────────────────────────────────────────────
    rep_sigs = det._detect_repeated_topics(
        current_topics=["career.job", "health.fitness"],
        topic_history={"career.job": 6, "health.fitness": 5, "relationships.romantic": 1},
    )
    assert_not_empty(rep_sigs, "Topics with history ≥ 3 → repeated topic signals")
    rep_node_ids = [s.concept for s in rep_sigs]
    info(f"Repeated topics detected: {[s.domain.value + '.' + s.concept for s in rep_sigs]}")
    assert_true(len(rep_sigs) == 2, "Two topics above threshold → 2 repeated signals")
    for s in rep_sigs:
        assert_equal(s.signal_type, ImplicitSignalType.REPEATED_TOPIC_RETURN,
                     f"{s.concept}: signal_type = REPEATED_TOPIC_RETURN")
        assert_range(s.confidence, 0.6, 1.0, f"{s.concept}: confidence in [0.6, 1.0]")

    # Topic below threshold → no signal
    no_rep = det._detect_repeated_topics(
        current_topics=["relationships.romantic"],
        topic_history={"relationships.romantic": 1},
    )
    assert_equal(no_rep, [], "Topic mentioned only once → no repeated signal")

    # ── Full detect() call with Turn 4 ───────────────────────────────────────
    turn4 = CHAT[3]
    sentences_t4 = [s["text"] for s in turn4["mock_tas"]["sentences"]]
    all_sigs = det.detect(
        message=turn4["mock_tas"]["original_text"],
        sentences=sentences_t4,
        topic_history=TOPIC_HISTORY,
        current_sentence_topics=["relationships.romantic", "career.job"],
        previously_discussed_domains=PRIOR_DOMAINS,
    )
    info(f"Turn 4 detect() → {len(all_sigs)} implicit signals total")
    signal_types = [s.signal_type.value for s in all_sigs]
    assert_not_empty(all_sigs, "Turn 4: at least 1 implicit signal detected")
    assert_true("question_type" in signal_types or "repeated_topic_return" in signal_types,
                "Turn 4: question_type or repeated_topic_return signal present")


def test_se_orchestrator():
    section("FILE 5 — se_orchestrator.py  (Full Pipeline End-to-End)")

    from se_orchestrator import SEOrchestrator, extract_signals, get_se
    from models import SignalDomain, SignalStrength, SignalLayer

    se = SEOrchestrator()

    # ── singleton helper ──────────────────────────────────────────────────────
    se2 = get_se()
    assert_true(se2 is not None, "get_se() returns a non-None orchestrator")

    # ─────────────────────────────────────────────────────────────────────────
    # Run all 5 chat turns through the orchestrator
    # ─────────────────────────────────────────────────────────────────────────

    results = []
    for turn in CHAT:
        result = se.extract(
            tas_output_dict=turn["mock_tas"],
            user_id="arjun_test",
            session_id=f"session_{turn['turn']}",
            topic_frequency_history=TOPIC_HISTORY,
            previously_discussed_domains=PRIOR_DOMAINS,
        )
        results.append(result)
        info(f"Turn {turn['turn']} → {len(result.node_updates)} updates, "
             f"{len(result.implicit_signals)} implicit, "
             f"{result.processing_time_ms:.1f}ms  flags={result.flags}")

    # ── Turn 1: identity detection ────────────────────────────────────────────
    r1 = results[0]
    assert_not_empty(r1.node_updates, "Turn 1: node_updates not empty")
    assert_true("identity_statement_detected" in r1.flags,
                "Turn 1: 'identity_statement_detected' flag set")
    assert_not_empty(r1.identity_signals, "Turn 1: identity_signals list not empty")

    # ── Turn 2: multi-domain + flags ─────────────────────────────────────────
    r2 = results[1]
    info(f"Turn 2 active_domains: {[d.value for d in r2.active_domains]}")
    assert_not_empty(r2.node_updates, "Turn 2: node_updates not empty")
    # Startup is heavily hedged — check weight is low
    startup_updates = [u for u in r2.node_updates if "startup" in u.node_id]
    if startup_updates:
        assert_true(startup_updates[0].weight_modifier < 0.5,
                    f"Turn 2: startup weight < 0.5 (got {startup_updates[0].weight_modifier:.2f})")

    # ── Turn 3: fitness DECREMENT + repeated topic ────────────────────────────
    r3 = results[2]
    assert_not_empty(r3.node_updates, "Turn 3: node_updates not empty")
    fitness_updates = [u for u in r3.node_updates if "fitness" in u.node_id]
    assert_not_empty(fitness_updates, "Turn 3: fitness node targeted")
    decrement_ops = [u for u in fitness_updates if u.graph_operation == "DECREMENT"]
    assert_not_empty(decrement_ops, "Turn 3: at least one DECREMENT on fitness")
    assert_true("high_salience_topic_confirmed" in r3.flags,
                "Turn 3: 'high_salience_topic_confirmed' flag (fitness seen 5 times)")

    # ── Turn 4: relationships + question signal + regret ─────────────────────
    r4 = results[3]
    assert_not_empty(r4.node_updates, "Turn 4: node_updates not empty")
    assert_not_empty(r4.implicit_signals, "Turn 4: implicit signals not empty")
    # Validation-seeking question should produce a QUESTION_TYPE implicit signal
    q_sigs = [s for s in r4.implicit_signals if s["signal_type"] == "question_type"]
    assert_not_empty(q_sigs, "Turn 4: question_type implicit signal detected")

    # ── Turn 5: strong finance + learning ────────────────────────────────────
    r5 = results[4]
    assert_not_empty(r5.node_updates, "Turn 5: node_updates not empty")
    domain_vals_5 = [d.value for d in r5.active_domains]
    info(f"Turn 5 active_domains: {domain_vals_5}")
    assert_true("finances" in domain_vals_5 or "learning" in domain_vals_5,
                "Turn 5: finances or learning domain active")
    strong_updates = [u for u in r5.node_updates if u.strength == SignalStrength.STRONG]
    assert_not_empty(strong_updates, "Turn 5: at least one STRONG signal (declared intention)")

    # ── EFIB layer distribution ───────────────────────────────────────────────
    for i, r in enumerate(results):
        assert_true(isinstance(r.layer_distribution, dict),
                    f"Turn {i+1}: layer_distribution is a dict")
        total_layers = sum(r.layer_distribution.values())
        assert_equal(total_layers, len(r.node_updates),
                     f"Turn {i+1}: layer_distribution sums to node_updates count")

    # ── Performance: all turns < 100ms ───────────────────────────────────────
    for i, r in enumerate(results):
        assert_true(r.processing_time_ms < 100,
                    f"Turn {i+1}: processing_time < 100ms (got {r.processing_time_ms:.1f}ms)")

    # ── extract_signals() convenience wrapper ─────────────────────────────────
    out = extract_signals(
        tas_output_dict=CHAT[0]["mock_tas"],
        user_id="arjun_test",
        topic_frequency_history=TOPIC_HISTORY,
    )
    assert_true(out is not None, "extract_signals() convenience function returns result")
    assert_equal(out.original_text, CHAT[0]["mock_tas"]["original_text"],
                 "extract_signals(): original_text preserved correctly")

    # ── Empty message (edge case) ─────────────────────────────────────────────
    empty_tas = {
        "original_text": "",
        "sentences": [],
        "sentence_level_events": [],
        "contrast_markers_detected": [],
        "session_zimbardo_delta": {},
        "processing_time_ms": 0.0,
    }
    empty_out = se.extract(empty_tas)
    assert_equal(empty_out.node_updates, [], "Empty TASOutput → 0 node_updates")
    assert_in("no_sentences_detected", empty_out.flags, "Empty TASOutput → 'no_sentences_detected' flag")


# =============================================================================
# CHAT PRINTOUT — show what we're testing against
# =============================================================================

def print_chat():
    print(f"\n{BOLD}{'═'*68}{RESET}")
    print(f"{BOLD}  SIMULATED CHAT — Arjun (5 turns){RESET}")
    print(f"{BOLD}{'═'*68}{RESET}")
    for turn in CHAT:
        print(f"\n{CYAN}[Turn {turn['turn']}]{RESET} {turn['text']}")
    print(f"\n{DIM}Topic history: {TOPIC_HISTORY}{RESET}")
    print(f"{DIM}Prior domains: {PRIOR_DOMAINS}{RESET}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print_chat()

    tests = [
        ("se_models.py",          test_se_models),
        ("topic_extractor.py",    test_topic_extractor),
        ("signal_assembler.py",   test_signal_assembler),
        ("implicit_detector.py",  test_implicit_detector),
        ("se_orchestrator.py",    test_se_orchestrator),
    ]

    for file_name, test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            section(f"EXCEPTION in {file_name}")
            traceback.print_exc()
            global FAIL_COUNT
            FAIL_COUNT += 1

    # ── Final summary ─────────────────────────────────────────────────────────
    total = PASS_COUNT + FAIL_COUNT
    pct   = int(PASS_COUNT / total * 100) if total else 0

    print(f"\n{BOLD}{'═'*68}{RESET}")
    print(f"{BOLD}  RESULTS{RESET}")
    print(f"{BOLD}{'═'*68}{RESET}")
    print(f"  {GREEN}{PASS_COUNT} passed{RESET}   {RED}{FAIL_COUNT} failed{RESET}   {total} total   {pct}%")

    if FAIL_COUNT == 0:
        print(f"\n  {GREEN}{BOLD}All tests passed.{RESET}")
    else:
        print(f"\n  {RED}{BOLD}{FAIL_COUNT} test(s) failed — see ✗ lines above.{RESET}")

    print(f"{BOLD}{'═'*68}{RESET}\n")
    sys.exit(0 if FAIL_COUNT == 0 else 1)


if __name__ == "__main__":
    main()