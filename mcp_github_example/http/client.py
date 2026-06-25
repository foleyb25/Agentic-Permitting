# client.py  —  MCP client connecting to the single /mcp endpoint with a bearer token
# uv add fastmcp
import asyncio

from fastmcp import Client


async def main() -> None:
    # Single endpoint + the auth header the server checks.
    async with Client("http://localhost:8000/mcp", auth="my-secret-token") as client:
        result = await client.call_tool(
            "lookup_permit", {"permit_id": "P-12345", "include_history": True}
        )
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
