# ChatGPT Local Archive

This Octop plugin is a thin adapter around a local-first archive core.

## Data boundaries

- The raw export copied into raw/<account>/<run_id>/ is the source of truth.
- Each run has a SHA-256 manifest with file paths, sizes and MIME guesses.
- index.sqlite3 is a rebuildable projection with conversation metadata and FTS5 search.
- The official ChatGPT export is a validation input; it is never treated as the only source.
- No cookies, tokens, credentials, or raw exports belong in this repository.

The default archive location is ~/.octop/chatgpt-archive. Set CHATGPT_ARCHIVE_ROOT
or configure the tool fields in the Octop dashboard to use another local disk.

## Open-source collectors and validation

The first input contract is a directory or JSON file produced by an open-source collector
(for example, a browser exporter that preserves conversation JSON, branches, and attachments).
A ChatGPT official ZIP can be passed directly to archive_validate after the primary capture; ZIP path traversal is rejected and extraction is temporary.

Validation reports classify:

- verified: same conversation ID, title, message count, and message content hash
- open_source_only: captured by the primary collector only
- official_only: present in the official export only
- content_mismatch: same ID but different title/message signature
- not_comparable: attachments or rich references represented differently by the two exports

Differences are evidence for review, not automatic deletion or overwrite.

## Tools

Install the plugin from the repository root:

    octop plugin install ./plugins/chatgpt-archive --force

Then enable the tools for an agent:

- archive_ingest(source_path, account_id, source_kind)
- archive_validate(primary_path, official_path)
- archive_search(query, account_id, limit)
- archive_runs(account_id)

source_kind is open_source, official, or manual.

## Safety and recovery

Run ingestion again with the same source to exercise idempotency. The manifest hash returns
the existing run instead of duplicating rows. Keep the raw run directories and manifests until
the validation report has been reviewed. The SQLite database can be deleted and rebuilt by
re-ingesting the raw runs.

## Offline CLI

The same core can be used without an Octop agent. From the plugin directory:

    python cli.py ingest path/to/export --account account-a --source-kind open_source
    python cli.py validate path/to/primary path/to/official.zip --report validation.json
    python cli.py search "关键词" --database ~/.octop/chatgpt-archive/index.sqlite3
    python cli.py runs --database ~/.octop/chatgpt-archive/index.sqlite3

The CLI prints JSON and never uploads the input paths.
