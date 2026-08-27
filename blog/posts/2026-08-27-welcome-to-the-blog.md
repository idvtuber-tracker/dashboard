---
title: "Welcome to the IDVTuber Tracker Blog"
date: 2026-08-27
tags: [announcement, meta]
image: /images/launch-banner.jpg
excerpt: "Why this blog exists, what it'll be used for, and a quick tour of the dashboard for anyone finding the project for the first time."
---

## Hi, welcome

This is the first post on the IDVTuber Tracker blog. If you've landed here
from the dashboard's new nav link and are wondering what this project
actually is, here's the short version.

![IDVTuber Tracker dashboard overview](/blog/images/launch-banner.jpg)

**IDVTuber Tracker** is a non-commercial fan analytics dashboard that
monitors YouTube livestream activity across 220+ Indonesian VTuber
channels, spanning 36 organisations (and counting). It tracks concurrent
viewers, likes, comments, and view counts for every stream it catches,
live and historical, and turns that into a browsable static site. No
account, no login, no tracking of you as a visitor.

## What this blog is for

The dashboard itself only shows numbers. This blog is where the numbers
get context:

- **Stream spotlights** — notable streams, milestone peaks, and anything
  that stood out in the data that week
- **New organisation announcements** — whenever a new org or channel gets
  added to the tracker
- **Behind-the-scenes notes** — the occasional post about how the tracker
  itself works, when something's worth explaining (quota handling, the
  partial-rebuild system, that kind of thing)

Posts will be irregular. This is a one-person side project, not a news
desk. Expect a handful a month, more when something interesting happens
in the scene.

## How the dashboard works, briefly

A self-hosted tracker polls channel activity every 60 seconds using the
YouTube Data API's `activities.list` endpoint (1 unit per call, instead of
the much pricier `search.list`), writes analytics to a Postgres database
during any live stream, and archives finished streams into a long-term
SQLite history once they age out of the 30-day retention window. A static
site generator then turns all of that into the four-level dashboard you're
browsing right now: organisations → channels → streams → per-stream detail
pages with zoomable viewer charts.

If you want the full technical rundown, the
[project's GitHub repo](https://github.com/idvtuber-tracker/tracker) has
the README and architecture notes. If you just want the numbers, the
[dashboard](/index.html) is the place to be.

Thanks for stopping by. More posts soon.
