#!/usr/bin/env python3
"""
Tense Migration Detector
========================

Detects behavioral shifts based on tense changes across sessions.
Part of the Tense-as-Signal Analyzer (TAS) in Psynapse.

Migration Events:
- DEPRIORITIZATION: Active (T1/T2) → Historical (T4)
  Signals: User stopped actively working on this topic
  
- REACTIVATION: Historical (T4) → Active (T1)
  Signals: User resumed focus on this topic
  
- COMMITMENT_DECAY: Declared (T7) → Hedged/Conditional (T8/T9)
  Signals: User's commitment is weakening
  
- COMMITMENT_INCREASE: Hedged/Conditional (T8/T9) → Declared (T7)
  Signals: User's commitment is strengthening
  
- BELIEF_QUESTIONING: Belief (T3) → Counterfactual (T10)
  Signals: User questioning core values
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from enum import Enum
import logging

from models import (
    TenseClass,
    MigrationEvent,
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
# MIGRATION DETECTION RULES
# ============================================================================

MIGRATION_RULES: Dict[Tuple[TenseClass, TenseClass], MigrationEvent] = {
    # DEPRIORITIZATION: Active → Historical
    (TenseClass.ACTIVE_PRESENT, TenseClass.HISTORICAL_PAST): MigrationEvent.DEPRIORITIZATION,
    (TenseClass.HABITUAL_PRESENT, TenseClass.HISTORICAL_PAST): MigrationEvent.DEPRIORITIZATION,
    (TenseClass.NARRATIVE_PRESENT, TenseClass.HISTORICAL_PAST): MigrationEvent.DEPRIORITIZATION,
    
    # REACTIVATION: Historical → Active
    (TenseClass.HISTORICAL_PAST, TenseClass.ACTIVE_PRESENT): MigrationEvent.REACTIVATION,
    (TenseClass.HISTORICAL_PAST, TenseClass.HABITUAL_PRESENT): MigrationEvent.REACTIVATION,
    (TenseClass.HISTORICAL_PAST, TenseClass.NARRATIVE_PRESENT): MigrationEvent.REACTIVATION,
    
    # COMMITMENT_DECAY: Declared → Hedged/Conditional
    (TenseClass.DECLARED_FUTURE, TenseClass.HEDGED_FUTURE): MigrationEvent.COMMITMENT_DECAY,
    (TenseClass.DECLARED_FUTURE, TenseClass.CONDITIONAL): MigrationEvent.COMMITMENT_DECAY,
    
    # COMMITMENT_INCREASE: Hedged/Conditional → Declared
    (TenseClass.HEDGED_FUTURE, TenseClass.DECLARED_FUTURE): MigrationEvent.COMMITMENT_INCREASE,
    (TenseClass.CONDITIONAL, TenseClass.DECLARED_FUTURE): MigrationEvent.COMMITMENT_INCREASE,
    
    # BELIEF_QUESTIONING: Belief → Counterfactual
    (TenseClass.STABLE_BELIEF_PRESENT, TenseClass.COUNTERFACTUAL_PAST): MigrationEvent.BELIEF_QUESTIONING,
}

# Contrast markers that indicate intentional shift (not just variation)
CONTRAST_MARKERS = {
    "but", "however", "though", "yet", "instead",
    "on the other hand", "conversely", "in contrast",
    "despite", "although", "whereas", "while",
    "lately", "recently", "these days", "now",
}


# ============================================================================
# MIGRATION DETECTOR
# ============================================================================

class MigrationDetector:
    """Detects behavioral shifts based on tense changes"""
    
    def __init__(self):
        """Initialize detector"""
        logger.info("Initializing MigrationDetector...")
        self.min_history_length = 2  # Need at least 2 classifications
    
    def detect_migration(
        self,
        tense_history: List[TenseClass],
        contrast_markers_present: bool = False
    ) -> Optional[MigrationEvent]:
        """
        Detect migration event from tense history.
        
        Args:
            tense_history: List of tense classifications (ordered by time)
            contrast_markers_present: Whether contrast markers detected in message
        
        Returns:
            MigrationEvent if detected, None otherwise
        """
        
        if len(tense_history) < self.min_history_length:
            return None
        
        # Get last two classifications
        prev_tense = tense_history[-2]
        curr_tense = tense_history[-1]
        
        # Check migration rules
        migration = MIGRATION_RULES.get((prev_tense, curr_tense))
        
        if migration and contrast_markers_present:
            # Boost confidence if contrast markers present
            logger.info(
                f"Migration detected: {TENSE_CLASS_DISPLAY_NAMES[prev_tense]} → "
                f"{TENSE_CLASS_DISPLAY_NAMES[curr_tense]} "
                f"(with contrast markers)"
            )
            return migration
        
        return migration
    
    def detect_trending_shift(
        self,
        tense_history: List[TenseClass],
        window_size: int = 5
    ) -> Optional[MigrationEvent]:
        """
        Detect trending shift over multiple sessions.
        
        More reliable than single-session migration because it
        detects patterns across multiple sessions.
        
        Args:
            tense_history: List of tense classifications
            window_size: Number of sessions to look at
        
        Returns:
            MigrationEvent if trending shift detected
        """
        
        if len(tense_history) < window_size:
            return None
        
        # Get recent window
        recent = tense_history[-window_size:]
        
        # Count tenses in first half vs second half
        first_half = recent[:window_size // 2]
        second_half = recent[window_size // 2:]
        
        # Get dominant tense in each half
        first_dominant = self._get_dominant_tense(first_half)
        second_dominant = self._get_dominant_tense(second_half)
        
        if first_dominant == second_dominant:
            return None
        
        # Check if this is a recognized migration
        migration = MIGRATION_RULES.get((first_dominant, second_dominant))
        
        if migration:
            logger.info(
                f"Trending shift detected over {window_size} sessions: "
                f"{TENSE_CLASS_DISPLAY_NAMES[first_dominant]} → "
                f"{TENSE_CLASS_DISPLAY_NAMES[second_dominant]}"
            )
        
        return migration
    
    def _get_dominant_tense(self, tenses: List[TenseClass]) -> TenseClass:
        """Get most common tense in list"""
        from collections import Counter
        if not tenses:
            return TenseClass.ACTIVE_PRESENT
        counts = Counter(tenses)
        return counts.most_common(1)[0][0]
    
    def get_migration_interpretation(
        self,
        migration: MigrationEvent,
        topic: Optional[str] = None
    ) -> str:
        """
        Get human-readable interpretation of migration.
        
        Args:
            migration: The detected migration event
            topic: Optional topic/node name
        
        Returns:
            Human-readable interpretation
        """
        
        topic_str = f" on '{topic}'" if topic else ""
        
        interpretations = {
            MigrationEvent.DEPRIORITIZATION:
                f"User has stopped actively working on this{topic_str}. "
                f"Shifted from active engagement to historical framing.",
            
            MigrationEvent.REACTIVATION:
                f"User is resuming focus on this{topic_str}. "
                f"Shifted from historical to active engagement.",
            
            MigrationEvent.COMMITMENT_DECAY:
                f"User's commitment is weakening{topic_str}. "
                f"Shifted from declared certainty to hedging/conditions.",
            
            MigrationEvent.COMMITMENT_INCREASE:
                f"User's commitment is strengthening{topic_str}. "
                f"Shifted from hedging/conditions to declared certainty.",
            
            MigrationEvent.BELIEF_QUESTIONING:
                f"User is questioning core beliefs{topic_str}. "
                f"Shifted from stable belief to counterfactual (regret).",
        }
        
        return interpretations.get(migration, "Unknown migration")
    
    def get_migration_actions(
        self,
        migration: MigrationEvent
    ) -> List[str]:
        """
        Get recommended actions based on migration.
        
        Args:
            migration: The detected migration event
        
        Returns:
            List of recommended actions
        """
        
        actions = {
            MigrationEvent.DEPRIORITIZATION: [
                "Check if user has genuinely moved on or facing obstacles",
                "Ask clarifying questions about current status",
                "Update graph node importance downward",
            ],
            
            MigrationEvent.REACTIVATION: [
                "Celebrate renewed engagement",
                "Identify what triggered reactivation",
                "Update graph node importance upward",
            ],
            
            MigrationEvent.COMMITMENT_DECAY: [
                "Explore reasons for weakening commitment",
                "Identify blockers or doubts",
                "Consider whether conditions can be met",
            ],
            
            MigrationEvent.COMMITMENT_INCREASE: [
                "Reinforce the increased commitment",
                "Support concrete next steps",
                "Update intention tracking upward",
            ],
            
            MigrationEvent.BELIEF_QUESTIONING: [
                "Deep exploration of belief shift",
                "Understand regret or dissatisfaction",
                "Explore value realignment",
            ],
        }
        
        return actions.get(migration, [])


# ============================================================================
# CONTRAST MARKER DETECTION
# ============================================================================

def detect_contrast_markers(text: str) -> List[str]:
    """
    Detect contrast markers in text.
    
    Contrast markers indicate the user is explicitly comparing
    two states/times, which strengthens migration signal.
    
    Args:
        text: The text to search
    
    Returns:
        List of detected contrast markers
    """
    text_lower = text.lower()
    found = []
    
    for marker in CONTRAST_MARKERS:
        if marker in text_lower:
            found.append(marker)
    
    return found


# ============================================================================
# TESTING
# ============================================================================

def run_tests():
    """Run migration detector tests"""
    print("\n" + "="*70)
    print("MIGRATION DETECTOR TESTS")
    print("="*70 + "\n")
    
    detector = MigrationDetector()
    
    # Test Case 1: Deprioritization
    print("Test 1: DEPRIORITIZATION")
    print("-" * 70)
    history1 = [
        TenseClass.ACTIVE_PRESENT,
        TenseClass.HABITUAL_PRESENT,
        TenseClass.HABITUAL_PRESENT,
        TenseClass.HISTORICAL_PAST,  # Shift!
    ]
    migration1 = detector.detect_migration(history1, contrast_markers_present=True)
    print(f"History: {[TENSE_CLASS_DISPLAY_NAMES[t] for t in history1]}")
    print(f"Migration: {migration1}")
    if migration1:
        print(f"Interpretation: {detector.get_migration_interpretation(migration1, 'fitness')}")
    print()
    
    # Test Case 2: Commitment Decay
    print("Test 2: COMMITMENT_DECAY")
    print("-" * 70)
    history2 = [
        TenseClass.DECLARED_FUTURE,
        TenseClass.DECLARED_FUTURE,
        TenseClass.HEDGED_FUTURE,  # Shift!
    ]
    migration2 = detector.detect_migration(history2, contrast_markers_present=False)
    print(f"History: {[TENSE_CLASS_DISPLAY_NAMES[t] for t in history2]}")
    print(f"Migration: {migration2}")
    if migration2:
        print(f"Interpretation: {detector.get_migration_interpretation(migration2, 'startup')}")
        print(f"Actions: {detector.get_migration_actions(migration2)}")
    print()
    
    # Test Case 3: Trending Shift
    print("Test 3: TRENDING_SHIFT (over 5 sessions)")
    print("-" * 70)
    history3 = [
        TenseClass.ACTIVE_PRESENT,
        TenseClass.ACTIVE_PRESENT,
        TenseClass.HABITUAL_PRESENT,
        TenseClass.HISTORICAL_PAST,  # Trend: Active → Historical
        TenseClass.HISTORICAL_PAST,
    ]
    migration3 = detector.detect_trending_shift(history3, window_size=5)
    print(f"History: {[TENSE_CLASS_DISPLAY_NAMES[t] for t in history3]}")
    print(f"Migration: {migration3}")
    print()
    
    # Test Case 4: Contrast Markers
    print("Test 4: CONTRAST_MARKER_DETECTION")
    print("-" * 70)
    texts = [
        "I used to run every day, but lately I've been sitting on the couch",
        "I will definitely finish this, however I'm not sure about the timeline",
        "I always exercise, I just go to the gym regularly",
    ]
    for text in texts:
        markers = detect_contrast_markers(text)
        print(f"Text: {text}")
        print(f"Markers: {markers}")
        print()


if __name__ == "__main__":
    run_tests()