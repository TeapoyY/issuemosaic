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
| **Google Cloud Agent Builder–ready** | Each agent exposes its `system_prompt` + `tool_spec` in the shape Agent Builder ingests (`src/issuemosaic/agents/manifest.py`). One CLI command (`issuemosaic manifest`) prints the JSON to paste into the Agent Builder UI. |
| **GitLab MCP integration** | `GitLabMCPClient` (`src/issuemosaic/mcp/gitlab.py`) speaks the Model Context Protocol over HTTP. Includes a `MockMCPServer` so the demo runs without a real GitLab instance. |
| **Move beyond chat** | Agents post **comments**, **labels**, and **milestone updates** to GitLab via MCP — the system actually *does* the triage, not just *describes* it. |
| **Multi-step mission** | Orchestrator drives a 3-step plan: (1) Triage categorises, (2) Resolution drafts a plan, (3) Reviewer validates against project history. The loop is event-driven on the blackboard, not a static prompt chain. |
| **Eval/observability** | `FastAPI` dashboard (`issuemosaic dashboard`) shows live trace: every event, every LLM call, every MCP roundtrip. |

## Project structure

```
issuemosaic/
├── src/issuemosaic/
│   ├── blackboard.py       # reactive event bus
│   ├── orchestrator.py     # multi-agent reactive loop
│   ├── cli.py              # `run`, `dashboard`, `manifest` commands
│   ├── agents/
│   │   ├── base.py         # Agent protocol
│   │   ├── triage.py       # categorises incoming issues
│   │   ├── resolver.py     # drafts the resolution plan
│   │   └── reviewer.py     # validates against project history
│   ├── llm/
│   │   ├── base.py         # LLM Protocol
│   │   ├── mock.py         # offline mock (no API key needed)
│   │   └── gemini.py       # Gemini LLM (drops in when GOOGLE_API_KEY set)
│   ├── mcp/
│   │   ├── base.py         # MCPClient protocol
│   │   ├── mock.py         # in-process mock GitLab MCP server
│   │   └── gitlab.py       # real GitLab MCP client (httpx)
│   ├── tools/
│   │   └── registry.py     # exposes MCP methods as AgentTools
│   └── dashboard.py        # FastAPI live trace UI
├── tests/
│   ├── test_blackboard.py
│   ├── test_mcp.py
│   ├── test_agents.py
│   ├── test_e2e.py
│   └── test_gemini_adapter.py
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

# 3. Run a single triage run against the mock GitLab server
.venv/bin/issuemosaic run --project demo --mock-gitlab

# 4. Launch the live dashboard
.venv/bin/issuemosaic dashboard --port 8000
# open http://localhost:8000
```

### With a real Gemini key

```bash
export GOOGLE_API_KEY="…"
.venv/bin/issuemosaic run --project demo
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
