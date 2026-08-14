"""
sync_open_now.py — pull date/opens_at/closes_at from the published Google Sheet
and merge them into sites.csv (matching rows by name; no other field is touched).
The map itself computes open/closed live from these three fields (see
build_map.py) -- this script's only job is keeping sites.csv in sync with
whatever COAD partners entered in the sheet.

Usage: python3 sync_open_now.py
Exits 0 with no output if nothing changed, prints a summary of changes otherwise.
"""

import csv
import subprocess
import sys

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTyNMG0g4YTXRx_G13jn7MluwjMowbtgBymPZ5hadQoALn0LhnqqBUuAnMh9F8AVSkW3w3tw9ZxsgH6/pub?output=csv"
SITES_CSV = "sites.csv"
SYNC_FIELDS = ["date", "opens_at", "closes_at"]


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
        date = _clean_field(row.get("date") or "", "date", name)
        opens_at = _clean_field(row.get("opens_at") or "", "opens_at", name)
        closes_at = _clean_field(row.get("closes_at") or "", "closes_at", name)
        status[name] = (date, opens_at, closes_at)
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
    # formatting/quoting -- only the trailing date/opens_at/closes_at values change per row.
    changes = []
    matched_names = set()
    new_lines = [lines[0]]
    for line in lines[1:]:
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped):]
        name = stripped.split(",", 1)[0].strip('"').strip()
        if name in remote_status:
            matched_names.add(name)
            rest, old_date, old_opens_at, old_closes_at = stripped.rsplit(",", len(SYNC_FIELDS))
            new_vals = remote_status[name]
            old_vals = (old_date.strip(), old_opens_at.strip(), old_closes_at.strip())
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
