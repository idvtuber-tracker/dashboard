"""
generate_blog.py
Converts markdown posts in blog/posts/*.md into static HTML pages that share
the dashboard's exact nav bar, footer, theme toggle, fonts, and CSS variables
(imported straight from dashboard_core.py — no visual drift possible).

Writes:
  dashboard/blog/index.html          <- post list, with a client-side tag
                                         filter (no separate tag pages —
                                         clicking a tag sets #tag=<slug> and
                                         JS shows/hides matching cards)
  dashboard/blog/{slug}.html         <- individual posts
  dashboard/blog/feed.xml            <- basic RSS feed (optional, cheap)

No database, no YouTube API, no manifest/dirty-tracking. With a handful of
posts, a full rebuild every run costs nothing — this intentionally skips the
partial-build complexity that generate_live.py/generate_backfill.py need for
thousands of stream pages.

Post format (blog/posts/YYYY-MM-DD-slug.md):

    ---
    title: "YouTube API Quota Renewal — Screencast Submitted"
    date: 2026-08-24
    excerpt: "One or two sentences shown on the index and in link previews."
    tags: [infra, api]
    ---

    Body in **markdown**. Headings, lists, code blocks, links all work.

    ![Pi 3B+ next to the old laptop runner](images/pi-setup.jpg)

    *Pi 3B+ next to the old laptop runner*

Images live in blog/images/ (sibling to blog/posts/) and are mirrored into
dashboard/blog/images/ on every build — reference them with a plain
relative path as shown above, from any post or the index alike. Leave a
blank line between the image and its caption line — markdown needs that
blank line to treat them as two separate paragraphs, which is what the
caption styling below targets.

Requires (add to requirements.txt):
    markdown==3.7
    python-frontmatter==1.1.0
"""

import re
import shutil
import logging
from pathlib import Path
from datetime import datetime, date

import frontmatter
import markdown as md

from dashboard_core import (
    OUTPUT_DIR, log as _base_log, _now_local, esc, slugify,
    _html_head, _html_foot, _breadcrumb, _FONTS,
)

log = logging.getLogger(__name__)

POSTS_DIR   = Path("blog/posts")
IMAGES_DIR  = Path("blog/images")
BLOG_OUT    = OUTPUT_DIR / "blog"
SITE_URL    = "https://idvtuber-tracker.github.io/dashboard"
# Matches --blue in theme.css/dashboard.css exactly (dark #4F9EFF / light
# #006FF8) rather than inventing a separate blog color — the blog isn't an
# org, so it borrows the site's own brand-blue identity instead of a
# one-off value that would drift from theme.css whenever that palette
# changes. Previously generate_blog.py called _html_head() with only 3
# positional args, so org_color_light silently fell back to the function's
# generic default (#6e7e00, an olive that has nothing to do with blue) —
# every blog page rendered wrong in light mode until this was caught.
BLOG_ACCENT       = "#4F9EFF"
BLOG_ACCENT_LIGHT = "#006FF8"

MD = md.Markdown(extensions=["fenced_code", "tables", "toc", "smarty"])


def copy_images() -> None:
    """
    Mirrors blog/images/ (source, committed alongside blog/posts/) into
    dashboard/blog/images/ (served). Markdown posts reference images with a
    plain relative path — e.g. ![caption](images/pi-setup.jpg) — which
    resolves correctly from both blog/index.html and blog/{slug}.html since
    they all live directly inside blog/.

    Plain copy, not a diff/sync: harmless and cheap even with a few dozen
    images, and avoids the complexity of tracking deletions. If an image is
    removed from blog/images/ in the source, the old copy under
    dashboard/blog/images/ will just sit there unused until the next time
    someone bothers to clean it — not worth building deletion-tracking for.
    """
    if not IMAGES_DIR.exists():
        return
    dest = BLOG_OUT / "images"
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in IMAGES_DIR.iterdir():
        if src.is_file():
            shutil.copy2(src, dest / src.name)
            copied += 1
    if copied:
        log.info("Copied %d image(s) from blog/images/ to blog/images/ (output).", copied)


# ── extra CSS, layered on top of the shared _BASE_CSS from dashboard_core ──
_BLOG_CSS = """
  .blog-hero { margin-bottom: 2.5rem; }
  .blog-lede { font-size: 0.85rem; color: var(--muted); max-width: 620px; margin-top: 0.75rem; }

  .blog-main-grid { display: grid; grid-template-columns: 1fr 280px; gap: 1.5rem; align-items: start; margin-top: 2.5rem; }
  @media (max-width: 820px) { .blog-main-grid { grid-template-columns: 1fr; } }

  .post-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem; }
  @media (max-width: 640px) { .post-grid { grid-template-columns: 1fr; } }

  .post-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    padding: 1.5rem; position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
  }
  .post-card::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: var(--org-color); transform: scaleX(0); transform-origin: left; transition: transform 0.35s;
  }
  .post-card:hover { border-color: var(--org-color); transform: translateY(-3px); }
  .post-card:hover::after { transform: scaleX(1); }
  /* The title/date/excerpt block is the actual link, stretched over the
     whole card via ::after so the entire card feels clickable — while the
     tag row sits on top (z-index 2) as its own independently clickable
     filter trigger. A single <a> wrapping both would mean nesting a
     tag-chip <a> inside it, which is invalid HTML and breaks click
     targeting on whichever element the browser decides to honor. */
  .post-card-link { display: block; color: inherit; text-decoration: none; }
  .post-card-link::after { content: ''; position: absolute; inset: 0; z-index: 1; }
  .post-date {
    font-size: 0.6rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.75rem; display: block;
  }
  .post-title {
    font-family: 'Fraunces', serif; font-size: 1.15rem; font-weight: 700;
    color: var(--white); line-height: 1.3; margin-bottom: 0.6rem;
  }
  .post-excerpt { font-size: 0.8rem; color: var(--muted); line-height: 1.6; margin-bottom: 1rem; }
  .tag-row { display: flex; gap: 0.4rem; flex-wrap: wrap; position: relative; z-index: 2; }
  .tag-chip {
    font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.18rem 0.5rem; border-radius: 2px;
    border: 1px solid var(--border); color: var(--muted);
  }
  a.tag-chip { cursor: pointer; text-decoration: none; }
  a.tag-chip:hover { border-color: var(--org-color); color: var(--accent-text); }

  /* .sidebar-col, .side-panel, .panel-hdr are intentionally NOT redefined
     here — dashboard.css already ships all three (byte-identical for the
     first two; the third already combines the typography from its own
     line ~366 with the flex layout from line ~582, which together produce
     exactly what this file used to duplicate). Blog pages load
     dashboard.css via _html_head(), so these are inherited for free. */

  /* ── archive sidebar — collapsible year > month groups ── */
  .archive-year-group { border-bottom: 1px solid var(--border); }
  .archive-year-group:last-child { border-bottom: none; }
  .archive-year-toggle {
    display: flex; justify-content: space-between; align-items: center; width: 100%;
    background: var(--surface2); border: none; cursor: pointer; font-family: inherit;
    padding: 0.55rem 1.25rem; font-size: 0.68rem; letter-spacing: 0.1em; color: var(--text);
    transition: color 0.15s;
  }
  .archive-year-toggle:hover { color: var(--accent-text); }
  .archive-year-chevron { font-size: 0.55rem; transition: transform 0.25s; }
  .archive-year-group.is-open .archive-year-chevron { transform: rotate(180deg); }
  .archive-year-body { display: none; }
  .archive-year-group.is-open .archive-year-body { display: block; }

  .archive-month-toggle {
    display: flex; justify-content: space-between; align-items: center; width: 100%;
    background: transparent; border: none; cursor: pointer; font-family: inherit;
    padding: 0.5rem 1.25rem 0.5rem 1.4rem; font-size: 0.6rem; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--muted); transition: color 0.15s;
  }
  .archive-month-toggle:hover { color: var(--accent-text); }
  .archive-month-toggle-left { display: flex; align-items: center; gap: 0.5rem; }
  .archive-month-toggle-left::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: var(--org-color); flex-shrink: 0; }
  .archive-month-count { font-size: 0.55rem; padding: 0.05rem 0.35rem; border-radius: 2px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.1); color: var(--accent-text); margin-left: 0.4rem; }
  .archive-month-chevron { font-size: 0.5rem; transition: transform 0.25s; }
  .archive-month-group.is-open .archive-month-chevron { transform: rotate(180deg); }
  .archive-month-body { display: none; }
  .archive-month-group.is-open .archive-month-body { display: block; }

  .archive-link {
    display: block; padding: 0.4rem 1.25rem 0.4rem 2.2rem; font-size: 0.76rem; line-height: 1.4;
    color: var(--text); text-decoration: none; transition: color 0.15s, background 0.15s;
  }
  .archive-link:hover { color: var(--accent-text); background: var(--surface2); }
  .archive-link .archive-day { color: var(--muted); font-size: 0.68rem; margin-right: 0.4rem; }

  /* ── browse-by-tag panel — click a pill to filter the post grid ── */
  .tag-cloud { padding: 1rem 1.25rem 1.25rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .tag-pill {
    font-size: 0.62rem; letter-spacing: 0.06em; text-transform: uppercase;
    padding: 0.3rem 0.7rem; border-radius: 99px; border: 1px solid var(--border);
    color: var(--muted); text-decoration: none; cursor: pointer;
    display: inline-flex; align-items: center; gap: 0.35rem;
    transition: border-color 0.2s, color 0.2s, background 0.2s;
  }
  .tag-pill:hover { border-color: var(--org-color); color: var(--accent-text); }
  .tag-pill .tag-count { color: var(--muted); font-size: 0.58rem; }
  .tag-pill.active { border-color: var(--org-color); color: var(--accent-text); background: color-mix(in srgb, var(--org-color) 10%, transparent); }

  /* ── filter status bar — shown above the grid once a tag filter is active ── */
  .filter-status {
    display: none; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;
    font-size: 0.72rem; color: var(--muted);
  }
  .filter-status.is-active { display: flex; }
  .filter-status strong { color: var(--accent-text); font-weight: 500; }
  .clear-filter {
    font-size: 0.65rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted); text-decoration: none; border: 1px solid var(--border);
    border-radius: 99px; padding: 0.2rem 0.65rem; transition: border-color 0.2s, color 0.2s;
  }
  .clear-filter:hover { border-color: var(--org-color); color: var(--accent-text); }
  .no-match { display: none; color: var(--muted); font-size: 0.8rem; font-style: italic; padding: 1rem 0; }
  .no-match.is-visible { display: block; }

  .post-header { margin-bottom: 2.5rem; }
  .post-meta-row {
    display: flex; gap: 1.25rem; flex-wrap: wrap; align-items: center;
    font-size: 0.68rem; color: var(--muted); margin-top: 1rem;
  }
  .post-meta-row .tag-chip { border-color: var(--org-color); color: var(--accent-text); }

  .prose { font-size: 0.92rem; line-height: 1.85; color: var(--text); max-width: 720px; }
  .prose h2 {
    font-family: 'Fraunces', serif; font-size: 1.4rem; font-weight: 700;
    color: var(--white); margin: 2.25rem 0 1rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }
  .prose h3 { font-family: 'Fraunces', serif; font-size: 1.1rem; font-weight: 700; color: var(--white); margin: 1.75rem 0 0.75rem; }
  .prose p { margin-bottom: 1.1rem; }
  .prose ul, .prose ol { padding-left: 1.4rem; margin-bottom: 1.1rem; }
  .prose li { margin-bottom: 0.4rem; }
  .prose a { color: var(--accent-text); text-decoration: underline; text-underline-offset: 2px; }
  .prose code {
    font-family: 'DM Mono', monospace; font-size: 0.85em; background: var(--surface2);
    padding: 0.1rem 0.35rem; border-radius: 3px; color: var(--accent-text);
  }
  .prose pre {
    background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    padding: 1rem 1.25rem; overflow-x: auto; margin-bottom: 1.25rem;
  }
  .prose pre code { background: none; padding: 0; color: var(--text); }
  .prose blockquote {
    border-left: 3px solid var(--org-color); padding-left: 1rem; margin: 1.25rem 0;
    color: var(--muted); font-style: italic;
  }
  .prose table { width: 100%; border-collapse: collapse; margin-bottom: 1.25rem; font-size: 0.85rem; }
  .prose th, .prose td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; text-align: left; }
  .prose th { background: var(--surface2); }

  .prose img {
    display: block; max-width: 100%; height: auto; margin: 1.5rem auto;
    border: 1px solid var(--border); border-radius: 6px; background: var(--surface2);
  }
  /* A markdown image on its own line becomes its own <p><img></p>. If the
     very next paragraph is a single italicised line, it's treated as a
     caption: *Pi 3B+ next to the old laptop runner* right below the image,
     no special syntax needed beyond markdown's own *italic* markup. */
  .prose p:has(> img:only-child) + p:has(> em:only-child) {
    text-align: center; font-size: 0.72rem; color: var(--muted);
    margin-top: -1rem; font-style: normal;
  }

  .back-to-blog {
    display: inline-flex; align-items: center; gap: 0.4rem; margin-top: 3rem;
    font-size: 0.68rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--muted); text-decoration: none;
  }
  .back-to-blog:hover { color: var(--accent-text); }
"""


def _load_posts() -> list[dict]:
    posts = []
    if not POSTS_DIR.exists():
        log.warning("No blog/posts directory found — nothing to build.")
        return posts

    for path in sorted(POSTS_DIR.glob("*.md")):
        try:
            post = frontmatter.load(path)
        except Exception as e:
            log.error("Could not parse %s: %s", path, e)
            continue

        meta = post.metadata
        title = meta.get("title") or path.stem
        raw_date = meta.get("date")
        if isinstance(raw_date, (datetime, date)):
            post_date = raw_date if isinstance(raw_date, date) else raw_date.date()
        else:
            try:
                post_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
            except Exception:
                # Fall back to the date prefix in the filename, e.g. 2026-08-24-slug.md
                m = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
                post_date = datetime.strptime(m.group(1), "%Y-%m-%d").date() if m else _now_local().date()

        slug = meta.get("slug") or slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem))
        html_body = MD.convert(post.content)
        MD.reset()

        words = len(post.content.split())
        read_min = max(1, round(words / 200))

        posts.append({
            "title":    title,
            "slug":     slug,
            "date":     post_date,
            "excerpt":  meta.get("excerpt", ""),
            "tags":     meta.get("tags", []) or [],
            "html":     html_body,
            "read_min": read_min,
        })

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _fmt_date(d: date) -> str:
    return d.strftime("%d %b %Y")


def _tag_slug(tag: str) -> str:
    return slugify(tag)


_ARCHIVE_JS = (
    '<script>\n'
    '(function () {\n'
    "  document.querySelectorAll('.archive-year-toggle').forEach(function (btn) {\n"
    "    btn.addEventListener('click', function () {\n"
    "      var grp = btn.closest('.archive-year-group');\n"
    "      var open = grp.classList.toggle('is-open');\n"
    "      btn.setAttribute('aria-expanded', open ? 'true' : 'false');\n"
    "    });\n"
    "  });\n"
    "  document.querySelectorAll('.archive-month-toggle').forEach(function (btn) {\n"
    "    btn.addEventListener('click', function () {\n"
    "      var grp = btn.closest('.archive-month-group');\n"
    "      var open = grp.classList.toggle('is-open');\n"
    "      btn.setAttribute('aria-expanded', open ? 'true' : 'false');\n"
    "    });\n"
    "  });\n"
    "})();\n"
    '</script>\n'
)


def _build_archive_sidebar(posts: list[dict], post_prefix: str = "") -> str:
    """
    Groups posts by year, then by month within each year, as collapsible
    sections — same expand/collapse mechanic as the channel page's
    'All streams — by month' panel. The most recent year and its most
    recent month start open; everything older starts collapsed so a long
    posting history doesn't turn the sidebar into an endless scroll.

    post_prefix lets this same builder be reused from pages at different
    folder depths: "" when called from blog/index.html (posts are
    siblings), "../" when called from blog/tags/{slug}.html (posts are
    one level up).
    """
    if not posts:
        return ""

    years: dict[int, dict[str, list[dict]]] = {}
    for p in posts:
        y = p["date"].year
        m = p["date"].strftime("%B")
        years.setdefault(y, {}).setdefault(m, []).append(p)

    year_html = ""
    for i, (year, months) in enumerate(years.items()):
        year_open = " is-open" if i == 0 else ""
        month_html = ""
        for j, (month_name, month_posts) in enumerate(months.items()):
            month_open = " is-open" if i == 0 and j == 0 else ""
            links = "".join(
                f'          <a class="archive-link" href="{post_prefix}{p["slug"]}.html">'
                f'<span class="archive-day">{p["date"].strftime("%d")}</span>{esc(p["title"])}</a>\n'
                for p in month_posts
            )
            month_html += (
                f'        <div class="archive-month-group{month_open}">\n'
                f'          <button class="archive-month-toggle" aria-expanded="{"true" if (i==0 and j==0) else "false"}">\n'
                f'            <span class="archive-month-toggle-left">{month_name}'
                f'<span class="archive-month-count">{len(month_posts)}</span></span>\n'
                f'            <span class="archive-month-chevron">&#9662;</span>\n'
                f'          </button>\n'
                f'          <div class="archive-month-body">\n{links}          </div>\n'
                f'        </div>\n'
            )
        year_html += (
            f'      <div class="archive-year-group{year_open}">\n'
            f'        <button class="archive-year-toggle" aria-expanded="{"true" if i == 0 else "false"}">\n'
            f'          <span>{year}</span>\n'
            f'          <span class="archive-year-chevron">&#9662;</span>\n'
            f'        </button>\n'
            f'        <div class="archive-year-body">\n{month_html}        </div>\n'
            f'      </div>\n'
        )

    return (
        f'      <div class="side-panel">\n'
        f'        <div class="panel-hdr">All posts</div>\n'
        f'{year_html}'
        f'      </div>\n'
    )


def _build_tag_cloud(posts: list[dict]) -> str:
    """
    Counts posts per tag and renders a pill for each, sorted by frequency
    (most-used tags first) then alphabetically as a tiebreaker. Pills are
    NOT links to separate pages — clicking one sets #tag=<slug> in the URL,
    which the filter JS on the index page picks up (both on click and via
    hashchange) to show/hide post cards client-side. An "All" pill clears
    the filter. Because the filter lives entirely in the URL hash, a
    filtered view is still bookmarkable/shareable even without a real page
    behind it.
    """
    counts: dict[str, int] = {}
    for p in posts:
        for t in p["tags"]:
            counts[t] = counts.get(t, 0) + 1
    if not counts:
        return ""

    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    pills = (
        f'          <a class="tag-pill" href="#" data-tag="">All'
        f'<span class="tag-count">{len(posts)}</span></a>\n'
    )
    pills += "".join(
        f'          <a class="tag-pill" href="#tag={_tag_slug(t)}" '
        f'data-tag="{_tag_slug(t)}" data-label="{esc(t)}">{esc(t)} '
        f'<span class="tag-count">{n}</span></a>\n'
        for t, n in ordered
    )
    return (
        f'      <div class="side-panel">\n'
        f'        <div class="panel-hdr">Browse by tag</div>\n'
        f'        <div class="tag-cloud">\n{pills}        </div>\n'
        f'      </div>\n'
    )


def _tag_chips_html(tags: list[str], base_href: str = "") -> str:
    """
    Tag chips as clickable filter triggers. base_href="" (default, used on
    the index page itself) points at "#tag=<slug>" on the current page.
    base_href="index.html" (used on individual post pages) points back at
    the index with the same hash, so clicking a tag on a post takes you to
    the filtered index rather than nowhere.
    """
    return "".join(
        f'<a class="tag-chip" href="{base_href}#tag={_tag_slug(t)}">{esc(t)}</a>' for t in tags
    )


_TAG_FILTER_JS = """
<script>
(function () {
  function readHashTag() {
    var m = location.hash.match(/tag=([^&]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function tagLabel(slug) {
    var pill = document.querySelector('.tag-pill[data-tag="' + slug + '"]');
    return pill ? pill.getAttribute('data-label') : slug;
  }

  function applyFilter(tag) {
    var cards = document.querySelectorAll('.post-card');
    var visible = 0;
    cards.forEach(function (c) {
      var tags = (c.getAttribute('data-tags') || '').split(' ').filter(Boolean);
      var show = !tag || tags.indexOf(tag) !== -1;
      c.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    document.querySelectorAll('.tag-pill').forEach(function (p) {
      p.classList.toggle('active', (p.getAttribute('data-tag') || '') === tag);
    });

    var status = document.getElementById('filterStatus');
    var text   = document.getElementById('filterStatusText');
    var empty  = document.getElementById('noMatch');
    if (tag) {
      status.classList.add('is-active');
      text.textContent = 'Showing ' + visible + ' post' + (visible === 1 ? '' : 's') +
        ' tagged \\u201C' + tagLabel(tag) + '\\u201D';
    } else {
      status.classList.remove('is-active');
    }
    if (empty) empty.classList.toggle('is-visible', tag && visible === 0);
  }

  window.addEventListener('hashchange', function () { applyFilter(readHashTag()); });

  var clearBtn = document.getElementById('clearFilter');
  if (clearBtn) {
    clearBtn.addEventListener('click', function (e) {
      e.preventDefault();
      history.replaceState(null, '', location.pathname + location.search);
      applyFilter('');
    });
  }

  applyFilter(readHashTag());
})();
</script>"""


def write_blog_index(posts: list[dict]) -> None:
    BLOG_OUT.mkdir(parents=True, exist_ok=True)

    cards = ""
    for p in posts:
        tags_html   = _tag_chips_html(p["tags"])
        tags_attr   = " ".join(_tag_slug(t) for t in p["tags"])
        cards += (
            f'\n      <div class="post-card" data-tags="{tags_attr}">\n'
            f'        <a class="post-card-link" href="{p["slug"]}.html">\n'
            f'          <span class="post-date">{_fmt_date(p["date"])} &nbsp;&#183;&nbsp; {p["read_min"]} min read</span>\n'
            f'          <div class="post-title">{esc(p["title"])}</div>\n'
            f'          <div class="post-excerpt">{esc(p["excerpt"])}</div>\n'
            f'        </a>\n'
            f'        <div class="tag-row">{tags_html}</div>\n'
            f'      </div>'
        )

    empty = '<p class="empty">No posts yet.</p>' if not posts else ""
    archive_panel = _build_archive_sidebar(posts)
    tag_panel     = _build_tag_cloud(posts)

    filter_status = (
        '  <div class="filter-status" id="filterStatus">\n'
        '    <span id="filterStatusText"></span>\n'
        '    <a class="clear-filter" href="#" id="clearFilter">Clear filter &#215;</a>\n'
        '  </div>\n'
    )

    body = (
        f'  <header class="blog-hero">\n'
        f'    <p class="eyebrow">IDVTuber Tracker &#8212; Notes</p>\n'
        f'    <h1>Project <em>Blog</em></h1>\n'
        f'    <p class="blog-lede">Development notes, incident write-ups, and updates on the tracker '
        f'infrastructure — API quota, runner migration, dashboard changes, and anything else worth logging.</p>\n'
        f'  </header>\n'
        + filter_status
        + f'  <div class="blog-main-grid">\n'
        f'    <div>\n'
        f'      <div class="post-grid">{cards}\n      </div>\n'
        f'      <p class="no-match" id="noMatch">No posts match this tag.</p>\n'
        f'    </div>\n'
        f'    <div class="sidebar-col">\n'
        + archive_panel
        + tag_panel
        + f'    </div>\n'
        f'  </div>\n'
        f'  {empty}\n'
        + _ARCHIVE_JS
        + _TAG_FILTER_JS
    )

    html = (
        _html_head("Blog", 1, BLOG_ACCENT, BLOG_ACCENT_LIGHT).replace("</style>", _BLOG_CSS + "</style>")
        + body
        + _html_foot(1)
    )
    (BLOG_OUT / "index.html").write_text(html, encoding="utf-8")
    log.info("Written: blog/index.html (%d posts)", len(posts))


def write_post_page(post: dict) -> None:
    # base_href="index.html" — clicking a tag here jumps to the index with
    # the same #tag=<slug> hash, which its filter JS reads on load.
    tags_html = _tag_chips_html(post["tags"], base_href="index.html")
    bc = _breadcrumb([("Home", "../index.html"), ("Blog", "index.html"), (post["title"], "")])

    body = (
        bc
        + f'  <header class="post-header">\n'
        f'    <p class="eyebrow">IDVTuber Tracker &#8212; Notes</p>\n'
        f'    <h1>{esc(post["title"])}</h1>\n'
        f'    <div class="post-meta-row">\n'
        f'      <span>{_fmt_date(post["date"])}</span>\n'
        f'      <span>{post["read_min"]} min read</span>\n'
        f'      {tags_html}\n'
        f'    </div>\n'
        f'  </header>\n'
        f'  <div class="prose">\n{post["html"]}\n  </div>\n'
        f'  <a class="back-to-blog" href="index.html">&#8592; All posts</a>\n'
    )

    html = (
        _html_head(post["title"], 1, BLOG_ACCENT, BLOG_ACCENT_LIGHT).replace("</style>", _BLOG_CSS + "</style>")
        + body
        + _html_foot(1)
    )
    (BLOG_OUT / f'{post["slug"]}.html').write_text(html, encoding="utf-8")
    log.info("  Written: blog/%s.html", post["slug"])


def write_feed(posts: list[dict]) -> None:
    items = ""
    for p in posts[:20]:
        items += (
            f"  <item>\n"
            f"    <title>{esc(p['title'])}</title>\n"
            f"    <link>{SITE_URL}/blog/{p['slug']}.html</link>\n"
            f"    <guid>{SITE_URL}/blog/{p['slug']}.html</guid>\n"
            f"    <pubDate>{p['date'].strftime('%a, %d %b %Y 00:00:00 +0700')}</pubDate>\n"
            f"    <description>{esc(p['excerpt'])}</description>\n"
            f"  </item>\n"
        )
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        "  <title>IDVTuber Tracker Blog</title>\n"
        f"  <link>{SITE_URL}/blog/index.html</link>\n"
        "  <description>Development notes and infrastructure updates.</description>\n"
        + items +
        "</channel></rss>\n"
    )
    (BLOG_OUT / "feed.xml").write_text(rss, encoding="utf-8")


def generate_blog() -> None:
    posts = _load_posts()
    copy_images()
    write_blog_index(posts)
    for p in posts:
        write_post_page(p)
    write_feed(posts)
    log.info("Blog build complete — %d post(s).", len(posts))


if __name__ == "__main__":
    generate_blog()
