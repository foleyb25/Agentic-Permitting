# github_api.py  —  Example GitHub REST endpoint an MCP tool would wrap
# uv add httpx
import os

import httpx

GITHUB_API = "https://api.github.com"


async def list_pull_requests(owner: str, repo: str, state: str = "open") -> list[dict]:
    """GET /repos/{owner}/{repo}/pulls — the endpoint a 'list_pull_requests'
    MCP tool would wrap. The PAT is the entire authorization boundary."""
    headers = {
        "Authorization": f"Bearer {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(base_url=GITHUB_API, headers=headers, timeout=10) as client:
        resp = await client.get(f"/repos/{owner}/{repo}/pulls", params={"state": state})
        resp.raise_for_status()
        return [
            {"number": pr["number"], "title": pr["title"], "user": pr["user"]["login"]}
            for pr in resp.json()
        ]


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(list_pull_requests("octocat", "Hello-World")))
