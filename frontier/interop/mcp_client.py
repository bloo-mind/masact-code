"""Calling an MCP tool (Section 22.3): in-memory and over stdio.

Two paths to the same tool. The *in-memory* path connects a client session
straight to the server's low-level object with no process boundary --- it
needs no subprocess and no network, so the hermetic test uses it. The
*stdio* path launches the server as a real child process and speaks the
protocol over its pipes --- the genuine cross-process case the book cares
about, kept here as a best-effort adapter.

The seam between them is the whole point of MCP: the call site is the same
tool name and arguments regardless of where the tool lives.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import (
    create_connected_server_and_client_session as connect,
)

from .mcp_server import build_server


async def call_in_memory(server: FastMCP, name: str, args: dict) -> str:
    """Call ``name`` on ``server`` with no process boundary.

    ``connect`` accepts the ``FastMCP`` object directly and unwraps it to
    its low-level server for us, so we hand it the public object rather than
    reaching for a private attribute. It wires a client session to the
    server, initialises it, and yields the client; we read the first text
    block of the tool result.
    """
    async with connect(server) as client:
        result = await client.call_tool(name, args)
        return result.content[0].text


def call_tool(name: str, args: dict) -> str:
    """Sync wrapper: call a tool on a fresh in-memory server."""
    return asyncio.run(call_in_memory(build_server(), name, args))


async def _call_over_stdio(name: str, args: dict) -> str:
    """Launch the server as a child process and call one tool."""
    params = StdioServerParameters(
        command="python", args=["-m", "frontier.interop.mcp_server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            result = await client.call_tool(name, args)
            return result.content[0].text


def call_tool_stdio(name: str, args: dict) -> str:
    """Sync wrapper for the real cross-process stdio path (best-effort)."""
    return asyncio.run(_call_over_stdio(name, args))
