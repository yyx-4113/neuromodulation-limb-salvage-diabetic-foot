# Reproducibility package: methodological appraisal of a Chinese expert consensus on spinal cord stimulation for diabetic foot

This repository contains the reproducibility package for the manuscript
"Methodological appraisal of a Chinese expert consensus on spinal cord stimulation for diabetic foot",
submitted to *BMC Health Services Research*.

It is a **secondary research** project: one published clinical practice guideline was appraised with
AGREE II, RIGHT and a GRADE evidence profile reconstructed from the guideline's own cited literature.
No human participants, samples or identifiable data were involved.

## What is in this release

| Path | Contents |
|---|---|
| `manuscript/methodological-appraisal-chinese-expert-consensus_v1.0_clean.md` | Clean manuscript source (no internal notes) |
| `manuscript/methodological-appraisal-chinese-expert-consensus_v1.0_submit.md` | Submission source with in-text citations converted to continuous journal numbering |
| `submission/methodological-appraisal-chinese-expert-consensus_v1.0_submission.docx` | Typeset submission docx (structured abstract, 4 tables, supplementary list) |
| `submission/abstract_for_submission_v0.2.md` | Four-paragraph structured abstract (323 words) |
| `submission/manuscript_references_final_2026-11-20.csv` | Final 13-reference journal list with consensus-label mapping |
| `submission/consensus_references_submission_final_2026-11-20.csv` | 47-reference table of the appraised consensus, with verification status |
| `submission/reference_table_final_2026-11-20.md` | Reference verification notes |
| `submission/cover-letter_redacted.md` | Cover letter (reviewer emails redacted) |
| `audit/agree2_scoring_2026-11-18.csv` | Appraiser 1, 23 AGREE II item scores with rationales and locators |
| `audit/agree2_appraiser2_returned_2026-11-19.csv` | Appraiser 2, masked independent AGREE II scores |
| `audit/agree2_interrater_reliability_2026-11-19.json` | AGREE II agreement statistics (exact, κ, weighted κ, ICC(2,1), bootstrap CI) |
| `audit/right_reporting_2026-11-18.csv` | RIGHT 35-subitem ratings with locators |
| `audit/grade_evidence_profile_2026-11-18.csv` | Appraiser 1 GRADE profiles (9 outcomes) |
| `audit/grade_appraiser2_completed_2026-11-20.csv` | Appraiser 2 masked independent GRADE profiles |
| `audit/grade_interrater_reliability_2026-11-20.json` | GRADE final-certainty and per-domain agreement |
| `audit/consensus_numeric_claims_2026.csv` | Five claims and their common cited source |
| `audit/consensus_recommendation_citation_map_2026.csv` | Recommendation-to-citation mapping |
| `audit/consensus_references_2026.csv` | Consensus reference inventory |
| `audit/key_citation_verification_report_2026-11-18.md` | Full-text verification of prioritised citations |
| `audit/ref3_fulltext_claim_audit_2026-11-18.md` | Source-claim mismatch audit for the five claims |
| `audit/numeric_provenance.csv` | Per-number provenance ledger |
| `scripts/` | Computation, revision, docx-build and consistency-gate scripts |
| `MANIFEST.sha256` | SHA-256 checksums of every file in this release |

## Reproduce

All appraisal scores and agreement statistics can be regenerated from the CSV inputs:

```bash
python scripts/compute_agree2_interrater_2026-11-19.py --selftest
python scripts/gate_submission_package_2026-11-20.py
python scripts/gate_submission_ready_v1.0.py
```

Expected headline statistics (derived from the deposited JSON/CSV, not hard-coded in the gate):
AGREE II exact item agreement 9/23 (39.1%), unweighted κ 0.258, linearly weighted κ 0.651,
ICC(2,1) 0.853 (95% CI 0.663–0.941); GRADE final-certainty agreement 9/9.

The gate expectations are derived from the product files; hard-coded expected numbers are not used.

## Software versions

| Item | Version |
|---|---|
| Python | 3.13.x |
| python-docx | 1.2.0 |
| Instruments | AGREE II, RIGHT, GRADE (version-free methodological standards) |

## Caveats and honest limits

1. This is an appraisal of a **single** guideline; results do not generalise to other SCS guidelines.
2. GRADE profiles are a **retrospective reconstruction** from the consensus' own cited literature, not a de novo systematic review.
3. GRADE κ=1.0 is non-informative in this near-constant distribution and is not used as a headline result.
4. The 100% inconsistency and 88.9% publication-bias domain "agreement" reflect agreement that the domain was *not assessable*, not concordance on graded judgements.
5. Two appraisers meet the AGREE II minimum, though the instrument preferably uses four.
6. RIGHT was applied by one reviewer; no RIGHT inter-rater agreement is available.
7. The source-claim mismatch is reported as a documentation failure established from the documents, **not** as a determination about intent.
8. Copyrighted full texts of third-party articles are **not** redistributed here; only derived facts, verification records and the appraisal dataset are included.

## Data availability

All appraisal data, scripts and checksums are publicly available in this repository under a version tag.
No "available on request" statement is used. Zenodo archival DOI: to be assigned on acceptance.

## Author

Yongxin Yang, B.M. — The Second Affiliated Hospital of Fujian University of Traditional Chinese
Medicine, Fuzhou, Fujian 350003, China. ORCID 0009-0004-9698-6552.
GitHub (research): `yyx-4113`. No postgraduate degree is claimed.
