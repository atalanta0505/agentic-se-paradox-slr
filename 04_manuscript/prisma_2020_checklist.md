# PRISMA 2020 27-Item Reporting Checklist (`M01_agentic_se_slr_20261111`)

| Item # | Section / Topic | PRISMA 2020 Checklist Requirement | Reported Location in Manuscript & Replication Package |
| :--- | :--- | :--- | :--- |
| `1` | **Title** | Identify the report as a systematic review. | Title (`PRISMA 2020 Systematic Literature Review`) |
| `2` | **Abstract** | Provide a structured summary addressing background, objectives, data sources, eligibility, synthesis, limitations, and conclusions. | Abstract |
| `3` | **Rationale** | Describe the rationale for the review in the context of existing knowledge. | Section 1 |
| `4` | **Objectives** | Provide an explicit statement of the objective(s) or question(s) the review addresses. | Section 3.1 (`RQ1`--`RQ4`) & Table 2 |
| `5` | **Eligibility criteria** | Specify the inclusion and exclusion criteria for the review and how studies were grouped for the syntheses. | Section 3.2, `00_protocol.md`, & Table 3 (`IC1`--`IC4`, `EC1`--`EC6`) |
| `6` | **Information sources** | Specify all databases, registers, websites, organisations, reference lists and other sources searched or consulted, with dates. | Section 3.1 & Appendix A (`OpenAlex`, `arXiv`, `Crossref`, `Semantic Scholar` + logged snowballing; `2022-11-01`--`2026-10-31`) |
| `7` | **Search strategy** | Present the full search strategies for all databases, registers and websites, including any filters and limits used. | Appendix A & `01_harvest/search_protocol.json` (verbatim queries for all 4 databases + 65 snowball seeds; 25-landmark recall audit) |
| `8` | **Selection process** | Specify the methods used to decide whether a study met the inclusion criteria, including number of reviewers and automation tools. | Section 3.2 (single-author deterministic screening `stage2_and_3_prisma.py` with `100.0%` replay identity; boundary adjudication rules) |
| `9` | **Data collection process** | Specify the methods used to collect data from reports, including number of reviewers, independence, and automation/verification. | Section 3.3 & `stage3_extract_and_verify.py` (API metadata extraction + token-verified verbatim abstract quote ledger) |
| `10a` | **Data items (outcomes)** | List and define all outcomes for which data were sought. | Section 3.3, `03_extraction/review_matrix.csv`, & `03_extraction/verified_evidence_ledger.csv` |
| `10b` | **Data items (other variables)** | List and define all other variables sought (study design, publication venue, cohort `Y1`--`Y4`, sub-layer `L1.1`--`L4.3`). | Sections 3.2--4 & `03_extraction/review_matrix.csv` |
| `11` | **Study risk of bias assessment** | Specify the methods used to assess risk of bias in the included studies (`Q1`--`Q5`, `0`--`10` scale). | Section 3.3, Section 6.2 (Table 10), Appendix C, & `03_extraction/quality_rob_assessment.csv` |
| `12` | **Effect measures** | Specify for each outcome the effect measure(s) used in the presentation of results. | Section 3.3 & Tables 5--9 (Pass@1, % delta, merge/revert rates, token/cost %, ASR %) |
| `13a` | **Synthesis methods (eligibility)** | Describe the processes used to decide which studies were eligible for each synthesis (`primary_rq` vs. multi-label `rqs`). | Section 3.2, Table 2, & Sections 5.1--5.4 |
| `13b` | **Synthesis methods (data preparation)** | Describe any methods required to prepare the data for presentation or synthesis. | Section 3.3 (disaggregation of heterogeneous cost/latency metrics; preservation of original scales) |
| `13c` | **Synthesis methods (tabulation/display)** | Describe any methods used to tabulate or visually display results of individual studies and syntheses. | Figures 1--5 & Tables 4--9 |
| `13d` | **Synthesis methods (narrative rationale)** | Describe methods used to synthesize results and provide rationale for choice over pooled meta-analysis. | Section 3.3 & Section 6.2 (structured narrative synthesis due to incommensurable SE outcomes) |
| `13e` | **Synthesis methods (heterogeneity)** | Describe any methods used to explore possible causes of heterogeneity among study results. | Sections 5.1--5.4 & Section 6.1 (stratification by developer tenure, repo maturity, task horizon, oracle strength) |
| `13f` | **Synthesis methods (sensitivity)** | Describe any sensitivity analyses conducted to assess robustness of the synthesized results. | Section 6.2 & Table 9 (publication-stage sensitivity check across `RQ1`--`RQ4`) |
| `14` | **Reporting bias assessment** | Describe any methods used to assess risk of bias due to missing results (publication/reporting lag bias). | Section 6.2 & Section 7 (survivorship, positive-result, and indexing-lag analysis) |
| `15` | **Certainty assessment** | Describe any methods used to assess certainty (or confidence) in the body of evidence for an outcome. | Section 6.2 & Table 9 (`RoB` tier stratification + publication-stage sensitivity check) |
| `16a` | **Study selection (flow)** | Describe the results of the search and selection process, ideally using a flow diagram. | Section 3.2, Figure 1 (`6,121 -> 4,205 -> 1,810 -> 193`), & `02_screening/screening_log.csv` |
| `16b` | **Study selection (excluded close calls)** | Cite studies that might appear to meet inclusion criteria, and explain why they were excluded. | Section 3.2, `02_screening/screening_log.csv`, & `03_extraction/preprint_quality_gate_audit.csv` |
| `17` | **Study characteristics** | Cite each included study and present its characteristics. | Section 4, Table 4, `03_extraction/review_matrix.csv`, & Bibliography |
| `18` | **Risk of bias in studies** | Present assessments of risk of bias for each included study. | Section 6.2 & `03_extraction/quality_rob_assessment.csv` |
| `19` | **Results of individual studies** | For all outcomes, present summary statistics/metrics for each study. | Tables 4--8 & `03_extraction/verified_evidence_ledger.csv` |
| `20a` | **Results of syntheses (characteristics/RoB)** | For each synthesis, briefly summarise the characteristics and risk of bias among contributing studies. | Sections 5.1--5.4 & Section 6.2 |
| `20b` | **Results of syntheses (outcomes)** | Present results of all syntheses conducted. | Sections 5.1--5.4 & Tables 5--9 |
| `20c` | **Results of syntheses (heterogeneity)** | Describe results of all investigations of possible causes of heterogeneity among study results. | Sections 5.1--5.4 & Section 6.1 |
| `20d` | **Results of syntheses (sensitivity)** | Present results of all sensitivity analyses conducted to assess robustness of synthesized results. | Section 6.2 & Table 9 (`155` peer-reviewed vs. full `193` corpus) |
| `21` | **Reporting biases** | Present assessments of risk of bias due to missing results in each synthesis. | Section 6.2 & Section 7 |
| `22` | **Certainty of evidence** | Present assessments of certainty (or confidence) in the body of evidence for each outcome assessed. | Section 6.2 & Table 9 |
| `23a` | **Discussion (interpretation)** | Provide a general interpretation of the results in the context of other evidence. | Section 6.1 & Section 8 |
| `23b` | **Discussion (evidence limitations)** | Discuss any limitations of the evidence included in the review. | Section 5.1 (observational confounding), Section 6.2, & Section 7 |
| `23c` | **Discussion (process limitations)** | Discuss any limitations of the review processes used. | Section 7 (single-author deterministic screening, preprint gate thresholds, English-only filter, local protocol freeze) |
| `23d` | **Discussion (implications)** | Discuss implications of the results for practice, policy, and future research. | Section 6.3 & Section 8 |
| `24a` | **Registration and protocol (registration)** | Provide registration information or state that the review was not externally registered. | Section 3 & `00_protocol.md` (explicitly states local pre-harvest freeze on `2026-11-11` without external OSF/PROSPERO registry) |
| `24b` | **Registration and protocol (access)** | Indicate where the review protocol can be accessed. | `00_protocol.md` & Data Availability Statement (`04_manuscript/artifact_sha256_manifest.json`) |
| `24c` | **Registration and protocol (amendments)** | Describe and explain any amendments to information provided at registration or in the protocol. | `00_protocol.md` & Section 3.2 |
| `25` | **Support** | Describe sources of financial or non-financial support for the review, and the role of funders. | Funding & Competing Interests Statement (Section 8 / End Matter) |
| `26` | **Competing interests** | Declare any competing interests of review authors. | Competing Interests Statement (none declared) |
| `27` | **Availability of data, code and other materials** | Report which of the review materials are publicly available and where they can be found. | Data and Replication Artifact Availability Statement & `04_manuscript/artifact_sha256_manifest.json` |
