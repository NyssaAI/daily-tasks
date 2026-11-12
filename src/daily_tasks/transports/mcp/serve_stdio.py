"""Responsibility: Run the MCP server over newline-delimited JSON-RPC on stdin and stdout.
Public interface:
`-- serve_stdio(server, reader, writer)
"""

from typing import TextIO

from daily_tasks.transports.mcp.mcp_server import McpServer


async def serve_stdio(server: McpServer, reader: TextIO, writer: TextIO) -> int:
    """Answer each request line until end of input, then return 0; blank lines are skipped."""
    for line in reader:
        text = line.strip()
        if not text:
            continue
        response = await server.handle(text)
        if response is not None:
            writer.write(response + "\n")
            writer.flush()
    return 0
