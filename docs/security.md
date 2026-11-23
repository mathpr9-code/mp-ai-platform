# Security and trust boundaries

Security is transversal: an interpretation, a retrieved document or an external result never becomes authorization by itself.

## Summary that applies to every agent

- Authentication, authorization and tenant isolation in every query and tool.
- Customer messages and retrieved content are untrusted data, never instructions.
- Approval tied to the exact action when the policy requires it.
- Secrets never enter chats, prompts or logs.
- Conversation content is minimized and anonymized before becoming evaluation data, with a defined retention period.

## Trust boundaries

| Input | Trust level |
| --- | --- |
| Customer message | Untrusted content |
| Retrieved document | Untrusted until origin and scope are validated |
| Tool result | External input: validate schema and provenance |
| LLM output | A proposal, not a fact and not an authorization |
| Business state | Comes from an authorized source |
| Identity and permission | Come from the authentication system, never from the conversation text |

## Minimum controls

- Tenant isolation in queries, storage, cache, embeddings, logs and tools.
- Server-side authorization for every operation; hiding a tool from the prompt is not a permission.
- Least privilege for services, users and agents.
- Secrets in a vault, never in prompts, datasets or logs.
- Minimization and masking of personal data; encryption in transit and at rest.
- Role-based access control and audit trail.
- Limits on rate, budget, input size and execution time.
- Validation of everything APIs and tools return.
- Separation of data between development, test, staging and production.

## Prompt injection

Content from customers, documents, pages and tool results is delimited as data and never mixed with instructions. An instruction found inside that data does not change policy, permissions, contracts or tool scope. Authorization is deterministic at the execution layer: even if the model asks for an improper action, the tool gateway rejects it. The mandatory cases SEC-004 and SEC-005 ([evaluation](evaluation.md)) test exactly this.

## Secrets

- Project keys are encrypted in the repository with an encrypted `.env` (e.g. dotenvx) and stored in a password vault.
- A secret never goes into a chat with a coding agent, a prompt, a dataset or a log.
- If a secret is exposed: revoke and rotate first, then investigate, then record the incident.
- Before publishing any repository, its full git history is scanned for secrets (e.g. `gitleaks`).

## Privacy by design

Each piece of data has a purpose, classification, access rule, retention period and deletion rule. Don't log full content for convenience. Don't promote conversations to datasets without sanitization, review and authorization. Never reuse one client's data for another.

**Anonymization in model and API calls** is a framework rule: personal identifiers are replaced or masked before content is sent to an external model whenever the task does not need them.

## Threat modeling

For each agent and tool, document assets, trust boundaries, data handled, authorized actors, external effects and failure scenarios. Review on every change of permission, scope, connector, knowledge source or write operation. The framework uses the OWASP Top 10 for agentic applications and the OWASP MCP Top 10 as checklists.

## Approval of critical actions

Actions with external effects follow the governed execution cycle (authorize → validate → log the attempt → execute → confirm with the source). Irreversible or financial actions require explicit confirmation from the customer (ESC4) and, when the policy says so, human approval tied to that exact action.
