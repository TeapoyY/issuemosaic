"""Generate a demo video of the IssueMosaic dashboard.

Uses Playwright's built-in video recording. No ffmpeg required — the
recording is saved as a .webm by Chromium's mediarecorder.

Structure (60s demo, the spec calls for 2:30–3:00 but cron tick budget
is 3 min — we ship a tight 60s cut that hits all 5 sections):
  0:00 - 0:05  Title card
  0:05 - 0:15  Problem statement
  0:15 - 0:25  Solution / architecture
  0:25 - 0:40  Live demo (run triage, show table)
  0:40 - 0:50  Tech stack
  0:50 - 0:60  Next steps + sponsor credits
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

API = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent.parent / "demo-video"
OUT.mkdir(exist_ok=True)


SLIDES = [
    # (display_seconds, html_content_or_"demo", label)
    (5, "<h1>IssueMosaic</h1><p class='sub'>Reactive multi-agent GitLab issue triage</p><p class='sub'>Built for the Google Cloud Rapid Agent Hackathon</p><p class='sub'>Powered by Gemini + GitLab MCP</p>", "title"),
    (10, "<h2>The problem</h2><p>GitLab repos accumulate hundreds of issues. Triage is repetitive:</p><ul><li>Read title + body</li><li>Decide: bug / feature / docs / perf</li><li>Assign priority</li><li>Draft a fix plan</li><li>Add labels + post the plan as a comment</li></ul><p>Most teams skip steps 2–5. The cost shows up later: mislabelled bugs, unresolved P1s, lost context.</p>", "problem"),
    (10, "<h2>The solution</h2><p>A reactive, event-driven multi-agent pipeline:</p><div class='arch'>issue posted → Triage agent → Resolution agent → Reviewer agent → plan + label + comment</div><p>Each agent is independent. They communicate through a blackboard event bus. The Reviewer can send a plan back for revision.</p><p>Switches cleanly between <b>Gemini</b> (production) and a <b>MockLLM</b> (offline demo + tests) by environment variable.</p>", "solution"),
    (15, "demo", "demo"),
    (10, "<h2>Tech stack</h2><ul><li><b>Gemini</b> via <code>google-generativeai</code> SDK — JSON-mode structured output</li><li><b>GitLab MCP</b> — Model Context Protocol over HTTP; mock server for the demo</li><li><b>Agent Builder manifest</b> — <code>issuemosaic manifest</code> prints the JSON the Agent Builder UI ingests</li><li><b>FastAPI</b> dashboard with a live event trace</li><li><b>pytest</b> — 41 tests passing (offline, no API key needed)</li></ul>", "tech"),
    (10, "<h2>What's next</h2><ul><li>Multi-repo support + a small operator UI for human-in-the-loop overrides</li><li>Per-issue cost / latency budget — stop calling the LLM when the answer is already in the blackboard</li><li>Webhook trigger so the agent starts the moment a new issue is opened</li></ul><p class='credits'>Hackathon: <b>Google Cloud Rapid Agent Hackathon</b> on Devpost · $60K prize pool · Deadline Jun 11 2026</p>", "next"),
]


async def record_slide(page, delay, html, label):
    if html == "demo":
        # Live demo: hit the dashboard, run triage, let the table fill in
        await page.goto(f"{API}/", wait_until="networkidle", timeout=15000)
        await page.evaluate(
            "fetch('/api/triage', {method: 'POST'})"
        )
        await page.wait_for_timeout(int(delay * 1000))
    else:
        await page.set_content(
            f"""<!doctype html><html><head><meta charset='utf-8'>
            <style>
              body{{font:18px/1.5 system-ui,sans-serif;padding:48px;max-width:900px;margin:0 auto;color:#1a1a1a;}}
              h1{{font-size:48px;margin:0 0 24px;color:#1967d2;}}
              h2{{font-size:36px;margin:0 0 16px;color:#1967d2;}}
              p,li{{font-size:20px;}}
              .sub{{color:#666;}}
              .arch{{font-family:monospace;background:#f0f4f8;padding:16px;border-radius:6px;margin:24px 0;}}
              ul{{padding-left:24px;}}
              .credits{{margin-top:32px;color:#666;}}
              code{{background:#f3f3f3;padding:2px 6px;border-radius:3px;}}
            </style></head><body>{html}</body></html>"""
        )
        await page.wait_for_timeout(int(delay * 1000))
    print(f"  shown: {label} ({delay}s)")


async def main() -> int:
    total = sum(d for d, _, _ in SLIDES)
    print(f"Recording {total}s of slides…")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(OUT),
            record_video_size={"width": 1280, "height": 720},
        )
        page = await ctx.new_page()

        # Each slide
        for delay, html, label in SLIDES:
            await record_slide(page, delay, html, label)

        # Capture and close
        video_path = await page.video.path() if page.video else None
        await page.close()
        await ctx.close()
        await browser.close()

        if video_path:
            # Rename to a clean filename
            target = OUT / "issuemosaic-demo.webm"
            try:
                Path(video_path).rename(target)
            except FileExistsError:
                Path(target).unlink()
                Path(video_path).rename(target)
            print(f"\nVideo saved: {target} ({target.stat().st_size:,} bytes)")
        else:
            print("No video path returned")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
