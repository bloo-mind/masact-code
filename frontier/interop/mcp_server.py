"""The tool altitude (Section 22.3): a team tool as a real MCP server.

The Model Context Protocol (MCP) lets a tool describe itself once and be
called by any client that speaks the protocol. Here the Chapter 20 team's
tester --- the node that runs the suite against a proposed diff and reports
``green`` or ``red`` --- is lifted out of the team and published as a
standalone MCP tool. The wrapping is faithful to the book's tester: a
*checkable outcome*, not an opinion. Any MCP client (this repo's in-memory
client, an editor, another agent) can now call it.

Uses the real ``mcp`` package (``FastMCP``). Run as a module under
``__main__`` to serve over stdio --- the transport a parent process speaks
to a child MCP server.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def build_server() -> FastMCP:
    """Build the ``masact-team-tools`` MCP server with one tool."""
    mcp = FastMCP("masact-team-tools")

    @mcp.tool()
    def run_tests(diff: str) -> str:
        """Report 'green' or 'red' for a proposed diff.

        This is a FIXED STUB, not a real test suite: it stands in for the
        Chapter 20 tester across the MCP seam. The verdict is keyed
        deterministically on a marker token --- a diff carrying a
        ``return`` statement is treated as a substantive fix and reported
        green; anything without it is reported red. The point of the lab is
        the transport (any MCP client can call this same tool by name), not
        the fidelity of the checker behind it.
        """
        marker = "return"
        return "green" if marker in diff else "red"

    return mcp


if __name__ == "__main__":
    build_server().run(transport="stdio")
