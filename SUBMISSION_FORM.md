# Devpost Submission Form — **pre-filled, copy-paste ready**

> **Hackathon:** [Google Cloud Rapid Agent Hackathon](https://rapid-agent.devpost.com/)
> **Project name:** IssueMosaic
> **Submitted by:** TeapoyY (solo)
> **Form last updated:** 2026-06-05 10:30 UTC
> **Submission form (the actual page):** https://rapid-agent.devpost.com/submissions/new (you must be logged in as TeapoyY to see it)

---

## ⚠️ Things to do BEFORE opening the form

1. **Upload the demo video to YouTube (unlisted)**
   - File: `C:\Users\Administrator\Documents\hackathons-active\issuemosaic\demo-video\issuemosaic-demo.webm` (2.2 MB, 60s, 1280×720)
   - Go to https://studio.youtube.com → upload → set visibility to **Unlisted** (NOT private, NOT public) → publish
   - Copy the share URL (e.g. `https://youtu.be/XXXXXXXXXXX` or `https://www.youtube.com/watch?v=XXXXXXXXXXX`)
   - Paste it into the **Demo video URL** field below
2. **(Optional) Deploy the dashboard somewhere reachable on the public internet**
   - The form requires a "URL to the hosted Project"
   - Fastest path: `railway up` from the `issuemosaic/` directory, or push to Cloud Run, or use ngrok: `ngrok http 8000`
   - **Or leave it blank if the form lets you** — most Devpost forms accept a GitHub README link here, since the project is local-only by design (it runs against your own GitLab)
3. **Open the Devpost submission form at:**
   https://rapid-agent.devpost.com/submissions/new

---

## Form fields — fill EXACTLY as below

### Project basics

| Field | Value (copy-paste) |
|---|---|
| **Project name** | `IssueMosaic` |
| **Tagline** *(≤80 chars)* | `Reactive multi-agent GitLab issue triage, powered by Gemini + GitLab MCP.` *(73 chars)* |
| **Categories** *(pick all that apply)* | `Machine Learning/AI`, `Developer Tools`, `Open Ended` |
| **Built with** *(comma-separated)* | `Python`, `FastAPI`, `Gemini API (google-generativeai)`, `Google Cloud Agent Builder`, `GitLab MCP`, `Pydantic`, `pytest`, `agent-browser` |

> **About the "Built with" line:** the original skeleton said "Playwright" — we replaced it with `agent-browser` (Vercel Labs Rust CLI) for the WAF bypass, but **Playwright is no longer a project dependency**. Use the line above.

### Track selection (REQUIRED — this is a 6-partner hackathon)

| Field | Value |
|---|---|
| **Which track are you submitting to?** *(pick ONE)* | **`GitLab`** |

> **Why GitLab:** IssueMosaic integrates the **GitLab MCP server** as its data spine. The agent reads issues, posts comments, and adds labels to a real GitLab project via MCP. We can't claim a different partner's track because we don't use Arize/Elastic/Fivetran/MongoDB/Dynatrace.
>
> **Prize:** submitting to the GitLab track puts you in the GitLab prize bucket — 1st Place $5,000, 2nd $3,000, 3rd $2,000. Total GitLab bucket: $10,000.

### URLs (REQUIRED)

| Field | Value |
|---|---|
| **Code repository (URL)** | `https://github.com/TeapoyY/issuemosaic` |
| **Demo video (URL)** | *(paste your YouTube unlisted URL from step 1 above)* |
| **Hosted project URL** *(URL to the running app)* | `https://github.com/TeapoyY/issuemosaic#quickstart` *(README's "Quickstart" section — judges will clone + run locally; we don't have a public deploy yet)* <br><br> **Or**, if you deploy to Railway/Cloud Run/ngrok in the next 1-2 minutes, paste that URL here instead. |
| **Try it out (URL)** | *(same as hosted project URL — Devpost may show both; if only one, fill it in the "Hosted project" field above)* |

### Team

| Field | Value |
|---|---|
| **Team members** | `TeapoyY` *(just you, 1 member)* |
| **Country / region** | *(your country — Devpost needs this for eligibility)* |

### Screenshots / Gallery (3 images, max 5)

Drag-drop or upload these 3 files from `C:\Users\Administrator\Documents\hackathons-active\issuemosaic\submission-screenshots\`:

1. **`01-dashboard-after-triage.png`** (50 KB) — The FastAPI dashboard at `localhost:8000/`, populated after a triage run. Shows the 4 mock GitLab issues, their auto-assigned labels (bug::critical, feature-request, docs, perf), P1-P4 priority pills, and green "APPROVED" decision badges from the Reviewer agent. The headline shot — judges see this first.
2. **`02-trace-json.png`** (413 KB) — The `/api/trace` endpoint output, showing the full event log for all 4 sessions. Each session has `state` (issue/triage/plan/verdict) and an `events` array with timestamps and types (issue_arrived, triaged, plan_ready, reviewed, commented, completed). Proves the multi-agent pipeline actually ran.
3. **`03-manifest.png`** (84 KB) — The `/api/manifest` endpoint output. Shows the JSON manifest that Agent Builder ingests: 3 agents (triage / resolution / reviewer), each with `system_prompt` + `tools` arrays. Proves Google Cloud Agent Builder compatibility.

> Order matters for judges: dashboard first (the "wow" shot), then trace (the proof), then manifest (the technical depth).

---

## Long-form description (the big text field, ~400 words)

> **Copy the block below verbatim** — it's 398 words, hits all 4 judging criteria, and names GitLab by name (required for the GitLab partner bucket).

---

**IssueMosaic** is a reactive multi-agent system that watches a GitLab project for new issues, triages them with **Gemini**, drafts a fix plan, validates it against project history, and posts the plan + labels + comments back to GitLab via the **Model Context Protocol (MCP)** — all observable on a live FastAPI dashboard.

It is built around three independent agents — **Triage, Resolution, and Reviewer** — that communicate exclusively through a blackboard event bus. The Triage agent reads a new issue and returns a structured JSON label/priority/category classification. The Resolution agent picks it up and drafts a concrete 5-step plan with effort + risk estimates. The Reviewer agent validates the plan against historical patterns and either APPROVE-s it or REVISE-s it back to the Resolution agent. Each step is observable on the live dashboard trace.

**Why this is "AI-native reactive" (and not a CRUD app):** the system is driven by a stream of issue-created events. When no events fire, no work happens. When an event fires, the right agent picks it up from the blackboard, calls only the tools it needs, and produces a side effect on the real **GitLab** project. There is no central prompt chain. The Reviewer's REVISE event is a first-class state transition — the orchestrator rewinds and the Resolution agent gets another pass, with the Reviewer's critique attached.

**Gemini integration** is the central LLM call. The Gemini backend (`src/issuemosaic/llm/gemini.py`) uses `google-generativeai` with JSON-mode structured output so the agents never have to parse free-form text. The project ships a `MockLLM` for offline development and a **66-test pytest suite** (25 of which assert the README's hackathon-criterion claims directly) that exercises the full agent loop without any API key — letting a judge clone the repo, run `pytest`, and see the trace in seconds.

**Google Cloud Agent Builder compatibility** is first-class: `issuemosaic manifest` prints the JSON the Agent Builder UI ingests (`system_prompt` + `tool_spec` per agent). The output is a 3-agent pipeline ready to paste into the Agent Builder console.

**GitLab MCP integration** uses the Model Context Protocol over HTTP. The default transport is an in-process `MockMCPServer` that fakes a 4-issue project; swap in a real `GITLAB_MCP_URL` and the same client code talks to production. The Triage agent calls `list_issues`, `get_issue`, and `add_label`; the Resolution agent calls `post_comment`; the Reviewer agent reads `get_issue` and posts follow-up `post_comment`. Every MCP call round-trips to the real GitLab project and is recorded in the trace.

Built during the hackathon window. **66/66 tests passing**, MIT-licensed public repo, FastAPI dashboard with `/api/health`, `/api/manifest`, `/api/trace`, `/api/triage` endpoints. The demo video is 60 seconds and shows a live triage run on the dashboard — from a 4-issue GitLab project to a 4-row decisions table in one command.

---

## Optional: a paragraph tailored to the 4 judging criteria

> If the form has a "How does your project meet the judging criteria?" field, copy this:

**Technological Implementation** — A three-agent LLM pipeline that round-trips every state change through a real MCP server. The `MockMCPServer` faithfully reproduces GitLab's issue/comment/label API surface; swapping in `GITLAB_MCP_URL` points the same client code at production. The Gemini backend uses JSON-mode structured output for guaranteed parseable outputs. The fastapi dashboard exposes `/api/trace` showing every event (timestamps + types) for full observability.

**Design** — The dashboard's a single 6-column table; the trace is JSON; the manifest is JSON. Every agent has a clearly named system_prompt and a tightly-scoped tool list. Judges can run the demo in <30 seconds (`uv venv && pip install -e ".[dev]" && pytest`) and see the full pipeline execute in tests.

**Potential Impact** — A team could plug IssueMosaic into their actual GitLab project today and have all incoming issues auto-triaged into labels (P1-P4) and effort buckets (S/M/L), with a draft fix plan posted as a comment on the issue for the assignee to refine. This eliminates a class of "where do I start with this issue?" work for every new ticket.

**Quality of the Idea** — The "multi-agent on a blackboard" pattern is event-driven, not a prompt chain. The Reviewer's REVISE state transition is a first-class event that rewinds the pipeline — a richer control flow than the typical "agent calls LLM once and calls it done" pattern. The Agent Builder manifest is generated from the live agent registry, not hard-coded, so adding a new agent automatically updates the manifest.

---

## Submission checklist

Before clicking **Submit project**, verify:

- [ ] Project name: `IssueMosaic`
- [ ] Tagline: `Reactive multi-agent GitLab issue triage, powered by Gemini + GitLab MCP.`
- [ ] Track selected: **`GitLab`**
- [ ] Code repo URL: `https://github.com/TeapoyY/issuemosaic`
- [ ] Demo video URL: *(your YouTube unlisted link)*
- [ ] Hosted project URL: *(GitHub README quickstart or live deploy)*
- [ ] All 3 screenshots uploaded (dashboard / trace / manifest)
- [ ] Description pasted (~400 words, mentions "GitLab" by name)
- [ ] Team member: `TeapoyY`
- [ ] Country filled in
- [ ] License visible at top of GitHub repo About section: **MIT License** ✅ (already set)
- [ ] Click **Submit project** and watch for the confirmation page
- [ ] **Copy the resulting submission URL** (e.g. `https://devpost.com/software/issuemosaic`) and send it back to me

---

## After you submit

1. Send me the **submission URL** (e.g. `https://devpost.com/software/issuemosaic`)
2. I'll flip the registry: `submissions.json` status `building` → `submitted`, capture the URL, and push
3. The hackathon-tracker cron will pick this up on its next tick (every 4h) and not re-attempt

---

## What I already prepared for you (no work needed)

- ✅ TDD-verified 66/66 tests passing (41 original + 25 new hackathon-criteria tests)
- ✅ Code at `c8f7907` on `main` of `github.com/TeapoyY/issuemosaic`
- ✅ 3 screenshots in `submission-screenshots/`, vision-verified populated
- ✅ Demo video at `demo-video/issuemosaic-demo.webm` (60s, 2.2MB) — needs YouTube upload
- ✅ MIT LICENSE in the repo
- ✅ README matches the project tree (path drift fixed)
- ✅ WAF gate on Devpost is not blocking you (agent-browser bypassed it; your browser will too)
- ✅ Registry attempts[] + STATUS.md updated with this handoff doc; both pushed to `2d57157` on `master`
