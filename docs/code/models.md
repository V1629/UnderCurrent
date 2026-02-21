# models.py — TAS Data Models

## Overview

`models.py` is the **foundation file** for the entire TAS (Tense-as-Signal Analyzer) module. It defines all data structures, enums, and Pydantic models that other TAS files depend on.

**Location**: `src/tas/models.py`

---

## What This File Contains

| Component | Type | Purpose |
|-----------|------|---------|
| `TenseClass` | Enum | 12 psychological tense categories (T1-T12) |
| `TemporalOrientation` | Enum | Past / Present / Future classification |
| `GraphOperation` | Enum | Operations for downstream graph engine |
| `MigrationEvent` | Enum | Behavioral shift event types |
| `ZimbardoProfile` | Dataclass | Temporal personality profile (5 dimensions) |
| `SentenceAnalysis` | Pydantic Model | Per-sentence analysis output |
| `TASOutput` | Pydantic Model | Complete message analysis output |
| `TASInput` | Pydantic Model | API input schema |

---

## Design Decisions

### 1. Why String Enums?

```python
class TenseClass(str, Enum):
    ACTIVE_PRESENT = "T1"
```

**Reason**: String enums serialize cleanly to JSON for API responses. `TenseClass.ACTIVE_PRESENT` becomes `"T1"` in JSON output.

### 2. Why Descriptive Enum Names?

| Before | After |
|--------|-------|
| `T1` | `ACTIVE_PRESENT` |
| `INCREMENT` | `INCREASE_WEIGHT` |
| `FLAG` | `FLAG_FOR_ATTENTION` |

**Reason**: Code should be self-documenting. A developer reading `GraphOperation.FLAG_FOR_ATTENTION` immediately understands intent without checking documentation.

### 3. Why Frozen Dataclass for ZimbardoProfile?

```python
@dataclass(frozen=True)
class ZimbardoProfile:
```

**Reason**: 
- **Immutability** = thread safety in async environments
- **Hashable** = can be used as dictionary keys
- Changes return new instances via `__add__` method

### 4. Why Pydantic for API Models?

```python
class SentenceAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
```

**Reason**:
- Automatic validation (e.g., `hedge_score` must be 0.0-1.0)
- JSON serialization built-in
- OpenAPI schema generation for FastAPI
- Type hints enforced at runtime

---

## The 12 Tense Classes Explained

| Class | Example | Psychological Signal |
|-------|---------|---------------------|
| `ACTIVE_PRESENT` (T1) | "I'm building a startup" | Active investment, high priority |
| `HABITUAL_PRESENT` (T2) | "I always wake up early" | Stable pattern, low decay rate |
| `STABLE_BELIEF_PRESENT` (T3) | "I believe in honesty" | Core value, identity-level |
| `HISTORICAL_PAST` (T4) | "I used to run daily" | Deprioritized, archived |
| `EXPERIENTIAL_PAST` (T5) | "I went through a tough time" | Context only, no weight change |
| `NARRATIVE_PRESENT` (T6) | "So I walk into the room..." | Vivid recall, psychologically past |
| `DECLARED_FUTURE` (T7) | "I will launch next month" | Strong intention |
| `HEDGED_FUTURE` (T8) | "I might try to exercise" | Weak intention, apply hedge discount |
| `CONDITIONAL` (T9) | "I would travel if I could" | Desire without commitment |
| `COUNTERFACTUAL_PAST` (T10) | "I should have left earlier" | Regret, internal conflict |
| `PRESENT_FATALISTIC` (T11) | "Nothing ever changes" | Low agency, mental health flag |
| `FUTURE_ANXIOUS` (T12) | "I'm scared of what might happen" | Anxiety signal |

---

## Mapping Dictionaries

### `TENSE_CLASS_DISPLAY_NAMES`

Converts enum to human-readable string for UI display.

```python
TenseClass.ACTIVE_PRESENT → "Active Present"
```

### `TENSE_TO_TEMPORAL_ORIENTATION`

Maps each tense class to past/present/future.

```python
TenseClass.HISTORICAL_PAST → TemporalOrientation.PAST
TenseClass.DECLARED_FUTURE → TemporalOrientation.FUTURE
```

**Note**: `NARRATIVE_PRESENT` maps to `PAST` because it's psychologically about the past, even though grammatically present.

### `TENSE_TO_DEFAULT_GRAPH_OPERATION`

Default routing for each tense class.

| Tense | Operation | Reason |
|-------|-----------|--------|
| T1 (Active) | INCREASE_WEIGHT | User actively engaged |
| T4 (Historical) | DECREASE_WEIGHT | Topic deprioritized |
| T10 (Counterfactual) | TRIGGER_EVENT | Regret = conflict signal |
| T11 (Fatalistic) | FLAG_FOR_ATTENTION | Mental health concern |

---

## ZimbardoProfile

Based on Philip Zimbardo's Time Perspective Theory.

### Five Dimensions

```python
past_negative: float    # Regret, trauma, rumination
past_positive: float    # Nostalgia, warm memories  
present_hedonistic: float  # Pleasure-seeking, impulsive
present_fatalistic: float  # Helpless, no agency
future_oriented: float     # Goal-driven, planning
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `__add__` | Combine two profiles (capped at 1.0) |
| `to_dict()` | JSON serialization |
| `dominant_orientation` | Return highest-scoring dimension |
| `normalize()` | Scale so all values sum to 1.0 |

---

## Pydantic Models

### SentenceAnalysis

Output for a **single sentence**. Contains:

- `text`: Original sentence
- `root_verb`: Extracted verb lemma
- `tense_class`: Classified tense (T1-T12)
- `hedge_score`: 1.0 = certain, 0.0 = uncertain
- `hedge_words`: List of detected hedge phrases
- `confidence`: Classification confidence
- `graph_operation`: What to tell graph engine
- `zimbardo_contribution`: Contribution to profile

### TASOutput

Output for a **complete message**. Contains:

- `original_text`: Full input message
- `sentences`: List of SentenceAnalysis
- `sentence_level_events`: Migration/contrast events
- `session_zimbardo_delta`: Total Zimbardo changes
- `processing_time_ms`: Performance metric

### TASInput

Input schema for API requests:

```python
{
    "message": "I'm building a startup but I used to hate coding",
    "user_id": "user_123",
    "session_id": "session_456",
    "tense_history": {"startup": ["T1", "T1", "T7"]}
}
```

---

## Dependency Graph

```
models.py (this file)
    ↓
hedge_scorer.py (uses HedgeAnalysisResult pattern)
    ↓
classifier.py (uses TenseClass, mappings)
    ↓
zimbardo.py (uses ZimbardoProfile)
    ↓
migration.py (uses MigrationEvent)
    ↓
analyzer.py (uses all models)
    ↓
api.py (uses TASInput, TASOutput)
```

---

## Usage Example

```python
from src.tas.models import (
    TenseClass,
    TENSE_CLASS_DISPLAY_NAMES,
    TENSE_TO_DEFAULT_GRAPH_OPERATION,
    ZimbardoProfile,
    SentenceAnalysis,
)

# Get display name
name = TENSE_CLASS_DISPLAY_NAMES[TenseClass.ACTIVE_PRESENT]
# → "Active Present"

# Get graph operation
op = TENSE_TO_DEFAULT_GRAPH_OPERATION[TenseClass.COUNTERFACTUAL_PAST]
# → GraphOperation.TRIGGER_EVENT

# Create Zimbardo profile
profile = ZimbardoProfile(future_oriented=0.6, past_negative=0.2)
print(profile.dominant_orientation)
# → "future_oriented"
```
