# Hedge Score Calculation

Multiplicative hedge scoring system.

```mermaid
flowchart LR
    subgraph INPUT[Input]
        S[Sentence]
    end
    
    subgraph DETECT[Detection]
        H1[kind of x0.20]
        H2[think x0.50]
        H3[might x0.50]
        H4[possibly x0.20]
    end
    
    subgraph CALC[Calculate]
        C[1.0 x 0.20 x 0.50 x 0.50 x 0.20]
    end
    
    subgraph OUTPUT[Result]
        R[score = 0.01]
    end
    
    S --> H1 & H2 & H3 & H4
    H1 & H2 & H3 & H4 --> C --> R
```

## Hedge Categories

| Category | Multiplier | Examples |
|----------|------------|----------|
| Strong | x0.20 | maybe, someday, kind of |
| Medium | x0.50 | probably, might, could |
| Light | x0.77 | usually, generally |
| None | x1.0 | definitely, I will |
