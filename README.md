# IssueMosaic

A reactive multi-agent system that triages and resolves GitLab issues using
**Gemini** as the reasoning brain and the **GitLab MCP server** as the data
spine. Built for the **Google Cloud Rapid Agent Hackathon** on Devpost
(deadline 2026-06-11, $60K prize pool, GitLab partner track).

```
issue posted ──▶ Triage agent ──▶ Resolution agent ──▶ Reviewer agent ──▶ plan + label
        │                                                                 │
        └─────── blackboard (reactive event bus) ────────────────────────┘
                          ▲
                          │ MCP tools
                          │ (list_issues, get_issue, post_comment, …)
                          ▼
                GitLab MCP server
```

## Why this fits the hackathon

| Hackathon criterion | How IssueMosaic answers it |
|---|---|
| **Powered by Gemini** | `GeminiLLM` backend (`src/issuemosaic/llm/gemini.py`) — drop-in `LLM` Protocol impl using `google-generativeai`. Falls back to `MockLLM` if `GOOGLE_API_KEY` is unset, so the project runs end-to-end offline. |
| **Google Cloud Agent Builder–ready** | Each agent exposes its `system_prompt` + `tool_spec` in the shape Agent Builder ingests (`src/issuemosaic/manifest.py`). One CLI command (`issuemosaic manifest`) prints the JSON to paste into the Agent Builder UI; same payload is served at `GET /api/manifest`. |
| **GitLab MCP integration** | `GitLabMCPClient` (`src/issuemosaic/mcp/client.py`) speaks the Model Context Protocol over HTTP. Includes a `MockMCPServer` (`src/issuemosaic/mcp/server.py`) so the demo runs without a real GitLab instance. |
| **Move beyond chat** | Agents post **comments**, **labels**, and **milestone updates** to GitLab via MCP — the system actually *does* the triage, not just *describes* it. |
| **Multi-step mission** | Orchestrator drives a 3-step plan: (1) Triage categorises, (2) Resolution drafts a plan, (3) Reviewer validates against project history. The loop is event-driven on the blackboard, not a static prompt chain. |
| **Eval/observability** | `FastAPI` dashboard (`issuemosaic serve` → `src/issuemosaic/api.py`) shows live trace: every event, every LLM call, every MCP roundtrip. Endpoints: `/api/health`, `/api/manifest`, `/api/trace`, `/api/triage`. |

## Project structure

```
issuemosaic/
├── src/issuemosaic/
│   ├── blackboard.py       # reactive event bus
│   ├── orchestrator.py     # multi-agent reactive loop
│   ├── cli.py              # `triage-all`, `serve`, `manifest` commands
│   ├── api.py              # FastAPI dashboard (live trace + manifest + triage)
│   ├── manifest.py         # builds the Agent Builder manifest from the live registry
│   ├── agents/
│   │   ├── base.py         # Agent protocol
│   │   ├── triage.py       # categorises incoming issues
│   │   ├── resolution.py   # drafts the resolution plan
│   │   └── reviewer.py     # validates against project history
│   ├── llm/
│   │   ├── base.py         # LLM Protocol
│   │   ├── mock.py         # offline mock (no API key needed)
│   │   └── gemini.py       # Gemini LLM (drops in when GOOGLE_API_KEY set)
│   ├── mcp/
│   │   ├── server.py       # in-process mock GitLab MCP server
│   │   └── client.py       # real GitLab MCP client (httpx) + factory
│   └── tools/
│       └── registry.py     # exposes MCP methods as AgentTools
├── tests/
│   ├── test_blackboard.py
│   ├── test_mcp_server.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   ├── test_api.py
│   ├── test_tools.py
│   ├── test_llm_mock.py
│   └── test_hackathon_criteria.py   # asserts the 6 README hackathon claims
├── pyproject.toml
└── README.md
```

## Quickstart

```bash
# 1. Install (mock mode — no API key needed)
uv venv
.venv/bin/pip install -e ".[dev]"

# 2. Run the test suite (offline, ~5s)
.venv/bin/pytest tests/

# 3. Run a triage run against the mock GitLab server
.venv/bin/issuemosaic triage-all --dry-run --json

# 4. Launch the live dashboard
.venv/bin/issuemosaic serve --port 8000
# open http://localhost:8000
```

### With a real Gemini key

```bash
export GOOGLE_API_KEY="…"
.venv/bin/issuemosaic triage-all
```

### With a real GitLab instance

```bash
export GITLAB_MCP_URL="https://your-mcp-server.example.com/sse"
export GITLAB_TOKEN="…"
.venv/bin/issuemosaic run --project mygroup/myproject
```

### Generate the Google Cloud Agent Builder manifest

```bash
.venv/bin/issuemosaic manifest --out manifest.json
# paste the contents into the Agent Builder UI as a new agent
```

## What gets submitted to the hackathon

1. **Hosted project URL** — the FastAPI dashboard, deployed to Vercel/Railway.
2. **Open-source repo** — this repo (MIT licensed, public).
3. **Demo video** — 2:30 walkthrough of a triage run + the live dashboard.
4. **What the agent does** — given a `new issue posted → webhook → triage → resolve → label`,
   IssueMosaic produces a triage label, a resolution plan comment, and an MR draft — all
   via MCP.

## License

MIT
