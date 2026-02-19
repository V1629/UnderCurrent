# Undercurrent System Architecture — Mermaid Diagrams

## 1. High-Level System Overview

```mermaid
flowchart TB
    subgraph INPUT[INPUT]
        UM[/User Message/]
    end

    subgraph UNDERCURRENT[UNDERCURRENT]
        
        subgraph TAS[TAS - Tense-as-Signal Analyzer]
            direction TB
            T1[Sentence Segmentation]
            T2[Root Verb Extraction]
            T3[Tense Classification]
            T4[Narrative Detection]
            T5[Psych Orientation]
            T6[Hedge Scoring]
            T7[Weight Modifier]
            T8[Graph Routing]
            T9[History Update]
            T10[Zimbardo Score]
            
            T1 --> T2 --> T3 --> T4 --> T5 --> T6 --> T7 --> T8 --> T9 --> T10
        end
        
        subgraph OTHER[OTHER MODULES]
            GE[Graph Engine]
            ED[Emotion Detection]
            TE[Topic Extractor]
            IE[Inference Engine]
        end
        
        TAS -->|Enriched Signal| GE
        TAS -->|Enriched Signal| ED
        TAS -->|Enriched Signal| TE
        GE --> IE
        ED --> IE
        TE --> IE
    end

    subgraph OUTPUT[OUTPUT]
        BI[/Behavioral Intelligence/]
    end

    UM --> TAS
    IE --> BI
```

---

## 2. TAS Module — Detailed Pipeline

```mermaid
flowchart TD
    subgraph INPUT[INPUT]
        MSG[/Raw Message/]
        HIST[(Tense History)]
    end

    subgraph TAS[TAS MODULE]
        direction TB
        
        subgraph PARSE[PARSING]
            S1[Segmentation]
            S2[Dependency Parse]
            S3[Root Verb]
        end
        
        subgraph CLASSIFY[CLASSIFICATION]
            C1{Tense?}
            C2{Narrative?}
            C3{Fatalistic?}
            C4{Conditional?}
            C5{Hedged?}
        end
        
        subgraph CLASSES[12 TENSE CLASSES]
            T1[T1: Active]
            T2[T2: Habitual]
            T3[T3: Belief]
            T4[T4: Historical]
            T5[T5: Experiential]
            T6[T6: Narrative]
            T7[T7: Future]
            T8[T8: Hedged]
            T9[T9: Conditional]
            T10[T10: Counterfactual]
            T11[T11: Fatalistic]
            T12[T12: Anxious]
        end
        
        subgraph SCORE[SCORING]
            H1[Hedge Detection]
            H2[Score Calc]
            H3[Weight Modifier]
        end
        
        subgraph ENRICH[ENRICHMENT]
            E1[Self-Reference]
            E2[Zimbardo]
            E3[Migration]
            E4[Graph Op]
        end
    end

    subgraph OUTPUT[OUTPUT]
        OUT[/TASOutput/]
    end

    MSG --> S1 --> S2 --> S3
    S3 --> C1 --> C2 --> C3 --> C4 --> C5
    C5 --> CLASSES
    CLASSES --> H1 --> H2 --> H3
    H3 --> E1 --> E2 --> E3 --> E4
    HIST --> E3
    E4 --> OUT
```

---

## 3. Information Flow — Message to Behavioral Intelligence

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant TAS as TAS
    participant GE as Graph
    participant ED as Emotion
    participant TE as Topic
    participant IE as Inference

    U->>TAS: User Message
    
    rect rgb(240, 240, 240)
        Note over TAS: TAS Processing
        TAS->>TAS: Segment sentences
        TAS->>TAS: Extract root verbs
        TAS->>TAS: Classify tenses
        TAS->>TAS: Score hedges
        TAS->>TAS: Detect migration
        TAS->>TAS: Update Zimbardo
    end

    TAS->>GE: Graph operations
    TAS->>ED: Enriched signal
    TAS->>TE: Enriched signal
    
    GE->>IE: Graph state
    ED->>IE: Emotions
    TE->>IE: Topics
    
    IE->>U: Behavioral Intelligence
```

---

## 4. Tense Classification Decision Tree

```mermaid
flowchart TD
    START((Start)) --> SELF{Self-Ref?}
    
    SELF -->|No| SKIP[Skip]
    SELF -->|Yes| NARR{Narrative?}
    
    NARR -->|Yes| T6[T6 Narrative]
    NARR -->|No| FATAL{Fatalistic?}
    
    FATAL -->|Yes| T11[T11 Fatalistic]
    FATAL -->|No| COUNTER{Counterfactual?}
    
    COUNTER -->|Yes| T10[T10 Counterfactual]
    COUNTER -->|No| COND{Conditional?}
    
    COND -->|Yes| T9[T9 Conditional]
    COND -->|No| TENSE{Tense?}
    
    TENSE -->|Future| HEDGE{Hedged?}
    HEDGE -->|Yes| T8[T8 Hedged]
    HEDGE -->|No| ANX{Anxious?}
    ANX -->|Yes| T12[T12 Anxious]
    ANX -->|No| T7[T7 Future]
    
    TENSE -->|Past| EXP{Type?}
    EXP -->|Habitual| T4[T4 Historical]
    EXP -->|Event| T5[T5 Experiential]
    
    TENSE -->|Present| PRES{Type?}
    PRES -->|Habitual| T2[T2 Habitual]
    PRES -->|Belief| T3[T3 Belief]
    PRES -->|Active| T1[T1 Active]
```

---

## 5. Hedge Score Calculation

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

---

## 6. Zimbardo Profile Accumulation

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

---

## 7. Tense Migration Detection

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

---

## 8. Complete Data Flow

```mermaid
flowchart TB
    subgraph USER[USER]
        MSG[User Message]
    end
    
    subgraph TAS[TAS MODULE]
        direction TB
        
        SEG[Segment]
        
        subgraph S1[Sentence 1]
            V1[verb: love]
            T1_1[T4: Historical]
            G1[DECREMENT]
        end
        
        subgraph S2[Sentence 2]
            V2[verb: am]
            T2_1[T1: Active]
            G2[INCREMENT]
        end
        
        MIG[MIGRATION: T4 to T1]
        ZIM[Zimbardo Delta]
    end

    subgraph OUTPUT[OUTPUT]
        JSON[TASOutput]
    end

    subgraph DOWN[DOWNSTREAM]
        GE[Graph Engine]
        ED[Emotion]
        IE[Inference]
    end

    MSG --> SEG
    SEG --> S1 & S2
    S1 & S2 --> MIG
    MIG --> ZIM --> JSON
    JSON --> GE & ED
    GE & ED --> IE
```

---

## How to View These Diagrams

1. **VS Code**: Install "Markdown Preview Mermaid Support" extension
2. **GitHub**: Renders automatically in markdown files
3. **Online**: Use [Mermaid Live Editor](https://mermaid.live/)

---

*Last Updated: February 2026*
