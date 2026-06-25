# MCP Reference Architecture

This directory is a **teaching kit** for the Model Context Protocol (MCP). Each file
plays one role in the MCP triad — **host**, **server**, **client** — plus the upstream
API and packaging around them. This document maps how the pieces connect.

> These are standalone examples. They are *not* the production `src/permit_mcp/`
> package described in the repo-root `CLAUDE.md`; they illustrate the moving parts.

---

## 0. Directory layout

Files are grouped by the **transport** the demo uses:

```
  mcp_github_example/
  ├── ARCHITECTURE.md        ← you are here (covers both demos)
  ├── http/                  ← Demo A: Streamable-HTTP transport
  │   ├── client.py
  │   └── server.py
  └── stdio/                 ← Demo B: stdio transport (+ supporting files)
      ├── host.py
      ├── github_api.py
      └── Dockerfile
```

---

## 1. The three MCP roles

MCP defines three participants. Knowing which file is which is the key to the diagrams below.

| Role       | Who it is                                  | File                        |
|------------|--------------------------------------------|-----------------------------|
| **Host**   | The LLM application that orchestrates tools | [`stdio/host.py`](./stdio/host.py) |
| **Client** | The connector that speaks MCP to a server   | [`http/client.py`](./http/client.py) + the `ClientSession` *inside* `host.py` |
| **Server** | Exposes tools/resources/prompts             | [`http/server.py`](./http/server.py) (ours) + the GitHub MCP server (external) |

Supporting cast:

| File                            | Role                                                    |
|---------------------------------|---------------------------------------------------------|
| [`stdio/github_api.py`](./stdio/github_api.py) | Raw upstream REST API — what a tool *wraps* internally |
| [`stdio/Dockerfile`](./stdio/Dockerfile)       | Packages `server.py` into a container                  |

---

## 2. Big picture — two independent demos

The directory actually contains **two separate flows** that share MCP concepts but do
not call each other. Keep them mentally distinct.

```
   ┌───────────────────────── DEMO A: "Our own server" ─────────────────────────┐
   │                                                                             │
   │     client.py  ──HTTP /mcp + Bearer──▶  server.py  ──▶  lookup_permit()     │
   │     (MCP client)                        (MCP server)     (in-process logic)  │
   │                                                                             │
   └─────────────────────────────────────────────────────────────────────────────┘

   ┌───────────────── DEMO B: "Host drives a 3rd-party server" ──────────────────┐
   │                                                                             │
   │   host.py  ──stdio──▶  GitHub MCP server  ──HTTPS──▶  api.github.com         │
   │   (host + client)      (Docker container)             (upstream REST)        │
   │                                                                             │
   │   github_api.py = a hand-written illustration of the HTTPS call the         │
   │                   GitHub MCP server makes internally (not imported anywhere) │
   └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Demo A — client ⇄ our FastMCP server

`client.py` connects to `server.py` over **Streamable HTTP** at a single `/mcp`
endpoint, authenticated with a bearer token. This demo highlights MCP's **two kinds
of "agent-passed variables"**: tool arguments vs. the request credential.

```
┌──────────────────────────────┐                       ┌────────────────────────────────────┐
│           client.py          │                       │              server.py               │
│        (MCP client)          │                       │            (MCP server)              │
│                              │                       │                                      │
│  Client("…/mcp",            │                       │   app = mcp.http_app(path="/mcp")    │
│         auth="my-secret…")   │                       │   app.add_middleware(BearerAuth)     │
│                              │                       │                                      │
│  call_tool(                  │   POST /mcp           │   ┌──────────────────────────────┐   │
│    "lookup_permit",          │   Authorization:      │   │       BearerAuth middleware    │   │
│    {permit_id:"P-12345",     │   Bearer my-secret…   │   │  header == "Bearer "+TOKEN ?   │   │
│     include_history:True})   │ ────────────────────▶ │   │   no  → 401 unauthorized       │   │
│                              │                       │   │   yes → call_next()            │   │
│                              │                       │   └───────────────┬──────────────┘   │
│                              │                       │                   ▼                  │
│                              │                       │   @mcp.tool                          │
│                              │                       │   async def lookup_permit(           │
│                              │                       │       permit_id, include_history)    │
│                              │                       │     • validates "P-" prefix          │
│                              │   {permit_id, status, │     • raises ToolError if invalid    │
│                              │ ◀──────────────────── │     • returns dict                   │
│  print(result.data)          │   history}            │                                      │
└──────────────────────────────┘                       └────────────────────────────────────┘
                                                            │
                                                            │ EXPECTED_TOKEN read at import
                                                            ▼
                                                     os.environ["MCP_AUTH_TOKEN"]
```

**Two variable channels (the lesson of this demo):**

```
  Tool arguments  ── model-supplied ──▶  permit_id, include_history
                                         (appear in the tool's input schema)

  Credential      ── caller-supplied ─▶  Authorization: Bearer <token>
                                         (HTTP header, validated in middleware,
                                          NEVER a tool parameter)
```

---

## 4. Demo B — host drives the GitHub MCP server

`host.py` is the **host**: it boots an MCP **client session** *and* runs the LLM loop.
It launches the official GitHub MCP server as a **Docker subprocess over stdio**,
discovers its tools, and hands them to Claude. Claude then calls those tools in a loop.

```
┌──────────────────────────────────────────────┐
│                   host.py                      │
│            (MCP host + MCP client)             │
│                                                │
│  client = AsyncAnthropic()  ◀── ANTHROPIC_API_KEY (env)
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ stdio_client(GITHUB_MCP)                  │ │   spawns
│  │   command="docker run … github-mcp-server"│─┼────────────┐
│  │   env={GITHUB_PERSONAL_ACCESS_TOKEN}      │ │            │
│  └──────────────────────────────────────────┘ │            ▼
│  ┌──────────────────────────────────────────┐ │   ┌────────────────────────────┐
│  │ ClientSession(read, write)                │ │   │   GitHub MCP server          │
│  │   await mcp.initialize()                  │ │   │   (Docker container, stdio)  │
│  │   tools = mcp.list_tools()  ──────────────┼─┼──▶│   • exposes GitHub tools     │
│  └──────────────────────────────────────────┘ │   │     (list_pull_requests, …)  │
│                       │ tools                   │   └─────────────┬──────────────┘
│                       ▼                         │                 │ HTTPS + PAT
│  ┌──────────────────────────────────────────┐ │                 ▼
│  │ client.beta.messages.tool_runner(         │ │        ┌──────────────────────┐
│  │   model="claude-opus-4-8", tools=tools)   │ │        │   api.github.com      │
│  │                                           │ │        │   (upstream REST)     │
│  │   LLM loop:                               │ │        └──────────────────────┘
│  │   ┌─────────────────────────────────────┐ │ │
│  │   │ Claude → "call list_pull_requests"  │ │ │     github_api.py mirrors this
│  │   │   ↓ tool call routed via ClientSession│ │ │     exact HTTPS call by hand:
│  │   │ GitHub MCP runs it → result          │ │ │       GET /repos/{owner}/{repo}/
│  │   │   ↓ result returned to Claude        │ │ │           pulls?state=…
│  │   │ Claude → text / next tool call       │ │ │       Authorization: Bearer <PAT>
│  │   └─────────────────────────────────────┘ │ │
│  │   loop until done                         │ │
│  └──────────────────────────────────────────┘ │
│                       │ text blocks            │
│                       ▼                         │
│                   print(block.text)            │
└──────────────────────────────────────────────┘
```

### Where `github_api.py` fits

`github_api.py` is **not imported** by any other file. It exists to show, in plain
`httpx`, the *upstream REST call* that the GitHub MCP server performs internally when
Claude invokes its `list_pull_requests` tool. Read it as the "under the hood" view of
one box in the diagram above.

```
  Claude tool call            GitHub MCP server                github_api.py shows
  "list_pull_requests"  ───▶  (does this internally)  ≈≈≈≈≈▶  GET /repos/{o}/{r}/pulls
                                                              Authorization: Bearer <PAT>
```

---

## 5. Secrets & trust boundaries

Every credential is read from the environment — none are hardcoded. This matches the
repo's `.claude/rules/security.md` baseline.

```
  Environment variable               Read in            Guards the boundary to
  ─────────────────────────────────────────────────────────────────────────────
  MCP_AUTH_TOKEN                     server.py          client → our server (/mcp)
  ANTHROPIC_API_KEY                  host.py            host  → Anthropic API
  GITHUB_PERSONAL_ACCESS_TOKEN       host.py            passed via Docker env →
                                     github_api.py        GitHub MCP / api.github.com
```

Trust boundaries crossed (each `║` is an authenticated hop):

```
   client.py  ║Bearer║  server.py
   host.py    ║API key║ Anthropic
   host.py    ║PAT/env║ GitHub MCP container ║PAT/HTTPS║ api.github.com
```

---

## 6. Transports at a glance

| Connection                       | Transport        | Auth                         |
|----------------------------------|------------------|------------------------------|
| `client.py` → `server.py`        | Streamable HTTP  | `Authorization: Bearer`      |
| `host.py` → GitHub MCP server    | stdio (subprocess)| PAT via Docker `-e` env      |
| GitHub MCP server → `api.github.com` | HTTPS         | PAT bearer header            |
| `host.py` → Anthropic API        | HTTPS            | `ANTHROPIC_API_KEY`          |

---

## 7. Packaging

[`stdio/Dockerfile`](./stdio/Dockerfile) containerizes **only Demo A's server**
(`http/server.py`):

```
  python:3.11-slim
     + uv (copied from astral-sh/uv image)
     + uv sync --frozen --no-dev   (needs pyproject.toml + uv.lock)
     + COPY server.py
     ▼
  CMD: uvicorn server:app --host 0.0.0.0 --port 8000   →   serves /mcp
```

> Note: the build copies `pyproject.toml` and `uv.lock`, which currently live at the
> repo root rather than in this directory — adjust the build context accordingly.

---

## 8. File-to-file reference summary

```
  client.py ───────HTTP /mcp──────▶ server.py ───────▶ lookup_permit()  [in-process]

  host.py ──spawn(stdio)──▶ GitHub MCP server ──HTTPS──▶ api.github.com

  github_api.py  ......... illustrative only; mirrors the GitHub MCP server's
                          internal REST call. Imported by nothing.

  Dockerfile  ............ wraps server.py only.
```
