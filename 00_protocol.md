# PRISMA 2020 & Zero-Hallucination SLR Protocol (`M01_agentic_se_slr_20261111`)

- **Protocol Freeze Date (Local Pre-Harvest Timestamp)**: `2026-11-11` (frozen locally prior to running `stage1_harvest.py`; **Registry Disclosure**: this protocol was frozen in the local replication repository on the same calendar date prior to API execution and was not pre-registered on an external registry such as OSF or PROSPERO—disclosed transparently in §3 and §7; full file-level SHA-256 cryptographic hashes are recorded in `04_manuscript/artifact_sha256_manifest.json`)
- **Exact Time Window**: `2022-11-01` to `2026-10-31` (exact 48-month window partitioned into four equal 12-month cohorts `Y1`–`Y4` by `first_release_date`)
- **Author**: Feiran Liu (China National Association of Engineering Consultants [CNAEC], Beijing, China | `liufr@pku.edu.cn` | ORCID: `0000-0002-9678-1299`)

---

## 1. Zero-Hallucination Iron Rules (Non-Negotiable)

1. **100% API-Derived Bibliographic Metadata (plus Verified Methodological Standards)**:
   - **Zero hand-typed primary-study metadata**. Every primary study in `references.bib`, `review_matrix.csv`, and the manuscript (`title`, `authors`, `year`, `venue`, `doi`, `arxiv_id`, `url`) MUST be parsed programmatically from verbatim HTTP API responses (`OpenAlex`, `arXiv`, `Crossref`, `Semantic Scholar`) normalized and archived under `01_harvest/`.
   - **Zero synthetic search links**: URLs such as `scholar.google.com/scholar?q=...` are strictly forbidden. Every primary study MUST resolve via a real DOI (`https://doi.org/...`) or official arXiv identifier (`https://arxiv.org/abs/...`). Foundational pre-DOI methodological technical reports (specifically Kitchenham & Charters 2007 `EBSE-2007-01`) are paired with their DOI-registered monograph (`10.1201/b19467`) and verified via programmatic author-title assertions.
   - **Zero anonymous/incomplete records**: Anonymous double-blind supplementary packages, short commentary stubs, and standalone non-manuscript uploads are automatically filtered by programmatic verification.

2. **100% Verbatim Quote-Backed & Token-Verified Quantitative Synthesis**:
   - Every headline quantitative metric cited in the manuscript MUST exist in `03_extraction/verified_evidence_ledger.csv` paired with:
     1. Exact `citation_key` and persistent `doi` / `arxiv_id`;
     2. Complete contiguous verbatim supporting passage extracted directly from the cached abstract (`s["abstract"]`), programmatically verified so that **100% of numeric tokens** in `headline_metric` appear verbatim inside `verbatim_quote` and `verbatim_quote` is an exact substring of the cached abstract;
     3. Explicit publication-stage metadata (`Peer-Reviewed` vs. `Preprint`), recorded from Version-of-Record journal/proceedings metadata for publication-stage sensitivity checking.
   - Any statistic that cannot be verified verbatim against the retrieved text/abstract on disk MUST NOT appear in the manuscript.

3. **100% Script-Computed PRISMA, Cohort, Taxonomy & RoB Counts**:
   - Every count in the PRISMA 2020 funnel, 12-month cohorts (`Y1`–`Y4`), Taxonomy layers (`L1`–`L4`), Research Questions (`primary_rq` partition vs. multi-label `rqs`), Risk-of-Bias (`RoB`) distribution, and Peer-Reviewed Sensitivity Analysis MUST be computed directly from `02_screening/screening_log.csv`, `03_extraction/review_matrix.csv`, `03_extraction/preprint_quality_gate_audit.csv`, and `03_extraction/quality_rob_assessment.csv`.

---

## 2. Four-Database Search Strategy + Logged Citation Snowballing

- **Databases Queried Live (`2022-11-01` .. `2026-10-31`)**:
   1. **OpenAlex Works API** (`title_and_abstract.search`, `from_publication_date:2022-11-01,to_publication_date:2026-10-31`)
   2. **arXiv Export API** (exact 5 categories queried in `01_harvest/search_protocol.json`: `cs.SE`, `cs.AI`, `cs.CL`, `cs.PL`, `cs.CR`; `submittedDate:[202211010000 TO 202610312359]`)
   3. **Crossref REST API** (6 structured `query.bibliographic` queries, `from-pub-date:2022-11-01,until-pub-date:2026-10-31`, `type:journal-article,proceedings-article`)
   4. **Semantic Scholar Graph Bulk API** (3-block conjunctive `+`/`|` query, `publicationDateOrYear=2022-11-01:2026-10-31`, `fieldsOfStudy=Computer Science`)
- **Logged Citation Snowballing (PRISMA 2020 "Other Methods")**:
   - Backward and forward citation tracking from core SE agent benchmarks and field studies, with every snowballed candidate fetched via official APIs, logged separately in `01_harvest/records_snowball.jsonl`, and subjected to the exact same `IC1`–`IC4` / `EC1`–`EC6` eligibility and preprint quality gates (no snowball bypass).

---

## 3. Screening, Operationalized Preprint Gate & Quality/RoB Assessment (`IC1–IC4`, `EC1–EC6`)

- **Single-Author Deterministic Screening Disclosure**: Screening and taxonomy coding are executed by a single author via deterministic rule scripts (`100.0%` computational replay identity across `4,205/4,205` deduplicated records); because no independent second human rater participated, Cohen's $\kappa$ inter-rater reliability is not claimed and single-author coding is documented as an internal validity limitation.
- **IC1 (Scope)**: **IC1-A** (Closed-loop LLM-based SE agent with multi-step tool/sandbox/repository interaction) OR **IC1-B** (Empirical RCT, field experiment, MSR repository study, queueing analysis, or governance/security evaluation of AI coding agents/assistants in SE workflows).
- **IC2 (Empirical Rigor)**: Reports original quantitative evaluation, empirical cohort metrics, or formal verification experiments.
- **IC3 (Publication Stage & Four-Criterion Preprint Screening Protocol)**:
   - Peer-reviewed journal/conference/companion/workshop Version-of-Record (with companion/industry/workshop venues explicitly inventoried), **OR** moderated academic preprint passing all four operationalized criteria (logged in `03_extraction/preprint_quality_gate_audit.csv`):
     - **`G1` (Moderated Preprint Server & Named Non-Anonymous Authorship)**: Hosted as a complete scholarly manuscript on a moderated academic preprint repository with named non-anonymous authors (excluding standalone non-manuscript data/code deposits);
     - **`G2` (Full Methodological Manuscript $\ge 6$ Pages)**: Full $\ge 6$-page methodological report with complete abstract ($\ge 160$ characters), excluding short notes/stubs;
     - **`G3` (Verifiable Benchmark, Open Artifact, or Empirical Cohort)**: Reports executable benchmark evaluation, open-source code/dataset artifact, or large-scale practitioner/PR cohort;
     - **`G4` (Age-Stratified Citation Impact Threshold)**: Meets deterministic age-stratified citation impact (`first_release_year <= 2024: cited_by >= 90`; `2025: cited_by >= 45`; `2026: cited_by >= 18`), applied uniformly across database-retrieved and snowballed preprints.
- **IC4 (Window & Language)**: English full text first released or published within `2022-11-01` to `2026-10-31`.
- **Exclusions**:
   - `EC1`: Out-of-scope non-SE application domains, outside window, or non-English text
   - `EC2`: Non-agentic single-turn code completion / static NLP tasks without closed-loop interaction or SE workflow impact
   - `EC3`: Secondary studies (surveys, SLRs, vision/position papers, short $<4$-page stubs, anonymous packages — cited as background only)
   - `EC4`: Insufficient repository/verification depth or peripheral venue without core SE grounding
   - `EC5`: Preprints not yet meeting all four criteria (`G1`–`G4`) of the operationalized `IC3` screening protocol or broad-scope low-selectivity venues
   - `EC6`: Companion datasets, replication packages, frozen tool archives, or earlier preprints consolidated into their parent Version-of-Record study unit
- **Methodological Quality & Risk-of-Bias (`RoB`) Rubric (`Q1`–`Q5`, `0–10`)**:
   - Every included primary study is scored on `Q1` Publication Stage (`0–2`), `Q2` Empirical Control/Ablation (`0–2`), `Q3` Benchmark Realism/Sample Scale (`0–2`), `Q4` Artifact Transparency (`0–2`), and `Q5` Construct/Contamination Validity (`0–2`), classified into `Low RoB` (`8–10`), `Moderate RoB` (`5–7`), or `Elevated RoB` (`0–4`), and exported to `03_extraction/quality_rob_assessment.csv`.
