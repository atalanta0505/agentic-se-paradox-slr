# The Productivity–Verification Paradox in Agentic Software Engineering: A Systematic Literature Review

[![PRISMA 2020](https://img.shields.io/badge/PRISMA-2020%20Compliant-00796B)](./04_manuscript/prisma_2020_checklist.md)
[![Primary Studies](https://img.shields.io/badge/Included%20Studies-N%20%3D%20193-123569)](./03_extraction/review_matrix.md)
[![Search Window](https://img.shields.io/badge/Window-2022--11--01%20to%202026--10--31-37474F)](./00_protocol.md)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0%20%2F%20MIT-blue)](./LICENSE)

**Author:** Feiran Liu  
**Affiliation:** China National Association of Engineering Consultants (CNAEC), Beijing, China  
**ORCID:** [0000-0002-9678-1299](https://orcid.org/0000-0002-9678-1299) | **Contact:** `liufr@pku.edu.cn`

📄 **[Read the Full Manuscript (`manuscript_en.pdf`)](./manuscript_en.pdf)** *(28 pages, two-column PDF compiled via TeX Live `pdflatex`; opens directly in browser)*

---

## Abstract

Generative AI tools in software engineering (SE) have evolved from single-turn code completion into repository-level *coding agents* capable of multi-step planning, command execution, static/dynamic analysis, and pull-request (PR) submission. Following PRISMA 2020 guidelines, this Systematic Literature Review (SLR) synthesizes **N = 193 primary studies** (**155** peer-reviewed articles and **38** moderated preprints) retrieved from OpenAlex, arXiv, Crossref, Semantic Scholar, and API-verified snowballing across the exact 48-month window from **November 1, 2022 through October 31, 2026** (**6,121** raw records $\to$ **4,205** deduplicated candidates $\to$ **1,810** Stage 3 assessments).

We organize the literature into a mutually exclusive **Four-Layer, Twelve-Sub-Layer Taxonomy** spanning *Context & Memory Scaffolding* (`L1`, *n* = 29), *Planning & Orchestration Topology* (`L2`, *n* = 35), *Program Grounding & Verification Oracles* (`L3`, *n* = 70), and *Socio-Technical, Queueing & Contract Governance* (`L4`, *n* = 59). Across four research questions (`RQ1`–`RQ4`), the synthesized evidence highlights a **Productivity–Verification Paradox**: while autonomous agents accelerate localized patch synthesis and routine task throughput, end-to-end engineering delivery is frequently constrained by test-suite overfitting, benchmark contamination, human review-queue congestion, context-window cost inflation, and tool/Model Context Protocol (MCP) prompt-injection surfaces. Using an analytical *G/G/k* queueing lens alongside a publication-stage sensitivity check (`n = 155` peer-reviewed subset), we synthesize architectural trade-offs and outline a governance roadmap pairing neuro-symbolic program grounding, differential verification oracles, disaggregated context compression, capability-isolated sandboxes, and risk-tiered review gates.

---

## PRISMA 2020 Screening & Taxonomy Summary

- **Stage 1 — Identification & Union-Find Deduplication**: `6,046` database records (`OpenAlex`: 1,323; `arXiv`: 2,224; `Crossref`: 1,200; `Semantic Scholar`: 1,299) + `75` API-verified snowball records = **`6,121`** raw records $\to$ `1,916` duplicates removed $\to$ **`4,205`** unique candidates.
- **Stage 2 — Title & Abstract Screening**: `2,395` excluded (`EC1`: 1,376; `EC2`: 90; `EC3`: 929) $\to$ **`1,810`** reports assessed at Stage 3 (`0` unretrieved; `25/25 [100.0%]` non-circular landmark seed recall).
- **Stage 3 — Eligibility & Uniform Preprint Protocol (`G1`–`G4`)**: `1,617` excluded (`EC4`: 273; `EC5`: 1,295; `EC6`: 49) $\to$ **`N = 193` included primary studies** (`155` peer-reviewed [80.3%] + `38` moderated preprints [19.7%]).

| Layer / Research Question | Primary Scope | Study Count |
| :--- | :--- | :---: |
| **`L1` Context & Memory Scaffolding** | Compaction/early-stop (`L1.1`), code RAG/distillation (`L1.2`), repo code graphs (`L1.3`) | `29` (15.0%) |
| **`L2` Planning & Orchestration Topology** | Single-agent ACI/pipelines (`L2.1`), tree search/MCTS (`L2.2`), multi-agent topologies (`L2.3`) | `35` (18.1%) |
| **`L3` Program Grounding & Verification Oracles** | AST/PDG & formal translation (`L3.1`), execution harnesses (`L3.2`), review agents (`L3.3`) | `70` (36.3%) |
| **`L4` Socio-Technical, Queueing & Governance** | Delegation contracts (`L4.1`), PR queues/RCTs/reverts (`L4.2`), IPI & MCP security (`L4.3`) | `59` (30.6%) |
| **Mutually Exclusive Primary `RQ` Partition** | `RQ1`: 66 · `RQ2`: 55 · `RQ3`: 15 · `RQ4`: 57 | **`193` (100%)** |

---

## Repository Structure (Complete Replication Package)

```text
agentic-se-paradox-slr/
├── manuscript_en.pdf                          # Full typeset two-column English manuscript (PDF)
├── 00_protocol.md                             # Locally frozen PRISMA 2020 eligibility, G1-G4 & RoB protocol
├── 01_harvest/
│   ├── search_protocol.json                   # Verbatim Boolean queries & date bounds across all 4 APIs
│   ├── records_openalex.jsonl                 # Normalized OpenAlex records (n = 1,323)
│   ├── records_arxiv.jsonl                    # Normalized arXiv records (n = 2,224)
│   ├── records_crossref.jsonl                 # Normalized Crossref records (n = 1,200)
│   ├── records_s2.jsonl                       # Normalized Semantic Scholar records (n = 1,299)
│   └── records_snowball.jsonl                 # API-verified backward/forward snowball records (n = 75)
├── 02_screening/
│   ├── screening_log.csv                      # Complete 4,205-record deduplicated screening & exclusion log
│   ├── prisma_counts.json                     # Machine-readable PRISMA 2020 funnel, cohort, layer & RoB counts
│   ├── prisma_report.md                       # Summary PRISMA 2020 screening report
│   ├── seed_recall_audit.json                 # Non-circular recall audit on 25 landmark peer-reviewed studies
│   └── intra_rater_blind_check_n20.csv        # 12-day blind 10% (n = 20) Stage 3 intra-rater consistency log
├── 03_extraction/
│   ├── review_matrix.csv                      # Master 193-study classification, RQ & RoB extraction table
│   ├── review_matrix.md                       # Browser-readable Markdown table of all 193 primary studies
│   ├── included_studies.jsonl                 # Full bibliographic metadata & cached abstracts (N = 193)
│   ├── preprint_quality_gate_audit.csv        # Item-level G1-G4 evaluation across 1,300 Stage 3 preprints
│   ├── quality_rob_assessment.csv             # 5-criterion (0-10) Risk-of-Bias scores for all 193 studies
│   └── verified_evidence_ledger.csv           # 38 headline quantitative claims with verbatim abstract quotes
├── 04_manuscript/
│   ├── main.tex                               # Self-contained 7-bit ASCII LaTeX manuscript source
│   ├── main.bbl                               # Compiled BibTeX bibliography (213 entries)
│   ├── main.pdf                               # Compiled PDF alongside main.tex for IDE preview
│   ├── references.bib                         # Complete BibTeX database (193 primary + 20 background refs)
│   ├── prisma_2020_checklist.md               # Item-by-item 27-item PRISMA 2020 reporting checklist
│   ├── artifact_sha256_manifest.json          # File-level SHA-256 checksum manifest
│   └── audit_certificate.json                 # Automated verification summary certificate
└── pipeline/
    ├── stage1_harvest.py                      # Programmatic 4-database + snowball harvesting script
    ├── stage2_and_3_prisma.py                 # Union-find deduplication, PRISMA screening & RoB scoring
    ├── stage3_extract_and_verify.py           # Matrix extraction, verbatim quote assertions & BibTeX export
    └── stage6_verify_all.py                   # Zero-dependency verification suite for all counts & hashes
```

---

## Quick Verification

All PRISMA 2020 funnel arithmetic (`6,121 -> 4,205 -> 1,810 -> 193`), 25-seed recall, 38/38 contiguous verbatim abstract substrings and numeric tokens, `213/213` BibTeX citation parity, and file-level SHA-256 checksums can be verified in `< 1 second` using standard Python 3 (`>= 3.9`, zero external packages required):

```bash
python pipeline/stage6_verify_all.py
```

---

## Citation

```bibtex
@misc{liu2026paradox,
  author       = {Feiran Liu},
  title        = {The Productivity--Verification Paradox in Agentic Software Engineering: A Systematic Literature Review of Architectures, Verification Bottlenecks, and Governance},
  year         = {2026},
  howpublished = {Working Paper / Systematic Literature Review Replication Package},
  url          = {https://github.com/atalanta0505/agentic-se-paradox-slr}
}
```
