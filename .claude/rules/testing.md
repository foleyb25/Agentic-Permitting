---
paths:
  - "**/test_*.py"
---

# Testing Conventions

These rules apply when working on test files (`test_*.py`).

## Structure

- Use pytest. Structure each test as Arrange-Act-Assert with a blank line
  separating the three sections.
- One behavior per test function. If you need "and" to describe what a test
  checks, split it into two tests.

## Naming

- Name tests by the behavior under test, phrased as an assertion of intent:
  `test_rejects_unknown_permit_id`, not `test_auth` or `test1`.
- Group related cases in a `Test<Unit>` class or a module named after the unit.

## Coverage

- Test tools/resources by calling the underlying functions directly, and add at
  least one end-to-end test that drives the server through an in-memory FastMCP
  `Client` so the registered schema and transport are exercised.
- Use `pytest.mark.asyncio` (or `anyio`) for async handlers.

## Data and isolation

- For code that touches the database, use the real Postgres test container, not
  mocks. Reset state between tests with the provided fixture.
- Build fixtures with the factory helpers in `tests/factories/`; do not hand-roll
  large literal objects inline.

## Hygiene

- Never commit focused (`-k`-only crutches) or skipped tests. CI fails on
  stray `@pytest.mark.skip` / `pytest.skip()` left in committed code.
- A bug fix ships with a regression test that fails before the fix and passes after.
- Prefer asserting on observable behavior (return values, tool results, db rows)
  over implementation details (which internal function was called).
