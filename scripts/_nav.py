"""Shared site-navigation bar injected into every published HTML page.

Keeps the public pages linked together so the GitHub Pages site can be shared as a
single entry point. Import and drop nav("<active-key>") immediately after <body>.

The site is organized as four "doors" — the questions a member of the public asks, in
order — plus two muted links (a catch-all for the narrower/older analyses, and the
oversight-committee materials). Secondary pages pass active="more" so the "Other
analyses" link highlights.
"""

_CSS = (
    "<style>"
    '.sitenav{max-width:960px;margin:0 auto;padding:14px 20px 0;display:flex;gap:8px;'
    'flex-wrap:wrap;align-items:center;font:600 13.5px/1.4 -apple-system,BlinkMacSystemFont,'
    '"Segoe UI",Roboto,Helvetica,Arial,sans-serif}'
    '.sitenav .brand{color:#0f172a;margin-right:4px;font-weight:800}'
    '.sitenav a,.sitenav .cur{display:inline-block;padding:6px 13px;border-radius:999px;'
    'text-decoration:none;border:1px solid #e2e8f0}'
    '.sitenav a{color:#2563eb;background:#fff}'
    '.sitenav a:hover{background:#eff6ff;border-color:#bfdbfe}'
    '.sitenav .cur{color:#0f172a;background:#f1f5f9;border-color:#cbd5e1}'
    '.sitenav .sep{flex-basis:100%;height:0;margin:0}'
    '.sitenav .more{color:#64748b;border-color:#eef2f7;background:#fff;font-weight:600}'
    '.sitenav .more:hover{background:#f8fafc;border-color:#e2e8f0}'
    '.sitenav .more.cur{color:#0f172a;background:#f1f5f9;border-color:#cbd5e1}'
    "</style>"
)

# Primary "doors" — the four questions, in the order a resident asks them.
_PRIMARY = [
    ("overview",  "index.html",                             "How ICCSD compares"),
    ("cushion",   "iccsd-cushion.html",                     "Does it have a cushion?"),
    ("data",      "iowa-district-financial-benchmark.html", "Dig into the data"),
]
# "Can we trust the numbers?" (integrity-checks.html) was moved out of the primary doors into
# "Other analyses" — it's a 3rd/4th-level detail page, not a landing-page question. The integrity
# page now navigates with active="more". Old pages get re-synced by scripts/resync_nav.py.
# Secondary links — narrower/older analyses, and the oversight-committee materials.
_SECONDARY = [
    ("more",      "other-analyses.html",                    "Other analyses"),
    ("foc",       "making-the-foc-work.html",               "Oversight committee"),
]


def nav(active):
    parts = ['<span class="brand">Iowa City CSD finances</span>']
    for key, href, label in _PRIMARY:
        parts.append(f'<span class="cur">{label}</span>' if key == active
                     else f'<a href="{href}">{label}</a>')
    parts.append('<span class="sep"></span>')
    for key, href, label in _SECONDARY:
        cur = " cur" if key == active else ""
        parts.append(f'<a class="more{cur}" href="{href}">{label}</a>')
    return _CSS + '<nav class="sitenav">' + "".join(parts) + "</nav>"
