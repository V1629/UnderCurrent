# Tense Migration Detection

Detecting behavioral shifts across sessions.

```mermaid
flowchart LR
    subgraph HISTORY[History]
        direction TB
        H1[S1: T1]
        H2[S2: T1]
        H3[S3: T2]
        H4[S4: T4]
        H5[S5: T4]
    end
    
    subgraph DETECT[Detection]
        D1{T1/T2 to T4?}
        D2[Active to Historical]
    end
    
    subgraph EVENT[Event]
        E[DEPRIORITIZATION]
    end
    
    subgraph ACTION[Action]
        A1[Reduce weight]
        A2[Flag shift]
    end
    
    H1 --> H2 --> H3 --> H4 --> H5
    H5 --> D1 -->|Yes| D2 --> E
    E --> A1 & A2
```

## Migration Types

| Migration | Signal | Action |
|-----------|--------|--------|
| T1/T2 → T4 | Deprioritization | Reduce weight |
| T4 → T1 | Reactivation | Increase weight |
| T7 → T8/T9 | Commitment decay | Flag concern |
| T8 → T7 | Commitment increase | Amplify |
