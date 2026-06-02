"""Capture screenshots of the IssueMosaic dashboard for the submission.

Captures three views:
  1. Dashboard with the trace table populated (post-triage).
  2. JSON manifest (rendered as text on a page).
  3. A clean "screenshot" of the GitHub repo (rendered via the GitHub
     raw README view).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

API = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent.parent / "submission-screenshots"
OUT.mkdir(exist_ok=True)


async def shoot(page, name, url, wait_for=None, post_action=None):
    print(f"  → {name}: {url}")
    await page.goto(url, wait_until="networkidle", timeout=15000)
    if post_action:
        await post_action(page)
    if wait_for:
        await page.wait_for_selector(wait_for, timeout=8000)
    # Give the JS a beat to render
    await page.wait_for_timeout(800)
    path = OUT / name
    await page.screenshot(path=str(path), full_page=True)
    size = path.stat().st_size
    print(f"     saved {path.name} ({size:,} bytes)")


async def main() -> int:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()

        # 1. Dashboard — run a triage first, then screenshot
        async def run_triage(p):
            r = await p.evaluate(
                """async () => {
                    const r = await fetch('/api/triage', {method: 'POST'});
                    return r.ok;
                }"""
            )
            print(f"  triage via JS: {r}")

        await page.goto(f"{API}/", wait_until="networkidle", timeout=15000)
        await run_triage(page)
        await page.wait_for_timeout(2000)  # let the table repaint
        out1 = OUT / "01-dashboard-after-triage.png"
        await page.screenshot(path=str(out1), full_page=True)
        print(f"  → 01-dashboard-after-triage.png ({out1.stat().st_size:,} bytes)")

        # 2. The /api/trace raw JSON (we render it ourselves)
        r = await page.evaluate("fetch('/api/trace').then(r => r.json())")
        pretty = json.dumps(r, indent=2)
        await page.set_content(
            f"""<!doctype html><html><head><meta charset='utf-8'>
            <style>body{{font:13px ui-monospace,monospace;padding:20px;background:#fafafa;}}
            pre{{background:#fff;padding:16px;border:1px solid #eee;border-radius:4px;
                 white-space:pre-wrap;word-wrap:break-word;}}</style></head>
            <body><h2>IssueMosaic — last triage trace</h2>
            <pre>{pretty[:8000]}</pre></body></html>"""
        )
        out2 = OUT / "02-trace-json.png"
        await page.screenshot(path=str(out2), full_page=True)
        print(f"  → 02-trace-json.png ({out2.stat().st_size:,} bytes)")

        # 3. The /api/manifest as a structured page
        m = await page.evaluate("fetch('/api/manifest').then(r => r.json())")
        agents_html = "".join(
            f"<li><b>{a['name']}</b> — {a['description']} <i>(model: {a['model']})</i></li>"
            for a in m['agents']
        )
        tools_html = "".join(
            f"<li><b>{t['name']}</b> — {t['description']}</li>"
            for t in m['tools']
        )
        await page.set_content(
            f"""<!doctype html><html><head><meta charset='utf-8'>
            <style>body{{font:14px system-ui;padding:24px;max-width:900px;margin:0 auto;}}
            h1{{margin:0 0 4px 0;}} .sub{{color:#666;margin-bottom:24px;}}
            h2{{border-bottom:1px solid #eee;padding-bottom:4px;}}
            ul{{line-height:1.7;}} code{{background:#f3f3f3;padding:1px 4px;border-radius:3px;}}
            </style></head>
            <body><h1>{m['display_name']}</h1>
            <div class="sub">{m['description']}</div>
            <h2>Agents</h2><ul>{agents_html}</ul>
            <h2>Tools</h2><ul>{tools_html}</ul>
            </body></html>"""
        )
        out3 = OUT / "03-manifest.png"
        await page.screenshot(path=str(out3), full_page=True)
        print(f"  → 03-manifest.png ({out3.stat().st_size:,} bytes)")

        await browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
