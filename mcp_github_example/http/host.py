# host.py  —  MCP host / LLM that drives our own HTTP server (server.py)
# uv add anthropic "anthropic[mcp]" mcp
#
# Mirror of ../stdio/host.py, but the client connects over Streamable HTTP
# (with a bearer token) instead of spawning a stdio subprocess. The agentic
# loop lives HERE, in the host — never in client.py (the dumb connector).
import asyncio
import os

from anthropic import AsyncAnthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

# Where server.py is listening, and the bearer token its BearerAuth middleware
# expects. The token is read from the environment, never hardcoded.
SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
AUTH_HEADERS = {"Authorization": f"Bearer {os.environ['MCP_AUTH_TOKEN']}"}


async def main(user_request: str) -> None:
    # Open an HTTP MCP client session to our server.py. This is the "client"
    # role — pure transport. The host wraps an LLM loop around it below.
    async with streamablehttp_client(SERVER_URL, headers=AUTH_HEADERS) as (read, write, _):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()

            # Discover server.py's tools (lookup_permit) and expose them to Claude.
            tools_result = await mcp.list_tools()
            tools = [async_mcp_tool(t, mcp) for t in tools_result.tools]

            # The agentic loop: Claude calls lookup_permit -> the MCP client
            # forwards it to server.py over HTTP -> result goes back to Claude
            # -> repeat until the model is done.
            runner = client.beta.messages.tool_runner(
                model="claude-opus-4-8",
                max_tokens=16000,
                thinking={"type": "adaptive"},
                tools=tools,
                messages=[{"role": "user", "content": user_request}],
            )
            async for message in runner:
                for block in message.content:
                    if block.type == "text":
                        print(block.text)


if __name__ == "__main__":
    asyncio.run(main("Look up permit P-12345 and tell me its status and history."))
