#!/usr/bin/env python3
"""
TAS Main Analyzer
=================

Main orchestrator for the Tense-as-Signal Analyzer.
Ties together: classifier, hedge_scorer, zimbardo, migration detection.

Entry point for all TAS analysis.
"""

from __future__ import annotations
import re
import time
from typing import List, Dict, Optional
import logging

from classifier import TenseClassifier
from models import (
    TenseClass,
    GraphOperation,
    SentenceAnalysis,
    TASOutput,
    TENSE_CLASS_DISPLAY_NAMES,
    TENSE_TO_TEMPORAL_ORIENTATION,
    TENSE_TO_DEFAULT_GRAPH_OPERATION,
)
from zimbardo import ZimbardoAccumulator
from migration import MigrationDetector, detect_contrast_markers

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,  # <--- set to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SENTENCE SEGMENTATION
# ============================================================================

def segment_sentences(text: str) -> List[str]:
    """
    Simple sentence segmentation.
    
    Splits on: . ! ? followed by space
    Handles abbreviations (Dr., Mr., etc.)
    """
    # Replace common abbreviations
    text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof)\.\s', r'\1 ', text)
    
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Clean and filter
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


# ============================================================================
# SELF-REFERENTIALITY CHECK
# ============================================================================

FIRST_PERSON_PRONOUNS = {"i", "we", "me", "us", "my", "our", "mine", "ours"}

def is_self_referential(text: str) -> bool:
    """Check if sentence is about the speaker"""
    tokens = text.lower().split()
    return any(token.strip(",.!?;:") in FIRST_PERSON_PRONOUNS for token in tokens)


# ============================================================================
# TAS ANALYZER
# ============================================================================

class TASAnalyzer:
    """
    Main TAS analyzer.
    
    Orchestrates:
    1. Sentence segmentation
    2. Tense classification (per sentence)
    3. Hedge scoring
    4. Zimbardo accumulation
    5. Migration detection
    """
    
    def __init__(self):
        """Initialize analyzer components"""
        logger.info("Initializing TASAnalyzer...")
        
        self.tense_classifier = TenseClassifier()
        self.zimbardo_accumulator = ZimbardoAccumulator()
        self.migration_detector = MigrationDetector()
        
        logger.info("TASAnalyzer ready")
    
    def analyze(
        self,
        message: str,
        user_id: str = "anonymous",
        session_id: str = "default",
        tense_history: Optional[Dict[str, List[str]]] = None
    ) -> TASOutput:
        """
        Analyze a message with full TAS pipeline.
        
        Args:
            message: User message text
            user_id: User identifier
            session_id: Session identifier
            tense_history: Dict of node_id → past tense classifications
        
        Returns:
            TASOutput with complete analysis
        """
        
        start_time = time.time()
        
        logger.info(f"Analyzing message from {user_id} (session {session_id})")
        logger.debug(f"Message: {message}")
        
        # Step 1: Segment sentences
        sentences_text = segment_sentences(message)
        logger.debug(f"Segmented into {len(sentences_text)} sentences")
        
        # Step 2: Analyze each sentence
        sentence_analyses: List[SentenceAnalysis] = []
        
        for sentence_text in sentences_text:
            if not sentence_text.strip():
                continue
            
            analysis = self._analyze_sentence(sentence_text)
            sentence_analyses.append(analysis)
        
        # Step 3: Detect migrations and events
        sentence_level_events = []
        contrast_markers = detect_contrast_markers(message)
        
        if tense_history:
            # Check for migrations (would need to implement per-topic tracking)
            # For now, just log contrasts
            if contrast_markers:
                sentence_level_events.append(f"CONTRAST_DETECTED: {', '.join(contrast_markers)}")
        
        # Step 4: Accumulate Zimbardo profile
        zimbardo_delta = {}
        for analysis in sentence_analyses:
            if analysis.self_referential:  # Only count self-referential
                # Add contribution (would use hedge score)
                contrib = self.zimbardo_accumulator.add_tense_contribution(
                    analysis.tense_class,
                    analysis.hedge_score,
                    analysis.text
                )
                
                # Accumulate delta
                for key, value in contrib.to_dict().items():
                    zimbardo_delta[key] = zimbardo_delta.get(key, 0.0) + value
        
        # Step 5: Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Analysis complete: {len(sentence_analyses)} sentences in {processing_time_ms:.1f}ms")
        
        return TASOutput(
            original_text=message,
            sentences=sentence_analyses,
            sentence_level_events=sentence_level_events,
            contrast_markers_detected=contrast_markers,
            session_zimbardo_delta=zimbardo_delta,
            processing_time_ms=processing_time_ms,
        )
    
    def _analyze_sentence(self, text: str) -> SentenceAnalysis:
        """Analyze a single sentence"""

        # Classify tense
        classification = self.tense_classifier.classify(text)
        tense_class = classification.tense_class
        confidence = classification.confidence
        features = classification.features

        # DEBUG: Log classifier output for tracing
        logger.debug(f"Classifier output for sentence: '{text}'")
        logger.debug(f"  tense_class: {tense_class}")
        logger.debug(f"  confidence: {confidence}")
        logger.debug(f"  features: {features}")

        # Determine self-referentiality
        self_ref = is_self_referential(text)

        # Extract root verb lemma from features (not the full sentence string)
        root_verb = None
        if features is not None:
            # TenseFeatures stores the full sentence in .sentence
            # The actual root verb lemma is extracted via spaCy internally
            # We use tense_morph as a proxy label since root lemma isn't stored separately
            root_verb = features.tense_morph  # e.g. "Pres", "Past" — best available without re-parsing

        # Hedge score: classifier's hedge_score runs 0.0–1.0 where LOWER = more hedged.
        # This matches the weight_modifier semantics (1.0 = full weight, 0.0 = no weight).
        # However classifier default is 0.5 (neutral), not 1.0 (certain).
        # Clamp to [0.01, 1.0] and treat as-is — it is the weight modifier directly.
        raw_hedge = features.hedge_score if features is not None else 1.0
        weight_modifier = max(0.01, min(1.0, raw_hedge))

        # Hedge words are not separately stored by classifier features;
        # hedge_score captures the aggregate signal.
        hedge_words = []

        # Get graph operation — now works correctly since both sides use models.TenseClass
        graph_op = TENSE_TO_DEFAULT_GRAPH_OPERATION.get(tense_class, GraphOperation.NO_OPERATION)

        # Determine flags
        flags = []
        if not self_ref:
            flags.append("non_self_referential")
        if weight_modifier < 0.3:
            flags.append("heavily_hedged")
        if tense_class == TenseClass.PRESENT_FATALISTIC:
            flags.append("fatalism_marker")
        if tense_class == TenseClass.COUNTERFACTUAL_PAST:
            flags.append("regret_marker")

        return SentenceAnalysis(
            text=text,
            root_verb=root_verb,
            grammatical_tense=features.tense_morph if features is not None else "Unknown",
            tense_class=tense_class,
            tense_class_name=TENSE_CLASS_DISPLAY_NAMES[tense_class],
            temporal_orientation=TENSE_TO_TEMPORAL_ORIENTATION[tense_class],
            self_referential=self_ref,
            hedge_score=weight_modifier,
            hedge_words=hedge_words,
            confidence=confidence,
            zimbardo_contribution={},
            graph_operation=graph_op,
            target_node_hint=None,
            weight_modifier=weight_modifier,
            flags=flags,
        )


# ============================================================================
# TESTING
# ============================================================================

def run_tests():
    """Run TAS analyzer tests"""
    print("\n" + "="*70)
    print("TAS ANALYZER TESTS")
    print("="*70 + "\n")
    
    analyzer = TASAnalyzer()
    
    test_messages = [
        "I'm building a startup. I will definitely launch next month.",
        "I used to run every day, but lately I've been getting back into it.",
        "I might kind of think about maybe exercising tomorrow. Nothing ever changes anyway.",
        "I think hard work matters. I believe in myself.",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[Test {i}]")
        print(f"Message: {message}\n")
        
        output = analyzer.analyze(message)
        
        print(f"Analyzed {len(output.sentences)} sentences:")
        print("-" * 70)
        
        for j, sentence in enumerate(output.sentences, 1):
            print(f"\nSentence {j}: {sentence.text}")
            print(f"  Tense: {sentence.tense_class_name} (confidence: {sentence.confidence:.2f})")
            print(f"  Self-referential: {sentence.self_referential}")
            print(f"  Hedge score: {sentence.hedge_score:.2f}")
            print(f"  Graph op: {sentence.graph_operation.value}")
            if sentence.flags:
                print(f"  Flags: {', '.join(sentence.flags)}")
        
        if output.contrast_markers_detected:
            print(f"\nContrast markers: {', '.join(output.contrast_markers_detected)}")
        
        print(f"\nProcessing time: {output.processing_time_ms:.1f}ms")
        print("=" * 70)


if __name__ == "__main__":
    run_tests()