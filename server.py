#!/usr/bin/env python3
"""
Slack MCP Server - Slack Community Data & Block Kit Generation

Provides LLM-friendly access to Slack community data and
tools for generating gorgeous Slack Block Kit posts.

Bare-bones version - works with JSON files, no database yet.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slack-mcp")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = Path.home()  # JSON files live in ~/


# =============================================================================
# Data Loading
# =============================================================================

def load_slack_data(json_path: Path) -> dict:
    """Load Slack extraction JSON"""
    if not json_path.exists():
        return {}
    with open(json_path) as f:
        return json.load(f)


def get_latest_extraction() -> Optional[Path]:
    """Find the most recent Slack extraction JSON in home directory"""
    # Look for common patterns: hemingway_*.json, slack_*.json, etc.
    patterns = ["hemingway_*.json", "slack_*.json", "*_slack_export.json"]
    candidates = []
    for pattern in patterns:
        candidates.extend(DATA_DIR.glob(pattern))

    if not candidates:
        return None
    # Sort by modification time, return newest
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


# =============================================================================
# Query Functions
# =============================================================================

def query_messages(data: dict, **filters) -> list:
    """
    Query messages with filters.

    Filters:
        channel: str - Channel name (e.g., '02-discussion')
        from_date: str - ISO date
        to_date: str - ISO date
        user: str - User name (partial match)
        search_text: str - Full-text search in message text
        has_replies: bool - Only threads with replies
        category: str - Message category (intro, ask, discussion, news, session)
    """
    messages = data.get("all_messages", [])
    results = []

    for msg in messages:
        # Channel filter
        if "channel" in filters:
            if filters["channel"] not in msg.get("channel_name", ""):
                continue

        # Date filters
        if "from_date" in filters or "to_date" in filters:
            ts = float(msg.get("ts", "0"))
            msg_date = datetime.fromtimestamp(ts)

            if "from_date" in filters:
                from_dt = datetime.fromisoformat(filters["from_date"])
                if msg_date < from_dt:
                    continue

            if "to_date" in filters:
                to_dt = datetime.fromisoformat(filters["to_date"])
                if msg_date > to_dt:
                    continue

        # User filter
        if "user" in filters:
            user_name = msg.get("user_name", "").lower()
            if filters["user"].lower() not in user_name:
                continue

        # Text search
        if "search_text" in filters:
            text = msg.get("text", "").lower()
            if filters["search_text"].lower() not in text:
                continue

        # Has replies filter
        if "has_replies" in filters:
            has_replies = msg.get("reply_count", 0) > 0
            if filters["has_replies"] != has_replies:
                continue

        # Category filter (simple channel mapping for now)
        if "category" in filters:
            category = filters["category"].lower()
            channel = msg.get("channel_name", "")

            # Map categories to channels
            category_map = {
                "intro": "07-intros",
                "ask": "05-asks",
                "discussion": "02-discussion",
                "news": "03-news",
                "session": "09-00-hemingway-sessions"
            }

            if category in category_map:
                if category_map[category] not in channel:
                    continue

        results.append(msg)

    return results


def get_new_members(data: dict, from_date: str = None, to_date: str = None) -> list:
    """Get new members who joined in date range"""
    members = data.get("new_members", [])

    if not from_date and not to_date:
        return members

    results = []
    for member in members:
        ts = float(member.get("ts", "0"))
        member_date = datetime.fromtimestamp(ts)

        if from_date:
            from_dt = datetime.fromisoformat(from_date)
            if member_date < from_dt:
                continue

        if to_date:
            to_dt = datetime.fromisoformat(to_date)
            if member_date > to_dt:
                continue

        results.append(member)

    return results


# =============================================================================
# Block Kit Builders
# =============================================================================

def build_header_block(text: str, emoji: bool = True) -> dict:
    """Generate Slack header block"""
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": emoji
        }
    }


def build_section_block(text: str, markdown: bool = True) -> dict:
    """Generate Slack section block"""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn" if markdown else "plain_text",
            "text": text
        }
    }


def build_divider_block() -> dict:
    """Generate Slack divider block"""
    return {"type": "divider"}


def build_button_block(text: str, url: str, action_id: str = "button") -> dict:
    """Generate Slack button action block"""
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True
                },
                "url": url,
                "action_id": action_id
            }
        ]
    }


def build_context_block(elements: list) -> dict:
    """Generate Slack context block"""
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": el} for el in elements
        ]
    }


# =============================================================================
# MCP Server
# =============================================================================

server = Server("slack-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # Data Query Tools
        Tool(
            name="query_messages",
            description="Query messages from Slack community. Returns list of messages matching filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name (e.g., '02-discussion', '05-asks', '07-intros')"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date (ISO format: YYYY-MM-DD)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date (ISO format: YYYY-MM-DD)"
                    },
                    "user": {
                        "type": "string",
                        "description": "User name (partial match)"
                    },
                    "search_text": {
                        "type": "string",
                        "description": "Search in message text (full-text search)"
                    },
                    "has_replies": {
                        "type": "boolean",
                        "description": "Only return threads with replies"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["intro", "ask", "discussion", "news", "session"],
                        "description": "Filter by message category"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_new_members",
            description="Get new members who joined the Slack community in a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_date": {
                        "type": "string",
                        "description": "Start date (ISO format: YYYY-MM-DD)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date (ISO format: YYYY-MM-DD)"
                    }
                }
            }
        ),
        Tool(
            name="get_channel_stats",
            description="Get activity statistics for channels in a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_date": {"type": "string"},
                    "to_date": {"type": "string"}
                }
            }
        ),

        # Block Kit Generation Tools
        Tool(
            name="build_header",
            description="Generate a Slack Block Kit header block",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Header text"},
                    "emoji": {"type": "boolean", "description": "Enable emoji (default: true)", "default": True}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="build_section",
            description="Generate a Slack Block Kit section block with text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Section text (supports markdown)"},
                    "markdown": {"type": "boolean", "description": "Use markdown formatting (default: true)", "default": True}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="build_divider",
            description="Generate a Slack Block Kit divider (horizontal line)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="build_button",
            description="Generate a Slack Block Kit button with link",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Button text"},
                    "url": {"type": "string", "description": "Button URL"},
                    "action_id": {"type": "string", "description": "Action ID (default: 'button')", "default": "button"}
                },
                "required": ["text", "url"]
            }
        ),
        Tool(
            name="build_context",
            description="Generate a Slack Block Kit context block (small gray text)",
            inputSchema={
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of context text elements"
                    }
                },
                "required": ["elements"]
            }
        ),

        # Utility Tools
        Tool(
            name="get_extraction_info",
            description="Get information about the current Slack data extraction",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # Load data (find latest extraction)
        data_file = get_latest_extraction()
        if not data_file:
            return [TextContent(
                type="text",
                text="No Slack extraction data found. Expected hemingway_*.json in home directory."
            )]

        data = load_slack_data(data_file)

        # Data Query Tools
        if name == "query_messages":
            limit = arguments.pop("limit", 50)
            messages = query_messages(data, **arguments)[:limit]

            # Simplify output - only include relevant fields
            simplified = []
            for msg in messages:
                simplified.append({
                    "user": msg.get("user_name", "Unknown"),
                    "channel": msg.get("channel_name", ""),
                    "text": msg.get("text", "")[:200],  # Truncate long messages
                    "timestamp": msg.get("ts", ""),
                    "reply_count": msg.get("reply_count", 0),
                    "permalink": f"https://hemingway-community.slack.com/archives/{msg.get('channel_id')}/p{msg.get('ts', '').replace('.', '')}"
                })

            return [TextContent(
                type="text",
                text=json.dumps(simplified, indent=2)
            )]

        elif name == "get_new_members":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            members = get_new_members(data, from_date, to_date)

            # Simplify output
            simplified = [
                {
                    "name": m.get("name", "Unknown"),
                    "intro_text": m.get("text", "")[:200],
                    "permalink": m.get("permalink", ""),
                    "joined_date": datetime.fromtimestamp(float(m.get("ts", "0"))).strftime("%Y-%m-%d")
                }
                for m in members
            ]

            return [TextContent(
                type="text",
                text=json.dumps(simplified, indent=2)
            )]

        elif name == "get_channel_stats":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")

            # Get all messages in date range
            messages = query_messages(
                data,
                from_date=from_date,
                to_date=to_date
            )

            # Count by channel
            stats = {}
            for msg in messages:
                channel = msg.get("channel_name", "unknown")
                stats[channel] = stats.get(channel, 0) + 1

            # Sort by activity
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

            return [TextContent(
                type="text",
                text=json.dumps(dict(sorted_stats), indent=2)
            )]

        elif name == "get_extraction_info":
            info = {
                "data_file": str(data_file),
                "workspace": data.get("workspace", "unknown"),
                "extracted_at": data.get("extracted_at", "unknown"),
                "time_range": data.get("time_range", {}),
                "total_messages": len(data.get("all_messages", [])),
                "total_channels": len(data.get("channels", [])),
                "total_users": len(data.get("users", [])),
                "new_members": len(data.get("new_members", []))
            }
            return [TextContent(
                type="text",
                text=json.dumps(info, indent=2)
            )]

        # Block Kit Building Tools
        elif name == "build_header":
            block = build_header_block(
                arguments["text"],
                arguments.get("emoji", True)
            )
            return [TextContent(type="text", text=json.dumps(block, indent=2))]

        elif name == "build_section":
            block = build_section_block(
                arguments["text"],
                arguments.get("markdown", True)
            )
            return [TextContent(type="text", text=json.dumps(block, indent=2))]

        elif name == "build_divider":
            block = build_divider_block()
            return [TextContent(type="text", text=json.dumps(block, indent=2))]

        elif name == "build_button":
            block = build_button_block(
                arguments["text"],
                arguments["url"],
                arguments.get("action_id", "button")
            )
            return [TextContent(type="text", text=json.dumps(block, indent=2))]

        elif name == "build_context":
            block = build_context_block(arguments["elements"])
            return [TextContent(type="text", text=json.dumps(block, indent=2))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception(f"Error in {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
