#!/usr/bin/env python3
"""Extract each district's Summary Schedule of Prior Audit Findings, per finding.

For audit year Y, the report restates the PRIOR year's (Y-1) findings and marks each
Corrected / Not corrected / Partially corrected / No longer applicable. This measures
how many of a year's findings are still unresolved 12 months later.

Parsing is per-finding: we anchor on each prior-year finding ID (e.g. 2023-001 in a
FY2024 report, or statutory codes like IV-H-23) and read the status token that follows
it. That is far more reliable than counting status words in a loosely-bounded section.

PDF text is cached under the scratchpad so re-runs are instant.

Writes data/prior-findings-status.csv and data/prior-findings-debug.txt.
Run from repo root: python scripts/extract_prior_findings.py
"""
import csv, glob, os, re, sys
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(ROOT, "auditreports")
OUT = os.path.join(ROOT, "data", "prior-findings-status.csv")
DEBUG = os.path.join(ROOT, "data", "prior-findings-debug.txt")
CACHE = os.environ.get("PDFTEXT_CACHE",
    "/tmp/claude-0/-home-user-ICCSD-Financial-Benchmarking/"
    "61785954-0cf5-548a-be50-c04026ffd875/scratchpad/pdftext")

YEARS = range(2021, 2026)
HEAD = re.compile(r"Summary Schedule of Prior", re.I)
# Stop only on the next *section heading* — NOT on "Corrective Action Plan", which also
# appears inside the schedule's own column header ("Reason for Recurrence and Corrective
# Action Plan or Other Explanation") and would chop off every finding.
CONT_STOP = re.compile(r"Independent auditor's report on", re.I)
NO_PRIOR = re.compile(r"no prior[- ]?(year)? ?audit findings|were no prior|"
                      r"no findings? (were )?(reported|noted) in the prior|"
                      r"There were no prior", re.I)


def pdf_text_pages(path):
    """Per-page text, cached to disk (joined with a page marker)."""
    key = os.path.join(CACHE, os.path.basename(path) + ".txt")
    if os.path.exists(key):
        return open(key, encoding="utf-8").read().split("\f")
    os.makedirs(CACHE, exist_ok=True)
    pages = [(p.extract_text() or "") for p in PdfReader(path).pages]
    open(key, "w", encoding="utf-8").write("\f".join(pages))
    return pages


def schedule_text(pages, fy):
    """Isolate the real prior-findings schedule (not the table of contents)."""
    py = fy - 1
    has_content = re.compile(rf"corrected|{py}-0?\d\d|[IVX]{{1,3}}-[A-Z]-{py%100:02d}|"
                             r"no prior", re.I)
    for i in range(len(pages) - 1, -1, -1):     # scan from the back
        t = pages[i]
        if HEAD.search(t) and has_content.search(t):
            chunk = [t]
            for j in range(i + 1, min(i + 3, len(pages))):
                t2 = pages[j]
                if HEAD.search(t2) or CONT_STOP.search(t2):
                    break
                if has_content.search(t2):
                    chunk.append(t2)
                else:
                    break
            return "\n".join(chunk)
    return None


STATUS = [
    ("partially", re.compile(r"partially corrected", re.I)),
    ("not_corrected", re.compile(r"not\s+(?:been\s+|yet\s+)?corrected|has not been corrected|"
                                 r"\bunresolved\b|\bnot corrected\b", re.I)),
    ("no_longer", re.compile(r"no longer applicable|no longer valid|no longer required|"
                             r"not applicable|no longer a finding", re.I)),
    ("corrected", re.compile(r"\bcorrected\b|\bresolved\b|\bimplemented\b", re.I)),
]


def classify(window):
    for label, rx in STATUS:
        if rx.search(window):
            return label
    return "unknown"


def parse_findings(text, fy):
    """Return list of (finding_id, status) for each prior-year finding in the schedule."""
    py = fy - 1
    anchor = re.compile(rf"\b{py}-0?\d\d\b|\b[IVX]{{1,3}}-[A-Z]-{py%100:02d}\b")
    seen, hits = set(), []
    matches = list(anchor.finditer(text))
    for k, m in enumerate(matches):
        fid = m.group(0)
        if fid in seen:
            continue
        seen.add(fid)
        end = matches[k + 1].start() if k + 1 < len(matches) else len(text)
        hits.append((fid, classify(text[m.start():end])))
    return hits


def main():
    rows, dbg = [], []
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    for fy in YEARS:
        for p in pdfs:
            base = os.path.basename(p)
            m = re.match(r"(.+?)-(\d{4})\.pdf$", base)
            if not m or int(m.group(2)) != fy:
                continue
            dist = m.group(1)
            try:
                pages = pdf_text_pages(p)
            except Exception as e:
                print(f"  !! {base}: {e}", file=sys.stderr)
                continue
            text = schedule_text(pages, fy)
            if text is None:
                rows.append([dist, fy, "", "", "", "", "", "", "no_schedule_found"])
                continue
            if NO_PRIOR.search(text) and not re.search(r"\d{4}-0?\d\d", text):
                rows.append([dist, fy, 0, 0, 0, 0, 0, 0, "no_prior_findings"])
                continue
            hits = parse_findings(text, fy)             # per-finding (for IDs / severity)
            # Authoritative AGGREGATE counts via status tokens — robust to the
            # column-interleaving that makes per-finding adjacency unreliable.
            pa = len(re.findall(r"partially corrected", text, re.I))
            nc = len(re.findall(r"not\s+(?:been\s+|yet\s+)?corrected", text, re.I))
            nl = len(re.findall(r"no longer applicable|no longer valid|"
                                r"no longer required|not applicable", text, re.I))
            co = len(re.findall(r"\bcorrected\b", text, re.I)) - nc - pa
            co = max(co, 0)
            total_tok = nc + pa + co + nl
            actionable = nc + pa + co
            pct = round(100 * nc / actionable, 1) if actionable else ""
            # flag if per-finding ID count disagrees with token total (worth eyeballing)
            note = "" if len(hits) == total_tok else f"check(ids={len(hits)},tok={total_tok})"
            rows.append([dist, fy, total_tok, nc, pa, co, nl, pct, note])
            dbg.append(f"===== {dist} FY{fy}  total={total_tok} not_corr={nc} part={pa} "
                       f"corr={co} no_longer={nl} pct_not={pct} ids={len(hits)} =====\n"
                       + "  ".join(f"{fid}:{st}" for fid, st in hits) + "\n"
                       + re.sub(r"[ \t]+", " ", text)[:1500])
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["district", "audit_fy", "prior_total", "prior_not_corrected",
                    "prior_partially", "prior_corrected", "prior_no_longer",
                    "pct_not_corrected", "note"])
        w.writerows(rows)
    with open(DEBUG, "w") as fh:
        fh.write("\n\n".join(dbg))
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(rows)} rows)")
    for r in rows:
        print(f"  {r[0][:22]:22} FY{r[1]}  total={str(r[2]):>2}  not_corr={str(r[3]):>2}  "
              f"corr={str(r[5]):>2}  no_longer={str(r[6]):>2}  pct_not={str(r[7]):>5}  {r[8]}")


if __name__ == "__main__":
    main()
