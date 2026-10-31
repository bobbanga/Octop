"""Octop adapter for the local ChatGPT archive core."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from octop_harness.plugins import PluginContext, get_tool_config

from archive import ingest, list_runs, search, validate


def _config(tool_name: str) -> tuple[Path, Path]:
    cfg = get_tool_config(tool_name) or {}
    archive_root = Path(
        str(cfg.get("archive_root") or os.getenv("CHATGPT_ARCHIVE_ROOT") or "~/.octop/chatgpt-archive")
    ).expanduser()
    db_path = Path(str(cfg.get("database_path") or archive_root / "index.sqlite3")).expanduser()
    return archive_root, db_path


async def archive_ingest(source_path: str, account_id: str, source_kind: str = "open_source") -> str:
    """Copy a local export into the raw archive and index its conversations."""
    archive_root, db_path = _config("archive_ingest")
    result = ingest(
        source_path,
        account_id=account_id,
        source_kind=source_kind,
        archive_root=archive_root,
        db_path=db_path,
    )
    return json.dumps(result, ensure_ascii=False)


async def archive_validate(primary_path: str, official_path: str) -> str:
    """Compare an open-source export with the official ZIP as a validation layer."""
    return json.dumps(validate(primary_path, official_path), ensure_ascii=False)


async def archive_search(query: str, account_id: str = "", limit: int = 20) -> str:
    """Search the local ChatGPT archive with SQLite FTS5."""
    _archive_root, db_path = _config("archive_search")
    return json.dumps(
        {"query": query, "results": search(db_path, query, account_id=account_id or None, limit=limit)},
        ensure_ascii=False,
    )


async def archive_runs(account_id: str = "") -> str:
    """List captured runs and their manifest hashes."""
    _archive_root, db_path = _config("archive_runs")
    return json.dumps({"runs": list_runs(db_path, account_id=account_id or None)}, ensure_ascii=False)


def setup(ctx: PluginContext) -> None:
    fields: list[dict[str, Any]] = [
        {"name": "archive_root", "type": "text", "required": False},
        {"name": "database_path", "type": "text", "required": False},
    ]
    ctx.tool("archive_ingest", archive_ingest, description="Archive a local ChatGPT export", config_fields=fields)
    ctx.tool("archive_validate", archive_validate, description="Validate an open-source export against the official export", config_fields=fields)
    ctx.tool("archive_search", archive_search, description="Search the local ChatGPT archive", config_fields=fields)
    ctx.tool("archive_runs", archive_runs, description="List local ChatGPT archive runs", config_fields=fields)
