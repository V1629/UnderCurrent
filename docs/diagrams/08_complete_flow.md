# Complete Data Flow

End-to-end example of message processing.

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

## Example

**Input**: "I used to love coding but now I'm really into it again"

**Output**:
- Sentence 1: T4 (Historical) → DECREMENT
- Sentence 2: T1 (Active) → INCREMENT
- Event: REACTIVATION migration detected
