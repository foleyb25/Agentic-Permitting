---
paths:
  - "src/permit_mcp/tools/**/*"
  - "src/permit_mcp/resources/**/*"
---

# Tool & Resource Conventions

These rules apply when working on MCP tools/resources under
`src/permit_mcp/tools/` and `src/permit_mcp/resources/`.

## Handler structure

- One file per domain group; register handlers with `@mcp.tool`,
  `@mcp.resource("scheme://path")`, or `@mcp.prompt`.
- Each handler does three things in order: validate input, call into a service or
  data layer, shape the result. Keep business logic out of the handler itself.
- Handlers must be thin. If a handler exceeds ~50 lines, extract a service module.
- Choose the right primitive: model read-only addressable data as a **resource**
  (use URI templates like `permit://{id}`), actions/computations as a **tool**.

## Input validation

- Type every parameter; let FastMCP derive the input schema from the signature.
  Use Pydantic models or `Annotated[..., Field(description=...)]` for rich schemas.
- Validate and coerce every argument at the top of the handler. Reject invalid
  input before any I/O. Treat all client-supplied values as untrusted.
- Never trust client-supplied IDs for authorization — re-check ownership server-side.

## Errors and responses

- Raise `ToolError` (`from fastmcp.exceptions import ToolError`) for errors meant
  to reach the client; never let a bare `Exception` leak internal detail or secrets.
- Do not return stack traces or internal messages to the client.

## Descriptions

- Every tool/resource/prompt needs a docstring — it becomes the description the
  model sees. Write it for the model: when to use it and what it returns.
- Document the failure modes a handler can produce.

## Transport hygiene

- Never `print()` to stdout — it corrupts the stdio JSON-RPC stream. Use the
  `logging` module or `ctx.info(...)` for diagnostics.
- I/O-bound handlers are `async def`; never block the event loop with sync I/O.
