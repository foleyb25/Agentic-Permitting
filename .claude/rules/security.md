# Security Baseline

Applies to all work in this repository (no path scoping — always in context).

- Never log secrets, tokens, or full request payloads that may contain PII.
- Read credentials from environment variables only; never hardcode them or commit
  them, even in tests or fixtures.
- Treat all client/external input as untrusted until validated at the boundary.
- Parameterize every SQL query; never build SQL by string concatenation.
- Never `print()` to stdout in a stdio MCP server — it corrupts the protocol and
  can leak data. Use the `logging` module or the request `Context`.
