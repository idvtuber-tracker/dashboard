\---

title: "September Uptime: What Happened, and Why Some Orgs Are Gone"
date: 2026-10-01
slug: september-2026-uptime-report
excerpt: "Tracker coverage fell to 82.7% in September, the first time it has ever dropped below 90%. Here's what happened, what the number does and doesn't tell you, and why two organisations no longer appear on the dashboard."
tags: \[uptime, status, roster]
---

September was the worst month the tracker has had. Coverage came in at **82.7%**, the first time since the project started that it has dropped below 90%. This post explains what that number means, what went wrong, and what happens next. It also covers why LAV and HRCOME are no longer on the dashboard.

## How uptime is measured

Uptime here is a coverage estimate, not a ping check. A script compares what the tracker should have recorded during every stream with what it actually recorded.

The tracker polls every live stream once a minute. For each stream, the script looks at the timestamps of the rows it wrote. If two consecutive rows are more than five minutes apart, the extra time between them counts as downtime. Uptime is then the covered stream time divided by the total stream time, across every stream in both the live database and the long-term archive.

This measures what matters most: how much of each stream the data actually covers. Hours when nobody was streaming don't count for or against it.

## The number: 82.7%

In September, coverage fell to **82.7%**. Here is every full month since tracking began:

|Month|Stream hours tracked|Coverage|
|-|-|-|
|March|1,507|99.1%|
|April|2,796|98.0%|
|May|2,739|98.9%|
|June|5,895|98.5%|
|July|6,355|97.8%|
|August|5,699|95.1%|
|**September**|**6,717**|**82.7%**|

Coverage had never dropped below 95% before. September is the first month under 90%, and a large drop from August. (February, the first partial month, is left out, and so is October, which has only a day of data so far.)

## What happened

The tracker runs on a local machine, and for about the last two months our internet connection has been intermittent and unstable. That is behind both the August dip and the much bigger September one.

The tracker runs in a six-hour loop that restarts itself by calling GitHub when a cycle ends. When the connection dropped, the runner lost contact, live workflows were cut short, and collection stopped partway through streams.

We didn't always notice right away. In one case the developer didn't notice until the next day. Outages on a self-hosted setup are expected sometimes. Not noticing for a day is the real failure.

## What that means for the data

Gaps in collection show up on the dashboard as gaps in a stream's viewer chart. A stream that began or ended during an outage may have an incomplete record. If a stream you care about looks thin for August or September, that is the likely reason.

Streams that were in progress when an outage began may also show as stuck "live" until they are corrected. This is a known failure mode, and affected streams are cleaned up when found.

## Limitations of this number

The 82.7% figure is an estimate, and it leans optimistic. Treat it as a best case, not a precise measurement.

* **Missing edges.** A stream's start and end are taken from the first and last data points the tracker recorded. If the tracker was down before a stream began, or went down before it ended, that missing time isn't counted as downtime. Only gaps in the middle of a recorded stream are.
* **Missed streams.** A stream the tracker never saw at all leaves no data, so it doesn't appear in the calculation.

Both effects push the estimate up, so real coverage in September was probably somewhat lower than 82.7%. The same method was used for every month in the table, so the trend is still a fair comparison, but the absolute figures should be read with that in mind. Making the measurement stricter is on our list.

## What We're changing

We don't have a single fix to announce, and we'd rather not pretend otherwise. While looking into this, we found several bugs and weak points across the tracker's subsystems. A quick patch for one of them wouldn't make the whole system dependable, so we're planning a gradual redesign of the architecture for reliability.

That will take time. In the meantime, our priority is simple: make sure the tracker works at crucial times, such as debuts from the the listed orgs, or major events which warrants number tracking, and that we find out within minutes, not a day later, if it stops.

## LAV and HRCOME

You may have noticed that **LAV** and **HRCOME** no longer appear on the dashboard. Both have ended their operations as groups, so there is no longer an active roster to track.

Their channels were counted in September's uptime calculation, and removing them could changes the 82.7% figure, but at this point, it's just a closure statement. Their historical data is archived, although regular users unfortunately need to confirm manually to the developer first if they wish to see it. If you have a question about a specific talent's earlier streams, get in touch.

## Looking ahead

82.7% is not where this project should be, and we'd rather say that directly. We'll report October's coverage in the same format so you can see whether things have improved.

Thanks for sticking with the tracker through a rough couple of months.

