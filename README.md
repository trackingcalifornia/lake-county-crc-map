# Lake County COAD Community Resilience Centers Map

Interactive map of Lake County COAD community resilience centers, showing
site status, contact information, and links for each location. Maintained
by Tracking California in partnership with Lake County COAD and the Lake
County Office of Climate Resiliency.

## How to update site information

Edit `sites.csv`. Each row is one site. Key columns:

| Column | Description |
|---|---|
| `name` | Site name |
| `address` | Full street address |
| `lat` | Latitude (decimal degrees — right-click in Google Maps to copy) |
| `lng` | Longitude (decimal degrees — will be negative for California) |
| `status` | `Active` or `Setup` — internal value only. Displays on the live map as "Ready" (orange marker) or "In Setup" (gray marker); "Active" is not shown to visitors. |
| `phone` | Phone number |
| `website` | Full URL including https:// |
| `services` | Pipe-separated: `cooling\|warming\|overnight` |
| `power` | Pipe-separated: `generator\|solar\|battery\|electric` |
| `pets` | Short pet policy text |
| `capacity` | Max occupancy number (optional) |
| `notes` | Additional notes shown in popup (optional) |
| `coords_approx` | `true` if coordinates are estimated; shows a warning in popup |
| `date` | First day open, e.g. `2026-08-20` or `8/20/2026`. Synced from the published Google Sheet (see below). Blank means not currently scheduled. |
| `opens_at` / `closes_at` | Opening and closing time, e.g. `9am` or `4:00:00 PM`. Synced from the same sheet. `12am` as a closing time means midnight at the end of the day. |
| `last_date` | Last day open. Blank means a single day. Also accepts a raw Sheets date serial (e.g. `46332`) if the column loses its Date format. |
| `overnight` | `Yes` = open continuously from `opens_at` on the first day to `closes_at` on the last day. Blank or `No` = the hours repeat each day in the range. |

Survey response workbooks in `source/` are the source data for site entries.

## Automatic "Open Now" status

Partners submit a Google Form (first day, optional last day, opening and
closing time, optional "Open overnight?"). The form feeds the "Form Responses 1"
tab, and the "DO NOT TOUCH" tab keeps the latest submission per site in the
columns `name, date, opens_at, closes_at, last_date, overnight`. That tab is
published to the web as CSV.

The page reads that CSV directly in each visitor's browser when it loads and
every 5 minutes after (`loadLiveSchedule()` in `build_map.py`). Google
refreshes the published CSV about every 5 minutes, so a form submission
reaches the map in roughly 5 to 10 minutes. Open/closed is computed in the
browser in Pacific time and rechecked every 60 seconds:

| Form entry | Map behavior |
|---|---|
| One day, overnight blank/No | Open between opening and closing time that day |
| First to last day, overnight blank/No | Open between those hours on each day, closed overnight |
| First to last day, overnight Yes | Open continuously from opening time on the first day to closing time on the last day |
| Closing time earlier than opening time (e.g. 7pm to 8am) | Treated as overnight; with no last day, closes the next morning |
| Date and times blank | Not scheduled (this is how partners cancel) |

All date and time parsing lives in the browser (`parseDay()`,
`parseMinutes()`, `scheduleFor()`), so the live fetch and the baked-in
fallback use the same rules. Unrecognized values mean "not scheduled" rather
than a guess.

**Note:** Coordinates flagged `coords_approx=true` should be verified before the site goes live. Right-click the address in Google Maps and copy the lat/lng.

## How to rebuild and publish the map

1. Edit `sites.csv` to add, remove, or update sites.
2. Run the build script (Python 3 stdlib only — no extra packages):
   ```
   python3 build_map.py
   ```
3. The updated map is written to `docs/index.html`.
4. Commit and push:
   ```
   git add docs/index.html sites.csv
   git commit -m "Update map"
   git push
   ```
5. The live site updates within ~1 minute at:
   `https://trackingcalifornia.github.io/lake-county-crc-map`

## Automated sheet sync (fallback)

`.github/workflows/sync-open-now.yml` runs `sync_open_now.py` on a 15-minute
cron (in practice GitHub runs it every few hours on this repo), copies the
schedule columns into `sites.csv`, rebuilds `docs/index.html`, and pushes.
The map no longer depends on this for timely updates; it keeps the values
baked into the page current so the map still works if the Google Sheet cannot
be reached. GitHub disables scheduled workflows after 60 days with no commits;
re-enable with `gh workflow enable sync-open-now.yml`.

## Troubleshooting: map not reflecting a change

1. **Rule out caching.** Hard-refresh (Cmd+Shift+R) or open the site in a
   private window. The page is cached up to 10 minutes and the published
   Sheet CSV up to 5, so allow about 10 minutes after a form submission.
   To see what the map is reading, open the published CSV URL
   (`SHEET_CSV_URL` in `sync_open_now.py`) in a browser.
2. **Check the sheet.** Confirm the site's `name` in the sheet matches
   `sites.csv` exactly — the sync silently skips unmatched names (logged as a
   warning in the workflow run, not shown anywhere else).
3. **Check the workflow ran:**
   ```
   gh run list --workflow=sync-open-now.yml --limit 5
   ```
   If the latest run failed, view why with `gh run view <run-id> --log-failed`.
   If it hasn't run recently, force one: `gh workflow run sync-open-now.yml`
4. **Check the commit landed on `main`:**
   ```
   git fetch origin
   git show origin/main:sites.csv | grep "<site name>"
   ```
   If the value here is already correct, the sync worked and the problem is
   downstream in GitHub Pages (step 5), not the sync.
5. **Check the Pages build status:**
   ```
   gh api repos/trackingcalifornia/lake-county-crc-map/pages/builds/latest --jq '{status, created_at, updated_at}'
   ```
   Normal builds finish in 20-30 seconds. If it's sat in `"building"` for more
   than a couple of minutes, check `https://www.githubstatus.com` for a GitHub
   Pages incident before assuming it's this repo — a GitHub-side outage can
   stall builds with nothing wrong on our end.
6. **Kick a fresh build** (only useful if GitHub Pages itself isn't degraded):
   ```
   gh api -X POST repos/trackingcalifornia/lake-county-crc-map/pages/builds
   ```
7. **Fallback:** if the automated path stays broken, the manual update path
   above always works as a bypass — a normal human push tends to unstick a
   misbehaving deploy even when bot-triggered ones don't.

## Embedding on another website

Paste this HTML wherever you want the map to appear:

```html
<iframe
  src="https://trackingcalifornia.github.io/lake-county-crc-map"
  width="100%"
  height="650px"
  frameborder="0"
  style="border-radius: 6px;">
</iframe>
```

## Enabling GitHub Pages (one-time setup)

1. Go to the repo on GitHub
2. Settings -> Pages
3. Source: Deploy from a branch
4. Branch: `main` / folder: `/docs`
5. Save

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — Copyright 2026 Tracking California (Public Health Institute). You may share and adapt this work for any purpose with attribution.

## Contact

Scarlet Sands-Bliss — scarlet.sandsbliss@trackingcalifornia.org
