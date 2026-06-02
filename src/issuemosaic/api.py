"""FastAPI dashboard for the orchestrator.

Endpoints:
  GET  /             — HTML dashboard (read-only).
  GET  /api/health   — health probe.
  POST /api/triage   — run the orchestrator on a posted issue (or all mock issues).
  GET  /api/manifest — return the Agent Builder manifest as JSON.
  GET  /api/trace    — return the most recent session's blackboard snapshot.
"""
from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .llm.base import make_default_llm
from .mcp import MockMCPServer
from .mcp.client import make_mcp_client
from .manifest import build_manifest
from .orchestrator import triage_all, triage_issue


app = FastAPI(title="IssueMosaic", version="0.1.0")

# Shared in-memory state — fine for a hackathon demo, swap for a real
# queue/DB in production.
_state_lock = threading.Lock()
_last_sessions: List[Dict[str, Any]] = []


def _dashboard_html() -> str:
    return """<!doctype html>
<html><head><meta charset="utf-8">
<title>IssueMosaic</title>
<style>
  body { font: 14px/1.4 system-ui, sans-serif; max-width: 920px; margin: 24px auto; padding: 0 16px; color: #1a1a1a; }
  h1 { margin: 0 0 4px 0; }
  .sub { color: #666; margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; }
  th { background: #fafafa; font-weight: 600; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .pill.approved { background: #e6f7ec; color: #137333; }
  .pill.revise   { background: #fde8e8; color: #b3261e; }
  .pill.P1 { background: #fde8e8; color: #b3261e; }
  .pill.P2 { background: #fef0e1; color: #b85a00; }
  .pill.P3 { background: #e6f0ff; color: #1967d2; }
  .pill.P4 { background: #f0f0f0; color: #5f6368; }
  code { background: #f3f3f3; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
  pre  { background: #f8f8f8; padding: 12px; border-radius: 6px; overflow-x: auto; }
  .actions { margin: 16px 0; }
  button { background: #1967d2; color: white; border: 0; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
  button:disabled { background: #999; cursor: wait; }
</style>
</head><body>
<h1>IssueMosaic</h1>
<div class="sub">Reactive multi-agent GitLab issue triage · powered by Gemini + GitLab MCP</div>
<div class="actions">
  <button id="run">Run triage on all mock issues</button>
  <span id="status" style="margin-left:12px;color:#666"></span>
</div>
<div id="out"></div>
<script>
async function refresh() {
  const r = await fetch('/api/trace');
  const data = await r.json();
  const sessions = data.sessions || [];
  if (!sessions.length) { document.getElementById('out').innerHTML = '<p><em>No sessions yet. Click the button to run a triage.</em></p>'; return; }
  let html = '<table><thead><tr><th>#</th><th>Title</th><th>Label</th><th>Priority</th><th>Decision</th><th>Plan steps</th></tr></thead><tbody>';
  for (const s of sessions) {
    const i = s.state.issue || {};
    const t = s.state.triage || {};
    const v = s.state.verdict || {};
    const p = s.state.plan || {};
    html += `<tr>
      <td>${i.iid ?? '?'}</td>
      <td>${escapeHtml(i.title || '')}</td>
      <td><code>${escapeHtml(t.label || '?')}</code></td>
      <td><span class="pill ${t.priority || ''}">${t.priority || '?'}</span></td>
      <td><span class="pill ${(v.decision||'').toLowerCase()}">${v.decision || '-'}</span></td>
      <td>${(p.steps || []).length}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  document.getElementById('out').innerHTML = html;
}
function escapeHtml(s){return s.replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
document.getElementById('run').onclick = async () => {
  const b = document.getElementById('run');
  const s = document.getElementById('status');
  b.disabled = true; s.textContent = 'Running…';
  const r = await fetch('/api/triage', {method:'POST'});
  const data = await r.json();
  s.textContent = 'Processed ' + data.issue_count + ' issues in ' + (data.elapsed_ms||0) + 'ms';
  b.disabled = false; refresh();
};
refresh();
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _dashboard_html()


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "version": "0.1.0"}


class TriageRequest(BaseModel):
    issue: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional single issue. If absent, triages all mock issues.",
    )


@app.post("/api/triage")
def post_triage(req: TriageRequest = TriageRequest()) -> Dict[str, Any]:
    import time

    mcp = make_mcp_client()
    llm = make_default_llm(role="api")
    started = time.time()
    if req.issue is not None:
        board = triage_issue(req.issue, mcp, llm=llm)
        result = {"issue_count": 1, "sessions": [board.snapshot()]}
    else:
        result = triage_all(mcp, llm=llm)
    elapsed = int((time.time() - started) * 1000)
    result["elapsed_ms"] = elapsed
    with _state_lock:
        _last_sessions.clear()
        _last_sessions.extend(result["sessions"])
    return result


@app.get("/api/manifest")
def get_manifest() -> Dict[str, Any]:
    return build_manifest(make_default_llm(role="manifest"))


@app.get("/api/trace")
def get_trace() -> Dict[str, Any]:
    with _state_lock:
        return {"sessions": list(_last_sessions)}
