# ICCSD staffing vs. peer districts — what the standardized data shows

*Unofficial community analysis · August 2026 · sources listed at the end*

## Summary

Iowa City CSD employs about **25% more staff per student** than Waukee, Ankeny and West Des Moines.
That difference is real, not a reporting artifact. But it is **not** an administrative-overhead story:

- **Central administration is the leanest of the four districts.** ICCSD reports 2.53 district
  administrators per 1,000 students, below Ankeny (2.82), West Des Moines (3.51) and Waukee (3.95).
- **Administration as a share of each district's own workforce is essentially flat** — ICCSD 10.8%,
  Ankeny 10.7%, West Des Moines 10.2%, Waukee 9.5%.
- **Over half the entire staffing difference sits in one category:** student support services, which is
  overwhelmingly special-education paraprofessionals — a ratio the Iowa Department of Education has
  already identified as a statewide outlier.

The defensible headline is therefore *not* "ICCSD is 33% above peers on administrative staffing," even
though that arithmetic is correct in isolation. Administrative staffing is up because **everything** is
up. Stated that way the finding is both stronger and harder to dismiss.

## The comparison — FTE per 1,000 students, SY2024-25

| Category | Iowa City | Waukee | Ankeny | W. Des Moines | vs peer avg |
|---|---:|---:|---:|---:|---:|
| District administrators | **2.53** | 3.95 | 2.82 | 3.51 | **−26%** |
| District admin support | 3.13 | 3.45 | 2.75 | 3.73 | −5% |
| School administrators | 5.40 | 3.38 | 4.39 | 4.06 | +37% |
| **School admin support** | **6.93** | 1.94 | 3.30 | 2.96 | **+153%** |
| Teachers | 72.34 | 62.51 | 64.49 | 68.94 | +11% |
| Instructional aides | 27.58 | 28.45 | 23.62 | 26.23 | +6% |
| Guidance counselors | 2.86 | 2.73 | 2.75 | 2.31 | +10% |
| Librarians | 1.60 | 0.93 | 0.86 | 1.32 | +54% |
| **Student support services** | **25.04** | 8.98 | 3.92 | 6.26 | **+292%** |
| Other staff | 17.32 | 12.41 | 11.44 | 17.45 | +26% |
| **TOTAL STAFF** | **166.72** | 134.15 | 124.20 | 140.61 | **+25%** |
| *Enrollment* | *15,013* | *13,917* | *12,746* | *9,110* | |

## Where the excess actually is

ICCSD's total staffing excess over the peer average is **33.7 FTE per 1,000 students**. It decomposes as:

| Category | Share of the excess |
|---|---:|
| Student support services | **55%** |
| Teachers | 21% |
| School admin support | **12%** |
| Other staff | 11% |
| School administrators | 4% |
| Instructional aides | 4% |
| District administrators | **−3%** *(below peers)* |

## What the student support category is

The Iowa Department of Education, in its special-education deficit review, told the district:

> "In FY23 – FY25, the number of special education paraprofessionals ranges from **446 – 479 FTEs**. In
> FY24, the district served a total of 1,594 special education students… please provide additional
> information regarding the district's systemic use of paraprofessionals in its special education program
> since **a 1:3 special education paraprofessional to special education student ratio is an outlier in the
> state.**"

That population sits directly on top of the 376 FTE the federal data reports as student support services.
The district's response identifies a structural cause:

> "ICCSD strives to serve all students in their assigned home school based on their residence. Therefore,
> we do not have programs regionally located at schools which can cause the number of paraeducators to be
> larger than districts that regionally serve students in programs."

If the peer districts regionalize special-education programming and ICCSD does not, that single service-model
choice may account for most of the peer gap. **This is a policy question about service model and cost, not a
question about administrative overhead** — and it connects directly to the district's special-education
deficit, reported above $18M and up roughly $10M in three years.

## The open question

**School administrative support at 6.93 per 1,000 — 153% above the peer average — is unexplained.**
At roughly 3.7 FTE per building against 1.4–2.4 in the peer districts, it is the one place where a coding
difference could plausibly be inflating an administrative category. Two possibilities, not yet distinguished:

1. ICCSD genuinely staffs building offices more heavily than its peers; or
2. ICCSD codes some building-level staff (health aides, paraeducators, media assistants) into administrative
   support where peers code them elsewhere — in which case part of this is the special-education story
   appearing in a second category.

Resolving it requires the district's **Fall BEDS Staff extract** — the annual submission to the Iowa DE
listing each position with its assignment code. That file is **not published**; Iowa DE's Fall BEDS Staff
page is a collection portal. Obtaining it would require an Iowa Code ch. 22 open-records request to the
district or the Department. The public [Iowa School Performance Profiles](https://reports.educateiowa.gov/COE/home/staffCharacteristicsSize)
staff report is not a substitute: it covers **full-time licensed staff only**, and so structurally excludes
the paraeducators at the centre of this question.

## Two cautions

**On language.** The data supports saying ICCSD *codes staff differently than its peers*. It does not, on
its own, support saying the district *misclassifies* staff — that is an assertion of misreporting to the
state, and it requires the BEDS extract to sustain.

**On the outcomes argument.** "More support staff should produce better outcomes" is a fair question, but
paraeducator assignment is driven by individual IEPs, and the district attributes its count to serving
students in home schools rather than regional programs. Comparable outcomes with more paraeducators may
reflect the cost of an inclusion model rather than inefficiency. The state has asked essentially this
question; the district's answer is on the record and can be evaluated on its merits.

## Sources

NCES Common Core of Data, LEA Universe Survey, SY2024-25, retrieved via the Urban Institute Education Data
API — saved to `data/ccd-staffing-peer-2024.csv` (LEAIDs: Iowa City 1914700, Waukee 1930510, Ankeny 1903690,
West Des Moines 1930930) · ICCSD Special Education Deficit presentation to the board, 2026, in the board
archive at `corpus/text/2026/29981/K_01_01_SE_Deficit_Presentation.md` · Iowa Department of Education,
[Fall BEDS Staff](https://educate.iowa.gov/pk-12/data/data-collections/basic-educational-data-survey/fall-beds-staff).

Percentages are computed from the FTE and enrollment values in the CSV; peer averages are the unweighted
mean of the three comparison districts. This is an unofficial document prepared by a community member. It
was not produced by ICCSD, the Financial Oversight Committee, the board, or any state or federal agency.
