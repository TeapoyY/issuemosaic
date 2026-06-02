"""Issuemosaic — reactive multi-agent GitLab issue triage.

A production-shape demo for the Google Cloud Rapid Agent Hackathon.
Runs end-to-end offline (MockLLM + MockMCPServer) and drops in real
Gemini / GitLab MCP backends when credentials are provided.
"""
from __future__ import annotations

__version__ = "0.1.0"
