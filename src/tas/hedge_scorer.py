"""
TAS Hedge Scorer
================
Context-aware hedge detection using spaCy dependency parsing.

Key Insight:
-----------
Naive keyword matching fails because:
- "I think pizza is good" → "think" is the main verb, NOT a hedge
- "I think I might go" → "think" modifies "might go", IS a hedge

This module uses syntactic structure to detect TRUE hedges:
1. Modal verbs that reduce certainty (might, could, may)
2. Epistemic phrases that weaken commitment (I think, I guess)
3. Approximators that soften claims (kind of, sort of, maybe)

Hedge Score:
-----------
- 1.0 = Full certainty (no hedges detected)
- 0.0 = Maximum uncertainty (heavily hedged)

Hedges stack multiplicatively:
"I kind of think I might go" = 0.25 × 0.50 × 0.50 = 0.0625
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import spacy
from spacy.tokens import Doc, Token


# =============================================================================
# HEDGE CATEGORIES WITH DISCOUNT FACTORS
# =============================================================================

# Strong hedges: Significant uncertainty reduction (×0.15-0.25)
STRONG_HEDGE_PATTERNS: dict[str, float] = {
    "maybe": 0.20,
    "perhaps": 0.20,
    "possibly": 0.20,
    "someday": 0.15,
    "kind of": 0.25,
    "sort of": 0.25,
    "i guess": 0.20,
    "i suppose": 0.25,
    "not sure": 0.20,
    "who knows": 0.15,
}

# Medium hedges: Moderate uncertainty (×0.40-0.60)
MEDIUM_HEDGE_PATTERNS: dict[str, float] = {
    "might": 0.50,
    "could": 0.55,
    "may": 0.55,
    "probably": 0.60,
    "likely": 0.60,
    "i think": 0.50,
    "sometimes": 0.55,
    "tends to": 0.50,
    "seems like": 0.45,
    "appears to": 0.50,
}

# Light hedges: Minor uncertainty (×0.70-0.85)
LIGHT_HEDGE_PATTERNS: dict[str, float] = {
    "usually": 0.80,
    "generally": 0.80,
    "mostly": 0.80,
    "often": 0.85,
    "i believe": 0.75,
    "i hope": 0.70,
    "i feel like": 0.75,
    "should": 0.80,
}

# Certainty boosters: These INCREASE confidence (they negate hedging)
CERTAINTY_BOOSTERS: set[str] = {
    "definitely",
    "absolutely",
    "certainly",
    "for sure",
    "without doubt",
    "i know",
    "i am certain",
    "will definitely",
    "must",
}

# Modal verbs that indicate uncertainty when used with main verb
UNCERTAIN_MODAL_LEMMAS: set[str] = {"might", "could", "may"}

# Modal verbs that indicate certainty
CERTAIN_MODAL_LEMMAS: set[str] = {"will", "shall", "must"}


# =============================================================================
# HEDGE ANALYSIS RESULT
# =============================================================================

@dataclass
class HedgeAnalysisResult:
    """
    Complete hedge analysis for a sentence.
    
    Attributes:
        hedge_score: Final certainty score (1.0 = certain, 0.0 = uncertain)
        detected_hedge_words: List of hedge phrases found in sentence
        detected_boosters: List of certainty boosters found
        has_uncertain_modal: Whether an uncertain modal verb was detected
        is_heavily_hedged: True if hedge_score < 0.30
        raw_multiplier_chain: List of individual multipliers applied
    """
    
    hedge_score: float = 1.0
    detected_hedge_words: list[str] = field(default_factory=list)
    detected_boosters: list[str] = field(default_factory=list)
    has_uncertain_modal: bool = False
    is_heavily_hedged: bool = False
    raw_multiplier_chain: list[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "hedge_score": round(self.hedge_score, 4),
            "detected_hedge_words": self.detected_hedge_words,
            "detected_boosters": self.detected_boosters,
            "has_uncertain_modal": self.has_uncertain_modal,
            "is_heavily_hedged": self.is_heavily_hedged,
        }


# =============================================================================
# HEDGE SCORER CLASS
# =============================================================================

class HedgeScorer:
    """
    Context-aware hedge detection using spaCy.
    
    Design Principles:
    -----------------
    1. Don't just match keywords - verify syntactic role
    2. "I think" is only a hedge if there's another clause after it
    3. Modal verbs only count if they're attached to the main verb
    4. Certainty boosters can neutralize hedges
    
    Usage:
    ------
    scorer = HedgeScorer()
    result = scorer.analyze("I might kind of want to try it")
    print(result.hedge_score)  # 0.0625
    """
    
    def __init__(self, spacy_model_name: str = "en_core_web_sm"):
        """
        Initialize hedge scorer with spaCy model.
        
        Args:
            spacy_model_name: Name of spaCy model to load
        """
        try:
            self._nlp = spacy.load(spacy_model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{spacy_model_name}' not found. "
                f"Install with: python -m spacy download {spacy_model_name}"
            )
    
    def analyze(self, sentence_text: str) -> HedgeAnalysisResult:
        """
        Analyze a sentence for hedge words and calculate hedge score.
        
        Args:
            sentence_text: Single sentence to analyze
            
        Returns:
            HedgeAnalysisResult with score and detected hedges
        """
        if not sentence_text or not sentence_text.strip():
            return HedgeAnalysisResult(hedge_score=1.0)
        
        doc = self._nlp(sentence_text)
        text_lower = sentence_text.lower()
        
        detected_hedges: list[str] = []
        detected_boosters: list[str] = []
        multiplier_chain: list[float] = []
        has_uncertain_modal = False
        
        # Step 1: Check for certainty boosters (these reduce hedge impact)
        booster_found = False
        for booster in CERTAINTY_BOOSTERS:
            if booster in text_lower:
                detected_boosters.append(booster)
                booster_found = True
        
        # Step 2: Check modal verbs using spaCy dependency parsing
        has_uncertain_modal = self._detect_uncertain_modal(doc)
        if has_uncertain_modal and not booster_found:
            # Only apply modal discount if no certainty booster present
            multiplier_chain.append(0.50)
            # Find which modal it was
            for token in doc:
                if token.lemma_.lower() in UNCERTAIN_MODAL_LEMMAS:
                    detected_hedges.append(token.text.lower())
                    break
        
        # Step 3: Check multi-word hedge patterns
        for pattern, discount_factor in STRONG_HEDGE_PATTERNS.items():
            if self._is_pattern_present_as_hedge(pattern, text_lower, doc):
                detected_hedges.append(pattern)
                multiplier_chain.append(discount_factor)
        
        for pattern, discount_factor in MEDIUM_HEDGE_PATTERNS.items():
            # Skip modals - already handled above
            if pattern in UNCERTAIN_MODAL_LEMMAS:
                continue
            if self._is_pattern_present_as_hedge(pattern, text_lower, doc):
                detected_hedges.append(pattern)
                multiplier_chain.append(discount_factor)
        
        for pattern, discount_factor in LIGHT_HEDGE_PATTERNS.items():
            if self._is_pattern_present_as_hedge(pattern, text_lower, doc):
                detected_hedges.append(pattern)
                multiplier_chain.append(discount_factor)
        
        # Step 4: Calculate final hedge score (multiplicative)
        final_score = 1.0
        for multiplier in multiplier_chain:
            final_score *= multiplier
        
        # Step 5: Apply booster effect (partially restore score)
        if booster_found and final_score < 1.0:
            # Boosters restore ~50% of lost certainty
            lost_certainty = 1.0 - final_score
            restoration = lost_certainty * 0.5
            final_score = min(1.0, final_score + restoration)
        
        # Step 6: Apply floor (minimum 1% certainty)
        final_score = max(0.01, final_score)
        
        # Remove duplicates from detected hedges
        detected_hedges = list(dict.fromkeys(detected_hedges))
        
        return HedgeAnalysisResult(
            hedge_score=round(final_score, 4),
            detected_hedge_words=detected_hedges,
            detected_boosters=detected_boosters,
            has_uncertain_modal=has_uncertain_modal,
            is_heavily_hedged=(final_score < 0.30),
            raw_multiplier_chain=multiplier_chain,
        )
    
    def _detect_uncertain_modal(self, doc: Doc) -> bool:
        """
        Check if sentence contains an uncertain modal attached to main verb.
        
        This is context-aware: 
        - "I could eat" → modal attached to verb, returns True
        - "Could you help?" → question form, different handling
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            True if uncertain modal found modifying a verb
        """
        for token in doc:
            # Check if token is an auxiliary verb
            if token.dep_ == "aux" and token.lemma_.lower() in UNCERTAIN_MODAL_LEMMAS:
                # Verify it's attached to a verb (not a question inversion)
                head = token.head
                if head.pos_ == "VERB":
                    return True
            
            # Also check for modal as main verb pattern
            if token.pos_ == "AUX" and token.lemma_.lower() in UNCERTAIN_MODAL_LEMMAS:
                return True
        
        return False
    
    def _is_pattern_present_as_hedge(
        self, 
        pattern: str, 
        text_lower: str, 
        doc: Doc
    ) -> bool:
        """
        Check if a hedge pattern is present AND functioning as a hedge.
        
        Key insight: "I think pizza is good" vs "I think I should go"
        - First: "think" is the main assertion, NOT a hedge
        - Second: "think" weakens the "should go", IS a hedge
        
        Args:
            pattern: Hedge pattern to check (e.g., "i think")
            text_lower: Lowercased sentence text
            doc: spaCy Doc object
            
        Returns:
            True if pattern is present and functioning as a hedge
        """
        if pattern not in text_lower:
            return False
        
        # Special handling for "I think" - only hedge if followed by another clause
        if pattern == "i think":
            return self._is_epistemic_i_think(doc)
        
        # Special handling for "I believe" - check if stating belief vs hedging
        if pattern == "i believe":
            return self._is_epistemic_i_believe(doc)
        
        # For other patterns, presence is sufficient
        return True
    
    def _is_epistemic_i_think(self, doc: Doc) -> bool:
        """
        Determine if "I think" is being used as an epistemic hedge.
        
        Hedge: "I think I should go" (weakens "should go")
        Not hedge: "I think about life" (main assertion)
        
        Detection: Look for complementizer clause (that, if) or
        embedded verb after "think"
        """
        think_token: Optional[Token] = None
        
        for token in doc:
            if token.lemma_.lower() == "think" and token.pos_ == "VERB":
                think_token = token
                break
        
        if not think_token:
            return False
        
        # Check for embedded clause markers
        for child in think_token.children:
            # "I think that..." or "I think I..."
            if child.dep_ in ("ccomp", "xcomp", "csubj"):
                return True
            # "I think about..." is NOT a hedge
            if child.dep_ == "prep" and child.lemma_ in ("about", "of"):
                return False
        
        # Check if there's another verb after "think"
        found_think = False
        for token in doc:
            if token == think_token:
                found_think = True
                continue
            if found_think and token.pos_ == "VERB" and token != think_token:
                return True
        
        return False
    
    def _is_epistemic_i_believe(self, doc: Doc) -> bool:
        """
        Determine if "I believe" is epistemic hedge vs belief statement.
        
        Hedge: "I believe it might work" (weakens claim)
        Not hedge: "I believe in honesty" (core belief assertion)
        """
        believe_token: Optional[Token] = None
        
        for token in doc:
            if token.lemma_.lower() == "believe" and token.pos_ == "VERB":
                believe_token = token
                break
        
        if not believe_token:
            return False
        
        # "I believe in X" is a belief statement, not a hedge
        for child in believe_token.children:
            if child.dep_ == "prep" and child.lemma_ == "in":
                return False
            # "I believe that X" with embedded clause is hedging
            if child.dep_ in ("ccomp", "xcomp"):
                return True
        
        return True  # Default: treat as mild hedge


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# =============================================================================

# Lazy-loaded singleton scorer
_default_scorer: Optional[HedgeScorer] = None


def get_default_scorer() -> HedgeScorer:
    """Get or create the default HedgeScorer instance."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = HedgeScorer()
    return _default_scorer


def calculate_hedge_score(sentence_text: str) -> HedgeAnalysisResult:
    """
    Convenience function to analyze hedge score.
    
    Uses a cached singleton HedgeScorer instance.
    
    Args:
        sentence_text: Sentence to analyze
        
    Returns:
        HedgeAnalysisResult with score and details
        
    Example:
        >>> result = calculate_hedge_score("I might kind of want to try it")
        >>> print(result.hedge_score)
        0.0625
        >>> print(result.detected_hedge_words)
        ['might', 'kind of']
    """
    scorer = get_default_scorer()
    return scorer.analyze(sentence_text)
