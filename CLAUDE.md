# Lake County CRC Map - Project Notes for Claude

## Project overview

Interactive Leaflet map of Lake County COAD community resilience centers
(cooling/warming/overnight sites), built by Tracking California in partnership
with Lake County COAD and the Lake County Office of Climate Resiliency. Static
site, served via GitHub Pages from `docs/`. See `README.md` for the full
update workflow, `sites.csv` column reference, and troubleshooting steps -
this file only covers what isn't already there.

## Stack

- `build_map.py` (Python 3, stdlib only) reads `sites.csv` and bakes a static
  `docs/index.html`. This is the authoritative build path.
- Repo also contains Quarto files (`index.qmd`, `_quarto.yml`) from an earlier
  approach - **not currently used to generate the live site.** Verify which
  path is authoritative before assuming `quarto render` does anything live.
- No R in this repo, unlike most of `tc-repos/` - pure Python/HTML/Leaflet.

## Critical gotcha: rebuild is not optional

Editing `sites.csv` alone and pushing does **not** update the live site -
GitHub Pages serves the pre-baked `docs/index.html`, not the CSV. Always run
`python3 build_map.py` after any `sites.csv` edit, before committing. (Learned
2026-07-14: Clear Lake Grange stayed "In Setup" live after its CSV status was
already "Active," because the HTML hadn't been regenerated.)

## How schedule data reaches the map (changed 2026-11-05)

Partners submit a Google Form: first day, optional last day, opening and
closing time, optional "Open overnight?". "Form Responses 1" -> "DO NOT TOUCH"
tab (latest submission per site; columns `name, date, opens_at, closes_at,
last_date, overnight`, filled by FILTER/MAXIFS formulas; `last_date` is form
column G, `overnight` column H) -> published to web as CSV.

**Primary path: the browser reads the published CSV directly**
(`loadLiveSchedule()` in `build_map.py`'s JS template, on load and every 5
min). Google sends CORS headers on both the 307 redirect and the final
response, so this works from GitHub Pages with no server. Updates land in
about 5-10 minutes.

**Fallback: the GitHub Actions sync** (`.github/workflows/sync-open-now.yml`
-> `sync_open_now.py`) still copies the same columns into `sites.csv` and
rebuilds, so the baked-in values are current if Google can't be reached.
Its "15-minute" cron runs about every 4 hours in practice (measured Oct 2026),
and GitHub disabled it once for 60 days without commits (re-enabled
2026-11-05). Neither matters for timeliness anymore.

**All date/time parsing is in the browser** (`parseDay()`, `parseMinutes()`,
`scheduleFor()`, `isOpenNow()`, `hoursLabel()`). `build_map.py` bakes the raw
sheet text. Don't reintroduce Python-side parsing; it would drift from the
live path. `TEMPLATE` is a raw string (`r'''`) because the JS contains regex
backslashes.

**Rules:** daily mode repeats the hours on each day first..last; overnight
`Yes` is one continuous window from first-day opening to last-day closing;
closing earlier than opening is treated as overnight (next morning if no last
day); `12am` closing = end-of-day midnight; `parseDay()` also accepts a raw
Sheets serial number (the `last_date` column showed `46332` before being
formatted as Date).

**Naming/color note:** the CSV's internal `status` value is still literally
`Active`/`Setup` (unchanged, not partner-facing) - only the *displayed*
label and colors changed: `Active` now renders as "Ready - in Standby" with
a lighter, more yellow orange (`#fbbf24`, adjusted 2026-08-14 from an
earlier `#f59e0b`) marker, and "Open Now" is a green (`#27ae60`) ring rather
than the amber ring it used to be; the "Only show centers open now" toggle
text is green (`#1a6b2e`) to match. Don't be confused by `status ===
'Active'` checks still in the code; that's the internal value, not what
Terre/Dan see on the map.

**Known limitation:** one schedule per site at a time ("newest form wins").
Different hours on different days (Mon 9-5, Tue 10-3) still need one
submission per day, each after the previous day ends.

## Known incident: 2026-08-06 GitHub Actions/Pages outage

During an active Lake County heatwave, GitHub Actions and Pages both went
down; git operations and the API stayed up. Bypass used: run
`sync_open_now.py` + `build_map.py` manually, push straight to `main`, and
mirror the live page via
`https://raw.githack.com/trackingcalifornia/lake-county-crc-map/main/docs/index.html`
(serves straight from git storage through a CDN, bypassing Pages). Not for
permanent use - swap any iframe embeds back to the real Pages URL once GitHub
recovers.

**Related gotcha (same incident):** a stacked PR (base = another feature
branch, not `main`) can show "MERGED" on GitHub without its commits ever
reaching `main`, if the base branch merged into `main` *before* the stacked
PR merged into the base. `gh pr list` status alone won't catch this - verify
with `git merge-base --is-ancestor <commit> origin/main`.

## Open decision: hosting

Whether to move off GitHub Pages for resilience against outages like
2026-08-06. Posit Connect only makes sense if TC/Berkeley already has server
access to publish to (unconfirmed). shinyapps.io ruled out (session-hour
billing, wrong model for static files). Plain static hosts (Netlify, Vercel,
Cloudflare Pages) are arguably the better technical fit if the goal is just
avoiding a repeat of this outage.

## Roles

Terre Logsdon (Lake County Office of Climate Resiliency) and Pastor Shannon
lead the COAD resilience center work and site content decisions. Scarlet is a
supporting/technical contributor, not the lead on CRC grant applications or
site partnerships - defer to them on which sites/status changes to make, not
just how to make them technically.

## Logging

Log work on this repo under CHARM / HEATwise in the tracker, not Admin TC.
