# TAS Code Documentation

This folder contains detailed documentation for each code file in the TAS module.

## Documentation Index

| File | Documentation | Status |
|------|---------------|--------|
| `src/tas/models.py` | [models.md](./models.md) | ✅ Complete |
| `src/tas/hedge_scorer.py` | [hedge_scorer.md](./hedge_scorer.md) | ✅ Complete |
| `src/tas/classifier.py` | [classifier.md](./classifier.md) | 🔜 Pending |
| `src/tas/zimbardo.py` | [zimbardo.md](./zimbardo.md) | 🔜 Pending |
| `src/tas/migration.py` | [migration.md](./migration.md) | 🔜 Pending |
| `src/tas/analyzer.py` | [analyzer.md](./analyzer.md) | 🔜 Pending |
| `src/tas/api.py` | [api.md](./api.md) | 🔜 Pending |
| `src/tas/main.py` | [main.md](./main.md) | 🔜 Pending |

---

## Documentation Structure

Each code documentation file follows this structure:

1. **Overview** - What the file does, one paragraph
2. **What This File Contains** - Table of components
3. **Design Decisions** - Why certain choices were made
4. **Detailed Explanations** - Logic, algorithms, formulas
5. **Usage Examples** - Code snippets showing how to use
6. **Edge Cases** - How edge cases are handled
7. **Dependency Graph** - What this file depends on / what depends on it

---

## Quick Reference

### Module Purpose

```
models.py      → Data structures (enums, dataclasses, Pydantic models)
hedge_scorer.py → Detect uncertainty/hedging in language
classifier.py   → Classify sentences into 12 tense classes (T1-T12)
zimbardo.py     → Calculate temporal personality profile
migration.py    → Detect behavioral shifts across sessions
analyzer.py     → Orchestrate full analysis pipeline
api.py          → FastAPI endpoints
main.py         → Entry point / CLI
```

### Import Graph

```
models.py
    │
    ├──► hedge_scorer.py
    │
    ├──► classifier.py ◄── hedge_scorer.py
    │
    ├──► zimbardo.py ◄── classifier.py
    │
    ├──► migration.py ◄── classifier.py
    │
    └──► analyzer.py ◄── all above
             │
             └──► api.py
                    │
                    └──► main.py
```

---

## Design Principles

1. **Self-documenting variable names** - Read the code, understand intent
2. **Context-aware over keyword matching** - Use spaCy for syntactic understanding
3. **Immutable data structures** - Thread safety in async environments
4. **Single responsibility** - Each file does one thing well
5. **Explicit over implicit** - No magic, clear data flow
