# MapStory Project Memory

## Project Purpose

MapStory is a local, Python-based historical event database manager. It is intended for historical research, alternate-history/worldline planning, fiction settings, daily event tracking, and other time/place/person-centered story records.

The central domain object is an event with structured time, optional historical time notes, optional coordinates/location notes, persons, an event description, a priority label, and a remark/source field.

## Current Architecture

- Main runtime path: `CLI / Flask Web UI -> EventStore -> SQLite`.
- Core package: `mapstory/`.
- Storage layer: `mapstory/store.py` owns SQLite schema creation/migration, CRUD, soft delete, search, and time sorting.
- Time handling: `mapstory/time/` owns `StructuredTime`, parsing, validation, formatting, sorting keys, and system time helpers.
- CLI: `mapstory/cli/` exposes `python -m mapstory --db data/mapstory.db event <create|get|update|delete|list|search>`.
- Web UI/API: `mapstory/ext/web.py` creates the Flask app, HTML views, and `/api/events` JSON endpoints.
- Validation: `mapstory/validators.py` normalizes and validates user inputs.
- Output formatting: `mapstory/output/` formats CLI table/JSON output.
- Era conversion data/API exists under `data/era.db` and `mapstory/time/era/`.

## Data Model Notes

- Default event DB path is `data/mapstory.db`; era DB path is `data/era.db`.
- The active events table includes split time columns: `time_year`, `time_month`, `time_day`, `time_hour`, `time_minute`, plus `time_note`.
- `time_iso` remains for compatibility, but current querying/sorting relies on split structured time fields.
- Supported time inputs are `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, `YYYY-MM-DD HH`, and `YYYY-MM-DD HH:MM`; negative years are supported.
- Deletion is soft by default via `deleted_at`; CLI/API hard delete exists only when explicitly requested.
- Priority inputs from CLI/API use keys `fact`, `doubt`, `fanon`, `abridged_fact`, and are stored as Chinese labels: `史实`, `史实（存疑）`, `自设`, `史实（删减）`.
- Person inputs may be strings/lists and are normalized for storage/display.

## Development Preferences

- Use `uv` for dependency/environment/test commands.
- Do not edit `README.md` unless the user explicitly asks.
- Keep changes scoped and follow the existing module split.
- When changing code behavior, update tests where appropriate.
- For code changes, provide the relevant `uv` command(s) used or recommended.
- If a code change is version-worthy, update `pyproject.toml` version and add a concise entry to `CHANGELOG.md` in the existing style.
- External data ingestion is lower priority than stable core CRUD, time handling, storage, CLI, and Web behavior.

## Useful Commands

- Run tests: `uv run python -m unittest`
- CLI example: `uv run python -m mapstory --db data/mapstory.db event list --limit 20`
- Start Web UI: `uv run python -c "from mapstory.ext import create_app; app = create_app('data/mapstory.db'); app.run(debug=True)"`

## Known Implementation Details

- `order=created` is SQL sorted by `created_at DESC, id DESC`.
- `order=time` fetches matching rows and sorts in Python using `build_sort_key`.
- The Flask app creates an `EventStore` per request and closes it in teardown.
- The Web UI templates are currently embedded in `mapstory/ext/web.py` via `DictLoader`.
- Tests are currently `unittest` based and create temporary SQLite databases.
