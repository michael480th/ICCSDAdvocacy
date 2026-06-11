"""Shared site-navigation bar injected into every published HTML page.

Keeps the public pages linked together so the GitHub Pages site can be shared as a
single entry point. Import and drop nav("<active-key>") immediately after <body>.
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
    "</style>"
)

_ITEMS = [
    ("overview",  "index.html",                            "How ICCSD compares"),
    ("trend",     "iccsd-liquidity-trend.html",            "Reserves over time"),
    ("filing",    "iccsd-filing-vs-uab-large.html",        "Audit timeliness"),
    ("car",       "car-vs-audited.html",                   "CAR vs. audited"),
    ("benchmark", "iowa-district-financial-benchmark.html", "Full benchmark (15 districts)"),
]


def nav(active):
    parts = ['<span class="brand">Iowa City CSD finances</span>']
    for key, href, label in _ITEMS:
        parts.append(f'<span class="cur">{label}</span>' if key == active
                     else f'<a href="{href}">{label}</a>')
    return _CSS + '<nav class="sitenav">' + "".join(parts) + "</nav>"
