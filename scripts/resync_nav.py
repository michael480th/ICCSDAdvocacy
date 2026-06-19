#!/usr/bin/env python3
"""Re-sync the shared site-nav into every published *.html (after a _nav.py change), without
re-running each page's full builder. Replaces the <nav class="sitenav">...</nav> block in place."""
import re, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIVE = {  # filename -> active nav key (default 'more' for the long tail of secondary pages)
 "index.html":"overview", "iccsd-vs-peers.html":"overview",
 "iccsd-cushion.html":"cushion", "iowa-district-financial-benchmark.html":"data",
 "making-the-foc-work.html":"foc", "other-analyses.html":"more",
}
def nav_only(active):
    h = nav(active); return h[h.index("<nav"):]   # strip the <style> prefix; pages keep their own CSS
n = 0
for path in glob.glob(os.path.join(ROOT, "*.html")):
    html = open(path).read()
    if '<nav class="sitenav">' not in html: continue
    active = ACTIVE.get(os.path.basename(path), "more")
    html2 = re.sub(r'<nav class="sitenav">.*?</nav>', nav_only(active), html, count=1, flags=re.S)
    if html2 != html:
        open(path, "w").write(html2); n += 1
print(f"re-synced nav in {n} files")
if __name__ == "__main__": pass
