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
| `open_now` | `true`/`false` — synced from a published Google Sheet, see below |
| `opens_at` / `closes_at` | Free text like `9am` or `4:00pm` — synced from the same sheet; shown as an hours range on the "Open Now" banner when both are present |

Survey response workbooks in `source/` are the source data for site entries.

## Open Now / hours sync

`open_now`, `opens_at`, and `closes_at` are pulled automatically from a
published Google Sheet by `sync_open_now.py` (see `.github/workflows/`).
The sheet's `opens_at`/`closes_at` columns should be formatted as **Time**
(Format → Number → Time, or a custom format like `h:mm am/pm`) with data
validation set to "Is valid time" — this is what lets someone type `9am`
into the cell and have it normalize automatically, rather than relying on
free-text parsing to guess at whatever they typed. `build_map.py` parses
whatever the Time format exports (it tolerates variations like with/without
seconds or a space before am/pm) and falls back to showing the raw text if
it doesn't recognize the format, rather than dropping it silently.

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
