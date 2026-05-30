#!/usr/bin/env python3
"""
Clean the raw "Type of Entity = School" list from the Auditor of State search
into a de-duplicated, join-ready roster of actual Iowa school districts.

The raw audit-entity list is NOT a clean district roster. It contains:
  - sub-entities that are not districts (booster clubs, departments, FFA/dance
    programs)  -> dropped
  - audit-type rows ("Reaudit", "Special Investigation of ...")  -> dropped
  - the same district written several ways ("Denver CSD" vs "Denver Community
    School District", "Akron-Westfield" vs the misspelled "Akron-Westfiled")
    -> merged
  - districts that REORGANIZED/MERGED over the years, so an older name and a
    newer name both appear (Garner-Hayfield vs Garner-Hayfield-Ventura)
    -> kept separate but flagged, because enrollment differs by era

Output (data/iowa_districts_cleaned.csv):
  canonical_name, n_source_rows, aliases, needs_review

Then join enrollment (see iowa_audit_scraper-style join or do it in a
spreadsheet) using `canonical_name`. Run:
  python scripts/clean_district_list.py \
      --in data/audit_entities_raw.txt --out data/iowa_districts_cleaned.csv
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# Rows that are NOT a standalone district (dropped). Matched case-insensitively
# as substrings.
DROP_IF_CONTAINS = [
    "booster",
    "athletic",
    "reaudit",
    "special investigation",
    "dance team",
    "future farmers",
    "facility services",
    "horticulture",
]

# Explicit name fixes applied BEFORE normalization (typos / odd legal forms).
PRE_FIXES = {
    "akron-westfiled csd": "akron-westfield csd",
    "olin consolidated independent school": "olin csd",
    "vinton-shellsburg community school district vinton, iowa": "vinton-shellsburg csd",
    "moc-floyd csd": "moc-floyd valley csd",  # MOC-Floyd Valley is the full name
    "moravia": "moravia csd",
}

# Districts that genuinely REORGANIZED — keep both rows, but flag for review
# because they are different entities in different years (enrollment differs).
REVIEW_NOTES = {
    "garner-hayfield csd": "Merged with Ventura (2014) -> Garner-Hayfield-Ventura CSD",
    "garner-hayfield-ventura csd": "Formed 2014 from Garner-Hayfield + Ventura",
    "north fayette csd": "Merged with Valley (2013) -> North Fayette Valley CSD",
    "north fayette valley csd": "Formed 2013 from North Fayette + Valley",
    "galva-holstein csd": "Later merged into Ridge View CSD",
    "schaller crestland csd": "Later merged into Ridge View CSD",
}


def normalize_key(name: str) -> str:
    """Collapse a district name to a canonical match key."""
    s = name.strip().lower()
    s = PRE_FIXES.get(s, s)
    s = re.sub(r"\bd/b/a\b.*$", "", s)          # drop "d/b/a ..." alternate names
    s = re.sub(r"\([^)]*\)", " ", s)            # drop "(Elkader)" style parentheticals
    s = s.replace("community school district", "csd")
    s = s.replace("community school", "csd")
    s = s.replace("consolidated independent school", "csd")
    s = s.replace("independent csd", "csd")     # "West Burlington Independent CSD" canonical form kept via display
    s = re.sub(r",?\s*iowa\b", " ", s)          # drop trailing ", Iowa"
    s = s.replace("&", "and")
    s = re.sub(r"[.'’]", "", s)                 # drop periods/apostrophes
    s = re.sub(r"[\-/]", " ", s)                # hyphens & slashes -> space
    s = re.sub(r"\s+", " ", s).strip()
    return s


def should_drop(name: str) -> bool:
    low = name.lower()
    return any(tok in low for tok in DROP_IF_CONTAINS)


def choose_canonical(variants: list[str]) -> str:
    """Pick a clean display name: prefer a 'CSD' form, then the shortest."""
    csd_forms = [v for v in variants if v.strip().lower().endswith("csd")]
    pool = csd_forms or variants
    return sorted(pool, key=lambda v: (len(v), v))[0].strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default=Path("data/audit_entities_raw.txt"), type=Path)
    ap.add_argument("--out", dest="outfile", default=Path("data/iowa_districts_cleaned.csv"), type=Path)
    args = ap.parse_args()

    raw = [ln.strip() for ln in args.infile.read_text(encoding="utf-8").splitlines() if ln.strip()]
    dropped = [r for r in raw if should_drop(r)]
    kept = [r for r in raw if not should_drop(r)]

    groups: dict[str, list[str]] = {}
    for name in kept:
        groups.setdefault(normalize_key(name), []).append(name)

    rows = []
    review_norm = {normalize_key(k): v for k, v in REVIEW_NOTES.items()}
    for key, variants in groups.items():
        canonical = choose_canonical(variants)
        note = review_norm.get(key, "")
        rows.append(
            dict(
                canonical_name=canonical,
                n_source_rows=len(variants),
                aliases="; ".join(sorted(set(variants))),
                needs_review=note,
            )
        )
    rows.sort(key=lambda r: r["canonical_name"].lower())

    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    with args.outfile.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["canonical_name", "n_source_rows", "aliases", "needs_review"])
        w.writeheader()
        w.writerows(rows)

    merged = [r for r in rows if r["n_source_rows"] > 1]
    review = [r for r in rows if r["needs_review"]]
    print(f"Raw rows ............... {len(raw)}")
    print(f"Dropped (not districts)  {len(dropped)}")
    for d in dropped:
        print(f"    - {d}")
    print(f"Variant groups merged .. {len(merged)}")
    for r in merged:
        print(f"    * {r['canonical_name']}  <=  {r['aliases']}")
    print(f"Unique districts ....... {len(rows)}")
    print(f"Flagged for review ..... {len(review)} (reorganized/merged districts)")
    for r in review:
        print(f"    ! {r['canonical_name']}: {r['needs_review']}")
    print(f"\nWrote {args.outfile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
