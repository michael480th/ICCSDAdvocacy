#!/usr/bin/env python3
"""
Iowa school-district audit scraper / parser.

Goal: answer "how many Iowa school districts COMPLETED audits by year, and how
many PASSED (clean opinion / no significant findings)?" by building a by-year
table from the primary source — the Auditor of State's public audit reports.

Two modes (run with no internet knowledge required for `parse`):

  parse   Read a folder of already-downloaded district audit PDFs and emit CSVs.
          This is the RELIABLE path: download the PDFs however you like (manual,
          the site's own export, a separate fetch) and point this at the folder.

  scrape  Attempt to walk the Auditor of State audit-reports index, filter to
          school districts, download each PDF, then parse. The site is a CMS
          whose exact search endpoint may change; the request details live in
          clearly marked constants below so you can point them at the live page
          without touching the parsing logic.

Output (written to --out dir):
  iowa_audit_reports.csv          one row per district per fiscal year
  iowa_audit_summary_by_year.csv  the aggregate answer, by fiscal year

Install:
  pip install requests beautifulsoup4 pdfplumber

Why opinion/findings detection works: the Auditor of State publishes a
standardized CSD (community school district) report template, so the
Independent Auditor's Report and Schedule of Findings use consistent wording
across the private CPA firms and the State Auditor alike.

NOTE ON COVERAGE: Iowa Code 11.6(1)(a) requires EVERY school district to be
audited annually (no small-district exemption like cities have). So the
expected denominator is effectively all ~325 districts each year; a district
with no report for a fiscal year is "behind / delinquent" (e.g., Iowa City CSD).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional

# Approximate count of Iowa public school districts (2024-25); used only for the
# completion-rate column. Adjust per the fiscal year you are analyzing.
IOWA_DISTRICT_COUNT = 325

# ---------------------------------------------------------------------------
# scrape-mode configuration — confirm against the live site before relying on it
# ---------------------------------------------------------------------------
# The Auditor of State audit-reports landing page. The actual result list is
# typically served by a search/AJAX endpoint behind this page; inspect the
# network panel on the live site and set INDEX_URL / params accordingly.
AOS_BASE = "https://www.auditor.iowa.gov"
INDEX_URL = f"{AOS_BASE}/reports/audit-reports"

# A polite, browser-like UA. Be respectful: low request rate, cache to disk.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY_SEC = 1.0  # be a good citizen

# Words that mark a report as a school-district audit (vs. city/county/agency).
SCHOOL_HINTS = re.compile(
    r"\b(community school district|school district|\bC\.?S\.?D\.?\b|"
    r"\bCSD\b|consolidated school)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------
def extract_text(pdf_path: Path) -> str:
    """Return the full text of a PDF. Prefers pdfplumber, falls back to pypdf."""
    try:
        import pdfplumber  # type: ignore

        chunks = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! could not read {pdf_path.name}: {exc}", file=sys.stderr)
        return ""


# ---------------------------------------------------------------------------
# Parsing: opinion, findings, fiscal year, entity name
# ---------------------------------------------------------------------------
def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_opinion(text: str) -> str:
    """Classify the auditor's opinion from the Independent Auditor's Report.

    Order matters: check the most severe / most specific phrasings first.
    Returns one of: unmodified, qualified, adverse, disclaimer, unknown.
    """
    t = _norm(text).lower()

    # Disclaimer of opinion
    if re.search(r"do not express an opinion|disclaim.{0,20}opinion", t):
        return "disclaimer"
    # Adverse
    if re.search(r"do not present fairly|present unfairly", t):
        return "adverse"
    # Qualified — "except for" within an opinion context
    if re.search(r"in our (qualified )?opinion[^.]{0,200}\bexcept for\b", t) or re.search(
        r"\bexcept for\b[^.]{0,120}present fairly", t
    ):
        return "qualified"
    # Unmodified / clean
    if re.search(r"present fairly, in all material respects", t):
        return "unmodified"
    return "unknown"


def count_findings(text: str) -> tuple[int, int, bool, bool, bool]:
    """Return (num_financial_findings, num_statutory_findings,
    material_weakness, significant_deficiency, going_concern).

    Iowa CSD reports use a "Schedule of Findings and Questioned Costs" with two
    parts: findings related to the financial statements, and "Other Findings
    Related to Required Statutory Reporting". Findings are numbered (e.g.
    "(A) ...", "II-A-...", or "Finding 2023-001"). We count numbered finding
    markers within each section as a robust approximation.
    """
    t = text

    material_weakness = bool(re.search(r"material weakness(es)?\b", t, re.I)) and not bool(
        re.search(r"no material weakness", t, re.I)
    )
    significant_deficiency = bool(
        re.search(r"significant deficienc(y|ies)\b", t, re.I)
    ) and not bool(re.search(r"no .{0,15}significant deficienc", t, re.I))
    going_concern = bool(re.search(r"going concern", t, re.I)) and not bool(
        re.search(r"no .{0,15}going concern|not .{0,15}going concern", t, re.I)
    )

    # Split into the two standard sections if we can find their headers.
    fin_sec, stat_sec = _split_findings_sections(t)
    fin_count = _count_finding_markers(fin_sec)
    stat_count = _count_finding_markers(stat_sec)
    return fin_count, stat_count, material_weakness, significant_deficiency, going_concern


def _split_findings_sections(text: str) -> tuple[str, str]:
    """Best-effort split into (financial findings section, statutory findings section)."""
    lower = text.lower()
    fin_start = lower.find("findings related to the financial statement")
    stat_start = lower.find("other findings related to required statutory reporting")
    if stat_start == -1:
        stat_start = lower.find("findings related to required statutory reporting")
    if fin_start == -1 and stat_start == -1:
        # No recognizable schedule headers; treat whole doc as financial section.
        return text, ""
    if fin_start == -1:
        fin_start = 0
    fin_sec = text[fin_start : stat_start if stat_start != -1 else len(text)]
    stat_sec = text[stat_start:] if stat_start != -1 else ""
    return fin_sec, stat_sec


# Finding markers seen in Iowa reports: "Finding 2023-001", "(A)", "II-A-",
# "Item No. 1", numbered list entries within a findings schedule.
_FINDING_MARKERS = re.compile(
    r"(finding\s+\d{4}-\d{2,3})"
    r"|(\b[IVX]+-[A-Z]-\d+\b)"
    r"|(\bitem\s+no\.?\s*\d+\b)",
    re.IGNORECASE,
)


def _count_finding_markers(section: str) -> int:
    if not section:
        return 0
    # Phrases that explicitly say there were none.
    if re.search(r"\bno (matters|findings|instances)\b", section, re.I) and not _FINDING_MARKERS.search(
        section
    ):
        return 0
    markers = {m.group(0).lower() for m in _FINDING_MARKERS.finditer(section)}
    return len(markers)


_FY_PATTERNS = [
    re.compile(r"(?:fiscal year (?:ended|ending)|year ended)\s+june 30,?\s*(\d{4})", re.I),
    re.compile(r"\bFY\s?(\d{4})\b", re.I),
    re.compile(r"\b(20\d{2})\b"),  # last-resort: any 20xx
]


def detect_fiscal_year(text: str, filename: str = "") -> Optional[int]:
    head = text[:4000]
    for pat in _FY_PATTERNS[:2]:
        m = pat.search(head)
        if m:
            return int(m.group(1))
    # filename hint, e.g. "..._FY2023..." or "23_CSD_..."
    m = re.search(r"(20\d{2})", filename) or re.search(r"\b(\d{2})_CSD", filename)
    if m:
        val = m.group(1)
        return int(val) if len(val) == 4 else 2000 + int(val)
    for pat in _FY_PATTERNS[2:]:
        m = pat.search(head)
        if m:
            return int(m.group(1))
    return None


def detect_entity(text: str, filename: str = "") -> str:
    head = text[:2000]
    m = re.search(r"([A-Z][A-Za-z.\-' ]+?(?:Community )?School District)", head)
    if m:
        return _norm(m.group(1))
    # fallback: filename stem
    return Path(filename).stem


def detect_auditor(text: str) -> str:
    head = text[:6000].lower()
    if "auditor of state" in head and "office of auditor of state" in head:
        return "Auditor of State"
    m = re.search(r"\n([A-Z][A-Za-z.,&' ]+(?:LLP|L\.L\.P\.|PLC|P\.C\.|CPAs?|& Co\.?))\b", text[:8000])
    if m:
        return _norm(m.group(1))
    return "unknown"


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------
@dataclass
class AuditRecord:
    entity_name: str
    fiscal_year: Optional[int]
    report_date: str = ""
    audited_by: str = ""
    opinion: str = "unknown"
    num_financial_findings: int = 0
    num_statutory_findings: int = 0
    material_weakness: bool = False
    significant_deficiency: bool = False
    going_concern: bool = False
    report_url: str = ""
    source_file: str = ""


def parse_pdf(pdf_path: Path) -> Optional[AuditRecord]:
    text = extract_text(pdf_path)
    if not text.strip():
        return None
    if not SCHOOL_HINTS.search(text[:3000]) and not SCHOOL_HINTS.search(pdf_path.name):
        # Not obviously a school-district report; skip in parse-all mode.
        return None
    fin, stat, mw, sd, gc = count_findings(text)
    return AuditRecord(
        entity_name=detect_entity(text, pdf_path.name),
        fiscal_year=detect_fiscal_year(text, pdf_path.name),
        audited_by=detect_auditor(text),
        opinion=detect_opinion(text),
        num_financial_findings=fin,
        num_statutory_findings=stat,
        material_weakness=mw,
        significant_deficiency=sd,
        going_concern=gc,
        source_file=pdf_path.name,
    )


def parse_dir(pdf_dir: Path) -> list[AuditRecord]:
    records: list[AuditRecord] = []
    pdfs = sorted(pdf_dir.rglob("*.pdf"))
    print(f"Found {len(pdfs)} PDF(s) under {pdf_dir}")
    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf.name}")
        rec = parse_pdf(pdf)
        if rec:
            records.append(rec)
    return records


# ---------------------------------------------------------------------------
# scrape mode
# ---------------------------------------------------------------------------
def scrape_index(years: range, download_dir: Path) -> list[str]:
    """Walk the AOS audit-reports index and return school-district PDF URLs.

    The exact result endpoint/markup must be confirmed against the live site;
    this implements the common pattern (HTML list of <a href="*.pdf">). If the
    site uses an AJAX/JSON search, adapt the request here — parsing downstream
    is unaffected.
    """
    try:
        import requests  # type: ignore
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        sys.exit("scrape mode needs: pip install requests beautifulsoup4")

    download_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"GET {INDEX_URL}")
    resp = session.get(INDEX_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pdf_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = f"{a.get_text(' ', strip=True)} {href}"
        if href.lower().endswith(".pdf") and SCHOOL_HINTS.search(label):
            url = href if href.startswith("http") else f"{AOS_BASE}{href}"
            pdf_urls.append(url)

    print(f"Discovered {len(pdf_urls)} candidate school-district PDF link(s).")
    if not pdf_urls:
        print(
            "  No links found via the simple HTML pattern. The index is likely\n"
            "  JavaScript/AJAX-rendered. Inspect the live page's network calls,\n"
            "  set INDEX_URL to the JSON search endpoint, or use `parse` mode on\n"
            "  manually downloaded PDFs.",
            file=sys.stderr,
        )

    saved: list[str] = []
    for url in pdf_urls:
        name = re.sub(r"[^A-Za-z0-9._-]", "_", url.split("/")[-1]) or "report.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        dest = download_dir / name
        if dest.exists():
            saved.append(str(dest))
            continue
        try:
            time.sleep(REQUEST_DELAY_SEC)
            r = session.get(url, timeout=60)
            r.raise_for_status()
            dest.write_bytes(r.content)
            saved.append(str(dest))
            print(f"  saved {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! failed {url}: {exc}", file=sys.stderr)
    return saved


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
DETAIL_FIELDS = list(asdict(AuditRecord("", None)).keys())


def write_detail_csv(records: list[AuditRecord], out_dir: Path) -> Path:
    path = out_dir / "iowa_audit_reports.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DETAIL_FIELDS)
        w.writeheader()
        for r in sorted(records, key=lambda x: (x.fiscal_year or 0, x.entity_name)):
            w.writerow(asdict(r))
    return path


def write_summary_csv(records: list[AuditRecord], out_dir: Path) -> Path:
    by_year: dict[int, dict] = {}
    for r in records:
        if r.fiscal_year is None:
            continue
        b = by_year.setdefault(
            r.fiscal_year,
            dict(
                fiscal_year=r.fiscal_year,
                districts_with_filed_audit=0,
                unmodified_opinions=0,
                modified_opinions=0,
                unknown_opinions=0,
                zero_findings=0,
                with_material_weakness=0,
            ),
        )
        b["districts_with_filed_audit"] += 1
        if r.opinion == "unmodified":
            b["unmodified_opinions"] += 1
        elif r.opinion in ("qualified", "adverse", "disclaimer"):
            b["modified_opinions"] += 1
        else:
            b["unknown_opinions"] += 1
        if r.num_financial_findings == 0 and r.num_statutory_findings == 0:
            b["zero_findings"] += 1
        if r.material_weakness:
            b["with_material_weakness"] += 1

    path = out_dir / "iowa_audit_summary_by_year.csv"
    fields = [
        "fiscal_year",
        "districts_with_filed_audit",
        "completion_rate_vs_expected",
        "unmodified_opinions",
        "modified_opinions",
        "unknown_opinions",
        "zero_findings",
        "with_material_weakness",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for year in sorted(by_year):
            b = by_year[year]
            b["completion_rate_vs_expected"] = round(
                b["districts_with_filed_audit"] / IOWA_DISTRICT_COUNT, 3
            )
            w.writerow({k: b.get(k, "") for k in fields})
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    pp = sub.add_parser("parse", help="parse a folder of downloaded PDFs")
    pp.add_argument("--pdf-dir", required=True, type=Path)
    pp.add_argument("--out", default=Path("./out"), type=Path)

    ps = sub.add_parser("scrape", help="attempt to scrape the AOS index, then parse")
    ps.add_argument("--years", default="2015-2025", help="e.g. 2015-2025")
    ps.add_argument("--download-dir", default=Path("./audit_pdfs"), type=Path)
    ps.add_argument("--out", default=Path("./out"), type=Path)

    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    if args.mode == "parse":
        records = parse_dir(args.pdf_dir)
    else:
        lo, hi = (int(x) for x in args.years.split("-"))
        saved = scrape_index(range(lo, hi + 1), args.download_dir)
        records = parse_dir(args.download_dir) if saved else []

    if not records:
        print("No school-district audit records produced. See notes above.", file=sys.stderr)
        return 1

    d = write_detail_csv(records, args.out)
    s = write_summary_csv(records, args.out)
    print(f"\nWrote {len(records)} record(s):\n  {d}\n  {s}")
    print("\nReminder: a district with NO row for a fiscal year is behind/delinquent")
    print("(Iowa requires an annual audit of every district). 'Passed' = unmodified")
    print("opinion AND/OR zero findings — see both columns in the summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
