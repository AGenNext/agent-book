"""
Open Notebook MCP Server

An MCP server that exposes Open Notebook capabilities to AI agents
for customer onboarding, assistance, and maximizing value from the platform.
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add the project root to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl
import asyncio

# Load environment
from dotenv import load_dotenv
load_dotenv()

from open_notebook.utils.encryption import get_secret_from_env


class OpenNotebookMCPServer:
    """MCP Server for Open Notebook functionality."""

    def __init__(self):
        self.server = Server("open-notebook-mcp")
        self._setup_handlers()
        self.api_base_url = os.getenv("API_URL", "http://localhost:5055")

    def _setup_handlers(self):
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return [
                # Notebooks
                Tool(
                    name="list_notebooks",
                    description="List all notebooks in Open Notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "order_by": {
                                "type": "string",
                                "description": "Sort order (default: updated desc)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number to return (default: 50)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_notebook",
                    description="Get details of a specific notebook by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "The notebook ID",
                            },
                        },
                        "required": ["notebook_id"],
                    },
                ),
                Tool(
                    name="create_notebook",
                    description="Create a new notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Notebook name",
                            },
                            "description": {
                                "type": "string",
                                "description": "Notebook description",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                # Sources
                Tool(
                    name="add_source",
                    description="Add a source (URL, PDF, text, or audio) to a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Target notebook ID",
                            },
                            "source_type": {
                                "type": "string",
                                "description": "Type: url, pdf, text, or audio",
                                "enum": ["url", "pdf", "text", "audio"],
                            },
                            "source_url": {
                                "type": "string",
                                "description": "URL or file path for the source",
                            },
                            "content": {
                                "type": "string",
                                "description": "Text content (for type=text)",
                            },
                            "title": {
                                "type": "string",
                                "description": "Title for the source",
                            },
                        },
                        "required": ["notebook_id", "source_type"],
                    },
                ),
                Tool(
                    name="list_sources",
                    description="List all sources in a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID",
                            },
                        },
                        "required": ["notebook_id"],
                    },
                ),
                # Notes
                Tool(
                    name="add_note",
                    description="Add a note to a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Target notebook ID",
                            },
                            "content": {
                                "type": "string",
                                "description": "Note content",
                            },
                            "title": {
                                "type": "string",
                                "description": "Note title (optional)",
                            },
                        },
                        "required": ["notebook_id", "content"],
                    },
                ),
                # Chat/QA
                Tool(
                    name="ask_question",
                    description="Ask a question about a notebook's content (RAG query)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID to query",
                            },
                            "question": {
                                "type": "string",
                                "description": "Question to ask",
                            },
                            "model": {
                                "type": "string",
                                "description": "Model to use (optional)",
                            },
                        },
                        "required": ["notebook_id", "question"],
                    },
                ),
                Tool(
                    name="chat_with_notebook",
                    description="Start or continue a chat session with a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID to chat with",
                            },
                            "message": {
                                "type": "string",
                                "description": "Chat message",
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session ID for continuing conversation (optional)",
                            },
                        },
                        "required": ["notebook_id", "message"],
                    },
                ),
                # Search
                Tool(
                    name="search_notebook",
                    description="Search within a notebook's content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID to search",
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "search_type": {
                                "type": "string",
                                "description": "text or vector",
                                "enum": ["text", "vector"],
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results (default: 10)",
                            },
                        },
                        "required": ["notebook_id", "query"],
                    },
                ),
                # Embeddings
                Tool(
                    name="rebuild_embeddings",
                    description="Rebuild embeddings for a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID",
                            },
                            "mode": {
                                "type": "string",
                                "description": "existing or all",
                                "enum": ["existing", "all"],
                            },
                        },
                        "required": ["notebook_id"],
                    },
                ),
                # Models
                Tool(
                    name="list_models",
                    description="List available AI models",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                # Settings
                Tool(
                    name="get_config",
                    description="Get current configuration settings",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="set_api_key",
                    description="Configure an API key for an AI provider",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Provider: openai, anthropic, google, groq, etc.",
                            },
                            "api_key": {
                                "type": "string",
                                "description": "API key",
                            },
                        },
                        "required": ["provider", "api_key"],
                    },
                ),
                # Podcast
                Tool(
                    name="generate_podcast",
                    description="Generate a podcast summary from a notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notebook_id": {
                                "type": "string",
                                "description": "Notebook ID",
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice for podcast (optional)",
                            },
                            "style": {
                                "type": "string",
                                "description": "Style: conversational or formal (optional)",
                            },
                        },
                        "required": ["notebook_id"],
                    },
                ),
                # Onboarding
                Tool(
                    name="onboard_user",
                    description="Guide a new user through onboarding",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_name": {
                                "type": "string",
                                "description": "User's name",
                            },
                            "use_case": {
                                "type": "string",
                                "description": "What they want to use the app for",
                            },
                        },
                        "required": ["user_name"],
                    },
                ),
                Tool(
                    name="get_help",
                    description="Get help and tips for using Open Notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic: notebooks, sources, chat, search, embeddings, podcasts",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _execute_tool(self, name: str, arguments: Any) -> Any:
        """Execute a tool call."""
        import httpx

        headers = self._get_auth_headers()

        async with httpx.AsyncClient(timeout=60.0) as client:
            if name == "list_notebooks":
                resp = await client.get(
                    f"{self.api_base_url}/notebooks",
                    headers=headers,
                    params=arguments,
                )
                return resp.json()

            elif name == "get_notebook":
                resp = await client.get(
                    f"{self.api_base_url}/notebooks/{arguments['notebook_id']}",
                    headers=headers,
                )
                return resp.json()

            elif name == "create_notebook":
                resp = await client.post(
                    f"{self.api_base_url}/notebooks",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "add_source":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/sources",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "list_sources":
                nb_id = arguments["notebook_id"]
                resp = await client.get(
                    f"{self.api_base_url}/notebooks/{nb_id}/sources",
                    headers=headers,
                )
                return resp.json()

            elif name == "add_note":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/notes",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "ask_question":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/ask",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "chat_with_notebook":
                nb_id = arguments.pop("notebook_id")
                session_id = arguments.get("session_id")
                if session_id:
                    resp = await client.post(
                        f"{self.api_base_url}/notebooks/{nb_id}/chat",
                        headers=headers,
                        params={"session_id": session_id},
                        json=arguments,
                    )
                else:
                    resp = await client.post(
                        f"{self.api_base_url}/notebooks/{nb_id}/chat",
                        headers=headers,
                        json=arguments,
                    )
                return resp.json()

            elif name == "search_notebook":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/search",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "rebuild_embeddings":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/embedding-rebuild",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "list_models":
                resp = await client.get(f"{self.api_base_url}/models", headers=headers)
                return resp.json()

            elif name == "get_config":
                resp = await client.get(f"{self.api_base_url}/config", headers=headers)
                return resp.json()

            elif name == "set_api_key":
                # Use credentials endpoint
                resp = await client.post(
                    f"{self.api_base_url}/credentials",
                    headers=headers,
                    json={
                        "name": f"{arguments['provider']}_key",
                        "provider": arguments["provider"],
                        "api_key": arguments["api_key"],
                    },
                )
                return resp.json()

            elif name == "generate_podcast":
                nb_id = arguments.pop("notebook_id")
                resp = await client.post(
                    f"{self.api_base_url}/notebooks/{nb_id}/podcast",
                    headers=headers,
                    json=arguments,
                )
                return resp.json()

            elif name == "onboard_user":
                return self._onboard_user(arguments)

            elif name == "get_help":
                return self._get_help(arguments.get("topic"))

            return {"error": f"Unknown tool: {name}"}

    def _get_auth_headers(self) -> dict:
        """Get authentication headers."""
        password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")
        if password:
            return {"Authorization": f"Bearer {password}"}
        return {}

    def _onboard_user(self, arguments: dict) -> dict:
        """Guide a new user through onboarding."""
        user_name = arguments.get("user_name", "User")
        use_case = arguments.get("use_case", "")

        guide = f"""# Welcome to Open Notebook, {user_name}! 🎉

I'm here to help you get started and get the most value from Open Notebook.

## Quick Start

1. **Create your first notebook** - Use `create_notebook` to organize your research
2. **Add sources** - Upload URLs, PDFs, text, or audio content
3. **Ask questions** - Use `ask_question` to query your sources with AI
4. **Chat with sources** - Start a conversation with `chat_with_notebook`

## What would you like to do?

- 📚 Research: Add sources and ask questions
- 🎙️ Podcast: Generate audio summaries
- 🔍 Search: Find content across notebooks

"""

        if use_case:
            guide += f"\n## Your goal: {use_case}\n\nI recommend starting by creating a notebook for this purpose."

        guide += """

## Pro Tips

- Use `search_notebook` to find specific information
- Rebuild embeddings if search results seem off
- Configure API keys with `set_api_key` for best results
- Generate podcasts to listen to your summaries on the go

What would you like to do first?
"""

        return {"onboarding_guide": guide, "user_name": user_name}

    def _get_help(self, topic: str = None) -> dict:
        """Get help for a specific topic."""
        topics = {
            "notebooks": """# Notebooks Help

Notebooks are containers for your research. They organize your sources, notes, and AI interactions.

**Commands:**
- `list_notebooks` - See all your notebooks
- `create_notebook` - Make a new notebook  
- `get_notebook` - View notebook details
- Add sources and notes to organize your research
""",
            "sources": """# Sources Help

Sources are the content you add to notebooks. You can add:
- URLs (web pages)
- PDFs (documents)
- Text (paste content)
- Audio (podcasts, recordings)

**Commands:**
- `add_source` - Add content to a notebook
- `list_sources` - See what's in a notebook
- Sources are processed and embedded for semantic search
""",
            "chat": """# Chat Help

Chat with your sources using AI-powered RAG (Retrieval Augmented Generation).

**Commands:**
- `ask_question` - Ask a single question
- `chat_with_notebook` - Have a conversation (remembers context)

**Tips:**
- Be specific in your questions
- Ask follow-up questions to dig deeper
- Use different models for different tasks
""",
            "search": """# Search Help

Search across your notebook content.

**Commands:**
- `search_notebook` - Text or vector search
- Use vector search for semantic queries
- Use text search for exact matches

**Tips:**
- Vector search finds conceptually similar content
- Adjust `limit` to get more/less results
""",
            "embeddings": """# Embeddings Help

Embeddings convert text into vector representations for semantic search.

**Commands:**
- `rebuild_embeddings` - Re-index notebook content

**When to rebuild:**
- After adding new sources
- If search results seem irrelevant
- Use `mode=existing` for quick updates
- Use `mode=all` for full rebuild
""",
            "podcasts": """# Podcasts Help

Generate podcast-style audio summaries of your notebooks.

**Commands:**
- `generate_podcast` - Create audio summary

**Tips:**
- Add more sources for richer summaries
- Choose voice and style options
- Great for learning on the go!
""",
        }

        if topic and topic in topics:
            return {"help": topics[topic]}
        elif topic:
            return {"help": f"Unknown topic: {topic}. Available: {list(topics.keys())}"}

        return {
            "help": """# Open Notebook Help

Available topics: notebooks, sources, chat, search, embeddings, podcasts

Use `get_help` with a topic to learn more!
"""
        }

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    server = OpenNotebookMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())