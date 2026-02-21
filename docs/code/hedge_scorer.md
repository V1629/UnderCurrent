# hedge_scorer.py — Context-Aware Hedge Detection

## Overview

`hedge_scorer.py` implements **context-aware hedge detection** using spaCy dependency parsing. Unlike naive keyword matching, it understands when a word is actually functioning as a hedge versus when it's the main assertion.

**Location**: `src/tas/hedge_scorer.py`

---

## The Problem With Naive Keyword Matching

Consider these two sentences:

| Sentence | Naive Approach | Reality |
|----------|----------------|---------|
| "I think pizza is good" | ❌ "think" detected → hedge | Main assertion, NOT a hedge |
| "I think I might go" | ✅ "think" detected → hedge | Weakens "might go", IS a hedge |

**The difference**: In the first, "think" IS the opinion. In the second, "think" weakens a separate claim.

This module solves this by checking the **syntactic role** of potential hedge words.

---

## What This File Contains

| Component | Type | Purpose |
|-----------|------|---------|
| `STRONG_HEDGE_PATTERNS` | dict | Severe uncertainty markers (×0.15-0.25) |
| `MEDIUM_HEDGE_PATTERNS` | dict | Moderate uncertainty markers (×0.40-0.60) |
| `LIGHT_HEDGE_PATTERNS` | dict | Minor uncertainty markers (×0.70-0.85) |
| `CERTAINTY_BOOSTERS` | set | Words that restore certainty |
| `HedgeAnalysisResult` | dataclass | Complete analysis output |
| `HedgeScorer` | class | Main analyzer with spaCy |
| `calculate_hedge_score()` | function | Convenience wrapper |

---

## Hedge Score Scale

```
1.0 ─────────────────────────────────── Maximum certainty
│   "I will do it" (no hedges)
│
0.7 ─────────────────────────────────── Light hedging
│   "I usually do it" (usually = ×0.80)
│
0.5 ─────────────────────────────────── Moderate hedging
│   "I might do it" (might = ×0.50)
│
0.3 ─────────────────────────────────── Heavy hedging threshold
│   "I think I might do it" (×0.50 × ×0.50)
│
0.01 ────────────────────────────────── Floor (minimum)
    "I kind of think I might possibly do it"
```

---

## Hedge Categories

### Strong Hedges (×0.15-0.25)

Significant uncertainty. User is barely committed.

| Pattern | Multiplier | Example |
|---------|------------|---------|
| `maybe` | ×0.20 | "Maybe I'll apply" |
| `perhaps` | ×0.20 | "Perhaps I should go" |
| `possibly` | ×0.20 | "I could possibly try" |
| `someday` | ×0.15 | "Someday I'll learn" |
| `kind of` | ×0.25 | "I kind of want to" |
| `sort of` | ×0.25 | "I sort of think so" |
| `i guess` | ×0.20 | "I guess I could" |
| `i suppose` | ×0.25 | "I suppose that's true" |
| `not sure` | ×0.20 | "I'm not sure if I will" |
| `who knows` | ×0.15 | "Who knows if it'll work" |

### Medium Hedges (×0.40-0.60)

Moderate uncertainty. User has some intent but with caveats.

| Pattern | Multiplier | Example |
|---------|------------|---------|
| `might` | ×0.50 | "I might try it" |
| `could` | ×0.55 | "I could do that" |
| `may` | ×0.55 | "I may attend" |
| `probably` | ×0.60 | "I'll probably go" |
| `likely` | ×0.60 | "I'll likely finish" |
| `i think` | ×0.50 | "I think I should go" |
| `sometimes` | ×0.55 | "Sometimes I feel" |
| `tends to` | ×0.50 | "It tends to work" |
| `seems like` | ×0.45 | "It seems like a good idea" |
| `appears to` | ×0.50 | "It appears to be working" |

### Light Hedges (×0.70-0.85)

Minor uncertainty. User is mostly committed.

| Pattern | Multiplier | Example |
|---------|------------|---------|
| `usually` | ×0.80 | "I usually do that" |
| `generally` | ×0.80 | "Generally, I agree" |
| `mostly` | ×0.80 | "I mostly finished" |
| `often` | ×0.85 | "I often think about it" |
| `i believe` | ×0.75 | "I believe it will work" |
| `i hope` | ×0.70 | "I hope to finish" |
| `i feel like` | ×0.75 | "I feel like I should" |
| `should` | ×0.80 | "I should do it" |

### Certainty Boosters

These **restore** certainty when present alongside hedges.

```python
CERTAINTY_BOOSTERS = {
    "definitely", "absolutely", "certainly",
    "for sure", "without doubt", "i know",
    "i am certain", "will definitely", "must"
}
```

**Effect**: Boosters restore ~50% of lost certainty.

```
"I might go" → 0.50
"I might definitely go" → 0.50 + (0.50 × 0.50) = 0.75
```

---

## Multiplicative Stacking

Hedges stack multiplicatively, not additively.

### Example Calculation

```
"I kind of think I might possibly start a business"

Hedges detected:
- "kind of" → ×0.25
- "I think" → ×0.50  (verified as epistemic hedge)
- "might"  → ×0.50
- "possibly" → ×0.20

Final score: 1.0 × 0.25 × 0.50 × 0.50 × 0.20 = 0.0125 (~1.25%)
```

**Interpretation**: Only 1.25% effective commitment to "starting a business."

---

## Context-Aware Detection Logic

### The "I think" Problem

```python
def _is_epistemic_i_think(self, doc: Doc) -> bool:
```

| Sentence | Is Hedge? | Why |
|----------|-----------|-----|
| "I think pizza is good" | ❌ No | "think" is the main verb, expressing opinion |
| "I think about life" | ❌ No | "think about" = contemplation, not hedging |
| "I think I should go" | ✅ Yes | Embedded clause detected, "think" weakens it |
| "I think that's right" | ✅ Yes | Complementizer "that" signals embedded assertion |

**Detection method**: 
1. Find "think" token via spaCy
2. Check for embedded clause (ccomp, xcomp dependencies)
3. Check for preposition "about/of" (NOT a hedge)
4. Check if another verb follows "think"

### The "I believe" Problem

```python
def _is_epistemic_i_believe(self, doc: Doc) -> bool:
```

| Sentence | Is Hedge? | Why |
|----------|-----------|-----|
| "I believe in honesty" | ❌ No | Core belief statement (T3 - Stable Belief) |
| "I believe it might work" | ✅ Yes | Weakens the "might work" claim |

**Detection method**:
1. Find "believe" token
2. If followed by "in" → belief statement, NOT hedge
3. If followed by embedded clause → IS hedge

### Modal Verb Detection

```python
def _detect_uncertain_modal(self, doc: Doc) -> bool:
```

Uses spaCy dependency parsing to find:
- Token with `dep_ == "aux"` (auxiliary)
- Lemma in `{"might", "could", "may"}`
- Attached to a `VERB` (not question inversion)

---

## HedgeAnalysisResult

```python
@dataclass
class HedgeAnalysisResult:
    hedge_score: float = 1.0              # 1.0 = certain, 0.0 = uncertain
    detected_hedge_words: list[str]       # ["might", "kind of"]
    detected_boosters: list[str]          # ["definitely"]
    has_uncertain_modal: bool             # True if might/could/may found
    is_heavily_hedged: bool               # True if score < 0.30
    raw_multiplier_chain: list[float]     # [0.50, 0.25] for debugging
```

### Why Track Multiplier Chain?

For debugging and explainability:

```python
result = scorer.analyze("I might kind of try")
print(result.raw_multiplier_chain)
# [0.50, 0.25]  ← shows exactly which hedges contributed
```

---

## Algorithm Steps

```
analyze(sentence) → HedgeAnalysisResult
│
├── Step 1: Check for certainty boosters
│   └── If found, set booster_found = True
│
├── Step 2: spaCy parse for uncertain modals
│   └── If modal found AND no booster: multiplier_chain.append(0.50)
│
├── Step 3: Check multi-word patterns
│   ├── Strong patterns (×0.15-0.25)
│   ├── Medium patterns (×0.40-0.60)  [skip modals, already handled]
│   └── Light patterns (×0.70-0.85)
│   
│   For each pattern:
│   └── _is_pattern_present_as_hedge() → syntactic validation
│
├── Step 4: Calculate final score
│   └── final_score = Π(multipliers)  # Product of all
│
├── Step 5: Apply booster restoration
│   └── If booster: final_score += (1 - final_score) × 0.50
│
└── Step 6: Apply floor
    └── final_score = max(0.01, final_score)
```

---

## Usage Examples

### Basic Usage

```python
from src.tas.hedge_scorer import calculate_hedge_score

result = calculate_hedge_score("I might try to exercise tomorrow")
print(result.hedge_score)        # 0.50
print(result.detected_hedge_words)  # ["might"]
print(result.is_heavily_hedged)  # False
```

### With Class Instance

```python
from src.tas.hedge_scorer import HedgeScorer

scorer = HedgeScorer(spacy_model_name="en_core_web_sm")

# Heavily hedged
result = scorer.analyze("I kind of think I might possibly do it")
print(result.hedge_score)  # 0.0125
print(result.is_heavily_hedged)  # True

# Context-aware: "I think" NOT a hedge here
result = scorer.analyze("I think pizza is great")
print(result.hedge_score)  # 1.0
print(result.detected_hedge_words)  # []
```

### With Certainty Booster

```python
result = scorer.analyze("I might definitely go")
print(result.hedge_score)  # 0.75 (booster restored certainty)
print(result.detected_boosters)  # ["definitely"]
```

---

## Edge Cases Handled

| Case | Input | Behavior |
|------|-------|----------|
| Empty string | `""` | Returns score 1.0 |
| No hedges | `"I will do it"` | Returns score 1.0 |
| "Think about" | `"I think about life"` | NOT detected as hedge |
| "Believe in" | `"I believe in justice"` | NOT detected as hedge |
| Question modal | `"Could you help?"` | Different handling (not uncertainty) |
| Booster + hedge | `"I definitely might"` | Partial restoration |
| Stacked hedges | `"maybe possibly"` | Multiplicative: 0.04 |

---

## Performance Considerations

- spaCy model loaded once (singleton pattern via `get_default_scorer()`)
- First call: ~200ms (model load)
- Subsequent calls: <5ms per sentence
- Memory: ~50MB for en_core_web_sm

---

## Dependency Graph

```
models.py (patterns for HedgeAnalysisResult)
    ↓
hedge_scorer.py (this file)
    ↓
classifier.py (uses hedge_score for T8 classification)
    ↓
analyzer.py (calls HedgeScorer per sentence)
```

---

## Future Improvements

1. **Configurable thresholds**: Allow tuning multipliers per domain
2. **Negation handling**: "I don't think" vs "I think not"
3. **Sarcasm detection**: "Oh, I'll *definitely* do that" (sarcastic)
4. **Multi-language**: Extend to other languages
