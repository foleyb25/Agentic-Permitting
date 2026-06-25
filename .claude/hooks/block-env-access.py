#!/usr/bin/env python3
"""
PreToolUse hook: block reading or shell access to .env files.

Covers two surfaces:
  - File tools (Read, Edit, Write, MultiEdit): checks tool_input.file_path
  - Bash: checks tool_input.command for any .env reference (cat, source, grep, ...)

Reference files (.env.example / .sample / .template / .dist) are allowed.
Blocks via exit code 2: stderr is fed back to Claude as the reason.
"""
import json
import os
import re
import sys

# Suffixes that are safe to read (no secrets).
ALLOW_SUFFIXES = {"example", "sample", "template", "dist"}

# Matches `.env` or `.env.<suffix>` as a whole token (not e.g. `.environment`).
ENV_RE = re.compile(r"\.env(?:\.([A-Za-z0-9_-]+))?(?![A-Za-z0-9])")


def references_env(text: str) -> bool:
    if not text:
        return False
    for match in ENV_RE.finditer(text):
        suffix = match.group(1)
        if suffix and suffix.lower() in ALLOW_SUFFIXES:
            continue
        return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed input: don't block, let the normal flow handle it.
        sys.exit(0)

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if tool in ("Read", "Edit", "Write", "MultiEdit"):
        path = tool_input.get("file_path", "") or ""
        hit = references_env(os.path.basename(path)) or references_env(path)
    elif tool == "Bash":
        hit = references_env(tool_input.get("command", "") or "")
    else:
        hit = False

    if hit:
        sys.stderr.write(
            "Blocked by policy: access to .env files is not allowed. "
            "Read .env.example for the list of required variables, or ask the "
            "user to supply a specific value.\n"
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
