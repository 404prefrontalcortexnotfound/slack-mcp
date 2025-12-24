# Slack MCP Server

**Slack Community Data & Block Kit Generation for LLMs**

An MCP (Model Context Protocol) server that provides Claude and other LLMs with tools to query Slack community data and generate Slack Block Kit posts.

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

**Bazel:**
```bash
# Install Bazel (if not already installed)
# See: https://bazel.build/install
```

**Python dependencies:**
```bash
pip install -r requirements.txt
```

### Build with Bazel

```bash
# Build the server
bazel build //:server

# Run the server
bazel run //:server
```

### Add to Claude Code

Add to your MCP config file (`.mcp.json` in project root):
```json
{
  "mcpServers": {
    "slack-mcp": {
      "type": "stdio",
      "command": "bazel",
      "args": [
        "run",
        "--ui_event_filters=-info,-stdout,-stderr",
        "--noshow_progress",
        "//:server"
      ],
      "cwd": "/absolute/path/to/slack-mcp",
      "description": "Slack community data & Block Kit generation"
    }
  }
}
```

**Alternative (direct Python):**
```json
{
  "mcpServers": {
    "slack-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["/absolute/path/to/slack-mcp/server.py"],
      "description": "Slack community data & Block Kit generation"
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
    "user": "User Name",
    "channel": "02-discussion",
    "text": "Discussion text...",
    "timestamp": "1734567890.123456",
    "reply_count": 5,
    "permalink": "https://workspace.slack.com/archives/..."
  }
]
```

### Get New Members
```
Use get_new_members to see who joined between Dec 15 and Dec 24
```

### Build Block Kit
```
Use build_section to create a section with:
"*Topic Title*\n\nDescription text here..."
```

Result:
```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "*Topic Title*\n\nDescription text here..."
  }
}
```

## Data Source

The server automatically finds the most recent Slack extraction JSON in your home directory.

**Supported patterns:**
- `hemingway_*.json`
- `slack_*.json`
- `*_slack_export.json`

**Workflow:**
1. Export Slack data to JSON (using your extraction script)
2. Place JSON file in home directory
3. MCP server auto-discovers and uses latest file
4. Query and build posts using MCP tools

## Architecture

**Current (Bare-bones MVP):**
- ✅ Bazel build system
- ✅ Reads JSON files directly
- ✅ No database (file-based)
- ✅ Works with any Slack community
- ✅ Generic Block Kit generation

**Future (Production):**
- PostgreSQL database with persistent storage
- Granular Bazel workers for each operation
- Incremental sync (cron job, not full re-extraction)
- Automated content generation and deployment
- Multi-community support

## Bazel Structure

```
slack-mcp/
├── MODULE.bazel          # Bazel module config (Bzlmod)
├── WORKSPACE.bazel       # Bazel workspace (compatibility)
├── BUILD.bazel           # Build targets
├── requirements.txt      # Python dependencies
├── requirements_lock.txt # Locked dependencies
└── server.py             # MCP server implementation
```

### Build Targets

```bash
# Build server binary
bazel build //:server

# Run server (for testing)
bazel run //:server

# Clean build artifacts
bazel clean
```

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

### Running Locally (Development Mode)
```bash
# Direct Python execution (no Bazel)
python3 server.py
```

### Testing
```bash
# Test server imports
python3 -c "from server import query_messages, build_section_block; print('OK')"

# Test with Bazel
bazel test //... # (when tests are added)
```

### Adding Dependencies
```bash
# Add to requirements.txt
echo "new-package>=1.0.0" >> requirements.txt

# Regenerate lock file
pip-compile requirements.txt --output-file=requirements_lock.txt

# Rebuild
bazel build //:server
```

## Troubleshooting

### "No Slack extraction data found"
Make sure you have a compatible JSON file in your home directory:
- `~/hemingway_*.json`
- `~/slack_*.json`
- `~/*_slack_export.json`

### Server not appearing in Claude Code
1. Check `.mcp.json` syntax (valid JSON)
2. Restart Claude Code completely
3. Verify paths are absolute (not relative)
4. Check Bazel is in PATH (`which bazel`)

### Bazel build errors
```bash
# Clean and rebuild
bazel clean --expunge
bazel build //:server

# Check Python version
bazel run @python_3_11//:python -- --version
```

### Import errors
```bash
pip install --upgrade mcp
pip-compile requirements.txt --output-file=requirements_lock.txt
```

## Contributing

This is a generic Slack MCP server for community automation projects.

### Development Workflow
1. Make changes to `server.py`
2. Test locally: `python3 server.py`
3. Build with Bazel: `bazel build //:server`
4. Commit and push

## License

MIT

---

**Status:** Bare-bones MVP with Bazel build system
**Next:** Database integration, workers, automation
