"""Command-line interface for IssueMosaic.

Subcommands:
  triage-all      Run the orchestrator over every open issue (mock or real).
  manifest        Print the Agent Builder manifest JSON.
  serve           Start the FastAPI dashboard on the given host/port.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional


def _cmd_triage_all(args: argparse.Namespace) -> int:
    from .llm.base import make_default_llm
    from .mcp import MockMCPServer
    from .mcp.client import make_mcp_client
    from .orchestrator import triage_all

    mcp = make_mcp_client(endpoint=args.gitlab_mcp or "", token=args.gitlab_token or "")
    if isinstance(mcp, MockMCPServer) and args.dry_run:
        # Use the canonical fixture explicitly
        pass
    llm = make_default_llm(role="cli")
    result = triage_all(mcp, llm=llm)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        for sess in result["sessions"]:
            issue = sess["state"].get("issue", {})
            triage = sess["state"].get("triage", {})
            verdict = sess["state"].get("verdict", {})
            print(
                f"#{issue.get('iid', '?'):>4}  "
                f"{triage.get('label', '?'):<24}  "
                f"{triage.get('priority', '?'):<3}  "
                f"{verdict.get('decision', '?'):<8}  "
                f"{issue.get('title', '')[:60]}"
            )
        print(f"\nProcessed {result['issue_count']} issues.")
    return 0


def _cmd_manifest(args: argparse.Namespace) -> int:
    from .llm.base import make_default_llm
    from .manifest import build_manifest

    llm = make_default_llm(role="manifest")
    print(json.dumps(build_manifest(llm), indent=2))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from .api import app
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="issuemosaic",
        description="Reactive multi-agent GitLab issue triage (Gemini + MCP).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_triage = sub.add_parser("triage-all", help="Triage all open issues in the mock MCP server.")
    p_triage.add_argument("--gitlab-mcp", default="", help="HTTP endpoint of the real GitLab MCP server (else use the mock).")
    p_triage.add_argument("--gitlab-token", default="", help="Bearer token for the real GitLab MCP server.")
    p_triage.add_argument("--dry-run", action="store_true", help="Use the bundled fixture (default).")
    p_triage.add_argument("--json", action="store_true", help="Print the full session JSON instead of a table.")
    p_triage.set_defaults(func=_cmd_triage_all)

    p_manifest = sub.add_parser("manifest", help="Print the Gemini Agent Builder manifest.")
    p_manifest.set_defaults(func=_cmd_manifest)

    p_serve = sub.add_parser("serve", help="Run the FastAPI dashboard.")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", default=8000, type=int)
    p_serve.add_argument("--log-level", default="info")
    p_serve.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
