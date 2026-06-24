# Project: Permit Intelligence MCP Server

A Python [MCP](https://modelcontextprotocol.io) server, built with **FastMCP**, that
exposes permit/regulatory data to MCP clients (Claude Desktop, Claude Code, etc.)
as tools, resources, and prompts. Scope is the MCP server only — no REST API, no web UI.

## Tech stack

- Runtime: Python 3.11+ (use modern typing: `X | None`, `list[str]`, no `typing.Optional`)
- Framework: FastMCP (`from fastmcp import FastMCP`)
- Package/env manager: `uv` (never pip/poetry directly — use `uv add`, `uv run`)
- Tests: pytest, files named `test_*.py`
- Lint/format: ruff (lint + format), type-check with mypy or pyright (strict)

## Build and test commands

- Install deps: `uv sync`
- Add a dependency: `uv add <pkg>`
- Run the server (stdio): `uv run python -m permit_mcp` (or `uv run fastmcp run src/permit_mcp/server.py`)
- Inspect interactively: `uv run fastmcp dev src/permit_mcp/server.py` (opens the MCP Inspector)
- Type-check: `uv run mypy src` (or `uv run pyright`)
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Test (all): `uv run pytest`
- Test (single file): `uv run pytest tests/test_tools.py`
- Test (single case): `uv run pytest tests/test_tools.py::test_name`
- Run `uv run ruff check . && uv run mypy src && uv run pytest` before opening a PR.

## MCP / FastMCP conventions

- One `FastMCP` instance per server, created in `src/permit_mcp/server.py`; expose it as `mcp`.
- Register capabilities with decorators: `@mcp.tool`, `@mcp.resource("scheme://path")`, `@mcp.prompt`.
- **Tools** are actions/side-effects or computed lookups the model calls. **Resources** are
  read-only addressable data (use URI templates like `permit://{id}` for parametrized reads).
  **Prompts** are reusable message templates. Pick the right primitive — don't model a read as a tool.
- Every tool/resource/prompt needs a clear docstring: it becomes the description the model sees.
  Write it for the model, describing when to use it and what it returns.
- Type every parameter and return value. FastMCP derives the input schema from the signature
  and type hints; use Pydantic models or `Annotated[..., Field(description=...)]` for rich schemas.
- I/O-bound tools should be `async def`; never block the event loop with sync network/file calls.
- Validate and sanitize all client-supplied input inside the tool — clients are untrusted.
- Raise `ToolError` (`from fastmcp.exceptions import ToolError`) for errors meant to reach the
  client; let unexpected exceptions surface as internal errors. Never leak secrets in messages.
- Read config/secrets from environment (e.g. via `os.environ` or pydantic-settings), never hardcode.
- Keep the transport stdio-compatible: **never `print()` to stdout** (it corrupts the protocol).
  Use the `logging` module or `ctx.info(...)` for diagnostics.

## Coding standards

- 4-space indentation; let ruff format enforce style.
- Full type annotations on all public functions; no bare `Any` — use a precise type or `object`.
- Prefer small, focused functions; keep them under ~50 lines and extract helpers over deep nesting.
- snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants.

## Testing conventions

- Every new module ships with tests under `tests/`.
- Tests follow Arrange-Act-Assert with a blank line between sections.
- Test tools/resources by calling the underlying functions directly, and add at least one
  end-to-end test that drives the server through an in-memory FastMCP `Client`.
- Name tests by behavior: `test_rejects_unknown_permit_id`, not `test1`.
- Do not commit focused or skipped tests.

## Git workflow

- Branch naming: `feat/<short-desc>`, `fix/<short-desc>`, `chore/<short-desc>`.
- Conventional Commits for messages (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- One logical change per PR; keep diffs reviewable.
- Never commit directly to `main`.

## Project layout

- `src/permit_mcp/server.py` — the `FastMCP` instance and entry point (`mcp.run()`)
- `src/permit_mcp/tools/` — tool definitions grouped by domain
- `src/permit_mcp/resources/` — resource handlers
- `src/permit_mcp/` — `__main__.py` so `python -m permit_mcp` starts the server
- `tests/` — pytest suite
- `pyproject.toml` — deps, ruff/mypy/pytest config (managed by uv)
- `.claude/rules/` — path-scoped conventions (loaded on demand)
- `.claude/skills/` — packaged workflows (loaded when invoked)

## Always

- Validate and sanitize all client input inside each tool/resource handler.
- Reference the originating issue number in PR descriptions.
- Update the test when you change a tool/resource/prompt's behavior or schema.
