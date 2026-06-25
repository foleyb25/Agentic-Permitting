---
name: convention-audit
description: >
  Scans the codebase for violations of this project's Python/FastMCP coding and
  testing conventions and returns a structured report. Use when preparing a PR,
  before a release, or when asked to audit code quality. Read-only; makes no edits.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# Convention Audit

Audit the codebase against this project's conventions and produce a report.
Audit only the path in $ARGUMENTS if provided; otherwise audit `src/`.

## Steps

1. Use Glob to enumerate source files in scope. Use Grep and Read to inspect
   them. Do not modify any file.

2. For each tool/resource handler under `src/permit_mcp/tools/` and
   `src/permit_mcp/resources/`, check for:
   - Handlers that raise a bare `Exception`/`ValueError` instead of `ToolError`
     for client-facing errors.
   - Arguments used before validation/coercion.
   - Tools/resources/prompts missing a docstring (the model-facing description).
   - I/O-bound handlers defined with `def` instead of `async def`.

3. Across all source files, check for:
   - Uses of the `Any` type or untyped public function signatures.
   - `print(` calls (forbidden — corrupts the stdio protocol; use `logging`).
   - Synchronous network/file I/O inside `async` handlers.
   - Functions longer than ~50 lines.

4. For test coverage, flag any `src/` module that has no corresponding
   `test_*.py` under `tests/`, and any committed `pytest.skip` / `@pytest.mark.skip`.

## Output

Return a single report with these sections, and nothing else:

- **Summary**: counts per category.
- **Findings**: a table of `file:line — issue — convention`.
- **Top fixes**: the 3 highest-impact items to address first.

Do not attempt to fix anything. Report only.
