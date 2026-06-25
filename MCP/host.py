# host.py  —  MCP host / LLM that talks to a GitHub MCP server
# uv add anthropic "anthropic[mcp]" mcp
import asyncio
import os

from anthropic import AsyncAnthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

# Launch the official GitHub MCP server locally (stdio). The PAT is passed
# through Docker's env, never embedded in the image or args.
GITHUB_MCP = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
          "ghcr.io/github/github-mcp-server"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]},
)


async def main(user_request: str) -> None:
    async with stdio_client(GITHUB_MCP) as (read, write):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()

            # Discover the GitHub MCP tools and expose them to Claude.
            tools_result = await mcp.list_tools()
            tools = [async_mcp_tool(t, mcp) for t in tools_result.tools]

            # The tool runner loops: Claude calls a GitHub tool -> the MCP server
            # runs it against github.com -> result goes back to Claude -> repeat.
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
    asyncio.run(main("List my 3 most recently updated repos and their open PR counts."))
