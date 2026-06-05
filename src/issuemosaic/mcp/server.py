"""In-memory mock MCP server.

Speaks a tiny subset of MCP over a Python API (not a real socket — the
client uses it as a library). This is what the orchestrator and tools
use during the demo + tests; swapping in a real GitLab MCP server is
just a constructor change in the client.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


class MockMCPServer:
    """A simple in-memory GitLab-shaped MCP server.

    Holds a small list of issues, supports the operations the agent
    pipeline needs: list_issues, get_issue, post_comment, add_label.
    """

    def __init__(self, issues: Optional[List[Dict[str, Any]]] = None) -> None:
        # Default fixture: 4 issues covering the main paths
        self._issues: List[Dict[str, Any]] = []
        if issues is not None:
            for i in issues:
                self._issues.append(copy.deepcopy(i))
        else:
            self._issues = [
                {
                    "iid": 101,
                    "title": "App crashes when uploading large CSV",
                    "body": "Traceback shows an OutOfMemoryError in the parser when the file is over 50MB. "
                            "Reproduction: upload a 60MB CSV via the admin panel.",
                    "labels": [],
                    "comments": [],
                },
                {
                    "iid": 102,
                    "title": "Feature request: support for XLSX exports",
                    "body": "It would be nice if the reports page could also export to XLSX, not just CSV. "
                            "A lot of our analysts live in Excel.",
                    "labels": [],
                    "comments": [],
                },
                {
                    "iid": 103,
                    "title": "Typo in README — 'recieve' should be 'receive'",
                    "body": "Just a small docs typo. Found it while onboarding.",
                    "labels": [],
                    "comments": [],
                },
                {
                    "iid": 104,
                    "title": "Latency spikes on /api/reports after deploy",
                    "body": "We deployed v2.4.1 yesterday and now /api/reports p99 latency is up to 4s "
                            "from the usual 200ms. No error rate change, just slow.",
                    "labels": [],
                    "comments": [],
                },
            ]

    # ---- MCP-shaped operations ----------------------------------------

    def list_issues(self, state: str = "opened") -> List[Dict[str, Any]]:
        # GitLab returns a flat record per issue including the issue state
        out = []
        for i in self._issues:
            rec = copy.deepcopy(i)
            rec.setdefault("state", "opened")
            out.append(rec)
        return out

    def get_issue(self, iid: int) -> Dict[str, Any]:
        for i in self._issues:
            if i["iid"] == iid:
                rec = copy.deepcopy(i)
                rec.setdefault("state", "opened")
                return rec
        raise KeyError(f"issue {iid} not found")

    def post_comment(self, iid: int, body: str) -> Dict[str, Any]:
        for i in self._issues:
            if i["iid"] == iid:
                comment = {"body": body, "author": "issuemosaic-bot"}
                i.setdefault("comments", []).append(comment)
                return comment
        raise KeyError(f"issue {iid} not found")

    def add_label(self, iid: int, label: str) -> Dict[str, Any]:
        for i in self._issues:
            if i["iid"] == iid:
                if label not in i.setdefault("labels", []):
                    i["labels"].append(label)
                return copy.deepcopy(i)
        raise KeyError(f"issue {iid} not found")

    def snapshot(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._issues)
