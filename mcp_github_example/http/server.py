# server.py  —  MCP server: single Streamable-HTTP endpoint, bearer auth
# uv add fastmcp starlette uvicorn python-dotenv
import hmac
import os
from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Load a project .env (searched upward from this file, so the repo-root .env is
# found regardless of cwd) into the environment BEFORE anything reads os.environ.
# The MCP Inspector spawns this server with only a safe subset of system env vars,
# so .env is how local config/secrets reach the server during `fastmcp dev`.
load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

mcp = FastMCP("permit-tools")

# Required only for the HTTP transport (BearerAuth below). Read lazily so the
# module still imports under `fastmcp dev` (stdio) without the env var set —
# stdio never goes through the middleware, so no token is needed to inspect tools.
EXPECTED_TOKEN = os.environ.get("MCP_AUTH_TOKEN")


@mcp.tool
async def lookup_permit(
    permit_id: Annotated[str, Field(description="The permit ID to fetch, e.g. 'P-12345'")],
    include_history: Annotated[bool, Field(description="Include status-change history")] = False,
) -> dict:
    """Fetch a permit by ID. The model fills in permit_id / include_history
    as tool arguments — those are the 'variables passed by the agent'."""
    if not permit_id.startswith("P-"):
        raise ToolError(f"Invalid permit id: {permit_id!r}")  # client-facing; no internals leaked
    history = [] if not include_history else [{"status": "submitted"}, {"status": "approved"}]
    return {"permit_id": permit_id, "status": "approved", "history": history}


class BearerAuth(BaseHTTPMiddleware):
    """Per-request credential — the OTHER kind of agent-passed variable: an HTTP
    header, validated server-side, never exposed as a tool parameter."""
    async def dispatch(self, request, call_next):
        if not EXPECTED_TOKEN:  # fail closed: HTTP transport must be configured
            return JSONResponse({"error": "server auth not configured"}, status_code=500)
        header = request.headers.get("authorization", "")
        if not hmac.compare_digest(header, f"Bearer {EXPECTED_TOKEN}"):  # constant-time
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


# One ASGI app, one endpoint at /mcp (Streamable HTTP), wrapped in auth.
app = mcp.http_app(path="/mcp")
app.add_middleware(BearerAuth)
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
