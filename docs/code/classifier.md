# classifier.py — TAS Tense Classifier

## Overview

`classifier.py` implements the **core logic** for classifying sentences into one of 12 psychological tense classes (T1-T12) as defined in the TAS system. It combines spaCy parsing, context-aware hedge scoring, and rule-based logic for robust, explainable tense classification.

**Location**: `src/tas/classifier.py`

---

## What This File Contains

| Component | Type | Purpose |
|-----------|------|---------|
| `TenseClassifier` | class | Main classifier, exposes `classify_sentence()` |
| `TenseClassificationResult` | class | Output: tense class, confidence, reason |
| `NARRATIVE_MARKERS` | set | Detects storytelling/narrative present |
| `FATALISTIC_PATTERNS` | set | Detects fatalistic present (T11) |
| `COUNTERFACTUAL_PATTERNS` | set | Detects counterfactual past (T10) |
| `CONDITIONAL_PATTERNS` | set | Detects conditional mood (T9) |

---

## Classification Pipeline

The classifier follows a **priority order** to assign tense classes:

1. **Narrative Present (T6)** — Storytelling markers ("so", "then", etc.)
2. **Present-Fatalistic (T11)** — "nothing ever changes", "no point"
3. **Counterfactual Past (T10)** — "should have", "if only"
4. **Conditional (T9)** — "would", "if I could"
5. **Hedged Future (T8)** — Future-oriented + hedge score < 0.7
6. **Declared Future (T7)** — Future-oriented ("will", "shall")
7. **Habitual Present (T2)** — "always", "usually", "every day"
8. **Stable Belief Present (T3)** — "I believe", "I think" (main verb)
9. **Historical Past (T4)** — "used to", past tense
10. **Experiential Past (T5)** — "went through", "experienced"
11. **Active Present (T1)** — Present tense, first person
12. **Future-Anxious (T12)** — "scared", "worried", "anxious"
13. **Default** — Fallback to T1 (Active Present)

---

## Design Decisions

### 1. Rule-Based, Not ML
- **Reason**: Rules are explainable, debuggable, and fast (<10ms per sentence)
- **LLM fallback**: Only if confidence < 0.6 (not implemented here)

### 2. spaCy for Parsing
- Used for POS tagging, dependency parsing, and morphological features
- Ensures tense, person, and aspect are detected robustly

### 3. Hedge Scoring Integration
- Uses `hedge_scorer.py` to discount future intentions (T8)
- If `hedge_score < 0.7` and future-oriented → T8 (Hedged Future)

### 4. Confidence Scores
- Each rule returns a confidence (0.60–0.98)
- Useful for downstream fallback or UI display

---

## Key Methods

### `classify_sentence(sentence: str) -> TenseClassificationResult`
- Returns: `tense_class`, `confidence`, `reason`
- Calls helper methods for each tense class in priority order

### Helper Methods
- `_is_narrative_present()` — Looks for narrative markers
- `_matches_any()` — Checks for any pattern in text
- `_is_future_oriented()` — Looks for future tense/modal
- `_is_habitual_present()` — Looks for habitual adverbs
- `_is_belief_statement()` — Checks for belief verbs as main assertion
- `_is_historical_past()` — Looks for "used to" or past tense
- `_is_experiential_past()` — Looks for "went through", "experienced"
- `_is_active_present()` — Present tense, first person

---

## Usage Examples

```python
from src.tas.classifier import TenseClassifier

classifier = TenseClassifier()

result = classifier.classify_sentence("I might try to exercise")
print(result.tense_class)   # TenseClass.HEDGED_FUTURE
print(result.confidence)    # 0.92
print(result.reason)        # "Future-oriented with hedge detected"

result = classifier.classify_sentence("I used to run every day")
print(result.tense_class)   # TenseClass.HISTORICAL_PAST
```

---

## Edge Cases Handled

| Case | Input | Behavior |
|------|-------|----------|
| Narrative present | "So I walk in and..." | T6 (Narrative Present) |
| Fatalistic | "Nothing ever changes" | T11 (Present-Fatalistic) |
| Counterfactual | "Should have left" | T10 (Counterfactual Past) |
| Conditional | "If I could..." | T9 (Conditional) |
| Hedged future | "I might try" | T8 (Hedged Future) |
| Declared future | "I will go" | T7 (Declared Future) |
| Habitual | "I always wake up" | T2 (Habitual Present) |
| Belief | "I believe in honesty" | T3 (Stable Belief Present) |
| Historical past | "I used to run" | T4 (Historical Past) |
| Experiential past | "I went through a lot" | T5 (Experiential Past) |
| Active present | "I'm building a startup" | T1 (Active Present) |
| Future-anxious | "I'm scared of what might happen" | T12 (Future-Anxious) |
| Default | "Let's go" | T1 (Active Present) |

---

## Dependency Graph

```
models.py
    ↓
hedge_scorer.py
    ↓
classifier.py (this file)
    ↓
zimbardo.py
    ↓
migration.py
    ↓
analyzer.py
```

---

## Performance
- spaCy model loaded once per classifier instance
- Typical classification: <10ms per sentence
- No external API calls

---

## Future Improvements
1. **LLM fallback** for low-confidence cases
2. **Multi-sentence context** (detect tense shifts)
3. **Customizable patterns** (domain adaptation)
4. **Explainability output** (return which rule fired)
