# Conversation flows

Diagrams are Mermaid and render on GitHub. Node IDs (e.g. `N03`) match the prompt inventory in [03-dialogue-scripts.md](03-dialogue-scripts.md).

**Legend:** rectangles are Sam's turns, diamonds are decisions, rounded boxes are system actions, red is an exit to a human.

## 1. Master flow

```mermaid
flowchart TD
    N01["N01 Greet + AI disclosure"] --> N02{"N02 Is anyone hurt<br/>or in danger?"}
    N02 -- "Yes / unsure" --> SAFE["S01 Safety: call 000<br/>+ offer callback"]:::human
    N02 -- "No" --> N03["N03 Verify identity"]
    N03 -- "Fails twice" --> H1["Handoff: identity"]:::human
    N03 -- "Verified" --> N04{"N04 Which car?<br/>(skip if one vehicle)"}
    N04 --> N05["N05 Tell me what happened"]
    N05 --> X1(("Extract slots<br/>from story"))
    X1 --> N06{"Slots missing?"}
    N06 -- "Yes" --> N07["N07-N13 Ask only<br/>for missing slots"]
    N07 --> N06
    N06 -- "No" --> N14["N14 Read back summary"]
    N14 -- "Correction" --> N07
    N14 -- "Confirmed" --> N15["N15 Photos (optional)"]
    N15 --> C1(("create_claim"))
    C1 -- "OK" --> N16["N16 Claim number<br/>+ what happens next"]
    C1 -- "Fails" --> E05["E05 Save + callback,<br/>no fake number"]:::human
    N16 --> N17["N17 Anything else?"]
    N17 --> N18["N18 Close"]

    classDef human fill:#fde2e1,stroke:#c0392b,color:#000
```

**Global listeners** (active on every node): ask for a human, complaint, injury mentioned, vulnerability cue, digression question, "stop / later". See sections 4-6.

## 2. Happy path: collision with another vehicle

Slots: `vehicle`, `incident_type`, `date_time`, `location`, `description`, `drivable`, `driver`, `other_party`, `police_ref`.

```mermaid
flowchart LR
    A["Story:<br/>'Someone ran a red<br/>and hit my passenger<br/>side on Logan Rd<br/>this morning'"] --> B(("Extract"))
    B --> C["Got: type=collision,<br/>location=Logan Rd,<br/>date=today, damage=<br/>passenger side"]
    C --> D["N08 Time + suburb?"]
    D --> E["N10 Can you drive it?"]
    E --> F["N11 Were you driving?"]
    F --> G["N12 Other driver's<br/>details?"]
    G --> H["N13 Police report?"]
    H --> I["N14 Summary ✓"]
    I --> J["N16 Claim WTL-12345<br/>+ next steps"]
```

Story-first means a good opening message can fill four or five slots at once, so the customer answers three or four questions instead of ten.

## 3. Error handling

### No-match and no-input (any question node)

```mermaid
flowchart TD
    Q["Sam asks question"] --> R{"Understood?"}
    R -- "Yes" --> NEXT["Continue"]
    R -- "No-match 1" --> RP1["Reprompt 1:<br/>rephrase + example"]
    RP1 --> R2{"Understood?"}
    R2 -- "Yes" --> NEXT
    R2 -- "No-match 2" --> RP2["Reprompt 2:<br/>offer buttons /<br/>'skip for now'"]
    RP2 --> R3{"Understood?"}
    R3 -- "Yes / skip" --> NEXT
    R3 -- "No-match 3" --> HO["Offer a person,<br/>keep what's captured"]:::human
    Q -- "No reply 3 min" --> NI["'Still there? Your<br/>details are saved.'"]
    NI -- "No reply 10 min" --> SAVE["Save draft +<br/>send resume link"]

    classDef human fill:#fde2e1,stroke:#c0392b,color:#000
```

### System and validation errors

| ID | Situation | Behaviour |
|----|-----------|-----------|
| E01 | Date in the future, or more than 12 months ago | Check, don't reject: "Just checking: was that 3 June this year?" |
| E02 | Rego doesn't match format | Accept it, flag `unverified`. Don't block a claim on a typo. |
| E03 | `get_policy` down | Continue capture without policy details; tell the customer the consultant will confirm cover details. |
| E04 | `verify_identity` down | Capture the story and contact details only; handoff with "identity not verified". |
| E05 | `create_claim` fails | Never invent a number. Save the draft, book a callback, say so plainly. |
| E06 | Customer contradicts an earlier answer | Ask once which is right. Don't accuse. |

## 4. Digressions: answer, bridge, resume

The customer asks something off the current path. Sam answers within its limits, then returns to the exact node it left.

```mermaid
flowchart LR
    NODE["Any node,<br/>e.g. N10"] --> DQ{"Digression<br/>detected"}
    DQ --> T{"Within Sam's<br/>limits?"}
    T -- "Yes: info only" --> ANS["Answer briefly"]
    T -- "No: decision<br/>or advice" --> DEF["Say who decides<br/>+ when they'll know"]
    ANS --> BR["Bridge: 'Shall we<br/>keep going?'"]
    DEF --> BR
    BR --> NODE
```

| Digression | Sam can say | Sam must not say |
|------------|-------------|------------------|
| "Is my excess covered?" / "How much is my excess?" | The excess on the policy schedule; that some excesses can be waived and the consultant confirms | "You'll pay $X" / "You won't pay excess" |
| "Will you cover this?" | What the policy type is (e.g. comprehensive); that cover is confirmed during assessment | "Yes, you're covered" |
| "Am I at fault?" | Fault is assessed from the details; general tip: don't admit fault at the scene | Any view on fault |
| "Can I get a hire car?" | Whether hire car cover is listed on the policy; consultant arranges it | "We'll get you a car today" |
| "Will my premium go up?" | Premiums are reviewed at renewal; can't predict | Any yes/no |
| "Should I claim or pay myself?" | Customer's choice; offers to note the incident without lodging, or a person to talk it through | A recommendation (personal advice) |
| "Where's my car being towed?" | Tow details if `book_tow` was used | A guess |

Two digressions in a row on cover or money, or any sign of confusion about cover, triggers an offer of a person.

## 5. Disambiguation

```mermaid
flowchart TD
    U["Ambiguous input"] --> K{"Type"}
    K -- "Which car?" --> V["List cars on policy by<br/>make, model, rego<br/>+ 'Something else'"]
    K -- "Relative date<br/>'last night'" --> D["Resolve + confirm:<br/>'Tuesday 27 Oct,<br/>in the evening?'"]
    K -- "Vague place<br/>'Main St'" --> L["Ask suburb, or offer<br/>to share location"]
    K -- "Incident type<br/>'someone hit me'" --> I["'Were you driving,<br/>or was it parked?'"]
    K -- "Who's reporting<br/>'my mate's car'" --> W["Check: policyholder,<br/>listed driver, or<br/>other party?"]
    W -- "Other party" --> TP["Third-party flow:<br/>no policy details shared"]:::human
    V --> OK["Resume"]
    D --> OK
    L --> OK
    I --> OK
    W -- "Policyholder /<br/>listed driver" --> OK

    classDef human fill:#fde2e1,stroke:#c0392b,color:#000
```

**Rules:** offer 2-4 options, most likely first, always with an escape ("Something else"). Never guess silently on anything that changes the claim (vehicle, date, incident type). Confirm resolved dates as a full date.

## 6. Escalation to a human

| Trigger | Detected by | Sam says / does |
|---------|-------------|-----------------|
| Anyone hurt, in danger, or unsure | N02 answer, or injury words anywhere | 000 first, then callback. Stops claim capture. |
| Customer asks for a person | "agent", "human", "real person", "call me" | Honour at once. One sentence on what's saved. No "are you sure?". |
| Complaint or dissatisfaction | "not happy", "complain", "ridiculous", "useless" | Acknowledge, log as a complaint, offer a person. Don't argue or defend. |
| Vulnerability cues | Mentions of family violence, financial hardship, disability, language difficulty, severe distress | Empathy level 3, offer a person, flag `vulnerability` in handoff (no label shown to customer). |
| Third party claiming against a customer | Disambiguation W | Third-party team. No policyholder data shared. |
| Three no-matches on one node | Error flow | Offer a person, keep the draft. |
| Question needing a decision or advice | Digression table | Explain who decides; offer a person if they want it now. |
| Possible fraud signals | Back-end rules only | No change to the conversation. Flag silently for the claims team. Never accuse. |

The handoff payload is specified in [06-nlu-and-handoff-spec.md](06-nlu-and-handoff-spec.md).
