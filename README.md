# Psynapse - TAS (Tense-as-Signal Analyzer)

A preprocessing submodule for the **Undercurrent** behavioral intelligence system. TAS analyzes grammatical tense in user messages to extract psychological signals about:

- **Psychological distance** from topics
- **Behavioral patterns** and habits
- **Commitment levels** to intentions
- **Temporal personality traits** (Zimbardo profile)

## Core Insight

> **Grammatical tense is not just a linguistic feature — it is a psychological distance signal.**

The same content in different tenses carries opposite behavioral implications:
- "I'm building a startup" → Active investment, high priority
- "I used to want to build a startup" → Historical, deprioritized

## Features

### 12-Class Tense Classification

| ID | Name | Example | Graph Operation |
|----|------|---------|-----------------|
| T1 | Active Present | "I'm building a startup" | INCREMENT |
| T2 | Habitual Present | "I always shut down in conflict" | INCREMENT |
| T3 | Stable Belief | "I believe hard work matters" | INCREMENT |
| T4 | Historical Past | "I used to run every day" | DECREMENT |
| T5 | Experiential Past | "I went through a hard period" | NONE |
| T6 | Narrative Present | "So I'm in this meeting and freeze" | INCREMENT |
| T7 | Declared Future | "I will launch in March" | INCREMENT |
| T8 | Hedged Future | "I might try to get fit" | INCREMENT (discounted) |
| T9 | Conditional | "I would love to travel if I could" | INCREMENT (low) |
| T10 | Counterfactual | "I should have left that job" | TRIGGER |
| T11 | Present-Fatalistic | "Nothing ever changes for me" | FLAG |
| T12 | Future-Anxious | "I'm scared of what might happen" | FLAG |

### Multiplicative Hedge Scoring

Quantifies commitment intensity on a 0.0-1.0 scale:

```
"I kind of think I might possibly start a business"
     ↓
0.20 × 0.50 × 0.50 × 0.20 = 0.01 (~1% effective weight)
```

### Zimbardo Time Perspective Profiling

Tracks five temporal orientations:
- Past-Negative (regret, rumination)
- Past-Positive (nostalgia, warmth)
- Present-Hedonistic (pleasure-seeking)
- Present-Fatalistic (helplessness)
- Future-Oriented (goal-driven)

### Tense Migration Detection

Detects behavioral shifts:
- T1/T2 → T4: Topic deprioritization
- T4 → T1: Topic reactivation
- T7 → T8: Commitment decay
- T8 → T7: Commitment increase

## Installation

```bash
# Clone the repository
git clone https://github.com/V1629/UnderCurrent.git
cd UnderCurrent/Psynapse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

## Quick Start

### Python API

```python
from src.tas import TASAnalyzer

# Create analyzer
analyzer = TASAnalyzer()

# Analyze a message
result = await analyzer.analyze(
    message="I used to run every day but lately I've been getting back into it",
    user_id="user123",
    session_id="session456",
)

# Access results
for sentence in result.sentences:
    print(f"Text: {sentence.text}")
    print(f"Tense: {sentence.tense_class_name}")
    print(f"Hedge Score: {sentence.hedge_score}")
    print(f"Graph Op: {sentence.graph_operation}")
```

### REST API

```bash
# Start the server
uvicorn src.tas.main:app --reload --port 8000

# Analyze message
curl -X POST "http://localhost:8000/api/v1/tas/analyze" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am learning Python", "user_id": "test"}'
```

API Documentation: http://localhost:8000/docs

## Project Structure

```
Psynapse/
├── src/
│   └── tas/
│       ├── __init__.py       # Package exports
│       ├── analyzer.py       # Main TAS orchestrator
│       ├── classifier.py     # 12-class tense classification
│       ├── hedge_scorer.py   # Multiplicative hedge scoring
│       ├── zimbardo.py       # Profile accumulation
│       ├── migration.py      # Migration detection
│       ├── models.py         # Pydantic schemas
│       ├── api.py            # FastAPI endpoints
│       └── main.py           # API server
├── tests/
│   └── test_tas.py           # Unit tests
├── docs/
│   ├── TAS_DOCUMENTATION.md  # Full technical docs
│   └── diagrams/             # Architecture diagrams
├── requirements.txt
├── pyproject.toml
└── conftest.py
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/tas --cov-report=html

# Run specific test class
pytest tests/test_tas.py::TestActiveVsHistorical -v
```

## Documentation

- [Full Technical Documentation](docs/TAS_DOCUMENTATION.md)
- [Architecture Diagrams](docs/diagrams/README.md)

## Success Criteria

TAS is working correctly when:

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1 | "I'm learning Python" vs "I used to learn Python" | Opposite graph operations |
| 2 | "I will definitely launch next month" | hedge_score ≥ 0.95, class = T7 |
| 3 | "I might kind of think about maybe starting something" | hedge_score ≤ 0.05 |
| 4 | "So I'm in this meeting and I freeze" | T6 (Narrative), NOT T1 |
| 5 | Topic: T1→T1→T2→T4→T4 | TENSE_MIGRATION fires |
| 6 | "Nothing ever works out for me" | present_fatalistic += delta |
| 7 | "Life is hard sometimes" (no first-person) | NO graph update |

## License

MIT License

## Author

Undercurrent Team
