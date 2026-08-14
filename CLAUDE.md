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

## Automated sync

`.github/workflows/sync-open-now.yml` runs `sync_open_now.py` on a 15-minute
cron to pull `date`/`opens_at`/`closes_at` from a published Google Sheet,
rebuilds `docs/index.html` if `sites.csv` changed, and commits/pushes both.
GitHub does not reliably honor the 15-minute schedule on low-traffic repos -
allow a couple of hours before treating it as broken. Full troubleshooting
steps (workflow logs, Pages build status, manual bypass) are in the README.

## "Open Now" is computed client-side, not server-side (added 2026-08-14)

There is no manual `open_now` toggle anymore. COAD (Terre/Dan) requested
fully automatic activation tied to heat events, which have no recurring
schedule, so each site's `date` + `opens_at`/`closes_at` in the sheet defines
a one-off activation window. The actual on/off decision is computed live in
each visitor's browser (`getPacificNow()`/`isOpenNow()`/`refreshOpenNow()` in
`build_map.py`'s JS template), explicitly in Pacific time via
`Intl.DateTimeFormat`, re-checked every 60 seconds - not baked into
`docs/index.html` at build/sync time. This was a deliberate choice over
computing it server-side in `sync_open_now.py`: a server-side flip would
still be bounded by the 15-minute (or slower, see incident below) cron
cadence, which was part of what prompted this change in the first place.

**Naming/color note:** the CSV's internal `status` value is still literally
`Active`/`Setup` (unchanged, not partner-facing) - only the *displayed*
label and colors changed: `Active` now renders as "Ready - in Standby" with
a lighter, more yellow orange (`#fbbf24`, adjusted 2026-08-14 from an
earlier `#f59e0b`) marker, and "Open Now" is a green (`#27ae60`) ring rather
than the amber ring it used to be; the "Only show centers open now" toggle
text is green (`#1a6b2e`) to match. Don't be confused by `status ===
'Active'` checks still in the code; that's the internal value, not what
Terre/Dan see on the map.

**Known limitation:** the open/close window assumes same-day hours
(`opens_at` < `closes_at`); an overnight window spanning midnight isn't
handled and would need `isOpenNow()` extended if that's ever requested.

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
