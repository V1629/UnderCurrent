# Zimbardo Profile Accumulation

How temporal personality profiles are built over time.

```mermaid
flowchart TD
    subgraph SENTENCES[Sentences]
        S1[T10: Counterfactual]
        S2[T11: Fatalistic]
        S3[T1: Active]
        S4[T7: Future]
    end
    
    subgraph CONTRIB[Contributions]
        C1[past_neg +0.05]
        C2[pres_fatal +0.05]
        C3[pres_hedon +0.02]
        C4[future +0.04]
    end
    
    subgraph PROFILE[Profile]
        P[past_neg: 0.15<br/>past_pos: 0.05<br/>pres_hedon: 0.22<br/>pres_fatal: 0.18<br/>future: 0.40]
    end
    
    subgraph PREDICT[Prediction]
        PR[FUTURE-ORIENTED<br/>Goal-driven]
    end
    
    S1 --> C1 --> P
    S2 --> C2 --> P
    S3 --> C3 --> P
    S4 --> C4 --> P
    P --> PR
```

## Profile Dimensions

| Dimension | Description |
|-----------|-------------|
| past_negative | Regret, rumination |
| past_positive | Nostalgia, warmth |
| present_hedonistic | Pleasure-seeking |
| present_fatalistic | Helplessness |
| future_oriented | Goal-driven |
