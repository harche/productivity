# Conversation Transcript Parsing

Claude Code conversation transcripts are stored as `.jsonl` files — one JSON object per line.

## File Location

Transcripts live under `~/.claude/projects/` in directories named after the working directory path (with `-` replacing `/`). Each conversation is a separate `.jsonl` file named with a UUID.

Example: `~/.claude/projects/-Users-harpatil-repos-cri-o/8d543f52-974a-49cb-a043-0753f582beca.jsonl`

## Finding the Current Conversation's JSONL

Claude Code stores session metadata at `~/.claude/sessions/<PID>.json`, where PID is the Claude Code process ID. From a Bash tool call, `$PPID` is the Claude Code PID.

The session file contains:

```json
{
  "pid": 80119,
  "sessionId": "2c3bcb84-11d0-4eb6-9354-25cc789f8f3c",
  "cwd": "/Users/harpatil/repos/cri-o",
  "startedAt": 1775221788405,
  "kind": "interactive",
  "entrypoint": "cli"
}
```

### One-liner to resolve the current conversation's JSONL path

```bash
CONVERSATION_JSONL=$(python3 -c "
import json, os
s = json.load(open(os.path.expanduser(f'~/.claude/sessions/{os.getppid()}.json')))
cwd = s['cwd'].replace('/', '-')
print(f\"{os.path.expanduser('~')}/.claude/projects/{cwd}/{s['sessionId']}.jsonl\")
")
```

When the user asks to ingest "this conversation", use this method to resolve the JSONL path automatically instead of guessing by timestamp.

## JSONL Structure

Each line is a JSON object. The `type` field determines what it is:

| type | What it is |
|------|-----------|
| `user` | User message |
| `assistant` | Assistant response |
| `system` | System message (command output, tool results) |
| `file-history-snapshot` | File state snapshot (skip these) |

### Extracting Text from Messages

For `user` and `assistant` types, the actual content is nested:

```
line.message.content → string or array
```

If `content` is a string, use it directly. If it's an array, look for objects where `type` is `text` and extract the `text` field.

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "text", "text": "The actual response text..."},
      {"type": "tool_use", "name": "Bash", "input": {"command": "..."}}
    ]
  }
}
```

### Messages to Skip

These are noise — skip them during extraction:

- Lines where `type` is `file-history-snapshot`
- Lines where `type` is `system`
- Text starting with `<local-command-caveat>` — these are auto-generated wrappers for local commands
- Text starting with `<command-name>` or `<command-message>` — skill invocation metadata
- Text starting with `<bash-input>` or `<bash-stdout>` or `<bash-stderr>` — terminal I/O
- Text starting with `<task-notification` — background task status
- Text starting with `Base directory for this skill` — skill loading boilerplate
- Text that is `[Request interrupted by user]` — aborted actions

### What to Extract

Focus on messages that contain:

1. **User questions and requests** — what was the user trying to do?
2. **Assistant findings and analysis** — what did Claude discover?
3. **Technical details** — commands, configurations, YAML, metrics, data tables
4. **Decisions** — what was decided and why?
5. **URLs and references** — links to issues, PRs, docs, tickets

### Synthesis, Not Transcription

After extracting the messages, synthesize them into a structured document organized by topic. The goal is a document that someone can read independently and understand the findings without needing the original conversation.

A good synthesized document has:
- Clear section headings for each topic covered
- Key findings stated as facts (not "Claude said..." or "the user asked...")
- Evidence: actual data, metrics, commands, configurations
- All links preserved with context about what they point to
- Decisions and their rationale
