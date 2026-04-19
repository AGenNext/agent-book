"""
Open Notebook MCP Package

Exposes Open Notebook capabilities via MCP protocol for AI agents.
Integrates with Slack, WhatsApp, and Discord for customer onboarding.
"""

from mcp.server import Server
from mcp.messaging import (
    Platform,
    InboundMessage,
    OutboundMessage,
    MessagingRouter,
)

__version__ = "1.0.0"

__all__ = [
    "Server",
    "Platform",
    "InboundMessage", 
    "OutboundMessage",
    "MessagingRouter",
]