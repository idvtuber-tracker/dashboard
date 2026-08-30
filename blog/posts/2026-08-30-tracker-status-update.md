---
title: "Tracker Status Update: New Orgs, a Change of Plans for the Pi, and an Indie Tracker Sibling"
date: 2026-08-30
tags: [announcement, organization, development]
excerpt: "Two new orgs join the roster, the Raspberry Pi's original migration plan got scrapped in favor of something more interesting, and the indie tracker project is starting to take shape."
---

A quick check-in on where things stand with IDVTuber Tracker, since there's been a bit of movement behind the scenes lately.

## Two more orgs on the board

**Reverie** and **ENIGMYST Pro** have been added to the tracked roster. That brings the total organization count up again, on top of the 36+ orgs and 220+ channels already being tracked.

Is this the last addition? Maybe! Every time I think the roster is "done," another group turns up that's worth tracking. So consider this the *hopeful* final addition rather than a firm one. If another group surfaces that deserves a spot, it'll get added like the rest.

## A change of plans for the Raspberry Pi

The original idea was to fully migrate the main tracker's self-hosted runner onto a dedicated SBC (the Raspberry Pi 3B+), replacing the whole PC setup entirely. That migration is now **cancelled**.

Instead, the Pi is being repurposed to run a *second*, fully separate tracker instance, one dedicated to **indie VTubers**: talents who aren't affiliated with any organization. Rather than squeezing everything into one pipeline, the indie tracker gets its own repos, its own database, its own `ORG_MAP`-equivalent, and now its own hardware. The main tracker stays where it is.

This felt like a better use of the Pi's capacity than just being a like-for-like replacement runner. One box, two independent jobs, no risk of the indie experiment destabilizing the main dashboard.

## Will the indie dashboard link up with the main one?

Possibly. Down the line, but there's no firm plan yet. The two dashboards are intentionally isolated right now (separate repos, separate Postgres, separate GCP project), which was the right call while the indie side was still being stood up and debugged. Once it's stable, it'd be nice to have some kind of cross-link between "orgs" and "indies" for anyone browsing the site, but figuring out a *good* way to do that, without just bolting on a janky nav link, still needs some thought. No rush on this one.

## Sitting on the fence about extra API quota for indies

The indie tracker is currently running on its own modest YouTube Data API allocation, and honestly, it's probably fine for now given how few channels it's tracking. Requesting a quota increase for it feels premature. That's more of a "when the indie list actually grows" problem than a "right now" problem. If the tracked indie count climbs meaningfully, that's when it'll be worth filing the request. Until then, no action needed.

## Summary

- ✅ Reverie and ENIGMYST Pro added. Main tracker now covers 30++ orgs
- ❌ Pi migration for the main tracker = cancelled
- ✅ Pi repurposed to run the indie tracker instead
- 🤔 Indie/main dashboard linking -> undecided, revisit later
- 🤔 Extra API quota for indies -> on hold until the indie roster grows

More updates as the indie side matures.
