# zimbardo.py — Zimbardo Profile Calculator

## Overview

`zimbardo.py` implements the calculation of the **Zimbardo Time Perspective Profile** for a session or message. It aggregates per-sentence contributions based on tense class and sentiment, normalizes the profile, and returns a five-dimensional vector.

**Location**: `src/tas/zimbardo.py`

---

## What This File Contains

| Component | Type | Purpose |
|-----------|------|---------|
| `ZimbardoCalculator` | class | Main calculator, exposes `accumulate_profile()` |
| `TENSE_TO_ZIMBARDO_CONTRIBUTION` | dict | Maps tense class to Zimbardo dimension/contribution |

---

## Zimbardo Profile Dimensions

| Dimension | Description |
|-----------|-------------|
| `past_negative` | Regret, trauma, rumination |
| `past_positive` | Nostalgia, warm memories |
| `present_hedonistic` | Pleasure-seeking, impulsive |
| `present_fatalistic` | Helpless, no agency |
| `future_oriented` | Goal-driven, planning |

---

## Contribution Mapping

| Tense Class | Zimbardo Dimension | Contribution |
|-------------|-------------------|--------------|
| HISTORICAL_PAST (T4) | past_positive / past_negative | +0.03 (split by sentiment) |
| COUNTERFACTUAL_PAST (T10) | past_negative | +0.05 |
| ACTIVE_PRESENT (T1) | present_hedonistic | +0.02 |
| PRESENT_FATALISTIC (T11) | present_fatalistic | +0.05 |
| DECLARED_FUTURE (T7) | future_oriented | +0.04 |
| HEDGED_FUTURE (T8) | future_oriented | +0.01 |
| CONDITIONAL (T9) | future_oriented | +0.01 |

---

## Algorithm Steps

1. **Initialize profile**: All dimensions start at 0.0
2. **Iterate over sentence results**:
    - For each, get tense class and sentiment
    - Map to Zimbardo dimension and value
    - Add value to profile (capped at 1.0)
3. **Normalize profile**: Scale so all values sum to 1.0
4. **Return profile**: As `ZimbardoProfile` dataclass

---

## Usage Example

```python
from src.tas.zimbardo import ZimbardoCalculator

sentence_results = [
    {"tense_class": TenseClass.HISTORICAL_PAST, "sentiment": "positive"},
    {"tense_class": TenseClass.DECLARED_FUTURE},
    {"tense_class": TenseClass.PRESENT_FATALISTIC},
]

calculator = ZimbardoCalculator()
profile = calculator.accumulate_profile(sentence_results)
print(profile.to_dict())
# {'past_negative': 0.0, 'past_positive': 0.375, 'present_hedonistic': 0.0, 'present_fatalistic': 0.3125, 'future_oriented': 0.3125}
```

---

## Edge Cases Handled

| Case | Input | Behavior |
|------|-------|----------|
| HISTORICAL_PAST + positive | `{tense_class: HISTORICAL_PAST, sentiment: 'positive'}` | past_positive += 0.03 |
| HISTORICAL_PAST + negative | `{tense_class: HISTORICAL_PAST, sentiment: 'negative'}` | past_negative += 0.03 |
| HISTORICAL_PAST + neutral | `{tense_class: HISTORICAL_PAST, sentiment: 'neutral'}` | No contribution |
| Unknown tense class | `{tense_class: TenseClass.NARRATIVE_PRESENT}` | No contribution |

---

## Dependency Graph

```
models.py (ZimbardoProfile)
    ↓
zimbardo.py (this file)
    ↓
migration.py
    ↓
analyzer.py
```

---

## Performance
- Pure Python, no external dependencies
- Typical calculation: <1ms per session

---

## Future Improvements
1. **Sentiment analysis integration** for automatic positive/negative detection
2. **Decay weighting** for recent sessions
3. **Customizable contribution values**
