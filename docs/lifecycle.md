# Lifecycle: Stage 0, sizing, the nine phases and the gate

## Two axes at the same time

- **The six stages of the turn** (Entry, Interpret, Investigate, Resolve, Clarify, Transfer) say what the agent does with each message. That is the execution axis.
- **The nine phases of the lifecycle** say how the agent is born, goes to production and improves. That is the construction axis.

A phase only closes when it has produced its deliverable for all six stages.

| Phase | Question it answers | Deliverable |
| --- | --- | --- |
| 1. Foundations | What type of agent is this and how much autonomy does it have? | Agent type and autonomy level (N0 to N4) |
| 2. Use case | Is it worth building? Which problem, for whom, with what value? | Use-case sheet with value and risk scores |
| 3. Components | Which pieces does the agent need? | Active components, each with an owner |
| 4. Stack | Which technology builds each piece? | Stack ADR |
| 5. Design | How does the agent behave and when does it fire? | Canvas, per-capability sheets, trigger sheet, prompts v0 |
| 6. Build and test | Does it work, and did nothing regress? | Code, gold set, green error suite, scenario simulation |
| 7. Deploy | How does it reach production without breaking? | Environment, pipeline, rollout plan, signed go-live |
| 8. Monitor | Is it working now, and what does it cost? | Dashboards, alerts, weekly report |
| 9. Optimize | How does it get better, faster, cheaper? | New version promoted through the gate |

Phases 1 to 5 happen inside Stage 0. Phase 6 builds the canvas column by column. Phases 7 to 9 are a loop: what monitoring finds becomes an error-suite case and an optimization hypothesis, which goes back through the gate and a new deploy.

### Phase × stage matrix (excerpt)

| Phase | Entry | Interpret | Investigate | Resolve | Clarify | Transfer |
| --- | --- | --- | --- | --- | --- | --- |
| Foundations | Reactive or proactive | LLM reads, code decides | Fixed or autonomous search | Action by code or by LLM from a closed list | Minimum question, never open planning | Autonomy ends where risk begins |
| Build and test | Duplicate and concurrency cases | Extractor suite | Retrieval suite | Writer verifier, action tests | Gap cases | Handoff and delivery cases |
| Monitor | Receive latency, lost messages | Invalid schema, abstention | Missing source, recall | Tool errors, cost per turn | Questions per conversation | Transfer rate, time to human |
| Optimize | Buffer window | Smaller model, cache, examples | Chunking, reranking | Model routing, writer prompt | Fewer questions per resolution | Recalibrated triggers |

---

## Stage 0 — before any prompt or code

No prompt, model or flow is created before four jobs are done:

| Job | Delivers | Recorded in |
| --- | --- | --- |
| Set up repository and skills | Repository ready for a coding agent, with rules and procedures loaded | `CLAUDE.md`, `AGENTS.md`, `docs/agents/`, skills folder |
| Map the data | Inventory of sources and systems, plus reading of real conversations | `docs/sources/`, `CONTEXT.md`, gold set v0 |
| Draw the architecture | Canvas with one piece per stage, each as a hypothesis with a metric | `docs/architecture/` and ADRs |
| Gate | Review and acceptance before the first line of code | `docs/plans/` |

Every decision, rule, limit and plan lives in a file. Chat conversations and informal memory do not count as a record.

### Order

1. **Setup:** repository created, skills installed, governance files in place.
2. **Discovery with the client**, in six dimensions: business and goal; audience and conversations; service process; knowledge and sources; risk and constraints; quality and indicators. Every piece of information is classified as observed, stated and approved, hypothesis, or pending.
3. **Data map:** sources, owner and authority per fact, plus **50 to 100 real conversations read and annotated by hand.** The intent list, the glossary and the first test cases come from here.
4. **Architecture on the canvas:** where the agent runs, entry (media and buffer), one piece per stage, one model per role and the observability tool, each registered as a hypothesis with an ADR for material choices.
5. **Register:** `PRODUCT.md`, `CONTEXT.md`, policies and a phased plan.
6. **Gold set v0:** 30 to 50 labeled conversations before the first prompt.
7. **Gate.**

### The canvas

One entry column, five stage columns (Interpret, Investigate, Resolve, Clarify, Transfer), and bands for control, models and where it runs. In each column you choose one piece from the catalog. The finished canvas becomes the plan: one phase per column, in the order entry → interpret → decision → investigate → resolve → clarify → transfer → control. The canvas is an Excalidraw file versioned in the repository (`docs/architecture/diagrams/`).

---

## Agent sizing

Sizing is the first design step, before choosing any piece. **The size is the size of the highest criterion**: a single "L" makes the agent L.

| Criterion | S (small) | M (medium) | L (large) |
| --- | --- | --- | --- |
| Volume | Up to ~1,000 conversations/month | 1,000 to 20,000 | Above 20,000 |
| LLM stages | 1 or 2 | 3 or 4 | 5+, or multi-agent |
| Actions | Read and transfer only | Reversible writes | Irreversible or financial writes |
| Integrations | None or one | Two or three | Four or more |
| Data | No relevant personal data | Common personal data | Sensitive data (health, financial) |
| Autonomy | N0 to N1 | N1 to N2 | N2 to N3 |

| What it requires | S | M | L |
| --- | --- | --- | --- |
| Where it runs | n8n on a VPS or smallest managed tier | Managed platform | Managed platform, multiple replicas, dedicated staging |
| Observability | Langfuse Cloud Hobby | Langfuse Core or self-hosted | Langfuse self-hosted + Grafana / OpenLIT |
| Evals | Gold set v0 + error suite | + scenario simulation and A/B | + online evaluation with a judge and red team |
| Guardrails | Code + personal-data filter | + output verifier model | + managed classifier and human in the loop |
| Rollout | Short shadow, then full | Shadow and canary | Shadow, percentage canary, expansion |
| Security | Security matrix + SEC suite | + threat modeling | + review in a separate session and red team before go-live |

Every expected difficulty (unstable client integration, dirty source data, ambiguous rules, volume peaks, audio or images as main input, actions that cannot be undone) becomes a box on the canvas with an owner and a mitigation.

---

## The Stage 0 gate

Signed by the builder and a **security reviewer** (when the team is one person, the review is done in a separate session, with the security matrix open and without the coding agent that wrote the project).

- [ ] Skills installed and repository set up
- [ ] Data map filled, with owner and authority per source
- [ ] Real conversations read and annotated
- [ ] `PRODUCT.md` and `CONTEXT.md` approved
- [ ] Canvas filled, editable source saved
- [ ] ADRs for material choices (including stack and hosting)
- [ ] Sources, rules, permissions and limits registered
- [ ] Phased plan with acceptance criteria
- [ ] Gold set v0 and evaluation plan per stage
- [ ] Use-case sheet with selection score and autonomy level
- [ ] Agent size (S, M, L) and expected difficulties on the canvas
- [ ] Trigger sheet (reactive and proactive)
- [ ] Open items and hypotheses with an owner
- [ ] Mandatory security cases written
- [ ] Security matrix review signed and dated

---

## Where the agent runs

The runtime decision comes before the pieces, because it conditions how buffer, state, queue, tests and publishing are built.

| Option | Comes ready | You build | Fits when | Cost and risk |
| --- | --- | --- | --- | --- |
| Visual orchestrator (n8n) on a VPS | Webhook, credentials, connectors, execution history | Decision in a code node, state in a database, buffer with nodes | Linear flow, fast first version | Logic spread across nodes; harder to version and to run the error suite |
| Own service in code | Nothing | Webhook server, queue, worker, state, tracing, deploy | Testable decision code, error suite in CI, loops, pause and resume | More initial work; you operate it |
| Managed agent platform | Durable execution, persistence, scaling | The agent and integrations | Small team that doesn't want to run infrastructure | Vendor lock-in, usage cost, data outside your infrastructure |

The same agent can be born in n8n and migrate to its own service when the signals appear, because the contracts between stages don't change. The one requirement for any runtime: **the error suite runs in full before publishing.** In n8n that means keeping the decision in a testable code node, not in visual IFs.
