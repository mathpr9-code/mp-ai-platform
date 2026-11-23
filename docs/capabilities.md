# The stages of a turn: contracts, pieces and failure modes

Each stage follows the same structure: **role, contract, catalog of pieces, when each piece fits, how to measure it, and how it fails.** Three rules apply to all of them:

1. **No piece is the truth.** Every choice enters the canvas as a hypothesis, with the metric that confirms or kills it.
2. **Start with the simplest piece that fulfils the contract.** Only go up in complexity when the eval shows the ceiling of the current one.
3. **Measure each stage alone before measuring the whole.** Without per-stage measurement you don't know where to fix.

Three boundaries must never be mixed: the **capability** (what the agent must do, e.g. interpret a correction), the **architectural pattern** (how, e.g. single-pass or incremental extraction) and the **technology** (which library or provider). The name of a library does not replace an architectural decision.

---

## Entry — from the webhook to Interpret

The entry is code, not LLM, and it is the same for every agent. What changes per client are the media and buffer pieces.

| Step | What it does | Why |
| --- | --- | --- |
| 1. Receive | Validates the webhook origin, stores the raw message, acknowledges immediately | Providers retry when they don't get a fast ack; processing inside the webhook creates duplicates |
| 2. Deduplicate | Drops a message whose ID was already seen | A provider retry cannot become a second reply |
| 3. Normalize | Converts everything to text: transcribed audio, described/read image, extracted document | The extractor works on text; otherwise media becomes an empty message |
| 4. Buffer | Joins messages sent in sequence into one turn | People write in three messages what is one sentence |
| 5. Lock | One execution per conversation at a time | Two concurrent runs read the same state and overwrite each other |
| 6. Load | History (author + order), state, open questions, agent's last message | Without it the extractor reads the message in isolation |

**Media pieces:** M1 text only · M2 transcribed audio · M3 image read by a vision model · M4 document extraction. Always keep the original and the derived text, and mark the origin (typed, transcribed, read from image), because transcription makes mistakes and the extractor needs to know.

**Buffer pieces:** B1 none · B2 fixed window · B3 sliding window with a hard cap (default for WhatsApp) · B4 adaptive (short window if the message looks complete, longer if it looks cut). Window, cap and "what happens when a new message arrives during processing" are calibrated per client; there is no universal number.

---

## 1. Interpret — the extractor

**Role:** translate free language into a closed vocabulary that code understands. Maximum comprehension, zero authority.

| Axis | Question | Right level in the extractor |
| --- | --- | --- |
| Comprehension | What did the person say, given history and the client's vocabulary? | High: needs context, glossary and definitions |
| Authority | What to do about it? | None: rules, state, policy and next step live in code |

### Three levels

Choose the lowest level whose output is enough for code to decide.

| Level | Returns | Fits when |
| --- | --- | --- |
| N1 — Classifier | Act and intent from a closed list | Triage, menus, routing |
| N2 — Commands and fields | Acts, fields, corrections, cancellations | Processes with data to collect |
| N3 — Full interpretation | N2 + references, conditions, ambiguities, evidence per item | Open language, many topics, high cost of error |

### Execution patterns

| Pattern | How it works | Consider when |
| --- | --- | --- |
| I1 Single pass | One LLM call returns everything | Small/medium scope, low latency |
| I2 Staged | Separates acts, references and fields | A specific slice fails in single pass |
| I3 Selector + extractor | One component says what changed; another extracts only that | Large schema, incremental conversation |
| I4 Context per field | Retrieves the relevant turns for each field | Long history, parallel topics |
| I5 Dynamic schema | Selects part of the schema and examples before extracting | Many domains and intents |
| I6 Router + specialist | A rule or classifier routes to a specific extractor | High volume, bounded intents |
| I7 Structured output | Output constrained to a schema by the provider | Always, when code consumes the output |
| I8 Incremental | Per field: inherit, update, remove or mark unknown | Data accumulated and corrected across turns |
| I9 Tuned model | Fine-tuning or distillation | Stable gold set and volume that pays for maintenance |

Patterns combine (I5 selects the schema, I4 builds context, I7 constrains output) without requiring three LLM calls; parts can be deterministic.

### What code does with the output

1. Validates schema and enums.
2. Checks that every quote exists **literally** in the cited turn.
3. Cross-checks deterministic evidence (IDs, dates, codes by regex). On conflict, deterministic wins.
4. Applies changes to state as **events**, never by overwriting.
5. Decides the next step.

Do not use the model's self-reported confidence as a gate. Use filled `ambiguities`, validation failures and, for high-risk fields, disagreement between two runs.

### Symptom → lever

| Symptom | Fix first |
| --- | --- |
| Gets "the second one", "that", "yes" wrong | Context: the agent's message with the options didn't arrive |
| Invents a similar intent | Contract: missing "out of list" exit and an abstention example |
| Right on simple sentences, wrong on compound ones | Contract: `acts` must be a list; then I2 |
| Loses a correction | Context: pending state in the input; contrastive example |
| Valid JSON, wrong field in long conversations | Context: cut redundancy; I4 |
| Output changes between runs | Rubric: the definition is ambiguous for humans too |
| Extractor right, action wrong | Not the extractor: look at the decision |

### Minimum test slices

Direct message · several intents in one message · short reply to a previous question · anaphora and choice between options · correction of given information · negation (initial and embedded) · condition, hypothesis, future intent · implicit vs. explicit information · topic change and return · contradiction across turns · multiple participants · truncated history · field outside the schema · malicious instruction in the message or in retrieved content.

A high average cannot hide a critical failure in negation, correction, author, reference or a high-impact field. Each critical slice has its own gate.

---

## 2. Investigate — code plus retrieval

**Role:** bring authorized, current, traceable evidence. In a known flow, code chooses the query from the extractor's output through an `intent → source` table. The LLM only chooses the query when the sequence depends on the previous result, from a closed tool list and with a step limit.

### Catalog

| Pattern | How it works | Consider when | Costs and limits |
| --- | --- | --- | --- |
| INV1 Direct SQL/API | Code queries the source of truth by contract | Transactional, structured, current data | Schema, authorization, failure handling |
| INV2 Lexical (BM25) | Retrieves by terms and textual relevance | Codes, names, exact expressions | Misses paraphrases |
| INV3 Vector | Retrieves by semantic similarity | Paraphrases, varied vocabulary | Semantically close but factually wrong items |
| INV4 Hybrid | Lexical + vector with rank fusion | Exact terms and varied language | More parameters and infrastructure |
| INV5 Reranking | Re-orders candidates with a second model | Good recall, wrong order | Extra cost and latency |
| INV6 Two-step RAG | Retrieve then generate | FAQ, policies, manuals | Rigid for multi-step queries |
| INV7 Agentic RAG | An agent plans, chooses tools, repeats searches | Open investigation, heterogeneous sources | Variability, latency, control |
| INV8 Corrective RAG | Evaluates retrieval and corrects or falls back | Incomplete sources, unstable recall | Evaluator can be wrong; fallback needs policy |
| INV9 Self-RAG | Model decides when to retrieve and critiques evidence | Models trained for it | Not just a prompt |
| INV10 GraphRAG | Entities, relations and communities | Multi-hop and global questions | Expensive indexing and maintenance |
| INV11 Multi-query | Rewrites or splits the query | Compound or vague questions | Noise and more calls |
| INV12 Conversational memory | Retrieves past turns and sessions | Preferences, commitments across sessions | Needs time, updates and provenance |

**A common assembly:** hybrid search with reranking as the main search, Corrective RAG evaluating the result, and "insufficient" leading to Clarify or Transfer. RAG is not a maturity scale: GraphRAG is not "better than" hybrid; it is a piece for a type of question.

### Evidence contract

Every result carries source and version, type and authority of the source, access scope, excerpt or record, query time, validity and a status: `found`, `insufficient`, `conflict`, `stale`, `no_access`, `unavailable`. A divergence between a document and a system is recorded as a conflict, never resolved by the model.

| Symptom | Fix first |
| --- | --- |
| The answer is in the base and didn't come back | Recall: chunking, lexical search, metadata filters |
| A similar excerpt from another product or unit came back | Metadata filter before search; reranking |
| Right excerpt, wrong answer | Not Investigate: look at Resolve |
| Outdated data | Wrong source: it was a system, not a document |

---

## 3. Resolve — code decides, LLM writes

| Step | Owner | Delivers |
| --- | --- | --- |
| Decide | Code: rule table or state machine | The conduct |
| Execute | Code: tool with validation and idempotency | Result confirmed by the source |
| Write | LLM, from a structured act | Reply text |
| Verify | Code; an LLM judge only for semantic criteria | Approved, retry or fallback |

| Signal in discovery | Piece |
| --- | --- |
| Objective rule or calculation | RES3 rule/table; LLM only writes |
| Known process with few judgment points | RES4 workflow with LLM in specific nodes |
| Factual answer with hallucination risk | RES2 generation + verification |
| Simple, bounded question | RES1 grounded single pass |
| Path depends on each step's result | RES5 agent with tools and a step limit, inside one node |
| Composite task with verifiable steps | RES6 plan and execute |
| Truly different contexts or tools | RES7 specialists |
| Any external effect | RES8 governed execution, always, on top of the above |

**Start with a workflow.** Only replace a node with an agent when the gold set shows the fixed path doesn't cover real cases.

**Writer protocol.** Critical text (clinical, safety, legal) and approved text are sent literally, without a model. The act carries `act_id`, `action`, `facts` (with origin; the only source of what can be stated), `must_contain`, `must_not`. Risk level and fallback template stay in code and never reach the model. Customer messages and retrieved content enter in their own block, as data, never as instructions.

**Action execution.** A proposed action carries type, registered tool, validated arguments, authorization scope, preconditions, risk level, idempotency key and validity. Cycle: authorize → validate → log the attempt *before* the effect → execute → validate the result → log → update state → emit the act. States: proposed, authorized, rejected, executing, success, failure, timeout, **unknown**, compensated. "Unknown" exists because a timeout can happen after the external system finished; reconcile before retrying.

---

## 4. Clarify — the minimum question

Before asking, code checks in order: is the data already in the history or state? Can a system answer it? Is the customer the right person to answer, or is the gap internal? What does it cost to follow the most likely reading and confirm it together with the answer?

| Type of gap | Signal comes from | Piece |
| --- | --- | --- |
| Required field missing | Code compares state with required fields | ESC1 field-driven |
| Ambiguous reference or intent | Extractor `ambiguities` | ESC2 ambiguity-driven |
| Several gaps at once | Code orders by the one that unlocks most | ESC3 max information gain |
| Action with consequences | Policy marks "confirm first" | ESC4 choice or confirmation |
| Reply didn't fit the pending question | Act incompatible with the pending item | ESC5 repair |
| Customer is not the source | Policy | ESC6 clarify with a human |

Good clarification asks only what is needed, does not repeat what was already validated, never asks the customer for data a system could look up, distinguishes "I don't know", "I don't want to say" and "I didn't understand", and stops insisting when the person can't or won't answer.

---

## 5. Transfer and close — the decision machine

| Trigger class | Examples | Who fires it | Metric that rules |
| --- | --- | --- | --- |
| Mandatory | Out of scope, human authority, risk above limit, persistent failure, clarification limit | Code, by rule (TR1) | Recall: none can be missed |
| Semantic | Asks for a human, dissatisfaction, sensitive topic | Extractor flags the act; code applies policy (TR2) | Precision and recall per signal |

Other pieces: TR3 pause and resume (needs persisted state and checkpoints) · TR4 queue routing with priority and SLA · TR5 agent-to-agent handoff · TR6 timeout fallback for unstable external systems.

**Handoff contract:** conversation ID, reason and category, priority and queue, factual summary (the only LLM-written part), structured interpretation and evidence, sources consulted, actions already executed with confirmed status, questions asked and answers, open points and contradictions, risks, continuity instructions, and the state needed to resume. While the human is working, the agent does not reply.

**Delivery protocol.** Every output goes to an outbox with turn ID, idempotency key and status (pending, accepted, delivered, read, failed, unknown). HTTP 200 means "accepted", not delivered. Retries reuse the same output and key; the machine never decides again or calls a model again.

---

## Conversational conduct and persona

Behavior is universal; identity and knowledge are client-specific. The decision chooses one **move** per turn (welcome, answer, explain, offer paths, recommend next, clarify, resolve selection, compare, bridge, recover, confirm, transfer, close) and the writer writes inside it. Menus are a navigation tool, not an identity: 2 to 4 short paths, only when there is a real choice, dropped as soon as the customer chooses. Persona (name, voice, tone, vocabulary) never carries business rules.
