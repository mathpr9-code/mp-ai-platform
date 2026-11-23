# Reference implementation

A deliberately small Python implementation of two ideas from the framework:

- **The decision layer as a pure function** ([`src/mp_agent/decision.py`](src/mp_agent/decision.py)): receives the extractor's interpretation, the conversation state and the conversation, and returns a conduct. No LLM, no I/O, fully testable.
- **The error suite as data** ([`tests/error_suite/`](tests/error_suite/)): every case is one YAML file; a single runner executes all of them.

The extractor itself (the LLM call) is out of scope here on purpose: the cases provide its output as `interpretation`, which is exactly how decision cases are run in the framework, without a model.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -v
```

## Rules implemented in `decide()`

| Order | Rule | Case |
| --- | --- | --- |
| 1 | Every quote must exist literally in the cited turn | SEC-008 |
| 2 | After the clarification limit, stop asking and transfer | ERR-0045 |
| 3 | An explicit, quoted request for a human is transferred | ERR-0044 |
| 4 | A reply is resolved against the open question it answers (the turn is a pair) | SEC-001, SEC-002, ERR-0043 |
| 5 | A short reply with no open question triggers nothing | SEC-003 |
| 6 | Actions with consequences are confirmed before the tool is called | SEC-011 |
| 7 | Facts are applied to state as events; missing fields produce one question | ERR-0042, ERR-0046 |

## Add a case

Copy any file in `tests/error_suite/cases/`, describe the smallest conversation that reproduces the bug and the expected conduct, and run `pytest`. The new case must fail before the fix and pass after it, with every other case still green.
