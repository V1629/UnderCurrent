#!/usr/bin/env python3
"""
TAS Tense Classifier - Approach 1 with SPACY
==============================================

Feature-Based Scoring using spaCy for linguistic analysis.
Ready to use - just install: pip install spacy
Then: python -m spacy download en_core_web_sm

Run with: python classifier_spacy.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum
import logging
import spacy

from models import TenseClass

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TenseFeatures:
    """Extracted linguistic features"""
    has_modal_will: bool = False
    has_modal_would: bool = False
    has_modal_should: bool = False
    has_modal_could: bool = False
    has_modal_might: bool = False
    has_if_clause: bool = False
    has_subordinate_clause: bool = False
    has_counterfactual_aux: bool = False
    has_habitual_adverb: bool = False
    has_perfective_aspect: bool = False
    has_progressive_aspect: bool = False
    tense_morph: str = "Unknown"
    emotion_words_count: int = 0
    narrative_markers_count: int = 0
    belief_verb: bool = False
    fatalistic_phrase: bool = False
    hedge_score: float = 0.5
    first_person: bool = False
    sentence: str = ""


@dataclass
class ClassificationResult:
    """Result of classification"""
    sentence: str
    tense_class: TenseClass
    confidence: float
    all_scores: Dict[TenseClass, float] = field(default_factory=dict)
    features: Optional[TenseFeatures] = None
    top_3_predictions: List[Tuple[TenseClass, float]] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.tense_class.value} (confidence: {self.confidence:.2f})"


# ============================================================================
# FEATURE EXTRACTION WITH SPACY
# ============================================================================

class SpacyFeatureExtractor:
    """Extract features using spaCy for better accuracy"""
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """Initialize with spaCy model"""
        try:
            self.nlp = spacy.load(spacy_model)
            logger.info(f"✓ Loaded spaCy model: {spacy_model}")
        except OSError:
            logger.error(f"✗ spaCy model '{spacy_model}' not found!")
            logger.info("Install with: python -m spacy download en_core_web_sm")
            raise RuntimeError(
                f"spaCy model '{spacy_model}' not found. "
                f"Install with: python -m spacy download {spacy_model}"
            )
        
        # Lexicons
        self.habitual_adverbs = {
            "always", "usually", "often", "never", "rarely", "sometimes",
            "generally", "typically", "regularly", "every", "once"
        }
        
        self.emotion_words = {
            "scared", "anxious", "worried", "afraid", "frightened",
            "nervous", "concerned", "stressed", "fearful", "terrified"
        }
        
        self.narrative_markers = {
            "so", "then", "suddenly", "next", "after", "later",
            "finally", "meanwhile", "before", "while"
        }
        
        self.counterfactual_patterns = {
            "should have", "could have", "would have", "if only",
            "wish i had", "had only", "i wish"
        }
        
        self.belief_verbs = {
            "believe", "think", "know", "suppose", "assume", "consider"
        }
        
        self.fatalistic_phrases = {
            "nothing ever changes", "it doesn't matter", "no point",
            "never works", "always fails", "can't change"
        }
    
    def extract(self, sentence: str) -> TenseFeatures:
        """Extract features using spaCy"""
        doc = self.nlp(sentence)
        text_lower = sentence.lower()
        root_verb = self._get_root_verb(doc)
        
        features = TenseFeatures(
            # Modals - precise with spaCy
            has_modal_will=self._has_modal(doc, "will"),
            has_modal_would=self._has_modal(doc, "would"),
            has_modal_should=self._has_modal(doc, "should"),
            has_modal_could=self._has_modal(doc, "could"),
            has_modal_might=self._has_modal(doc, "might"),
            
            # Structure
            has_if_clause="if" in text_lower,
            has_subordinate_clause=self._has_subordinate_clause(doc),
            
            # Aspect
            has_counterfactual_aux=self._matches_any(text_lower, self.counterfactual_patterns),
            has_habitual_adverb=self._matches_any(text_lower, self.habitual_adverbs),
            has_perfective_aspect=self._has_perfective_aspect(doc),
            has_progressive_aspect=self._has_progressive_aspect(doc),
            
            # Tense - from morphology (spaCy)
            tense_morph=self._get_tense(root_verb),
            
            # Semantic
            emotion_words_count=self._count_matches(text_lower, self.emotion_words),
            narrative_markers_count=self._count_matches(text_lower, self.narrative_markers),
            belief_verb=self._has_belief_verb(doc),
            fatalistic_phrase=self._matches_any(text_lower, self.fatalistic_phrases),
            
            # Hedging
            hedge_score=self._calculate_hedge_score(text_lower),
            
            # Structure
            first_person=self._has_first_person(doc),
            
            sentence=sentence,
        )
        
        return features
    
    # ---- Helper Methods ----
    
    def _get_root_verb(self, doc):
        """Find ROOT verb in dependency tree"""
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ in ("VERB", "AUX"):
                return token
        return None
    
    def _has_modal(self, doc, modal: str) -> bool:
        """Check for modal by lemma"""
        return any(t.lemma_ == modal for t in doc if t.pos_ == "AUX")
    
    def _has_subordinate_clause(self, doc) -> bool:
        """Detect subordinate clause"""
        return any(t.dep_ in ("acl", "advcl", "relcl") for t in doc)
    
    def _has_perfective_aspect(self, doc) -> bool:
        """Check for 'have + past participle'"""
        for token in doc:
            if token.lemma_ == "have" and token.pos_ in ("AUX", "VERB"):
                for child in token.children:
                    if child.tag_ == "VBN":
                        return True
        return False
    
    def _has_progressive_aspect(self, doc) -> bool:
        """Check for 'be + gerund'"""
        for token in doc:
            if token.lemma_ == "be" and token.pos_ == "AUX":
                for child in token.children:
                    if child.tag_ == "VBG":
                        return True
        return False
    
    def _get_tense(self, token) -> str:
        """Get morphological tense"""
        if not token:
            return "Unknown"
        tense = token.morph.get("Tense")
        return tense[0] if tense else "Unknown"
    
    def _has_first_person(self, doc) -> bool:
        """Check for I/we"""
        return any(t.pos_ == "PRON" and t.lemma_ in ("i", "we") for t in doc)
    
    def _has_belief_verb(self, doc) -> bool:
        """Check if root is belief verb"""
        root = self._get_root_verb(doc)
        return root and root.lemma_ in self.belief_verbs
    
    def _matches_any(self, text: str, patterns: set) -> bool:
        return any(pat in text for pat in patterns)
    
    def _count_matches(self, text: str, patterns: set) -> int:
        return sum(1 for pat in patterns if pat in text)
    
    def _calculate_hedge_score(self, text: str) -> float:
        """Calculate hedging level"""
        hedge_words = {"might", "could", "maybe", "perhaps", "seem", 
                      "appear", "may", "possibly", "probably"}
        count = sum(1 for w in hedge_words if w in text)
        return min(count * 0.15, 1.0)


# ============================================================================
# SCORING RULES
# ============================================================================

@dataclass
class ScoringRule:
    """Single scoring rule"""
    name: str
    score_func: Callable[[TenseFeatures], float]
    weight: float = 1.0


class TenseClassScorer:
    """Score against all tense classes"""
    
    def __init__(self):
        """Initialize rules"""
        self.rules = {
            TenseClass.ACTIVE_PRESENT: [
                ScoringRule("present_tense", 
                           lambda f: 1.0 if f.tense_morph == "Pres" else 0.0, 1.0),
                ScoringRule("first_person",
                           lambda f: 0.7 if f.first_person else 0.0, 0.8),
                ScoringRule("low_hedging",
                           lambda f: 1.0 if f.hedge_score < 0.6 else 0.3, 0.7),
            ],
            
            TenseClass.HABITUAL_PRESENT: [
                ScoringRule("present_tense",
                           lambda f: 1.0 if f.tense_morph == "Pres" else 0.0, 1.0),
                ScoringRule("habitual_marker",
                           lambda f: 1.0 if f.has_habitual_adverb else 0.0, 1.0),
            ],
            
            TenseClass.NARRATIVE_PRESENT: [
                ScoringRule("present_tense",
                           lambda f: 0.9 if f.tense_morph == "Pres" else 0.1, 0.9),
                ScoringRule("narrative_marker",
                           lambda f: min(f.narrative_markers_count / 1.0, 1.0), 1.0),
            ],
            
            TenseClass.STABLE_BELIEF_PRESENT: [
                ScoringRule("belief_verb",
                           lambda f: 1.0 if f.belief_verb else 0.0, 1.0),
                ScoringRule("present_tense",
                           lambda f: 1.0 if f.tense_morph == "Pres" else 0.5, 0.8),
            ],
            
            TenseClass.HISTORICAL_PAST: [
                ScoringRule("past_tense",
                           lambda f: 1.0 if f.tense_morph == "Past" else 0.0, 1.0),
                ScoringRule("not_perfective",
                           lambda f: 1.0 if not f.has_perfective_aspect else 0.5, 0.7),
            ],
            
            TenseClass.EXPERIENTIAL_PAST: [
                ScoringRule("perfective",
                           lambda f: 1.0 if f.has_perfective_aspect or f.tense_morph == "Perf" else 0.0, 1.0),
                ScoringRule("have_been_pattern",
                           lambda f: 0.8 if "have been" in f.sentence.lower() or "has been" in f.sentence.lower() else 0.0, 0.9),
            ],
            
            TenseClass.COUNTERFACTUAL_PAST: [
                ScoringRule("counterfactual_pattern",
                           lambda f: 1.0 if f.has_counterfactual_aux else 0.0, 1.0),
                ScoringRule("past_tense",
                           lambda f: 1.0 if f.tense_morph == "Past" else 0.0, 0.9),
            ],
            
            TenseClass.DECLARED_FUTURE: [
                ScoringRule("will_modal",
                           lambda f: 1.0 if f.has_modal_will else 0.0, 1.0),
                ScoringRule("low_hedging",
                           lambda f: 1.0 if f.hedge_score < 0.5 else 0.2, 0.8),
            ],
            
            TenseClass.HEDGED_FUTURE: [
                ScoringRule("future_modal",
                           lambda f: 1.0 if (f.has_modal_could or f.has_modal_might) else 0.4, 1.0),
                ScoringRule("hedging",
                           lambda f: 1.0 if f.hedge_score > 0.1 else 0.1, 0.9),
            ],
            
            TenseClass.CONDITIONAL: [
                ScoringRule("if_clause",
                           lambda f: 1.0 if f.has_if_clause else 0.0, 1.0),
                ScoringRule("would_modal",
                           lambda f: 1.0 if f.has_modal_would else 0.0, 1.0),
                ScoringRule("not_present_tense",
                           lambda f: 1.0 if f.tense_morph != "Pres" else 0.5, 0.8),
            ],
            
            TenseClass.PRESENT_FATALISTIC: [
                ScoringRule("present_tense",
                           lambda f: 1.0 if f.tense_morph == "Pres" else 0.1, 0.8),
                ScoringRule("fatalistic_phrase",
                           lambda f: 1.0 if f.fatalistic_phrase else 0.0, 1.0),
            ],
            
            TenseClass.FUTURE_ANXIOUS: [
                ScoringRule("emotion_words",
                           lambda f: 1.0 if f.emotion_words_count > 0 else 0.0, 1.0),
                ScoringRule("future_modal",
                           lambda f: 0.8 if (f.has_modal_will or f.has_modal_would or
                                            f.has_modal_could) else 0.3, 0.8),
            ],
        }
    
    def score_all(self, features: TenseFeatures) -> Dict[TenseClass, float]:
        """Score all tense classes"""
        scores = {}
        
        for tense_class, rules in self.rules.items():
            rule_scores = []
            for rule in rules:
                score = rule.score_func(features) * rule.weight
                rule_scores.append(score)
            
            total_weight = sum(r.weight for r in rules)
            avg = sum(rule_scores) / total_weight if total_weight > 0 else 0.0
            scores[tense_class] = avg
        
        return scores


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

class TenseClassifier:
    """Production-ready tense classifier with spaCy"""
    
    def __init__(self):
        """Initialize classifier"""
        self.feature_extractor = SpacyFeatureExtractor()
        self.scorer = TenseClassScorer()
        logger.info("✓ TenseClassifier initialized successfully\n")
    
    def classify(self, sentence: str) -> ClassificationResult:
        """Classify a sentence"""
        features = self.feature_extractor.extract(sentence)
        scores = self.scorer.score_all(features)
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_class = sorted_scores[0][0]
        confidence = sorted_scores[0][1]
        
        result = ClassificationResult(
            sentence=sentence,
            tense_class=best_class,
            confidence=confidence,
            all_scores=scores,
            features=features,
            top_3_predictions=[(tc, score) for tc, score in sorted_scores[:3]],
        )
        
        return result
    
    def explain(self, sentence: str) -> str:
        """Detailed explanation"""
        result = self.classify(sentence)
        f = result.features
        
        explanation = f"\n{'='*70}\n"
        explanation += f"TENSE CLASSIFICATION EXPLANATION\n"
        explanation += f"{'='*70}\n"
        explanation += f"Sentence: {sentence}\n\n"
        
        explanation += f"RESULT:\n"
        explanation += f"-" * 70 + "\n"
        explanation += f"  Class: {result.tense_class.value}\n"
        explanation += f"  Confidence: {result.confidence:.2f}\n\n"
        
        explanation += f"TOP 3 PREDICTIONS:\n"
        explanation += f"-" * 70 + "\n"
        for i, (tc, score) in enumerate(result.top_3_predictions, 1):
            explanation += f"  {i}. {tc.value:.<40} {score:.2f}\n"
        explanation += "\n"
        
        explanation += f"EXTRACTED FEATURES:\n"
        explanation += f"-" * 70 + "\n"
        explanation += f"  Tense: {f.tense_morph}\n"
        explanation += f"  First person: {f.first_person}\n"
        explanation += f"  Modals: will={f.has_modal_will}, would={f.has_modal_would}, "
        explanation += f"could={f.has_modal_could}, might={f.has_modal_might}\n"
        explanation += f"  Aspects: perfective={f.has_perfective_aspect}, "
        explanation += f"progressive={f.has_progressive_aspect}\n"
        explanation += f"  Semantic: emotions={f.emotion_words_count}, "
        explanation += f"narrative={f.narrative_markers_count}, "
        explanation += f"belief_verb={f.belief_verb}\n"
        explanation += f"  Hedge score: {f.hedge_score:.2f}\n"
        explanation += f"  Counterfactual: {f.has_counterfactual_aux}\n"
        explanation += f"  If-clause: {f.has_if_clause}\n"
        explanation += f"  Fatalistic: {f.fatalistic_phrase}\n"
        explanation += f"\n{'='*70}\n"
        
        return explanation


# ============================================================================
# TESTING
# ============================================================================

def run_tests():
    """Run tests"""
    print("\n" + "="*70)
    print("TAS TENSE CLASSIFIER - WITH SPACY")
    print("="*70)
    print("\nInitializing classifier...\n")
    
    classifier = TenseClassifier()
    
    test_cases = [
        ("I am running to the store", TenseClass.ACTIVE_PRESENT),
        ("I always go to the gym on weekends", TenseClass.HABITUAL_PRESENT),
        ("I think honesty is important", TenseClass.STABLE_BELIEF_PRESENT),
        ("I used to play football", TenseClass.HISTORICAL_PAST),
        ("I have been through a lot", TenseClass.EXPERIENTIAL_PAST),
        ("So I run into the store and see him", TenseClass.NARRATIVE_PRESENT),
        ("I will definitely attend the meeting", TenseClass.DECLARED_FUTURE),
        ("I might go to the party tomorrow", TenseClass.HEDGED_FUTURE),
        ("I would go if I had the time", TenseClass.CONDITIONAL),
        ("I should have finished earlier", TenseClass.COUNTERFACTUAL_PAST),
        ("Nothing ever changes in my life", TenseClass.PRESENT_FATALISTIC),
        ("I'm worried about my future", TenseClass.FUTURE_ANXIOUS),
    ]
    
    print("="*70)
    print("RUNNING CLASSIFICATION TESTS")
    print("="*70 + "\n")
    
    correct = 0
    for i, (sentence, expected) in enumerate(test_cases, 1):
        result = classifier.classify(sentence)
        is_correct = result.tense_class == expected
        
        if is_correct:
            correct += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
        
        print(f"[{i:2d}] {status}")
        print(f"     Sentence: {sentence}")
        print(f"     Expected: {expected.value}")
        print(f"     Got:      {result.tense_class.value} (conf: {result.confidence:.2f})")
        print()
    
    accuracy = correct / len(test_cases) * 100
    print("="*70)
    print(f"SUMMARY: {correct}/{len(test_cases)} tests passed ({accuracy:.1f}%)")
    print("="*70 + "\n")
    
    print("DETAILED EXPLANATION EXAMPLE:")
    print("-" * 70)
    sample = "I might try to exercise tomorrow"
    print(classifier.explain(sample))


if __name__ == "__main__":
    run_tests()