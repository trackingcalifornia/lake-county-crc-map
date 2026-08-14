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
| `date` | The date this site is scheduled to activate, e.g. `2026-08-20` or `8/20/2026` — synced from a published Google Sheet, see below. Blank means not currently scheduled. |
| `opens_at` / `closes_at` | Free text like `9am` or `4:00pm` — synced from the same sheet. Drives both the displayed hours range and the automatic "Open Now" on/off below. |

Survey response workbooks in `source/` are the source data for site entries.

## Automatic "Open Now" status

A site shows as "Open Now" (green ring around its marker) automatically,
the moment Pacific time enters the window defined by its `date` +
`opens_at`/`closes_at`, and automatically turns back off when `closes_at`
passes — computed live in each visitor's browser, not by a server or a
rebuild. To activate a site for a heat event, set its `date`, `opens_at`,
and `closes_at` in the Google Sheet (see below); to deactivate it afterward,
clear the `date` field back out so it doesn't imply the same window applies
again next time.

`date`, `opens_at`, and `closes_at` are pulled automatically from a
published Google Sheet by `sync_open_now.py` (see `.github/workflows/`).
The sheet's `date` column should be formatted as **Date** and `opens_at`/
`closes_at` as **Time** (Format → Number → Date or Time, or a custom format
like `h:mm am/pm`) with data validation set to "Is valid date"/"Is valid
time" — this is what lets someone type `8/20/2026` or `9am` into a cell and
have it normalize automatically, rather than relying on free-text parsing to
guess at whatever they typed. `build_map.py` parses whatever the Date/Time
format exports (it tolerates ISO or US date order, and time with/without
seconds or a space before am/pm) and treats the site as not scheduled if it
doesn't recognize the format, rather than guessing.

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

## Automated sheet sync

The `date`/`opens_at`/`closes_at` schedule is kept in sync automatically from
a published Google Sheet (name + those three columns), via
`.github/workflows/sync-open-now.yml`. That workflow runs on a 15-minute
cron, calls `sync_open_now.py` to pull the sheet and update `sites.csv`,
rebuilds `docs/index.html` if anything changed, and commits/pushes both
files. Partners editing the sheet don't need to touch this repo. In practice
GitHub does not always run the schedule exactly every 15 minutes on
low-traffic repos — allow up to a couple of hours before treating it as
broken.

This cron only needs to run often enough to pick up a newly entered or
changed schedule — the actual on/off flip for "Open Now" does not depend on
it (see above); that happens live in the visitor's browser regardless of
when this workflow last ran.

## Troubleshooting: map not reflecting a change

1. **Rule out caching.** Hard-refresh (Cmd+Shift+R) or open the site in a
   private window.
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
