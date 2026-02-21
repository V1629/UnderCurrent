"""
Signal Extractor — Data Models
================================
Core data structures for the Signal Extractor (SE) submodule.
Pure stdlib (dataclasses + enums) — no external dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# =============================================================================
# ENUMS
# =============================================================================

class SignalDomain(str, Enum):
    CAREER        = "career"
    HEALTH        = "health"
    RELATIONSHIPS = "relationships"
    FINANCES      = "finances"
    CREATIVITY    = "creativity"
    IDENTITY      = "identity"
    LEARNING      = "learning"
    UNKNOWN       = "unknown"


class SignalLayer(str, Enum):
    EMOTION   = "emotion"
    FEELING   = "feeling"
    INTENTION = "intention"
    BEHAVIOUR = "behaviour"


class SignalStrength(str, Enum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK   = "weak"


class ImplicitSignalType(str, Enum):
    REPEATED_TOPIC_RETURN  = "repeated_topic_return"
    AVOIDANCE              = "avoidance"
    UNPROMPTED_ELABORATION = "unprompted_elaboration"
    QUESTION_TYPE          = "question_type"
    ASYMMETRIC_ELABORATION = "asymmetric_elaboration"


# =============================================================================
# CORE SIGNAL DATACLASSES
# =============================================================================

@dataclass
class ExplicitSignal:
    raw_text: str
    domain: SignalDomain
    layer: SignalLayer
    concept: str
    strength: SignalStrength
    tense_class: str
    graph_operation: str
    weight_modifier: float
    self_referential: bool
    is_identity_statement: bool
    emotional_intensity: float
    keywords: list = field(default_factory=list)


@dataclass
class ImplicitSignal:
    signal_type: ImplicitSignalType
    domain: SignalDomain
    concept: str
    evidence: str
    confidence: float
    weight_modifier: float


@dataclass
class NodeUpdate:
    node_id: str
    domain: SignalDomain
    concept: str
    graph_operation: str
    weight_modifier: float
    layer: SignalLayer
    signal_source: str
    strength: SignalStrength
    tense_class: str
    is_identity_anchored: bool
    emotional_intensity: float
    source_text: str
    confidence: float


@dataclass
class SEOutput:
    original_text: str
    user_id: str
    session_id: str
    node_updates: list = field(default_factory=list)
    implicit_signals: list = field(default_factory=list)
    active_domains: list = field(default_factory=list)
    identity_signals: list = field(default_factory=list)
    layer_distribution: dict = field(default_factory=dict)
    flags: list = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class SEInput:
    tas_output: dict
    user_id: str = "anonymous"
    session_id: str = "default"
    topic_frequency_history: dict = field(default_factory=dict)
    previously_discussed_domains: list = field(default_factory=list)