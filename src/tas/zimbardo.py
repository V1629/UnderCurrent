#!/usr/bin/env python3
"""
Zimbardo Profile Accumulator
=============================

Accumulates temporal personality traits based on tense classifications.
Part of the Tense-as-Signal Analyzer (TAS) in Psynapse.

Zimbardo's Time Perspective Theory defines 5 temporal orientations:
- Past-Negative: Regret, trauma, rumination
- Past-Positive: Nostalgia, warm memories
- Present-Hedonistic: Pleasure-seeking, impulsive
- Present-Fatalistic: Helpless, no agency
- Future-Oriented: Goal-driven, planning

Each tense class contributes fractionally to these dimensions.
"""

from __future__ import annotations
from typing import Dict, Tuple
import logging

from models import (
    TenseClass,
    ZimbardoProfile,
    TENSE_CLASS_DISPLAY_NAMES,
)

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ZIMBARDO CONTRIBUTION MATRIX
# ============================================================================
# Maps tense class + sentiment → Zimbardo profile deltas

ZIMBARDO_CONTRIBUTIONS: Dict[TenseClass, Dict[str, float]] = {
    TenseClass.ACTIVE_PRESENT: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.02,
        "present_fatalistic": 0.0,
        "future_oriented": 0.0,
    },
    
    TenseClass.HABITUAL_PRESENT: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.01,
        "present_fatalistic": 0.0,
        "future_oriented": 0.01,
    },
    
    TenseClass.STABLE_BELIEF_PRESENT: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.0,
        "future_oriented": 0.02,  # Values guide planning
    },
    
    TenseClass.HISTORICAL_PAST: {
        "past_negative": 0.01,      # Can be regret
        "past_positive": 0.02,      # Or nostalgia
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.0,
        "future_oriented": 0.0,
    },
    
    TenseClass.EXPERIENTIAL_PAST: {
        "past_negative": 0.01,      # Experience = learning
        "past_positive": 0.01,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.0,
        "future_oriented": 0.0,
    },
    
    TenseClass.NARRATIVE_PRESENT: {
        "past_negative": 0.01,      # Reliving past
        "past_positive": 0.02,
        "present_hedonistic": 0.01, # Vividness
        "present_fatalistic": 0.0,
        "future_oriented": 0.0,
    },
    
    TenseClass.DECLARED_FUTURE: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.0,
        "future_oriented": 0.04,    # Strong future orientation
    },
    
    TenseClass.HEDGED_FUTURE: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.0,
        "future_oriented": 0.02,    # Weak future orientation
    },
    
    TenseClass.CONDITIONAL: {
        "past_negative": 0.0,
        "past_positive": 0.0,
        "present_hedonistic": 0.01, # Desire
        "present_fatalistic": 0.01, # If-then = limited agency
        "future_oriented": 0.01,
    },
    
    TenseClass.COUNTERFACTUAL_PAST: {
        "past_negative": 0.05,      # Regret signal
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.01, # Helplessness
        "future_oriented": 0.0,
    },
    
    TenseClass.PRESENT_FATALISTIC: {
        "past_negative": 0.02,
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.05, # Strong fatalism signal
        "future_oriented": 0.0,
    },
    
    TenseClass.FUTURE_ANXIOUS: {
        "past_negative": 0.01,
        "past_positive": 0.0,
        "present_hedonistic": 0.0,
        "present_fatalistic": 0.02, # Anxiety = helplessness
        "future_oriented": 0.02,    # Future-focused (anxiously)
    },
}


# ============================================================================
# SENTIMENT MODIFIERS
# ============================================================================
# Additional modifiers based on emotional valence of the content

POSITIVE_SENTIMENT_WORDS = {
    "love", "happy", "great", "amazing", "wonderful", "excellent",
    "proud", "excited", "grateful", "good", "best", "perfect",
    "success", "achieve", "win", "strong", "confident", "capable"
}

NEGATIVE_SENTIMENT_WORDS = {
    "hate", "sad", "terrible", "awful", "horrible", "bad",
    "ashamed", "scared", "worried", "anxious", "fail", "weak",
    "struggle", "difficult", "pain", "regret", "sorry", "upset"
}


# ============================================================================
# ZIMBARDO ACCUMULATOR
# ============================================================================

class ZimbardoAccumulator:
    """Accumulates Zimbardo profile scores from tense classifications"""
    
    def __init__(self):
        """Initialize accumulator"""
        logger.info("Initializing ZimbardoAccumulator...")
        self.current_profile = ZimbardoProfile()
    
    def add_tense_contribution(
        self,
        tense_class: TenseClass,
        hedge_score: float = 1.0,
        text: str = ""
    ) -> ZimbardoProfile:
        """
        Add contribution to profile based on tense classification.
        
        Args:
            tense_class: The classified tense
            hedge_score: Certainty level (0-1). Reduces impact if hedged.
            text: Original text for sentiment analysis
        
        Returns:
            The delta contribution (not the full profile)
        """
        
        # Get base contribution
        base_contribution = ZIMBARDO_CONTRIBUTIONS.get(
            tense_class,
            {k: 0.0 for k in ["past_negative", "past_positive", 
                              "present_hedonistic", "present_fatalistic", 
                              "future_oriented"]}
        )
        
        # Apply hedge discount
        contribution = {k: v * hedge_score for k, v in base_contribution.items()}
        
        # Apply sentiment modifier
        if text:
            sentiment_mod = self._get_sentiment_modifier(text)
            if sentiment_mod != 1.0:
                # Sentiment mostly affects past and present dimensions
                if tense_class in [TenseClass.HISTORICAL_PAST, TenseClass.EXPERIENTIAL_PAST]:
                    contribution["past_negative"] *= sentiment_mod
                    contribution["past_positive"] *= (2.0 - sentiment_mod)  # Inverse
        
        # Create profile from contribution
        delta_profile = ZimbardoProfile(**contribution)
        
        # Update running profile
        self.current_profile = self.current_profile + delta_profile
        
        logger.debug(
            f"Added {TENSE_CLASS_DISPLAY_NAMES[tense_class]} "
            f"(hedge={hedge_score:.2f}): {delta_profile.to_dict()}"
        )
        
        return delta_profile
    
    def _get_sentiment_modifier(self, text: str) -> float:
        """
        Get sentiment modifier (0.5-1.5) based on emotional words.
        
        < 1.0 = negative sentiment
        = 1.0 = neutral
        > 1.0 = positive sentiment
        """
        text_lower = text.lower()
        
        pos_count = sum(1 for word in POSITIVE_SENTIMENT_WORDS if word in text_lower)
        neg_count = sum(1 for word in NEGATIVE_SENTIMENT_WORDS if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 1.0  # Neutral
        
        # Range: 0.5 (very negative) to 1.5 (very positive)
        net_sentiment = (pos_count - neg_count) / (pos_count + neg_count)
        return 1.0 + (net_sentiment * 0.5)  # Map [-1, 1] to [0.5, 1.5]
    
    def reset(self) -> None:
        """Reset profile to zero"""
        self.current_profile = ZimbardoProfile()
        logger.info("Zimbardo profile reset")
    
    def get_profile(self) -> ZimbardoProfile:
        """Get current profile"""
        return self.current_profile
    
    def get_dominant_orientation(self) -> str:
        """Get dominant temporal orientation"""
        return self.current_profile.dominant_orientation
    
    def normalize_profile(self) -> ZimbardoProfile:
        """
        Normalize profile so dimensions sum to 1.0.
        
        Useful for comparing profiles on same scale.
        """
        profile_dict = self.current_profile.to_dict()
        total = sum(profile_dict.values())
        
        if total == 0:
            return self.current_profile
        
        normalized = {k: v / total for k, v in profile_dict.items()}
        return ZimbardoProfile(**normalized)


# ============================================================================
# BATCH ACCUMULATION
# ============================================================================

def accumulate_tense_list(
    tense_data: list[Tuple[TenseClass, float, str]]
) -> ZimbardoProfile:
    """
    Accumulate a list of tense classifications into a Zimbardo profile.
    
    Args:
        tense_data: List of (tense_class, hedge_score, text) tuples
    
    Returns:
        Aggregated ZimbardoProfile
    """
    accumulator = ZimbardoAccumulator()
    
    for tense_class, hedge_score, text in tense_data:
        accumulator.add_tense_contribution(tense_class, hedge_score, text)
    
    return accumulator.get_profile()


# ============================================================================
# TESTING
# ============================================================================

def run_tests():
    """Run Zimbardo accumulator tests"""
    print("\n" + "="*70)
    print("ZIMBARDO ACCUMULATOR TESTS")
    print("="*70 + "\n")
    
    accumulator = ZimbardoAccumulator()
    
    test_cases = [
        (TenseClass.DECLARED_FUTURE, 1.0, "I will launch my startup next month"),
        (TenseClass.HABITUAL_PRESENT, 1.0, "I always exercise in the morning"),
        (TenseClass.COUNTERFACTUAL_PAST, 1.0, "I should have taken that job"),
        (TenseClass.PRESENT_FATALISTIC, 1.0, "Nothing ever changes in my life"),
        (TenseClass.HEDGED_FUTURE, 0.3, "I might kind of try to exercise"),
    ]
    
    print("Adding tense contributions:\n")
    
    for tense_class, hedge_score, text in test_cases:
        delta = accumulator.add_tense_contribution(tense_class, hedge_score, text)
        print(f"Text: {text}")
        print(f"  Tense: {TENSE_CLASS_DISPLAY_NAMES[tense_class]}")
        print(f"  Hedge: {hedge_score:.2f}")
        print(f"  Delta: {delta.to_dict()}")
        print()
    
    # Show final profile
    print("="*70)
    print("FINAL ACCUMULATED PROFILE:")
    print("="*70)
    final_profile = accumulator.get_profile()
    for key, value in final_profile.to_dict().items():
        print(f"  {key:.<40} {value:.4f}")
    
    print(f"\nDominant orientation: {final_profile.dominant_orientation}")
    print()
    
    # Normalized profile
    print("="*70)
    print("NORMALIZED PROFILE (sum=1.0):")
    print("="*70)
    normalized = accumulator.normalize_profile()
    for key, value in normalized.to_dict().items():
        print(f"  {key:.<40} {value:.4f}")
    print()


if __name__ == "__main__":
    run_tests()