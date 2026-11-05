"""
sync_open_now.py — pull date/opens_at/closes_at/last_date/overnight from the published Google Sheet
and merge them into sites.csv (matching rows by name; no other field is touched).
The map reads the Sheet directly in the browser and computes open/closed live
(see build_map.py); the values this script keeps in sites.csv are baked into
the page as the fallback if the Sheet cannot be reached.

Usage: python3 sync_open_now.py
Exits 0 with no output if nothing changed, prints a summary of changes otherwise.
"""

import csv
import subprocess
import sys

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTyNMG0g4YTXRx_G13jn7MluwjMowbtgBymPZ5hadQoALn0LhnqqBUuAnMh9F8AVSkW3w3tw9ZxsgH6/pub?gid=0&single=true&output=csv"
SITES_CSV = "sites.csv"
SYNC_FIELDS = ["date", "opens_at", "closes_at", "last_date", "overnight"]


def _clean_field(value, field_name, site_name):
    value = value.strip()
    if "," in value:
        value = value.replace(",", " ")
        print(f"warning: '{site_name}' {field_name} contained a comma, replaced with a space", file=sys.stderr)
    return value


def fetch_remote_status():
    result = subprocess.run(
        ["curl", "-fsSL", SHEET_CSV_URL], capture_output=True, check=True
    )
    text = result.stdout.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    status = {}
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        status[name] = tuple(_clean_field(row.get(f) or "", f, name) for f in SYNC_FIELDS)
    return status


def main():
    remote_status = fetch_remote_status()

    with open(SITES_CSV, encoding="utf-8") as f:
        lines = f.readlines()

    header_fields = next(csv.reader([lines[0]]))
    if header_fields[-len(SYNC_FIELDS):] != SYNC_FIELDS:
        sys.exit(
            f"{SYNC_FIELDS} must be the last columns, in that order, "
            f"in {SITES_CSV} for this script's text-level replace to be safe"
        )

    # Text-level replace (not csv.writer) so untouched rows keep byte-identical
    # formatting/quoting -- only the trailing SYNC_FIELDS values change per row.
    changes = []
    matched_names = set()
    new_lines = [lines[0]]
    for line in lines[1:]:
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped):]
        name = stripped.split(",", 1)[0].strip('"').strip()
        if name in remote_status:
            matched_names.add(name)
            rest, *old = stripped.rsplit(",", len(SYNC_FIELDS))
            new_vals = remote_status[name]
            old_vals = tuple(v.strip() for v in old)
            if old_vals != new_vals:
                changes.append((name, old_vals, new_vals))
                stripped = rest + "," + ",".join(new_vals)
        new_lines.append(stripped + ending)

    unmatched = set(remote_status) - matched_names
    for name in sorted(unmatched):
        print(f"warning: '{name}' in Google Sheet not found in {SITES_CSV}, skipped", file=sys.stderr)

    if not changes:
        print("No changes.")
        return

    with open(SITES_CSV, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Updated {len(changes)} site(s):")
    for name, old, new in changes:
        print(f"  {name}: {old} -> {new}")


if __name__ == "__main__":
    main()
