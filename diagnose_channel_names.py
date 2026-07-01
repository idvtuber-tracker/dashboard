"""
diagnose_channel_names.py
ONE-OFF DIAGNOSTIC — run this and share the output before we write another
fix. It does not modify anything.

For each target channel below, prints:
  - The ORG_MAP display name (from dashboard_core.ORG_MAP)
  - The channel_name currently stored in Postgres' `channels` table (matched
    by channel_id, which is stable)
  - Every DISTINCT channel_name string found in history.db's `streams` table
    that is either an exact match OR a fuzzy (substring) match against the
    target's first name — so we catch renames, trailing spaces, differing
    brackets, etc.
  - Row counts per distinct name found in history.db, and the earliest/
    latest stream_start for each, so we can see if old data is sitting
    under an orphaned name.

Usage: same env vars as the other scripts (AIVEN_DATABASE_URL / DATABASE_URL,
HISTORY_DB_PATH). Run from the dashboard repo checkout (needs dashboard_core.py
importable, and idvt-history cloned alongside or HISTORY_DB_PATH set).
"""

from dashboard_core import get_conn, get_history_conn, get_channel_rows, ORG_MAP

# Add/remove channel_ids here as needed. These are pulled straight from
# ORG_MAP's PANDAVVA entries for Nakula Nalendra and Sadewa Sagara.
TARGETS = [
    ("Nakula Nalendra【PANDAVVA】", "UCtGgHePeV6ePoTtlEspXJbQ", "Nakula"),
    ("Sadewa Sagara【PANDAVVA】",   "UCaQwGFUjKGFz0kqxJrP6etA", "Sadewa"),
]


def main():
    conn = get_conn()
    hist = get_history_conn()
    if hist is None:
        print("ERROR: could not open history.db — check HISTORY_DB_PATH.")
        return

    db_channels = get_channel_rows(conn)
    db_by_id = {ch["channel_id"]: ch for ch in db_channels}

    for org_map_name, channel_id, fuzzy_key in TARGETS:
        print("=" * 80)
        print(f"ORG_MAP name:        {org_map_name!r}")
        print(f"Channel ID:          {channel_id}")

        db_row = db_by_id.get(channel_id)
        if db_row:
            print(f"Postgres channel_name: {db_row['channel_name']!r}")
            print(f"Postgres table_name:   {db_row['table_name']!r}")
        else:
            print("Postgres channel_name: NOT FOUND by this channel_id!")

        print("\nDistinct channel_name values in history.db matching "
              f"'{fuzzy_key}' (case-insensitive):")
        rows = hist.execute(
            """
            SELECT channel_name,
                   COUNT(*) AS n,
                   MIN(stream_start) AS earliest,
                   MAX(stream_start) AS latest
            FROM streams
            WHERE channel_name LIKE ?
            GROUP BY channel_name
            ORDER BY n DESC
            """,
            (f"%{fuzzy_key}%",),
        ).fetchall()

        if not rows:
            print(f"  (none found — no row in history.db has a channel_name "
                  f"containing '{fuzzy_key}' at all)")
        else:
            for r in rows:
                exact = "  <-- EXACT MATCH to Postgres name" if db_row and r["channel_name"] == db_row["channel_name"] else ""
                exact2 = "  <-- EXACT MATCH to ORG_MAP name" if r["channel_name"] == org_map_name else exact
                print(f"  {r['channel_name']!r}: {r['n']} streams, "
                      f"{r['earliest']} -> {r['latest']}{exact2}")
        print()

    conn.close()
    hist.close()


if __name__ == "__main__":
    main()
