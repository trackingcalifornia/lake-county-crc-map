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

## Contact

Scarlet Sands-Bliss — scarlet.sandsbliss@trackingcalifornia.org
