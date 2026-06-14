"""Load and index execution reports from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import get_settings


def list_reports(limit: int = 50) -> list[dict[str, Any]]:
    settings = get_settings()
    reports_dir = settings.reports_dir
    if not reports_dir.exists():
        return []

    summaries: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.name == ".gitkeep":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summaries.append(
            {
                "run_id": data.get("run_id", path.stem),
                "url": data.get("url", ""),
                "intent": data.get("intent", ""),
                "status": data.get("status", "unknown"),
                "flows_total": data.get("flows_total", 0),
                "flows_passed": data.get("flows_passed", 0),
                "generated_at": data.get("generated_at", ""),
                "dashboard_url": f"/dashboard/{data.get('run_id', path.stem)}",
            }
        )
        if len(summaries) >= limit:
            break
    return summaries


def load_report(run_id: str) -> dict[str, Any] | None:
    settings = get_settings()
    path = settings.reports_dir / f"{run_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
