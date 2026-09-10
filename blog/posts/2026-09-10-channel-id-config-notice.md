---
title: "A Note on a Backend Config Issue and changes to the Tracker Dashboard"
date: 2026-09-10
slug: channel-id-config-notice
excerpt: "We found a mismatch between some internal channel ID references and the real channel IDs. Here's what happened, why it didn't affect what you see, and what we're doing about it."
tags: [maintenance, organization]
---

During routine maintenance, we found that a handful of channel ID references in our internal configuration didn't actually match the real YouTube channel ID for that channel, likely left over from an earlier slopy copy-paste jobs during the early development of the dashboard.

**The short version: nothing on the dashboard was wrong.** No stream data, avatars, subscriber counts, or "Watch on YouTube" links were affected for any channel, as far as we've been able to confirm.

## How this happened 

Our dashboard doesn't actually look up a channel's stream data by that internal ID first. It looks it up by **channel name**. Only if the name lookup comes up empty does it fall back to matching by ID.

Since the affected channels' names still matched correctly between our configuration and our database, every stream page, logo, and subscriber count kept resolving through the name match. The incorrect ID was just sitting there unused, like a typo in a comment nobody reads.

<div style="background: rgba(79,195,247,0.06); border-left: 3px solid #4fc3f7; border-radius: 4px; padding: 1rem 1.25rem; margin: 1.5rem 0; font-size: 0.9rem;">
If the affected channel's stored name had drifted even slightly from what's in our configuration: a trailing space, a different bracket style, a rename. This same mismatch could have quietly shown the wrong avatar, subscriber count, or outbound YouTube link. That's the scenario we're specifically checking for as part of the fix, even though we haven't found an instance of it happening.
</div>

## What we're doing

We're auditing and correcting the internal ID references as part of ongoing maintenance, alongside adding a few new channels. This is purely a backend cleanup, you shouldn't notice any change on the dashboard itself.

As always, thanks for using the tracker. If you ever spot something that looks off: a wrong avatar, a link that goes to the wrong channel, anything, feel free to reach out via the contact info in the footer.

## New additions

While we were in there, we also added a few new names to the tracker:

- **Project:LIVIUM — Chapter 3**, a new wave of talents joining Project:LIVIUM: Arvent Durra, Pierre Iddamont, Edgar Tyrsonted, Kian Kishanya, and Wansy Hyerr.
- **MIQELA**, a new organisation joining the tracker for the first time, with three talents: Ayako Miyuki, Teaqilla, and Stellaria Vernakila.
- **Matchuan**, a new talent under Nawasena.

Welcome to the tracker! It may take a little while for stream history to build up on their pages as we start collecting data.

## Removal

We have also removed **JKT48V** from the dashboard, following the group's cessation of activities on September 5th. Their org and channel pages will no longer be updated going forward.

## Summary

- ✅ Found backend issue and fixed it for posterity
- ✅ Additional new names and org on the tracker
- ✅ Removal of JKT48v from the IDVT dashboard

More updates as data from the mentioned names above are to be collected.
