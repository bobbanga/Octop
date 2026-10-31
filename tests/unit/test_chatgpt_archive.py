from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).parents[2] / "plugins" / "chatgpt-archive"
sys.path.insert(0, str(PLUGIN_DIR))
from archive import ingest, search, validate  # noqa: E402


def _write_export(root: Path, conversation_id: str = "conv-1", text: str = "hello archive") -> Path:
    root.mkdir()
    payload = [{
        "conversation_id": conversation_id,
        "title": "Archive test",
        "create_time": 1,
        "update_time": 2,
        "mapping": {
            "node": {
                "message": {
                    "id": "msg-1",
                    "author": {"role": "user"},
                    "content": {"parts": [text]},
                    "create_time": 1,
                }
            }
        },
    }]
    (root / "conversations.json").write_text(json.dumps(payload), encoding="utf-8")
    (root / "asset.txt").write_text("attachment", encoding="utf-8")
    return root


def test_ingest_preserves_raw_manifest_and_is_idempotent(tmp_path: Path) -> None:
    source = _write_export(tmp_path / "source")
    archive = tmp_path / "archive"

    first = ingest(source, account_id="account one", source_kind="open_source", archive_root=archive)
    second = ingest(source, account_id="account one", source_kind="open_source", archive_root=archive)

    assert first["conversation_count"] == 1
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    raw = Path(first["raw_path"])
    assert (raw / "manifest.json").exists()
    assert (raw / "conversations.json").exists()
    assert (raw / "asset.txt").read_text() == "attachment"


def test_search_uses_local_fts_and_account_filter(tmp_path: Path) -> None:
    source = _write_export(tmp_path / "source")
    archive = tmp_path / "archive"
    result = ingest(source, account_id="one", source_kind="open_source", archive_root=archive)

    rows = search(result["db_path"], "hello", account_id="one")
    assert [row["conversation_id"] for row in rows] == ["conv-1"]
    assert search(result["db_path"], "hello", account_id="missing") == []


def test_validation_classifies_primary_only_and_mismatch(tmp_path: Path) -> None:
    primary = _write_export(tmp_path / "primary")
    official = _write_export(tmp_path / "official", conversation_id="conv-2", text="different")
    report = validate(primary, official)

    assert report["summary"]["open_source_only"] == 1
    assert report["summary"]["official_only"] == 1
    assert report["summary"]["content_mismatch"] == 0
    assert report["not_comparable"]


@pytest.mark.parametrize("kind", ["open_source", "official", "manual"])
def test_supported_source_kinds(tmp_path: Path, kind: str) -> None:
    source = _write_export(tmp_path / f"source-{kind}")
    result = ingest(source, account_id="a", source_kind=kind, archive_root=tmp_path / "archive")
    assert result["source_kind"] == kind
