#!/usr/bin/env python3
"""Validate keyword research used configured Nanobot search/fetch presets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def host_of(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return (parsed.netloc or parsed.path.split("/")[0]).lower().removeprefix("www.")


def events(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        items = data.get("events") or data.get("toolCalls") or data.get("calls") or []
    else:
        items = data
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def event_tool(event: dict[str, Any]) -> str:
    return str(event.get("tool") or event.get("name") or event.get("function") or "")


def event_preset(event: dict[str, Any]) -> str:
    args = event.get("arguments") if isinstance(event.get("arguments"), dict) else event.get("args")
    if isinstance(args, dict):
        return str(args.get("preset") or "")
    return str(event.get("preset") or "")


def event_urls(event: dict[str, Any]) -> list[str]:
    urls = event.get("urls") or event.get("resultUrls") or event.get("sourceUrls") or []
    if isinstance(urls, list):
        return [str(url).strip() for url in urls if str(url).strip()]
    url = str(event.get("url") or "").strip()
    return [url] if url else []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, help="research-trace.json written by the skill run")
    parser.add_argument("--context", help="Context JSON with website/websiteUrl")
    parser.add_argument("--require-fetch", action="store_true", help="Require at least one fetch preset call")
    args = parser.parse_args()

    trace = events(load_json(args.trace))
    if not trace:
        fail("research trace must contain events[]")

    has_search = any(event_tool(event) == "model_preset_call" and event_preset(event) == "search" for event in trace)
    has_fetch = any(event_tool(event) == "model_preset_call" and event_preset(event) == "fetch" for event in trace)
    used_web_search = any(event_tool(event) == "web_search" for event in trace)
    if not has_search:
        fail('research must call model_preset_call with preset="search"')
    if args.require_fetch and not has_fetch:
        fail('research must call model_preset_call with preset="fetch"')
    if used_web_search:
        fail("web_search is not allowed as the primary search path; use model_preset_call preset=search")

    ctx = load_json(args.context) if args.context else {}
    official_host = host_of(str(ctx.get("website") or ctx.get("websiteUrl") or "")) if isinstance(ctx, dict) else ""
    third_party_urls = [url for event in trace for url in event_urls(event) if official_host and host_of(url) != official_host]
    if official_host and not third_party_urls:
        fail("research trace must include at least one third-party URL discovered by search")

    print(json.dumps({"ok": True, "events": len(trace), "search": has_search, "fetch": has_fetch, "thirdPartyUrls": len(third_party_urls)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
