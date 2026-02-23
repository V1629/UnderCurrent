# Signal Extraction Approaches — Psynapse

A reference document covering 8 psychological signal extraction techniques used in the Psynapse behavioral intelligence module. Each approach is grounded in psychological research, has a concrete computational method, and feeds into a specific downstream module.

---

## 1. Implicit Behavioural Fingerprinting

### Psychological Basis
People's revealed preferences — what they actually do, ask about, and return to — are more accurate predictors of their priorities than their stated preferences. This is the behavioral economics principle of **revealed preference** (Samuelson, 1938) applied to language. What someone keeps coming back to in conversation, even unprompted, is what occupies their cognitive real estate. The brain allocates attention proportional to emotional and motivational salience.

### How to Detect and Calculate
Track topic frequency across sessions, not just within a single message.

```
implicit_salience(topic) = mention_count / total_sentences × recency_weight

recency_weight = e^(-λ × sessions_since_last_mention)
```

Fingerprint signals fire when:
- Topic mentioned **3+ times** across sessions unprompted
- User **initiates** the topic (not responding to a question)
- Topic appears across **multiple domains** (e.g. startup appears in career AND finance AND identity turns)

Cross-domain repetition is the strongest signal — it means the concept has infected multiple areas of the user's thinking.

### Contribution
- Feeds directly into **Graph Engine node significance** as a multiplier
- Identifies the user's **true top 3 priorities** regardless of what they claim matters
- Flags **approach-avoidance loops** — topics mentioned repeatedly but never acted on (fitness in Arjun's case)
- Input to **Temporal Personality Profiler** — dominant implicit topics reveal Zimbardo orientation

---

## 2. Narrative Arc Detection

### Psychological Basis
When people tell stories about themselves, the **structure** of the narrative reveals their psychological relationship to the event — not just the content. Jerome Bruner's narrative psychology research shows that humans impose story structure (setup → complication → resolution) on experience to make sense of it. Whether a story has a resolution or trails off unresolved is itself a signal. An unresolved narrative indicates the person is still psychologically inside that experience.

### How to Detect and Calculate
Detect narrative present tense (T6) sequences and track whether they reach resolution.

```
narrative_arc_score = {
    "has_setup":       bool,   # past tense or scene-setting
    "has_complication": bool,  # contrast marker + negative signal
    "has_resolution":  bool,   # future declared (T7) or stable belief (T3)
    "resolution_confidence": hedge_score of resolution sentence
}

arc_completeness = (has_setup + has_complication + has_resolution) / 3
```

Unresolved arc = `arc_completeness < 0.67` with no T7/T3 resolution sentence.

Markers of narrative mode: sequential connectors ("so", "then", "and then", "suddenly"), present tense for past events, high emotional intensity score.

### Contribution
- Unresolved narratives → **open loop signal** → high-weight node with FLAG operation
- Resolution confidence (hedge score of the resolution) = **closure quality score**
- Repeated unresolved narratives on same topic = candidate for **conflict detection**
- Feeds **EFIB layer classifier** — narratives are predominantly EMOTION or FEELING layer, not INTENTION

---

## 3. Asymmetric Elaboration Technique

### Psychological Basis
In cognitive dissonance theory (Festinger, 1957), when people hold conflicting beliefs or when reality contradicts their self-image, they rationalize. Rationalization has a linguistic signature: **over-elaboration of the uncomfortable side**. When someone spends 40 words justifying why their job is fine and 5 words on the problem, they are working against internal resistance. The elaboration asymmetry IS the signal — not the content on either side.

### How to Detect and Calculate
Split sentence at contrast marker. Count words on each side. Calculate ratio.

```
asymmetry_ratio = max(words_before, words_after) / min(words_before, words_after)

dominant_side = "before" if words_before > words_after else "after"

asymmetry_signal fires when: ratio >= 2.5
```

Interpretation by dominant side:
- **Over-elaborated before "but"** → rationalization of the positive, suppressed dissatisfaction
- **Over-elaborated after "but"** → the complaint is what's really consuming them, positive framing is performative

Confidence of signal: `min(0.90, 0.50 + (ratio - 2.5) × 0.08)`

### Contribution
- Fires **ASYMMETRIC_ELABORATION** implicit signal
- Maps to **cognitive dissonance node** in the graph
- Strong predictor of **Value-Behaviour gap conflicts**
- Can surface hidden domain — user talking about career but asymmetry is on relationship side = real issue is relationships

---

## 4. Social Reference Signal

### Psychological Basis
Who people reference when talking about themselves reveals their **social comparison orientation** and **attachment style**. Social comparison theory (Festinger, 1954) shows people evaluate their own opinions and abilities by comparing to others. The specific person referenced and the framing of that reference (competitive, deferential, resentful, admiring) carries strong psychological signal. Referencing a partner's opinion as validation-seeking vs. referencing a competitor as threat-awareness are completely different psychological states despite similar surface structure.

### How to Detect and Calculate
Detect named or relational third-party references and classify the framing.

```
reference_types = {
    "authority_deference":  ["my boss said", "my therapist thinks", "my dad always"],
    "social_comparison":    ["my friend already", "people my age", "everyone else"],
    "partner_validation":   ["she thinks", "he says I", "my partner told me"],
    "competitive_reference":["unlike them", "better than", "they managed to"],
    "blame_attribution":    ["because of them", "they made me", "it's their fault"]
}

reference_weight = confidence × (1 if self_referential_consequence else 0.5)
```

Social comparison references get a **domain signal** inferred from what's being compared — career comparisons → career domain node; lifestyle comparisons → identity or finances node.

### Contribution
- Authority deference → **low agency signal** → Present-Fatalistic Zimbardo score
- Partner validation-seeking → **relationship strain + identity self-acceptance** conflict node
- Competitive reference → **identity threat signal** → high-significance identity node update
- Blame attribution → **external locus of control** → persistent flag on identity layer
- Feeds **Conflict Detector** — social comparison on a topic the user claims not to care about = concealed priority

---

## 5. Question Type as Intent Signal

### Psychological Basis
Questions are not neutral information requests. The **type of question** someone asks reveals their underlying emotional state, fear, and unmet need. Motivational interviewing theory (Miller & Rollnick) and Socratic questioning research both confirm that what someone asks about is a proxy for what they are **internally struggling with**. A person in a secure state does not ask "is it weird that I feel relieved when she cancels?" — that question only exists because they already feel shame about the answer.

### How to Detect and Calculate
Classify questions into intent categories using pattern matching.

```
question_signals = {
    "validation_seeking":    r"is it (weird|normal|okay|wrong) that i",
    "escape_planning":       r"how (do|can) i (quit|leave|get out of)",
    "motivation_collapse":   r"how (do|can) (you|i) stay (motivated|going)",
    "urgency_financial":     r"(fastest|quickest) way to (make|earn) money",
    "permission_seeking":    r"(should i|am i allowed to|is it okay if i)",
    "comparison_seeking":    r"(is .* normal|do most people|does everyone)",
    "repair_seeking":        r"how (do|can) i (fix|save|repair) my (relationship|marriage)"
}

intent_confidence = base_confidence × hedge_score_of_question
```

Questions with high hedge score themselves (e.g. "I don't know maybe is it weird that...") = even stronger suppressed signal.

### Contribution
- Each question type maps to a specific **implicit signal domain and concept**
- Validation-seeking → **identity.self_acceptance** node + shame flag
- Escape-planning → **career.job_dissatisfaction** node escalation
- Motivation collapse → **Present-Fatalistic** Zimbardo score increment
- All question signals weighted at `0.7×` explicit signal weight — they are implicit
- Strong input to **Conflict Detector** — questions about a topic + FLAG operation on same topic = active internal conflict confirmed

---

## 6. The Pressure Signal

### Psychological Basis
Psychological pressure manifests linguistically through **temporal urgency markers**, **obligation language**, and **catastrophizing**. When someone frames a goal with urgency they didn't have before, or uses "I have to / I need to / I must" rather than "I want to / I'd like to", the motivational structure has shifted from autonomous to controlled motivation (Self-Determination Theory, Deci & Ryan). Controlled motivation predicts lower follow-through and higher burnout. The pressure signal detects this shift.

### How to Detect and Calculate
Detect obligation vs. desire language and urgency framing per topic.

```
pressure_markers = {
    "high":   ["i have to", "i must", "i need to", "i can't keep", "running out of time",
               "before it's too late", "i should have already", "everyone expects"],
    "medium": ["i should", "i'm supposed to", "i really need", "i keep telling myself"],
    "low":    ["i want to", "i'd like to", "i'm hoping to", "i plan to"]
}

pressure_score = Σ(marker_weight × occurrence_count) / sentence_length

pressure_delta = pressure_score_current - pressure_score_previous_session
```

Rising pressure delta on a topic = pressure escalation event.

### Contribution
- High pressure + low hedge score = **burnout risk flag** on health domain
- Obligation language on a desire node = **Value-Behaviour gap** — want vs. should are in tension
- Pressure escalation event → triggers **EFIB layer shift** from INTENTION to EMOTION (desire becoming stress)
- Feeds **Zimbardo profiler** — sustained pressure language = Present-Fatalistic score increment
- Pressure on identity statements = **identity threat** — "I have to be a good father" vs "I am a good father" are psychologically opposite

---

## 7. Hedges vs Boosters: Ratio per Topic

### Psychological Basis
Epistemic modality research (Hyland, 1998) shows that hedges and boosters are not random — they are calibrated to the speaker's **actual internal certainty**, even when they are unaware of it. A person can claim commitment ("I'm definitely doing this") while using 4 hedge words in the same sentence. The **ratio of boosters to hedges per topic** across a conversation reveals the true commitment level independently of the explicit claim. This is the linguistic equivalent of a lie detector — not for lies, but for self-deception.

### How to Detect and Calculate
Track hedge and booster counts per topic node across all mentions of that topic.

```
hedges   = ["maybe", "might", "kind of", "sort of", "probably", "i think",
            "someday", "possibly", "i guess", "not sure", "i suppose"]

boosters = ["definitely", "absolutely", "certainly", "always", "for sure",
            "i know", "i will", "i am certain", "must", "without doubt"]

per_topic:
    hedge_count   = Σ hedge occurrences in sentences mentioning topic
    booster_count = Σ booster occurrences in sentences mentioning topic

commitment_ratio = booster_count / (hedge_count + booster_count + ε)

# 0.0 = pure hedging, 1.0 = pure boosting
```

Track `commitment_ratio` per topic across sessions. A declining ratio = **commitment decay** even if the user keeps saying they want the thing.

Compound hedge stacking: `"I kind of think I might possibly"` = multiplicative discount `0.25 × 0.50 × 0.25 = 0.03`

### Contribution
- Commitment ratio < 0.3 on a goal node → **HEDGED_FUTURE (T8)** regardless of surface grammar
- Declining commitment ratio across sessions → fires **COMMITMENT_DECAY** migration event
- Booster on a topic the user claims to not care about → **concealed priority** signal
- Commitment ratio feeds directly into **Graph Engine weight_modifier** — the final weight applied to any node update is scaled by this ratio
- Discrepancy between stated priority and commitment ratio = input to **conflict detector**

---

## 8. Pronominal Fingerprinting

### Psychological Basis
The pronouns people use reveal their **psychological ownership, agency, and distance** from a topic. Research by James Pennebaker (The Secret Life of Pronouns, 2011) shows that first-person singular usage ("I") correlates with self-focus, depression risk, and authenticity. First-person plural ("we") signals identification with a group. Passive constructions with no clear agent ("it happened", "things went wrong") signal **low agency and external locus of control**. Shifting from "I" to "we" or to passive mid-topic is a detectable psychological maneuver.

### How to Detect and Calculate
Track pronoun distribution per topic and detect shifts.

```
pronoun_categories = {
    "self_ownership":   ["i", "me", "my", "mine", "myself"],
    "collective":       ["we", "us", "our", "ours"],
    "other_blame":      ["they", "them", "their", "he", "she"],
    "passive_agentless":detect via missing subject in clause (no nsubj dep)
}

per_topic:
    ownership_score = self_ownership_count / total_pronouns_on_topic

agency_score = 1 - passive_agentless_ratio

# High ownership + high agency = active, self-directed engagement
# Low ownership + high other = blame/external attribution
# Low ownership + passive = helplessness / dissociation
```

Pronoun shift detection: if same topic moves from "I'm building" to "we were supposed to" to "it fell apart" across sessions = **agency collapse sequence**.

### Contribution
- Low ownership score on a goal node → **low commitment**, reduce weight modifier
- High other-blame on a domain → **external locus of control** flag → Present-Fatalistic Zimbardo increment
- Agency collapse sequence → fires **DEPRIORITIZATION** migration event
- Passive agentless constructions on identity statements → **identity fragmentation** signal → high-priority conflict flag
- Collective pronoun surge on a previously individual topic → **relationship influence signal** — someone else is now shaping this domain for the user

---

## Summary Table

| Approach | Primary Input | Graph Operation | Downstream Module |
|---|---|---|---|
| Implicit Behavioural Fingerprinting | Topic frequency history | Node significance multiplier | Graph Engine, Zimbardo |
| Narrative Arc Detection | T6 sentence sequences | FLAG / open-loop node | EFIB Classifier, Conflict Detector |
| Asymmetric Elaboration | Contrast marker word counts | ASYMMETRIC_ELABORATION implicit signal | Conflict Detector |
| Social Reference Signal | Third-party mentions + framing | Domain node update + agency flag | Zimbardo, Conflict Detector |
| Question Type as Intent | Question pattern matching | Implicit signal → node FLAG | Conflict Detector, Identity layer |
| The Pressure Signal | Obligation vs desire language | EFIB layer shift, burnout flag | Health domain, Zimbardo |
| Hedges vs Boosters Ratio | Per-topic hedge/booster counts | weight_modifier scaling, migration event | Graph Engine, Migration Detector |
| Pronominal Fingerprinting | Pronoun distribution per topic | Agency score, locus of control flag | Zimbardo, Conflict Detector |