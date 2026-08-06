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
| `status` | `Active` or `Setup` |
| `phone` | Phone number |
| `website` | Full URL including https:// |
| `services` | Pipe-separated: `cooling\|warming\|overnight` |
| `power` | Pipe-separated: `generator\|solar\|battery\|electric` |
| `pets` | Short pet policy text |
| `capacity` | Max occupancy number (optional) |
| `notes` | Additional notes shown in popup (optional) |
| `coords_approx` | `true` if coordinates are estimated; shows a warning in popup |

Survey response workbooks in `source/` are the source data for site entries.

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

## Automated "Open Now" sync

`open_now` is kept in sync automatically from a published Google Sheet (name +
open_now columns), via `.github/workflows/sync-open-now.yml`. That workflow
runs on a 15-minute cron, calls `sync_open_now.py` to pull the sheet and
update `sites.csv`, rebuilds `docs/index.html` if anything changed, and
commits/pushes both files. Partners editing the sheet don't need to touch
this repo. In practice GitHub does not always run the schedule exactly every
15 minutes on low-traffic repos — allow up to a couple of hours before
treating it as broken.

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
