# 📊 IDVTuber Dashboard

The live analytics dashboard for the [IDVTuber Tracker](https://github.com/idvtuber-tracker/tracker) project. This repository holds the **generated static HTML site** deployed to GitHub Pages — it does not contain any application source code.

---

## What This Is

The dashboard provides a browsable, multi-level view of YouTube livestream analytics collected from Indonesian VTuber (IDVTuber) channels. It covers more than 16 organisations, tracking concurrent viewers, view counts, likes, and comments across live and past streams.

The site is rebuilt and pushed here automatically by the tracker's GitHub Actions workflow every few minutes. You do not need to run anything manually to keep it up to date.

---

## Site Structure

The site is organised as four levels of pages, each linking to the next:

```
index.html                             ← All tracked organisations
└── {org}/index.html                   ← Channels within an organisation
    └── {org}/{channel}/index.html     ← Stream history for a channel
        └── {org}/{channel}/{id}.html  ← Detail page for a single stream
```

**Organisation index** — Cards for every tracked org, showing active stream count and a summary of recent activity.

**Channel list** — All channels belonging to an organisation, with subscriber counts, logos, and a count of tracked streams.

**Stream cards** — A chronological list of streams for a channel, including peak viewers, total view count, and stream duration. Live and upcoming streams are highlighted.

**Stream detail** — Full time-series charts for concurrent viewers, likes, and comments over the course of a single stream, alongside summary statistics.

All timestamps are displayed in **WIB (UTC+7)**. The site supports light and dark themes, following the system preference by default with a manual toggle available.

---

## How It Gets Updated

This repo is the deployment target for the tracker pipeline. The flow on each tracker run is:

1. `tracker.py` collects analytics from the YouTube Data API and writes them to Supabase PostgreSQL.
2. `generate_dashboard.py` reads from PostgreSQL and the long-term SQLite archive (`history.db`), then writes a fresh `dashboard/` folder.
3. The tracker pushes the updated `dashboard/` folder to this repository via `git push`.
4. A `repository_dispatch` event (`deploy-dashboard`) is fired on this repo.
5. The `deploy_dashboard.yml` workflow here picks up that event and deploys the site to GitHub Pages.

Only pages that have changed (new streams or currently live streams) are regenerated on each run. Completed VOD pages are written once and never touched again, keeping deploy times fast.

---

## Repository Contents

```
.
├── dashboard/                 ← Generated site output (auto-updated)
│   ├── index.html
│   ├── manifest.json          ← Partial-build state (managed by tracker)
│   └── {org}/...
└── .github/
    └── workflows/
        └── deploy_dashboard.yml   ← GitHub Pages deployment workflow
```

Everything inside `dashboard/` is machine-generated. Do not edit those files manually — they will be overwritten on the next tracker run.

---

## Related Repositories

| Repository | Purpose |
|---|---|
| [`idvtuber-tracker/tracker`](https://github.com/idvtuber-tracker/tracker) | Source code — tracker, dashboard generator, archiver |
| [`idvtuber-tracker/dashboard`](https://github.com/idvtuber-tracker/dashboard) | This repo — generated site + Pages deployment |
| `idvtuber-tracker/idvt-history` | Long-term stream archive (`history.db`, SQLite) |

---

## Deployment

GitHub Pages is configured to serve from the `dashboard/` folder on the `main` branch. The `deploy_dashboard.yml` workflow is triggered by the `repository_dispatch` event sent by the tracker after each successful push, ensuring the live site reflects the latest data shortly after every collection cycle.
