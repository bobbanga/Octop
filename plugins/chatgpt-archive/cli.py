"""Command-line entry point for the local ChatGPT archive."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive import ingest, list_runs, search, validate


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path("~/.octop/chatgpt-archive").expanduser(),
        help="Raw archive root (default: ~/.octop/chatgpt-archive)",
    )
    parser.add_argument("--database", type=Path, default=None, help="SQLite path (default: <archive-root>/index.sqlite3)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-first ChatGPT export archive")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest_parser = commands.add_parser("ingest", help="copy and index an export")
    ingest_parser.add_argument("source", type=Path)
    ingest_parser.add_argument("--account", required=True)
    ingest_parser.add_argument("--source-kind", choices=("open_source", "official", "manual"), default="open_source")
    _common(ingest_parser)

    validate_parser = commands.add_parser("validate", help="compare primary and official exports")
    validate_parser.add_argument("primary", type=Path)
    validate_parser.add_argument("official", type=Path)
    validate_parser.add_argument("--report", type=Path, default=None)

    search_parser = commands.add_parser("search", help="search the SQLite FTS5 index")
    search_parser.add_argument("query")
    search_parser.add_argument("--database", type=Path, required=True)
    search_parser.add_argument("--account", default=None)
    search_parser.add_argument("--limit", type=int, default=20)

    runs_parser = commands.add_parser("runs", help="list captured runs")
    runs_parser.add_argument("--database", type=Path, required=True)
    runs_parser.add_argument("--account", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "ingest":
        result = ingest(
            args.source,
            account_id=args.account,
            source_kind=args.source_kind,
            archive_root=args.archive_root,
            db_path=args.database,
        )
    elif args.command == "validate":
        result = validate(args.primary, args.official)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif args.command == "search":
        result = {"query": args.query, "results": search(args.database, args.query, account_id=args.account, limit=args.limit)}
    else:
        result = {"runs": list_runs(args.database, account_id=args.account)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
