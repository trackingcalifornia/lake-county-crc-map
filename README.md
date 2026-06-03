# Lake County COAD Community Resilience Centers Map

Interactive map of Lake County COAD community resilience centers, showing
site status, contact information, and links for each location. Maintained
by Tracking California in partnership with Lake County COAD and the Lake
County Office of Climate Resiliency.

## How to update site information

Open `sites.csv` (or the shared Google Sheet if one has been set up).
Each row is one site. Columns:

| Column | Description |
|---|---|
| `name` | Site name |
| `address` | Full street address |
| `lat` | Latitude (decimal degrees — look up on Google Maps if adding a new site) |
| `lng` | Longitude (decimal degrees — will be negative for California) |
| `status` | `Active` or `Setup` |
| `phone` | Phone number |
| `website` | Full URL including https:// |
| `facebook` | Full Facebook URL |
| `hours` | Operating hours during events (optional) |
| `services` | Brief description of services offered (optional) |
| `notes` | Any additional notes shown in the popup (optional) |

**Note:** Site coordinates are approximate and should be verified.
To find exact coordinates: open Google Maps, right-click the location,
and copy the lat/lng shown at the top of the menu.

## How to rebuild and publish the map

1. Open RStudio and set your working directory to this folder.
2. Make sure these R packages are installed:
   ```r
   install.packages(c("leaflet", "readr", "dplyr", "htmltools"))
   ```
3. Render the map:
   ```r
   quarto::quarto_render("index.qmd")
   ```
   Or click **Render** in RStudio with `index.qmd` open.
4. The updated map will be saved to `docs/index.html`.
5. Commit and push:
   ```
   git add docs/index.html sites.csv
   git commit -m "Update map"
   git push
   ```
6. The live site updates within ~1 minute at:
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
