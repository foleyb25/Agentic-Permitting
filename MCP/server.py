# server.py  —  MCP server: single Streamable-HTTP endpoint, bearer auth
# uv add fastmcp starlette uvicorn
import os
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

mcp = FastMCP("permit-tools")

EXPECTED_TOKEN = os.environ["MCP_AUTH_TOKEN"]  # the server's expected bearer token


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
        header = request.headers.get("authorization", "")
        if header != f"Bearer {EXPECTED_TOKEN}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


# One ASGI app, one endpoint at /mcp (Streamable HTTP), wrapped in auth.
app = mcp.http_app(path="/mcp")
app.add_middleware(BearerAuth)
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
