#!/usr/bin/env python3
"""Mirror lists/*.json from the upstream mappings project.

Upstream: https://github.com/anime-and-manga/lists
Identified by matching this repo's lists/README.md byte-for-byte against
upstream's, and by the {idAL, idAniDB, idMal, titles, type, cover, nsfw,
nextEpisode} schema, which is specific to that project.

These files ship to users via raw.githubusercontent, so the bar is: it is
strictly better to keep yesterday's good data than to publish today's
truncated download. Every file must clear every gate below before it is
allowed to replace what is on disk; if any file fails, that file is left
alone and the job exits non-zero.

Usage: refresh_lists.py [--scope airing|all] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # noqa: E402

UPSTREAM = "https://raw.githubusercontent.com/anime-and-manga/lists/main"
LISTS_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "lists")

# required : keys every entry must carry
# min_rows : absolute floor; below this the payload is not credible
# shrink   : how much smaller than the on-disk copy we tolerate. The catalogue
#            files only ever grow, so a real shrink means a broken export.
#            anime-airing is seasonal and legitimately swings hard, so it gets
#            no ratio gate -- only the absolute floor.
SPECS = {
    "anime.json": {
        "required": ["idAL", "idMal"],
        "min_rows": 15000,
        "shrink": 0.95,
        "scope": "all",
    },
    "anime-full.json": {
        "required": ["idAL", "idMal", "titles", "type"],
        "min_rows": 15000,
        "shrink": 0.95,
        "scope": "all",
    },
    "manga.json": {
        "required": ["idAL", "idMal"],
        "min_rows": 50000,
        "shrink": 0.95,
        "scope": "all",
    },
    "manga-full.json": {
        "required": ["idAL", "idMal", "titles", "type"],
        "min_rows": 50000,
        "shrink": 0.95,
        "scope": "all",
    },
    "anime-airing.json": {
        "required": ["idAL", "idMal", "titles", "type"],
        "min_rows": 50,
        "shrink": None,
        "scope": "airing",
    },
}


def validate(name: str, data, spec: dict, prev_rows: int) -> None:
    """Raise ValueError unless `data` is a credible replacement."""
    if not isinstance(data, list):
        raise ValueError(f"{name}: top level is {type(data).__name__}, expected a list")

    rows = len(data)
    if rows < spec["min_rows"]:
        raise ValueError(
            f"{name}: only {rows} entries, floor is {spec['min_rows']} "
            "-- looks truncated"
        )

    if spec["shrink"] is not None and prev_rows:
        floor = int(prev_rows * spec["shrink"])
        if rows < floor:
            raise ValueError(
                f"{name}: {rows} entries vs {prev_rows} on disk "
                f"({rows / prev_rows:.1%}) -- below the {spec['shrink']:.0%} "
                "shrink gate, refusing to overwrite"
            )

    # Schema check on a sample spread across the file, not just the head:
    # a truncation or a partial re-export shows up at the tail.
    idx = {0, rows // 2, rows - 1} | set(range(0, rows, max(1, rows // 50)))
    for i in sorted(idx):
        row = data[i]
        if not isinstance(row, dict):
            raise ValueError(f"{name}: entry {i} is {type(row).__name__}, expected object")
        for key in spec["required"]:
            if key not in row:
                raise ValueError(f"{name}: entry {i} is missing required key {key!r}")
        # idAL is the primary key and is always present. idMal/idAniDB are
        # genuinely nullable upstream (~1650 anime rows have idMal: null for
        # titles AniList carries but MAL does not), so null is valid data --
        # only a wrong *type* is a problem.
        if not isinstance(row["idAL"], int):
            raise ValueError(
                f"{name}: entry {i} idAL is {type(row['idAL']).__name__}, expected int")
        if row.get("idMal") is not None and not isinstance(row["idMal"], int):
            raise ValueError(
                f"{name}: entry {i} idMal is {type(row['idMal']).__name__}, "
                "expected int or null")

    # Ids must be unique; duplicates mean a concatenated / double-appended export.
    ids = [r["idAL"] for r in data if isinstance(r, dict) and isinstance(r.get("idAL"), int)]
    if len(set(ids)) < len(ids) * 0.99:
        raise ValueError(
            f"{name}: {len(ids) - len(set(ids))} duplicate idAL values "
            "-- export looks doubled"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["airing", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = {
        n: s for n, s in SPECS.items()
        if args.scope == "all" or s["scope"] == "airing"
    }

    print(f"scope={args.scope}  upstream={UPSTREAM}")
    print(f"files: {', '.join(sorted(targets))}\n")

    changed, failed, unchanged = [], [], []

    for name in sorted(targets):
        spec = targets[name]
        dest = os.path.join(LISTS_DIR, name)

        prev_rows, prev_bytes = 0, b""
        if os.path.exists(dest):
            try:
                with open(dest, "rb") as fh:
                    prev_bytes = fh.read()
                prev_rows = len(json.loads(prev_bytes.decode("utf-8")))
            except (OSError, ValueError) as exc:
                print(f"  {name}: WARNING existing copy unreadable ({exc}); "
                      "treating as empty")

        url = f"{UPSTREAM}/{name}"
        try:
            # Keep upstream's bytes verbatim -- see fetch_json's docstring.
            data, new_bytes = probe.fetch_json(
                url, timeout=240, expect_min_bytes=1024, return_raw=True)
            validate(name, data, spec, prev_rows)
        except (RuntimeError, ValueError) as exc:
            print(f"  FAIL  {exc}")
            failed.append(str(exc))
            continue

        if new_bytes == prev_bytes:
            print(f"  same  {name}  ({len(data)} entries)")
            unchanged.append(name)
            continue

        delta = len(data) - prev_rows
        print(f"  UPD   {name}  {prev_rows} -> {len(data)} entries ({delta:+d})")
        changed.append(name)

        if args.dry_run:
            continue

        # Atomic replace: a killed job must never leave half a file behind.
        os.makedirs(LISTS_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=LISTS_DIR, prefix=f".{name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(new_bytes)
            os.replace(tmp, dest)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    summary = (f"{len(changed)} updated, {len(unchanged)} unchanged, "
               f"{len(failed)} failed")
    print(f"\n{summary}")

    step_out = os.environ.get("GITHUB_OUTPUT")
    if step_out:
        with open(step_out, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\n")
            fh.write(f"files={' '.join(changed)}\n")
            fh.write(f"summary={summary}\n")

    if failed:
        print("\nFAILED -- upstream payload was not trustworthy, on-disk data kept:")
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
