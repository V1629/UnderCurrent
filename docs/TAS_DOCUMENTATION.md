# Tense-as-Signal Analyzer (TAS) — Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Theoretical Foundations](#theoretical-foundations)
3. [Architecture](#architecture)
4. [Tense Classification System](#tense-classification-system)
5. [Hedge Scoring](#hedge-scoring)
6. [Zimbardo Profile System](#zimbardo-profile-system)
7. [Tense Migration Detection](#tense-migration-detection)
8. [Edge Cases](#edge-cases)
9. [Output Schema](#output-schema)
10. [Integration API](#integration-api)
11. [Success Criteria](#success-criteria)

---

## Overview

### What is TAS?
**Tense-as-Signal Analyzer (TAS)** is a preprocessing submodule within the **Undercurrent** behavioral intelligence system. It analyzes grammatical tense in user messages to extract psychological signals about:

- **Psychological distance** from topics
- **Behavioral patterns** and habits
- **Commitment levels** to intentions
- **Temporal personality traits** (Zimbardo profile)

### Core Insight
> **Grammatical tense is not just a linguistic feature — it is a psychological distance signal.**

The same content in different tenses carries opposite behavioral implications:
- "I'm building a startup" → Active investment, high priority
- "I used to want to build a startup" → Historical, deprioritized

### Position in System
```
User Message
     ↓
┌─────────────────┐
│   TAS Module    │  ← First processing layer
│  (This Module)  │
└────────┬────────┘
         ↓
   Enriched Signal
         ↓
┌─────────────────┐
│  Graph Engine   │
│  Emotion Layer  │
│  Topic Extract  │
│  Inference Eng  │
└─────────────────┘
```

---

## Theoretical Foundations

### 1. Construal Level Theory (Trope & Liberman)

| Psychological Distance | Construal Level | Tense Signal |
|------------------------|-----------------|--------------|
| **Near** | Concrete, detailed, specific | Present tense |
| **Far** | Abstract, general, categorical | Past tense |

**Implication**: Present tense = active investment; Past tense = historical framing

### 2. Tense Predicts Behavioral Drivers

Research finding (2013 peer-reviewed study):

| Recall Tense | Behavioral Driver | Prediction |
|--------------|-------------------|------------|
| Present tense | **Behavior-driven** | Habits predict future actions |
| Past tense | **Attitude-driven** | Values/opinions guide decisions |

**Example**:
- "So I'm in this meeting and I shut down" → Habit signal (will repeat)
- "I used to shut down in meetings" → Attitude signal (may have changed)

### 3. Zimbardo's Time Perspective Theory

Five temporal orientations as stable personality traits:

| Orientation | Description | Linguistic Markers |
|-------------|-------------|--------------------|
| **Past-Negative** | Regret, trauma, rumination | "should have", "if only", negative past |
| **Past-Positive** | Nostalgia, warmth | "back when", "those were", positive past |
| **Present-Hedonistic** | Pleasure-seeking, impulsive | "right now", "these days", sensory |
| **Present-Fatalistic** | Helpless, no agency | "nothing changes", passive voice |
| **Future-Oriented** | Goal-driven, planning | "I will", "planning to", "next" |

### 4. Critical Distinction: Grammatical vs. Psychological Tense

**They are NOT the same!**

| Sentence | Grammatical Tense | Psychological Orientation |
|----------|-------------------|---------------------------|
| "So I walk into the room..." | Present | **Past** (narrative present) |
| "I always shut down in conflict" | Present | **Habitual** (pattern) |
| "I believe hard work matters" | Present | **Stable belief** (values) |

**Rule**: Always resolve to psychological orientation, not surface grammar.

---

## Architecture

### 10-Step Processing Pipeline

```
[1] Sentence Segmentation
     │
[2] Root Verb Extraction (spaCy dependency parse)
     │
[3] Grammatical Tense Classification
     │
[4] Narrative vs Factual Frame Detection
     │
[5] Psychological Temporal Orientation Resolution
     │
[6] Hedge Intensity Scoring
     │
[7] Tense Tag Assignment + Weight Modifier
     │
[8] Graph Operation Routing
     │
[9] Tense History Update (per node)
     │
[10] Zimbardo Score Accumulation
     │
     ↓
Enriched Signal → Downstream Modules
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Core implementation |
| NLP | spaCy (en_core_web_sm/md) | Parsing, morphology |
| Framework | FastAPI | API deployment |
| Validation | Pydantic | Schema validation |

### Performance Target
- **<50ms per message** for rule-based classification
- LLM fallback only when confidence < 0.6

---

## Tense Classification System

### 12 Tense Classes

| ID | Name | Example | Graph Operation |
|----|------|---------|-----------------|
| **T1** | Active Present | "I'm building a startup" | INCREMENT (strong) |
| **T2** | Habitual Present | "I always shut down in conflict" | INCREMENT habit (low decay) |
| **T3** | Stable Belief Present | "I believe hard work matters" | INCREMENT values (high stability) |
| **T4** | Historical Past | "I used to run every day" | DECREMENT / ARCHIVE |
| **T5** | Experiential Past | "I went through a hard period" | ADD to history (low weight) |
| **T6** | Narrative Present | "So I'm in this meeting and freeze" | INCREMENT behavior (vivid) |
| **T7** | Declared Future | "I will launch in March" | INCREMENT intention (high) |
| **T8** | Hedged Future | "I might try to get fit" | INCREMENT × hedge discount |
| **T9** | Conditional | "I would love to travel if I could" | INCREMENT desire (low) |
| **T10** | Counterfactual Past | "I should have left that job" | TRIGGER conflict/regret |
| **T11** | Present-Fatalistic | "Nothing ever changes for me" | FLAG Zimbardo score |
| **T12** | Future-Anxious | "I'm scared of what might happen" | INCREMENT anxiety |

### Classification Logic

```python
def classify_tense(sentence, root_verb, morphology):
    """
    Classification priority:
    1. Check for narrative markers → T6
    2. Check for fatalistic patterns → T11
    3. Check for counterfactual → T10
    4. Check for conditional mood → T9
    5. Check for future + hedge → T8
    6. Check for declared future → T7
    7. Check for habitual markers → T2
    8. Check for belief markers → T3
    9. Check for past tense → T4/T5
    10. Default to active present → T1
    """
```

---

## Hedge Scoring

### Hedge Score Scale
- **1.0** = Maximum certainty (no hedging)
- **0.0** = Maximum uncertainty (heavily hedged)

### Hedge Word Categories

| Category | Multiplier | Examples |
|----------|------------|----------|
| **Strong Hedge** | ×0.15–0.25 | maybe, someday, possibly, I guess, kind of, sort of |
| **Medium Hedge** | ×0.40–0.60 | probably, might, could, I think, sometimes, tends to |
| **Light Hedge** | ×0.70–0.85 | usually, generally, mostly, I believe, I hope |
| **No Hedge** | ×1.0 | I am, I will, definitely, absolutely, I know |

### Hedge Stacking (Multiplicative)

```
"I kind of think I might possibly start a business"
     ↓
0.25 × 0.45 × 0.25 = 0.028 (~3% effective weight)
```

### Implementation

```python
HEDGE_WEIGHTS = {
    "strong": ["maybe", "someday", "possibly", "i guess", "kind of", "sort of"],
    "medium": ["probably", "might", "could", "i think", "sometimes"],
    "light": ["usually", "generally", "mostly", "i believe", "i hope"]
}

def calculate_hedge_score(text: str) -> float:
    score = 1.0
    text_lower = text.lower()
    
    for word in HEDGE_WEIGHTS["strong"]:
        if word in text_lower:
            score *= 0.20
    for word in HEDGE_WEIGHTS["medium"]:
        if word in text_lower:
            score *= 0.50
    for word in HEDGE_WEIGHTS["light"]:
        if word in text_lower:
            score *= 0.77
    
    return max(score, 0.01)  # Floor at 1%
```

---

## Zimbardo Profile System

### Profile Vector

```python
@dataclass
class ZimbardoProfile:
    past_negative: float = 0.0      # Range: 0.0–1.0
    past_positive: float = 0.0      # Range: 0.0–1.0
    present_hedonistic: float = 0.0 # Range: 0.0–1.0
    present_fatalistic: float = 0.0 # Range: 0.0–1.0
    future_oriented: float = 0.0    # Range: 0.0–1.0
```

### Accumulation Rules

1. Each classified sentence contributes fractionally
2. Recent sessions weighted more (exponential decay)
3. Contributions are small (~0.01–0.05 per sentence)
4. Profile normalizes over time

### Tense → Zimbardo Mapping

| Tense Class | Zimbardo Contribution |
|-------------|----------------------|
| T4 (Historical Past) + positive | past_positive += 0.03 |
| T4 (Historical Past) + negative | past_negative += 0.03 |
| T10 (Counterfactual) | past_negative += 0.05 |
| T1 (Active Present) | present_hedonistic += 0.02 |
| T11 (Present-Fatalistic) | present_fatalistic += 0.05 |
| T7 (Declared Future) | future_oriented += 0.04 |
| T8/T9 (Hedged/Conditional) | future_oriented += 0.01 |

### Behavioral Predictions by Dominant Profile

| Profile | Behavior Pattern | Recommended Intervention |
|---------|------------------|--------------------------|
| **Past-Negative** | Rumination, avoidance | Reframe past, build future intentions |
| **Past-Positive** | Nostalgia bias, change-resistant | Anchor new goals to past identity |
| **Present-Hedonistic** | Impulsive, poor deferred gratification | Frame goals as immediate rewards |
| **Present-Fatalistic** | Low agency, passive | Encourage small action signals |
| **Future-Oriented** | Goal-driven, planning | Support intentions, track decay |

---

## Tense Migration Detection

### What is Tense Migration?
When a topic's dominant tense **shifts across sessions**, signaling a behavioral change.

### Migration Events

| Migration | Signal | System Action |
|-----------|--------|---------------|
| T1/T2 → T4 | Topic becoming historical | DEPRIORITIZE node |
| T4 → T1 | Dormant topic reactivating | REACTIVATE node |
| T7 → T8/T9 | Commitment weakening | DECAY intention weight |
| T8 → T7 | Commitment strengthening | AMPLIFY intention weight |
| T3 → T10 | Belief being questioned | FLAG cognitive dissonance |

### Detection Rules

```python
def detect_migration(node_id: str, tense_history: List[str]) -> Optional[str]:
    """
    Fire migration event when:
    1. Dominant tense shifts between sessions
    2. Active node (T1/T2) receives 3+ consecutive T4/T5
    3. Declared (T7) shifts to hedged (T8/T9)
    4. Hedged (T8) shifts to declared (T7)
    """
    if len(tense_history) < 2:
        return None
    
    prev = tense_history[-2]
    curr = tense_history[-1]
    
    if prev in ["T1", "T2"] and curr == "T4":
        return "DEPRIORITIZATION"
    if prev == "T4" and curr == "T1":
        return "REACTIVATION"
    if prev == "T7" and curr in ["T8", "T9"]:
        return "COMMITMENT_DECAY"
    if prev in ["T8", "T9"] and curr == "T7":
        return "COMMITMENT_INCREASE"
    
    return None
```

---

## Edge Cases

### 1. Narrative Present (False Present)

**Problem**: Present tense used for past events  
**Example**: "So I'm walking into the interview and my hands are shaking"  
**Detection**: Storytelling markers ("so", "and then"), sequential events  
**Classification**: T6 (Narrative Present), NOT T1 (Active Present)  
**Tag**: `[HISTORICAL_VIVID]`

### 2. Generic Present (Non-Self-Referential)

**Problem**: Statements about the world, not the user  
**Example**: "Anxiety affects a lot of people"  
**Detection**: No first-person subject  
**Action**: Do NOT trigger graph update

### 3. Quoted Speech

**Problem**: Past tense describing others' words  
**Example**: "She told me I should quit"  
**Detection**: Reporting verbs ("told", "said", "asked")  
**Tag**: `[OTHER_SPEECH]`  
**Weight**: Significantly reduced

### 4. Rhetorical Future

**Problem**: Future tense expressing fatalism, not intention  
**Example**: "Who knows what'll happen"  
**Detection**: Question form + uncertainty  
**Classification**: T12 (Future-Anxious), NOT T7 (Declared Future)

### 5. Mixed-Tense Sentences

**Problem**: Multiple tenses in one sentence  
**Example**: "I used to run but lately I've been getting back into it"  
**Action**: Split and route each clause independently  
**Event**: Fire TENSE_MIGRATION if contrast marker detected ("but", "however")

---

## Output Schema

### Per-Sentence Output

```json
{
  "text": "I used to run every day",
  "root_verb": "run",
  "grammatical_tense": "simple_past",
  "tense_class": "T4",
  "tense_class_name": "Historical Past",
  "temporal_orientation": "past",
  "self_referential": true,
  "hedge_score": 0.9,
  "hedge_words": [],
  "confidence": 0.85,
  "zimbardo_contribution": {
    "past_positive": 0.04
  },
  "graph_operation": "DECREMENT",
  "target_node_hint": "fitness/health",
  "weight_modifier": 0.9,
  "flags": ["behavioral_shift_candidate"]
}
```

### Full Message Output

```json
{
  "original_text": "I used to run every day but lately I've been getting back into it",
  "sentences": [
    { /* sentence 1 analysis */ },
    { /* sentence 2 analysis */ }
  ],
  "sentence_level_events": [
    "TENSE_MIGRATION: T4→T1 on topic:fitness"
  ],
  "contrast_markers_detected": ["but", "lately"],
  "session_zimbardo_delta": {
    "past_positive": 0.04,
    "present_hedonistic": 0.04
  },
  "processing_time_ms": 23
}
```

---

## Integration API

### Main Interface

```python
async def analyze_tense(
    message: str,
    user_id: str,
    session_id: str,
    tense_history: dict[str, list[str]]  # node_id → past classifications
) -> TASOutput:
    """
    Primary entry point for TAS module.
    
    Args:
        message: Raw user message text
        user_id: Unique user identifier
        session_id: Current session identifier
        tense_history: Historical tense data per topic node
    
    Returns:
        TASOutput with per-sentence annotations, migration events,
        zimbardo deltas, and graph routing instructions
    """
```

### Data Models

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class TenseClass(str, Enum):
    T1 = "Active Present"
    T2 = "Habitual Present"
    T3 = "Stable Belief Present"
    T4 = "Historical Past"
    T5 = "Experiential Past"
    T6 = "Narrative Present"
    T7 = "Declared Future"
    T8 = "Hedged Future"
    T9 = "Conditional"
    T10 = "Counterfactual Past"
    T11 = "Present-Fatalistic"
    T12 = "Future-Anxious"

class GraphOperation(str, Enum):
    INCREMENT = "INCREMENT"
    DECREMENT = "DECREMENT"
    ARCHIVE = "ARCHIVE"
    FLAG = "FLAG"
    TRIGGER = "TRIGGER"

class SentenceAnalysis(BaseModel):
    text: str
    root_verb: str
    grammatical_tense: str
    tense_class: str
    tense_class_name: str
    temporal_orientation: str
    self_referential: bool
    hedge_score: float
    hedge_words: list[str]
    confidence: float
    zimbardo_contribution: dict[str, float]
    graph_operation: GraphOperation
    target_node_hint: Optional[str]
    weight_modifier: float
    flags: list[str]

class TASOutput(BaseModel):
    original_text: str
    sentences: list[SentenceAnalysis]
    sentence_level_events: list[str]
    contrast_markers_detected: list[str]
    session_zimbardo_delta: dict[str, float]
    processing_time_ms: float
```

---

## Success Criteria

TAS is working correctly when:

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1 | "I'm learning Python" vs "I used to learn Python" | Opposite graph operations (INCREMENT vs DECREMENT) |
| 2 | "I will definitely launch next month" | hedge_score ≥ 0.95, class = T7 |
| 3 | "I might kind of think about maybe starting something" | hedge_score ≤ 0.05 |
| 4 | "So I'm in this meeting and I freeze" | T6 (Narrative Present), NOT T1 |
| 5 | Fitness: T1 → T1 → T2 → T4 → T4 (5 sessions) | TENSE_MIGRATION fires after session 4 |
| 6 | "Nothing ever works out for me" | present_fatalistic += (increment) |
| 7 | "Life is hard sometimes" (no first-person) | NO graph update triggered |

---

## What TAS Does NOT Do

To maintain single responsibility:

| NOT Responsible For | Handled By |
|---------------------|------------|
| Graph building/updates | Graph Engine |
| Emotion classification | Emotion Detection Layer |
| Topic/entity extraction | Topic Extractor |
| Behavioral predictions | Inference Engine |

**TAS is purely**: Text → Tense Analysis → Structured Signal + Routing Instructions

---

## Common Implementation Mistakes

### Mistake 1: Conflating Grammatical and Psychological Tense
❌ "So I walk into the room" → Active Present  
✅ "So I walk into the room" → Narrative Present (T6)

### Mistake 2: Treating All Present Tense Equally
❌ "I believe in hard work" = "I'm applying to jobs"  
✅ T3 (Stable Belief) ≠ T1 (Active Present) — different decay rates

### Mistake 3: Ignoring Hedge Stacking
❌ Count hedges once  
✅ Multiply hedges: "kind of might maybe" = 0.20 × 0.50 × 0.20 = 0.02

### The Golden Rule
> **What is the psychological distance between the speaker and this content?**
> - Close = active, high weight, low decay
> - Distant = historical, low weight, archive

---

## File Structure

```
Psynapse/
├── docs/
│   └── TAS_DOCUMENTATION.md  (this file)
├── src/
│   └── tas/
│       ├── __init__.py
│       ├── analyzer.py       # Main TAS class
│       ├── classifier.py     # Tense classification logic
│       ├── hedge_scorer.py   # Hedge scoring
│       ├── zimbardo.py       # Profile accumulation
│       ├── migration.py      # Migration detection
│       └── models.py         # Pydantic schemas
├── tests/
│   └── test_tas.py
├── requirements.txt
└── tense_submodule_prompt.md
```

---

*Last Updated: February 2026*  
*Version: 1.0.0*
