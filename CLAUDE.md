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
cron to pull `open_now`/`opens_at`/`closes_at` from a published Google Sheet,
rebuilds `docs/index.html` if `sites.csv` changed, and commits/pushes both.
GitHub does not reliably honor the 15-minute schedule on low-traffic repos -
allow a couple of hours before treating it as broken. Full troubleshooting
steps (workflow logs, Pages build status, manual bypass) are in the README.

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
