"""
TAS Data Models
===============
Core data structures for the Tense-as-Signal Analyzer.

This file defines:
1. TenseClass enum (T1-T12) - The 12 psychological tense categories
2. GraphOperation enum - Operations to send to downstream graph engine
3. TemporalOrientation enum - Past/Present/Future orientation
4. MigrationEvent enum - Behavioral shift event types
5. ZimbardoProfile dataclass - Temporal personality profile
6. Pydantic models for API I/O (SentenceAnalysis, TASOutput, TASInput)

All other TAS files depend on these definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class TenseClass(str, Enum):
    """
    12 psychological tense classes.
    
    Each class represents a distinct psychological relationship
    between the speaker and the content they're expressing.
    """
    
    ACTIVE_PRESENT = "T1"           # "I'm building a startup"
    HABITUAL_PRESENT = "T2"         # "I always wake up early"
    STABLE_BELIEF_PRESENT = "T3"    # "I believe in honesty"
    HISTORICAL_PAST = "T4"          # "I used to run daily"
    EXPERIENTIAL_PAST = "T5"        # "I went through a tough time"
    NARRATIVE_PRESENT = "T6"        # "So I walk into the room and..."
    DECLARED_FUTURE = "T7"          # "I will launch next month"
    HEDGED_FUTURE = "T8"            # "I might try to exercise"
    CONDITIONAL = "T9"              # "I would travel if I could"
    COUNTERFACTUAL_PAST = "T10"     # "I should have left earlier"
    PRESENT_FATALISTIC = "T11"      # "Nothing ever changes"
    FUTURE_ANXIOUS = "T12"          # "I'm scared of what might happen"


class TemporalOrientation(str, Enum):
    """Psychological temporal orientation."""
    
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


class GraphOperation(str, Enum):
    """
    Operations to route to the downstream graph engine.
    
    These tell the graph engine how to update node weights
    based on the tense analysis.
    """
    
    INCREASE_WEIGHT = "INCREMENT"       # Active engagement → boost node
    DECREASE_WEIGHT = "DECREMENT"       # Disengagement → reduce node
    MOVE_TO_ARCHIVE = "ARCHIVE"         # Historical → archive node
    FLAG_FOR_ATTENTION = "FLAG"         # Concerning pattern → flag node
    TRIGGER_EVENT = "TRIGGER"           # Conflict/regret → trigger event
    NO_OPERATION = "NONE"               # Non-self-referential → skip


class MigrationEvent(str, Enum):
    """
    Tense migration event types.
    
    These events fire when a topic's dominant tense
    shifts across sessions, signaling behavioral change.
    """
    
    DEPRIORITIZATION = "DEPRIORITIZATION"       # T1/T2 → T4 (active → historical)
    REACTIVATION = "REACTIVATION"               # T4 → T1 (historical → active)
    COMMITMENT_DECAY = "COMMITMENT_DECAY"       # T7 → T8/T9 (declared → hedged)
    COMMITMENT_INCREASE = "COMMITMENT_INCREASE" # T8/T9 → T7 (hedged → declared)
    BELIEF_QUESTIONING = "BELIEF_QUESTIONING"   # T3 → T10 (belief → counterfactual)


# =============================================================================
# MAPPINGS
# =============================================================================

# Human-readable names for each tense class
TENSE_CLASS_DISPLAY_NAMES: dict[TenseClass, str] = {
    TenseClass.ACTIVE_PRESENT: "Active Present",
    TenseClass.HABITUAL_PRESENT: "Habitual Present",
    TenseClass.STABLE_BELIEF_PRESENT: "Stable Belief Present",
    TenseClass.HISTORICAL_PAST: "Historical Past",
    TenseClass.EXPERIENTIAL_PAST: "Experiential Past",
    TenseClass.NARRATIVE_PRESENT: "Narrative Present",
    TenseClass.DECLARED_FUTURE: "Declared Future",
    TenseClass.HEDGED_FUTURE: "Hedged Future",
    TenseClass.CONDITIONAL: "Conditional",
    TenseClass.COUNTERFACTUAL_PAST: "Counterfactual Past",
    TenseClass.PRESENT_FATALISTIC: "Present-Fatalistic",
    TenseClass.FUTURE_ANXIOUS: "Future-Anxious",
}

# Mapping tense classes to temporal orientation
TENSE_TO_TEMPORAL_ORIENTATION: dict[TenseClass, TemporalOrientation] = {
    TenseClass.ACTIVE_PRESENT: TemporalOrientation.PRESENT,
    TenseClass.HABITUAL_PRESENT: TemporalOrientation.PRESENT,
    TenseClass.STABLE_BELIEF_PRESENT: TemporalOrientation.PRESENT,
    TenseClass.HISTORICAL_PAST: TemporalOrientation.PAST,
    TenseClass.EXPERIENTIAL_PAST: TemporalOrientation.PAST,
    TenseClass.NARRATIVE_PRESENT: TemporalOrientation.PAST,      # Narrative = psychological past
    TenseClass.DECLARED_FUTURE: TemporalOrientation.FUTURE,
    TenseClass.HEDGED_FUTURE: TemporalOrientation.FUTURE,
    TenseClass.CONDITIONAL: TemporalOrientation.FUTURE,
    TenseClass.COUNTERFACTUAL_PAST: TemporalOrientation.PAST,
    TenseClass.PRESENT_FATALISTIC: TemporalOrientation.PRESENT,
    TenseClass.FUTURE_ANXIOUS: TemporalOrientation.FUTURE,
}

# Default graph operations per tense class
TENSE_TO_DEFAULT_GRAPH_OPERATION: dict[TenseClass, GraphOperation] = {
    TenseClass.ACTIVE_PRESENT: GraphOperation.INCREASE_WEIGHT,     # Active = boost node
    TenseClass.HABITUAL_PRESENT: GraphOperation.INCREASE_WEIGHT,   # Habitual = stable boost
    TenseClass.STABLE_BELIEF_PRESENT: GraphOperation.INCREASE_WEIGHT,  # Belief = values layer
    TenseClass.HISTORICAL_PAST: GraphOperation.DECREASE_WEIGHT,    # Historical = reduce weight
    TenseClass.EXPERIENTIAL_PAST: GraphOperation.NO_OPERATION,     # Experiential = context only
    TenseClass.NARRATIVE_PRESENT: GraphOperation.INCREASE_WEIGHT,  # Narrative = vivid, engaged
    TenseClass.DECLARED_FUTURE: GraphOperation.INCREASE_WEIGHT,    # Declared = strong intention
    TenseClass.HEDGED_FUTURE: GraphOperation.INCREASE_WEIGHT,      # Hedged = weak boost
    TenseClass.CONDITIONAL: GraphOperation.INCREASE_WEIGHT,        # Conditional = desire
    TenseClass.COUNTERFACTUAL_PAST: GraphOperation.TRIGGER_EVENT,  # Counterfactual = regret
    TenseClass.PRESENT_FATALISTIC: GraphOperation.FLAG_FOR_ATTENTION,   # Fatalistic = concern
    TenseClass.FUTURE_ANXIOUS: GraphOperation.FLAG_FOR_ATTENTION,       # Anxious = concern
}


# =============================================================================
# ZIMBARDO PROFILE
# =============================================================================

@dataclass(frozen=True)
class ZimbardoProfile:
    """
    Zimbardo Time Perspective Profile.
    
    Based on Philip Zimbardo's research on temporal personality.
    Each dimension represents a stable trait about how someone
    relates to time.
    
    All values normalized to 0.0-1.0 range.
    Immutable (frozen) for thread safety.
    """
    
    past_negative: float = 0.0      # Regret, trauma, rumination
    past_positive: float = 0.0      # Nostalgia, warm memories
    present_hedonistic: float = 0.0 # Pleasure-seeking, impulsive
    present_fatalistic: float = 0.0 # Helpless, no agency
    future_oriented: float = 0.0    # Goal-driven, planning
    
    def __add__(self, other: ZimbardoProfile) -> ZimbardoProfile:
        """Add two profiles together (capped at 1.0)."""
        return ZimbardoProfile(
            past_negative=min(1.0, self.past_negative + other.past_negative),
            past_positive=min(1.0, self.past_positive + other.past_positive),
            present_hedonistic=min(1.0, self.present_hedonistic + other.present_hedonistic),
            present_fatalistic=min(1.0, self.present_fatalistic + other.present_fatalistic),
            future_oriented=min(1.0, self.future_oriented + other.future_oriented),
        )
    
    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "past_negative": self.past_negative,
            "past_positive": self.past_positive,
            "present_hedonistic": self.present_hedonistic,
            "present_fatalistic": self.present_fatalistic,
            "future_oriented": self.future_oriented,
        }
    
    @property
    def dominant_orientation(self) -> str:
        """Return the dominant temporal orientation."""
        values = self.to_dict()
        return max(values, key=lambda k: values[k])
    
    def normalize(self) -> ZimbardoProfile:
        """Normalize profile so values sum to 1.0."""
        total = sum(self.to_dict().values())
        if total == 0:
            return self
        return ZimbardoProfile(
            past_negative=self.past_negative / total,
            past_positive=self.past_positive / total,
            present_hedonistic=self.present_hedonistic / total,
            present_fatalistic=self.present_fatalistic / total,
            future_oriented=self.future_oriented / total,
        )


# =============================================================================
# PYDANTIC MODELS (API I/O)
# =============================================================================

class SentenceAnalysis(BaseModel):
    """
    Analysis result for a single sentence.
    
    This is the core output unit — one per sentence in the input.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Original text
    text: str = Field(..., description="Original sentence text")
    
    # Parsing results
    root_verb: Optional[str] = Field(None, description="Extracted root verb lemma")
    grammatical_tense: str = Field(..., description="Surface grammatical tense")
    
    # Classification
    tense_class: TenseClass = Field(..., description="Classified tense (T1-T12)")
    tense_class_name: str = Field(..., description="Human-readable tense name")
    temporal_orientation: TemporalOrientation = Field(..., description="Past/Present/Future")
    
    # Context
    self_referential: bool = Field(..., description="Is sentence about 'I/we'?")
    
    # Hedge analysis
    hedge_score: float = Field(..., ge=0.0, le=1.0, description="1.0=certain, 0.0=uncertain")
    hedge_words: list[str] = Field(default_factory=list, description="Detected hedge words")
    
    # Confidence
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    
    # Zimbardo
    zimbardo_contribution: dict[str, float] = Field(
        default_factory=dict,
        description="Contribution to Zimbardo profile dimensions"
    )
    
    # Graph routing
    graph_operation: GraphOperation = Field(..., description="Operation for graph engine")
    target_node_hint: Optional[str] = Field(None, description="Suggested topic node")
    weight_modifier: float = Field(1.0, ge=0.0, le=1.0, description="Weight for graph op")
    
    # Flags
    flags: list[str] = Field(default_factory=list, description="Special flags")


class TASOutput(BaseModel):
    """
    Complete TAS analysis output for a message.
    
    Contains all sentence analyses plus aggregated metrics.
    """
    
    model_config = ConfigDict(frozen=True)
    
    # Input
    original_text: str = Field(..., description="Original input message")
    
    # Per-sentence results
    sentences: list[SentenceAnalysis] = Field(
        default_factory=list,
        description="Analysis for each sentence"
    )
    
    # Events
    sentence_level_events: list[str] = Field(
        default_factory=list,
        description="Migration and contrast events"
    )
    contrast_markers_detected: list[str] = Field(
        default_factory=list,
        description="Detected contrast words (but, however)"
    )
    
    # Aggregated Zimbardo
    session_zimbardo_delta: dict[str, float] = Field(
        default_factory=dict,
        description="Total Zimbardo changes this message"
    )
    
    # Performance
    processing_time_ms: float = Field(..., ge=0.0, description="Processing time")


class TASInput(BaseModel):
    """Input schema for TAS analysis requests."""
    
    message: str = Field(..., min_length=1, description="User message to analyze")
    user_id: str = Field(default="anonymous", description="User identifier")
    session_id: str = Field(default="default", description="Session identifier")
    tense_history: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Historical tense data per topic node"
    )