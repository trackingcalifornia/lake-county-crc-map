"""
sync_open_now.py — pull open_now status from the published Google Sheet
and merge it into sites.csv (matching rows by name; no other field is touched).

Usage: python3 sync_open_now.py
Exits 0 with no output if nothing changed, prints a summary of changes otherwise.
"""

import csv
import subprocess
import sys

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTyNMG0g4YTXRx_G13jn7MluwjMowbtgBymPZ5hadQoALn0LhnqqBUuAnMh9F8AVSkW3w3tw9ZxsgH6/pub?output=csv"
SITES_CSV = "sites.csv"


def fetch_remote_status():
    result = subprocess.run(
        ["curl", "-fsSL", SHEET_CSV_URL], capture_output=True, check=True
    )
    text = result.stdout.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    status = {}
    for row in reader:
        name = (row.get("name") or "").strip()
        raw = (row.get("open_now") or "").strip().lower()
        if name:
            status[name] = "true" if raw == "true" else "false"
    return status


def main():
    remote_status = fetch_remote_status()

    with open(SITES_CSV, encoding="utf-8") as f:
        lines = f.readlines()

    header_fields = next(csv.reader([lines[0]]))
    if header_fields[-1] != "open_now":
        sys.exit("open_now must be the last column in sites.csv for this script's text-level replace to be safe")

    # Text-level replace (not csv.writer) so untouched rows keep byte-identical
    # formatting/quoting -- only the trailing open_now value changes per row.
    changes = []
    matched_names = set()
    new_lines = [lines[0]]
    for line in lines[1:]:
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped):]
        name = stripped.split(",", 1)[0].strip('"').strip()
        if name in remote_status:
            matched_names.add(name)
            rest, old_val = stripped.rsplit(",", 1)
            new_val = remote_status[name]
            if old_val.strip().lower() != new_val:
                changes.append((name, old_val, new_val))
                stripped = rest + "," + new_val
        new_lines.append(stripped + ending)

    unmatched = set(remote_status) - matched_names
    for name in sorted(unmatched):
        print(f"warning: '{name}' in Google Sheet not found in {SITES_CSV}, skipped", file=sys.stderr)

    if not changes:
        print("No open_now changes.")
        return

    with open(SITES_CSV, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Updated {len(changes)} site(s):")
    for name, old, new in changes:
        print(f"  {name}: {old!r} -> {new!r}")


if __name__ == "__main__":
    main()
