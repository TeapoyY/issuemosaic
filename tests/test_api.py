"""FastAPI app tests using TestClient."""
from __future__ import annotations

from fastapi.testclient import TestClient

from issuemosaic.api import app


client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_manifest_endpoint_returns_expected_shape():
    r = client.get("/api/manifest")
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "IssueMosaic"
    assert len(body["agents"]) == 3
    assert {a["name"] for a in body["agents"]} == {"triage", "resolution", "reviewer"}
    assert len(body["tools"]) == 4


def test_triage_endpoint_runs_all_issues():
    r = client.post("/api/triage", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["issue_count"] == 4
    assert len(body["sessions"]) == 4
    assert "elapsed_ms" in body


def test_triage_endpoint_runs_single_issue():
    r = client.post(
        "/api/triage",
        json={"issue": {"iid": 42, "title": "Test bug", "body": "crash"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["issue_count"] == 1
    assert body["sessions"][0]["state"]["issue"]["iid"] == 42


def test_trace_endpoint_reflects_last_run():
    client.post("/api/triage", json={})
    r = client.get("/api/trace")
    assert r.status_code == 200
    body = r.json()
    assert len(body["sessions"]) >= 1


def test_index_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "IssueMosaic" in r.text
