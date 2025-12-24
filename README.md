# Hemingway MCP Server

**Slack Community Data & Block Kit Generation for LLMs**

An MCP (Model Context Protocol) server that provides Claude and other LLMs with tools to query Hemingway Slack community data and generate gorgeous Slack Block Kit posts.

## Features

### Data Query Tools
- `query_messages` - Query messages with filters (channel, date range, user, text search, category)
- `get_new_members` - Get new members who joined in a date range
- `get_channel_stats` - Activity statistics by channel
- `get_extraction_info` - Information about current data extraction

### Block Kit Generation Tools
- `build_header` - Generate header blocks
- `build_section` - Generate section blocks (with markdown support)
- `build_divider` - Generate divider blocks
- `build_button` - Generate button blocks with URLs
- `build_context` - Generate context blocks (small gray text)

## Installation

### Prerequisites
```bash
pip install -r requirements.txt
```

### Add to Claude Code

Add to your MCP config file (`.mcp.json` in project root or `~/.mcp.json`):
```json
{
  "mcpServers": {
    "hemingway-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": [
        "/absolute/path/to/hemingway-mcp/server.py"
      ],
      "description": "Hemingway Slack community data & Block Kit generation"
    }
  }
}
```

Restart Claude Code to load the server.

## Usage

### Query Messages
```
Use query_messages to find all discussions about "FDA" from Dec 15-24
```

Result:
```json
[
  {
    "user": "Acacia Parks",
    "channel": "02-discussion",
    "text": "FDA TEMPO programme clarification...",
    "timestamp": "1734567890.123456",
    "reply_count": 5,
    "permalink": "https://hemingway-community.slack.com/archives/..."
  }
]
```

### Get New Members
```
Use get_new_members to see who joined between Dec 15 and Dec 24
```

### Build Block Kit
```
Use build_section to create a section with this text:
"*FDA TEMPO Programme*\n\nAcacia Parks clarified how TEMPO works..."
```

Result:
```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "*FDA TEMPO Programme*\n\nAcacia Parks clarified how TEMPO works..."
  }
}
```

## Data Source

The server automatically finds the most recent `hemingway_*.json` file in your home directory.

**Current workflow:**
1. Run extraction script to generate JSON file
2. MCP server reads this file automatically
3. Query and build posts using MCP tools

## Architecture

**Current (Bare-bones MVP):**
- Reads JSON files directly
- No database
- Perfect for rapid prototyping
- Works immediately with existing data

**Future (Production):**
- PostgreSQL database with persistent storage
- Granular Bazel workers for each operation
- Incremental sync (cron job, not full re-extraction)
- Automated content generation and deployment
- See architecture docs for full plan

## Block Kit Tips

### Traffic Director Pattern
When building weekly digest posts:
- Link to original threads (not summaries)
- Motivating content: WHO + WHAT + WHY YOU SHOULD CARE
- Varied CTAs - never repeat the same call-to-action
- Inline links: `<permalink|CTA text>` format
- Purposeful emoji: 1-2 per section header max
- Scannable copy: One-liners, not walls of text

### Slack Markdown Formatting
- Bold: `*text*`
- Italic: `_text_`
- Strikethrough: `~text~`
- Code: `` `text` ``
- Link: `<url|link text>`
- Permalink: `<https://slack-url/p123456|Read more>`

## Development

### Running Locally
```bash
python3 server.py
```

The server runs in stdio mode for MCP communication.

### Testing
Test individual functions:
```python
from server import query_messages, build_section_block
# Test your queries here
```

## Troubleshooting

### "No Slack extraction data found"
Make sure you have a `hemingway_*.json` file in your home directory.

### Server not appearing in Claude Code
1. Check `.mcp.json` syntax (valid JSON)
2. Restart Claude Code completely
3. Verify absolute path to `server.py` is correct

### Import errors
```bash
pip install --upgrade mcp
```

## Contributing

This is a standalone MCP server for the Hemingway community automation project.

## License

MIT

---

**Status:** Bare-bones MVP (works with JSON files)
**Next:** Database integration, workers, automation
