# migration.py — TAS Migration Detector

## Overview

`migration.py` implements detection of **behavioral migration events** based on tense history shifts across sessions for each topic node. It tracks tense history and signals when a user's psychological relationship to a topic changes.

**Location**: `src/tas/migration.py`

---

## What This File Contains

| Component | Type | Purpose |
|-----------|------|---------|
| `MigrationDetector` | class | Main detector, exposes `detect_migration()` |

---

## Migration Events

| Event | Trigger | Signal |
|-------|---------|--------|
| DEPRIORITIZATION | T1/T2 → T4 | Topic becoming historical |
| REACTIVATION | T4 → T1 | Dormant topic reactivating |
| COMMITMENT_DECAY | T7 → T8/T9 | Commitment weakening |
| COMMITMENT_INCREASE | T8/T9 → T7 | Commitment strengthening |
| BELIEF_QUESTIONING | T3 → T10 | Belief being questioned |

---

## Algorithm Steps

1. **Check tense history length**: Must have at least 2 entries
2. **Compare last two tenses**: prev, curr
3. **Match migration patterns**:
    - Active → Historical: DEPRIORITIZATION
    - Historical → Active: REACTIVATION
    - Declared → Hedged/Conditional: COMMITMENT_DECAY
    - Hedged/Conditional → Declared: COMMITMENT_INCREASE
    - Belief → Counterfactual: BELIEF_QUESTIONING
4. **Return migration event**: As `MigrationEvent` enum

---

## Usage Example

```python
from src.tas.migration import MigrationDetector

detector = MigrationDetector()
event = detector.detect_migration("startup", ["T1", "T1", "T4"])
print(event)  # MigrationEvent.DEPRIORITIZATION
```

---

## Edge Cases Handled

| Case | Input | Behavior |
|------|-------|----------|
| Too short history | `["T1"]` | Returns None |
| No migration | `["T1", "T1"]` | Returns None |
| Multiple migrations | `["T1", "T4", "T1"]` | Detects REACTIVATION |

---

## Dependency Graph

```
models.py (MigrationEvent, TenseClass)
    ↓
migration.py (this file)
    ↓
analyzer.py
```

---

## Performance
- Pure Python, no external dependencies
- Typical detection: <1ms per topic

---

## Future Improvements
1. **Multi-session analysis** for long-term migration
2. **Customizable migration patterns**
3. **Integration with graph engine for node updates**
