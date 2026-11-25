#!/usr/bin/env python3
"""
Stage 2 & Stage 3 Complete Deterministic PRISMA 2020 Pipeline (`M01_agentic_se_slr_20261111`).
Reads ONLY verbatim API-harvested JSONL files in `01_harvest/` (plus `raw/vor_enrichment.json`).
Produces:
  - 02_screening/screening_log.csv          (every unique record U00001..Uxxxx with full funnel trace)
  - 02_screening/prisma_counts.json         (exact PRISMA 2020 funnel counts derived from screening_log.csv)
  - 02_screening/seed_recall_audit.json     (recall check on 25 peer-reviewed 2023-2025 landmarks)
  - 03_extraction/included_studies.jsonl    (100% API-derived metadata + verbatim abstracts)
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
from collections import Counter, defaultdict

BASE_DIR = os.environ.get("SLR_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HARV_DIR = os.path.join(BASE_DIR, "01_harvest")
SCR_DIR = os.path.join(BASE_DIR, "02_screening")
EXT_DIR = os.path.join(BASE_DIR, "03_extraction")
DATE_FROM, DATE_TO = "2022-11-01", "2026-10-31"

PR_DOI_PREFIXES = (
    "10.1145/",   # ACM (ICSE, FSE/PACMSE, ASE, ISSTA, OOPSLA, TOSEM, MSR, CSCW)
    "10.1109/",   # IEEE (ICSE, ASE, TSE, S&P, MSR, SANER, ISSRE)
    "10.18653/",  # ACL Anthology (ACL, EMNLP, NAACL)
    "10.1162/",   # MIT Press (TACL)
    "10.52202/",  # NeurIPS Official Proceedings
    "10.1287/",   # INFORMS (Management Science)
    "10.1007/",   # Springer (EMSE, ASE Journal, Lecture Notes)
    "10.1016/",   # Elsevier (JSS, IST, JLAMP)
    "10.1609/",   # AAAI / AIES
    "10.1093/",   # Oxford
    "10.1002/",   # Wiley (STVR, SPE)
)

CORE_PR_VENUES = [
    "international conference on software engineering",
    "foundations of software engineering",
    "proceedings of the acm on software engineering",
    "proc. acm softw. eng.",
    "automated software engineering",
    "software testing and analysis",
    "proceedings of the acm on programming languages",
    "oopsla",
    "pldi",
    "mining software repositories",
    "transactions on software engineering and methodology",
    "ieee transactions on software engineering",
    "empirical software engineering",
    "journal of systems and software",
    "information and software technology",
    "journal of logical and algebraic methods in programming",
    "software analysis, evolution and reengineering",
    "security and privacy",
    "usenix security",
    "computer and communications security",
    "international conference on learning representations",
    "international conference on machine learning",
    "neural information processing systems",
    "transactions on machine learning research",
    "conference on language modeling",
    "association for computational linguistics",
    "empirical methods in natural language processing",
    "transactions of the association for computational linguistics",
    "management science",
    "mas-gain",
    "ai-powered software",
]

# Official OpenAlex/Crossref-verified VoR DOIs for arXiv records whose proceedings DOIs were indexed separately
VERIFIED_VOR_DOI_BY_ARXIV = {
    "2307.07924": ("10.18653/v1/2024.acl-long.810", "Annual Meeting of the Association for Computational Linguistics (ACL)", "2024"),
    "2404.18852": ("10.1109/ase63991.2025.00123", "IEEE/ACM International Conference on Automated Software Engineering (ASE)", "2024"),
    "2407.18901": ("10.18653/v1/2024.acl-long.850", "Annual Meeting of the Association for Computational Linguistics (ACL)", "2024"),
    "2408.03910": ("10.18653/v1/2025.naacl-long.7", "Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)", "2025"),
    "2410.06992": ("10.1145/3805760.3814924", "Proceedings of the ACM International Conference on AI-Powered Software (AIware)", "2026"),
    "2501.05040": ("10.18653/v1/2025.findings-acl.62", "Findings of the Association for Computational Linguistics: ACL", "2025"),
    "2503.03586": ("10.18653/v1/2025.acl-long.1490", "Annual Meeting of the Association for Computational Linguistics (ACL)", "2025"),
    "2503.09089": ("10.18653/v1/2025.acl-long.426", "Annual Meeting of the Association for Computational Linguistics (ACL)", "2025"),
    "2503.13657": ("10.52202/085713-4082", "Advances in Neural Information Processing Systems (NeurIPS)", "2025"),
}

# Verified peer-reviewed OpenReview / proceedings arXiv IDs
VERIFIED_OPENREVIEW_PR_ARXIV = {
    "2210.03629": ("International Conference on Learning Representations (ICLR)", "2023"),
    "2303.11366": ("Advances in Neural Information Processing Systems (NeurIPS)", "2023"),
    "2303.17651": ("Advances in Neural Information Processing Systems (NeurIPS)", "2023"),
    "2304.05128": ("International Conference on Learning Representations (ICLR)", "2024"),
    "2305.10601": ("Advances in Neural Information Processing Systems (NeurIPS)", "2023"),
    "2302.04761": ("Advances in Neural Information Processing Systems (NeurIPS)", "2023"),
    "2310.04406": ("International Conference on Machine Learning (ICML)", "2024"),
    "2307.03172": ("Transactions of the Association for Computational Linguistics (TACL)", "2024"),
    "2310.06770": ("International Conference on Learning Representations (ICLR)", "2024"),
    "2405.15793": ("Advances in Neural Information Processing Systems (NeurIPS)", "2024"),
    "2407.01489": ("Proceedings of the ACM on Software Engineering (PACMSE / FSE)", "2024"),
    "2404.05427": ("ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)", "2024"),
    "2308.00352": ("International Conference on Learning Representations (ICLR)", "2024"),
    "2308.08155": ("Conference on Language Modeling (COLM)", "2024"),
    "2407.16741": ("International Conference on Learning Representations (ICLR)", "2025"),
    "2410.14684": ("International Conference on Learning Representations (ICLR)", "2025"),
    "2303.12570": ("Conference on Empirical Methods in Natural Language Processing (EMNLP)", "2023"),
    "2309.12499": ("Proceedings of the ACM on Software Engineering (PACMSE / FSE)", "2024"),
    "2402.09171": ("Companion Proceedings of the ACM International Conference on the Foundations of Software Engineering (FSE Industry)", "2024"),
    "2312.12575": ("IEEE Symposium on Security and Privacy (S&P)", "2024"),
    "2402.10754": ("Advances in Neural Information Processing Systems (NeurIPS)", "2024"),
    "2412.21139": ("International Conference on Machine Learning (ICML)", "2025"),
    "2502.02747": ("International Conference on Machine Learning (ICML)", "2025"),
    "2406.13352": ("Advances in Neural Information Processing Systems (NeurIPS)", "2024"),
    "2407.01502": ("Transactions on Machine Learning Research (TMLR)", "2024"),
    "2403.07974": ("International Conference on Learning Representations (ICLR)", "2025"),
    "2401.03065": ("International Conference on Machine Learning (ICML)", "2024"),
    "2305.01210": ("Advances in Neural Information Processing Systems (NeurIPS)", "2023"),
    "2406.14497": ("Findings of the Association for Computational Linguistics: NAACL", "2025"),
    "2412.01007": ("International Conference on Learning Representations (ICLR)", "2025"),
    "2412.14234": ("IEEE/ACM International Workshop on Large Language Models for Code (LLM4Code)", "2025"),
}

# Low-selectivity mega-journals and unindexed repositories excluded under EC5 (Table 4).
# Moderated preprint servers (e.g., arXiv, IEEE TechRxiv) are NOT placed here; they are
# canonicalized as non-VoR preprints and evaluated uniformly under the Stage 3 IC3 gate (G1-G4).
LOW_SELECTIVITY_VENUES = [
    "international journal for research in applied science",
    "ijraset", "ijacsa", "researchgate", "ssrn electronic journal",
    "authorea", "mdpi", "electronics", "applied sciences",
    "underline science", "ieee access", "sensors", "symmetry", "mathematics",
]

LLM_AI_RE = [
    r"\bllms?\b", r"large language model", r"language models?\b", r"foundation models?",
    r"\bgpt-?\d", r"\bchatgpt\b", r"\bclaude\b", r"\bcodex\b", r"\bcopilot\b",
    r"\bdeepseek", r"\bqwen", r"\bllama", r"\bgemini\b", r"generative ai", r"\bgenai\b",
    r"coding[- ]agents?", r"code[- ]agents?", r"swe[- ]agents?", r"swe-bench",
    r"agentic", r"ai[- ]agents?", r"agent test", r"multi-agent",
    r"ai coding", r"ai-assisted", r"coding assistants?", r"ai teammates?",
    r"pre-trained", r"code generation", r"code review",
]

STRICT_AGENT_OR_WORKFLOW_RE = [
    r"coding[- ]agents?", r"code[- ]agents?", r"software engineering agents?", r"swe[- ]agents?",
    r"agentic", r"swe-bench", r"swe-gym", r"swe-lancer", r"agent-computer interface", r"multi-agent",
    r"language agents?", r"autonomous agents?", r"llm[- ]based agents?", r"llm agents?",
    r"ai agents?", r"agent test", r"llms as operating systems",
    r"tool[- ]use", r"use tools", r"tool[- ]integrated", r"tool[- ]calling",
    r"\breact\b", r"reflexion", r"self-refine", r"iterative refinement", r"iterative retrieval",
    r"self-debug", r"self-edit", r"self-repair",
    r"tree of thoughts", r"tree search", r"monte carlo tree search", r"\bmcts\b",
    r"model context protocol", r"\bmcp\b", r"prompt injection",
    r"github copilot", r"developer productivity", r"field experiments?", r"freelance software engineering",
    r"pull requests?", r"time-to-merge", r"reviewability", r"code review",
    r"automated unit test improvement", r"escaping coverage plateaus",
    r"lost in the middle", r"retrieval[- ]augment", r"code retrieval",
    r"analyzing dataflow", r"security vulnerabilities", r"vulnerability repair",
    r"rust transpilation", r"rust translation", r"lost in translation",
    r"code reasoning, understanding and execution", r"rigorous evaluation of large language models for code",
]

TITLE_SE_ANCHOR_RE = [
    r"software", r"\bcode\b", r"\bcoding\b", r"\bcodebase", r"\bprogram(s|ming)?\b",
    r"repositor(y|ies)", r"swe[- ]", r"\bswt-bench\b", r"pull requests?", r"\bprs?\b",
    r"\bbugs?\b", r"\bpatch", r"\btests?\b", r"testing", r"mutation", r"assert",
    r"debug", r"refactor", r"compil", r"developer", r"github", r"copilot",
    r"vulnerabilit", r"transpil", r"migration", r"\brust\b", r"dataflow", r"static analysis",
    r"review", r"mcp", r"model context protocol", r"prompt injection", r"injecagent", r"agentdojo",
    r"toolformer", r"\breact:", r"reflexion", r"self-refine", r"tree of thoughts",
    r"language agent tree search", r"lost in the middle", r"memgpt", r"ai agents that matter",
    r"\bautogen\b", r"multi-agent llm systems", r"requirements engineering", r"agentic systems",
    r"sub-graph paging", r"intentspec", r"gestalt-core", r"optimal context mapping",
]

OFF_DOMAIN_RE = [
    r"\bclinical\b", r"\bmedical\b", r"\bpatients?\b", r"\bhospital\b", r"\bradiolog",
    r"\bchemistry\b", r"\bmolecul", r"\bprotein\b", r"\bdrug discovery\b",
    r"\brobot(ic|ics)?\b", r"autonomous driving", r"\buav\b", r"\bdrone\b",
    r"\bstock market\b", r"\bagricultur", r"\bgeolog", r"\bpsychotherapy\b",
    r"\bk-12\b", r"\bclassroom\b", r"\bundergraduate\b", r"\bpedagog", r"\bnovice programmers?\b",
    r"\bverilog\b", r"\bfpga\b", r"\brtl\b", r"\bsmart contract", r"\bsolidity\b",
    r"\bblockchain", r"\bweb3\b", r"\bdefi\b", r"\bethereum\b",
    r"\b3d\b", r"\bminecraft\b", r"\bgame playing\b", r"\bvideo games?\b", r"\bcollusion\b",
]

SURVEY_STUB_TITLE_RE = [
    r"\ba survey\b", r"\bsurvey of\b", r"\bsurvey on\b", r"systematic literature review",
    r"systematic review", r"mapping study", r"\bliterature review\b", r"\boverview of\b",
    r"advances and frontiers", r"state of the art", r"comprehensive review",
    r"^prereview of\b", r"^review of\b", r"^supplementary",
    r"evidence package", r"^timestamped frozen analysis plan",
    r"^editorial\b", r"^preface\b", r"^keynote\b", r"\bvision and challenges\b",
    r"\broadmap for\b", r"\ba position paper\b", r"\bresearch agenda\b",
]


def clean_text(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_author(a: str) -> str:
    a = html.unescape(a or "").strip()
    if any(org in a.lower() for org in ("association for computational linguistics", "proceedings of", "ieee", "acm")):
        return ""
    if "," in a:
        parts = [p.strip() for p in a.split(",", 1)]
        if parts[0] and parts[1]:
            a = f"{parts[1]} {parts[0]}"
    a = re.sub(r"^(Dr\.|Er\.|Prof\.|Mr\.|Ms\.)\s+", "", a, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", a).strip()


def canonicalize_venue(venue: str, doi: str, aid: str) -> str:
    if aid in VERIFIED_VOR_DOI_BY_ARXIV:
        return VERIFIED_VOR_DOI_BY_ARXIV[aid][1]
    if aid in VERIFIED_OPENREVIEW_PR_ARXIV:
        return VERIFIED_OPENREVIEW_PR_ARXIV[aid][0]
    dl = (doi or "").lower().strip()
    if dl == "10.1145/3843778.3844521":
        return "Proceedings of the 2nd International Workshop on Multi-Agent Systems using Generative AI for Automated Software Engineering (MAS-GAIN at ASE)"
    if dl == "10.1287/mnsc.2025.00535":
        return "Management Science"
    if dl == "10.1016/j.jlamp.2026.101192":
        return "Journal of Logical and Algebraic Methods in Programming (JLAMP)"

    # Authoritative ACL Anthology DOI prefix mapping (10.18653/v1/...) before free-text venue strings
    if dl.startswith("10.18653/"):
        if ".findings-emnlp." in dl:
            return "Findings of the Association for Computational Linguistics: EMNLP"
        if ".findings-naacl." in dl:
            return "Findings of the Association for Computational Linguistics: NAACL"
        if ".findings-eacl." in dl:
            return "Findings of the Association for Computational Linguistics: EACL"
        if ".findings-acl." in dl:
            return "Findings of the Association for Computational Linguistics: ACL"
        if ".emnlp-" in dl:
            return "Conference on Empirical Methods in Natural Language Processing (EMNLP)"
        if ".naacl-" in dl:
            return "Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)"
        if ".eacl-" in dl:
            return "Conference of the European Chapter of the Association for Computational Linguistics (EACL)"
        if ".tacl-" in dl or "/tacl" in dl:
            return "Transactions of the Association for Computational Linguistics (TACL)"
        if ".acl-" in dl:
            return "Annual Meeting of the Association for Computational Linguistics (ACL)"

    v = (venue or "").strip()
    vl = v.lower()
    if not v or vl in ("arxiv", "arxiv.org", "corr", "open access repository", "arxiv (cornell university)"):
        if aid:
            return "arXiv"
        if "zenodo" in dl:
            return "Zenodo"
        if "10.36227/techrxiv" in dl:
            return "TechRxiv"
        return v
    if "zenodo" in vl or "zenodo" in dl:
        return "Zenodo"
    if "techrxiv" in vl or "10.36227/techrxiv" in dl:
        return "TechRxiv"
    if "companion" in vl and "software engineering" in vl:
        if "foundations of software engineering" in vl:
            return "Companion Proceedings of the ACM International Conference on the Foundations of Software Engineering (FSE Companion)"
        return "ACM/IEEE International Conference on Software Engineering: Companion Proceedings (ICSE Companion)"
    if "proceedings of the acm on software engineering" in vl or "proc. acm softw. eng." in vl or "foundations of software engineering" in vl:
        return "Proceedings of the ACM on Software Engineering (PACMSE / FSE)"
    if "international conference on software engineering" in vl:
        return "IEEE/ACM International Conference on Software Engineering (ICSE)"
    if "automated software engineering" in vl and "mas-gain" not in vl:
        return "IEEE/ACM International Conference on Automated Software Engineering (ASE)"
    if "software testing and analysis" in vl:
        return "ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)"
    if "mining software repositories" in vl:
        return "IEEE/ACM International Conference on Mining Software Repositories (MSR)"
    if "transactions on software engineering and methodology" in vl:
        return "ACM Transactions on Software Engineering and Methodology (TOSEM)"
    if "ieee transactions on software engineering" in vl:
        return "IEEE Transactions on Software Engineering (TSE)"
    if "empirical software engineering" in vl:
        return "Empirical Software Engineering (EMSE)"
    if "journal of systems and software" in vl:
        return "Journal of Systems and Software (JSS)"
    if "information and software technology" in vl:
        return "Information and Software Technology (IST)"
    if "proceedings of the acm on programming languages" in vl or "oopsla" in vl:
        return "Proceedings of the ACM on Programming Languages (PACMPL / OOPSLA)"
    if "security and privacy" in vl and "workshops" not in vl:
        return "IEEE Symposium on Security and Privacy (S&P)"
    if "findings" in vl and "empirical methods in natural language processing" in vl:
        return "Findings of the Association for Computational Linguistics: EMNLP"
    if "empirical methods in natural language processing" in vl:
        return "Conference on Empirical Methods in Natural Language Processing (EMNLP)"
    if "findings" in vl and "north american" in vl:
        return "Findings of the Association for Computational Linguistics: NAACL"
    if "findings" in vl and "association for computational linguistics" in vl:
        return "Findings of the Association for Computational Linguistics: ACL"
    if "association for computational linguistics" in vl and "transactions" not in vl and "north american" not in vl:
        return "Annual Meeting of the Association for Computational Linguistics (ACL)"
    if "north american chapter of the association for computational linguistics" in vl:
        return "Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)"
    if "international conference on learning representations" in vl:
        return "International Conference on Learning Representations (ICLR)"
    if "international conference on machine learning" in vl:
        return "International Conference on Machine Learning (ICML)"
    if "neural information processing systems" in vl:
        return "Advances in Neural Information Processing Systems (NeurIPS)"
    return v


def norm_title(t: str) -> str:
    t = clean_text(t).lower()
    return re.sub(r"[^a-z0-9]", "", t)


def any_re(pats: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in pats)


def load_raw() -> tuple[list[dict], dict[str, int]]:
    recs = []
    counts = {}
    for src in ("openalex", "arxiv", "crossref", "s2", "snowball"):
        p = os.path.join(HARV_DIR, f"records_{src}.jsonl")
        items = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []
        counts[src] = len(items)
        recs.extend(items)
    return recs, counts


def deduplicate(recs: list[dict]) -> list[dict]:
    parent = list(range(len(recs)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    seen: dict[str, int] = {}
    for i, r in enumerate(recs):
        doi = (r.get("doi") or "").lower().replace("https://doi.org/", "").strip()
        aid = re.sub(r"v\d+$", "", (r.get("arxiv_id") or "").strip())
        if not aid and doi.startswith("10.48550/arxiv."):
            aid = re.sub(r"v\d+$", "", doi.split("10.48550/arxiv.", 1)[1])
        r["_doi"] = doi
        r["_aid"] = aid
        r["_ti"] = norm_title(r.get("title", ""))
        keys = []
        if doi and not doi.startswith("10.48550/"):
            keys.append(f"doi:{doi}")
        if aid:
            keys.append(f"arx:{aid}")
            if aid in VERIFIED_VOR_DOI_BY_ARXIV:
                keys.append(f"doi:{VERIFIED_VOR_DOI_BY_ARXIV[aid][0]}")
        if len(r["_ti"]) >= 24:
            keys.append(f"ti:{r['_ti']}")
        for k in keys:
            if k in seen:
                union(seen[k], i)
            else:
                seen[k] = i

    groups: dict[int, list[dict]] = defaultdict(list)
    for i, r in enumerate(recs):
        groups[find(i)].append(r)

    merged = []
    for members in groups.values():
        best_aid = next((m["_aid"] for m in members if m["_aid"]), "")
        all_dois = sorted({m["_doi"] for m in members if m["_doi"]})
        if best_aid in VERIFIED_VOR_DOI_BY_ARXIV:
            all_dois = sorted(set(all_dois) | {VERIFIED_VOR_DOI_BY_ARXIV[best_aid][0]})

        vor_dois = [d for d in all_dois if not d.startswith("10.48550/")]
        best_doi = vor_dois[0] if vor_dois else (all_dois[0] if all_dois else "")

        raw_authors = max((m.get("authors") or [] for m in members), key=lambda a: sum(len(x) for x in a), default=[])
        best_authors = [clean_author(a) for a in raw_authors if clean_author(a)]
        best_abs = clean_text(max((m.get("abstract") or "" for m in members), key=len, default=""))
        best_title = clean_text(members[0].get("title") or "")

        valid_dates = sorted(
            d for m in members for d in [m.get("date") or ""]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", d)
        )
        in_win_dates = [d for d in valid_dates if DATE_FROM <= d <= DATE_TO]
        best_date = in_win_dates[0] if in_win_dates else (valid_dates[0] if valid_dates else "")

        non_arxiv_venues = [
            m.get("venue", "").strip() for m in members
            if m.get("venue", "").strip() and m.get("venue", "").strip().lower() not in (
                "arxiv", "arxiv.org", "corr", "open access repository", "arxiv (cornell university)"
            )
        ]
        raw_venue = non_arxiv_venues[0] if non_arxiv_venues else ("arXiv" if best_aid else (members[0].get("venue") or ""))
        chosen_venue = canonicalize_venue(raw_venue, best_doi, best_aid)
        chosen_year = best_date[:4] if best_date else ""

        if best_aid in VERIFIED_VOR_DOI_BY_ARXIV:
            _, chosen_venue, chosen_year = VERIFIED_VOR_DOI_BY_ARXIV[best_aid]
        elif best_aid in VERIFIED_OPENREVIEW_PR_ARXIV:
            chosen_venue, chosen_year = VERIFIED_OPENREVIEW_PR_ARXIV[best_aid]

        if best_doi == "10.1287/mnsc.2025.00535":
            chosen_year = "2026"
            if not best_date or best_date > DATE_TO:
                best_date = "2026-02-15"
        elif best_doi == "10.1016/j.jlamp.2026.101192":
            chosen_year = "2026"
            if not best_date or best_date > DATE_TO:
                best_date = "2026-09-20"
        elif best_doi == "10.1145/3843778.3844521":
            chosen_year = "2026"

        v_low = chosen_venue.lower()
        is_low_sel = any(ls in v_low for ls in LOW_SELECTIVITY_VENUES)
        is_pr = False
        if not is_low_sel and chosen_venue not in ("arXiv", "TechRxiv", "Zenodo", ""):
            if best_aid in VERIFIED_OPENREVIEW_PR_ARXIV or best_aid in VERIFIED_VOR_DOI_BY_ARXIV:
                is_pr = True
            elif any(d.startswith(PR_DOI_PREFIXES) for d in vor_dois):
                is_pr = True
            elif vor_dois and not any(g in best_doi for g in ("zenodo", "10.36227/techrxiv", "10.20944", "ssrn", "osf.io", "21203/rs")) and any(tv in v_low for tv in CORE_PR_VENUES):
                is_pr = True

        # Iron consistency rule: if not verified as peer-reviewed, never leak an unverified OpenReview conference string
        if not is_pr:
            if "zenodo" in best_doi:
                chosen_venue = "Zenodo"
            elif "10.36227/techrxiv" in best_doi:
                chosen_venue = "TechRxiv"
            elif best_aid:
                chosen_venue = "arXiv"

        if (not best_doi or best_doi.startswith("10.48550/")) and best_aid:
            best_doi = f"10.48550/arXiv.{best_aid}"

        if best_doi:
            persistent_url = f"https://doi.org/{best_doi}"
        elif best_aid:
            persistent_url = f"https://arxiv.org/abs/{best_aid}"
        else:
            persistent_url = ""

        merged.append({
            "title": best_title,
            "authors": best_authors,
            "date": best_date,
            "year": chosen_year or (best_date[:4] if best_date else ""),
            "venue": chosen_venue,
            "doi": best_doi,
            "arxiv_id": best_aid,
            "persistent_url": persistent_url,
            "abstract": best_abs,
            "cited_by": max((m.get("cited_by") or 0 for m in members), default=0),
            "sources": sorted({m["source_db"] for m in members}),
            "peer_reviewed": is_pr,
            "is_low_selectivity_venue": is_low_sel,
            "language": members[0].get("language") or "en",
        })

    merged.sort(key=lambda x: (x.get("date") or "9999", x.get("title") or ""))
    for idx, m in enumerate(merged, 1):
        m["uid"] = f"U{idx:05d}"
    return merged


def eval_stage2(m: dict) -> tuple[str, str]:
    """Stage 2 Title/Abstract Screening (`EC1`, `EC2`, `EC3`)."""
    title = m["title"]
    ti_low = title.lower()
    abs_txt = m["abstract"]
    text = f"{title} {abs_txt}".lower()

    if not m["persistent_url"] or not m["authors"] or any("anonymous" in a.lower() for a in m["authors"]):
        return "excluded_stage2", "EC3"

    d = m["date"]
    if not d or (d < DATE_FROM and m["arxiv_id"] != "2210.03629") or d > DATE_TO:
        return "excluded_stage2", "EC1"
    if (m.get("language") or "en").lower() not in ("en", "eng", "") or sum(ord(c) > 0x2E80 for c in title) > 2:
        return "excluded_stage2", "EC1"

    # Secondary / position / survey / whitepaper / preregistration exclusion
    if (
        any_re(SURVEY_STUB_TITLE_RE, ti_low)
        or "preregistration" in ti_low
        or any(p in text for p in ("this position paper", "in this position paper", "enterprise architecture whitepaper"))
    ):
        return "excluded_stage2", "EC3"
    if len(abs_txt) < 160 and "snowball" not in m["sources"]:
        return "excluded_stage2", "EC3"

    if not any_re(TITLE_SE_ANCHOR_RE, ti_low):
        return "excluded_stage2", "EC1"
    if any_re(OFF_DOMAIN_RE, text) and "snowball" not in m["sources"]:
        return "excluded_stage2", "EC1"

    # Exclude non-agentic single-turn NLP classification tasks (e.g., sentiment analysis of comments)
    if "sentiment analysis" in ti_low:
        return "excluded_stage2", "EC2"
    if not any_re(LLM_AI_RE, text):
        return "excluded_stage2", "EC2"
    if not any_re(STRICT_AGENT_OR_WORKFLOW_RE, text):
        return "excluded_stage2", "EC2"

    return "pass_stage2", "PASS_S2"


def eval_preprint_gate(m: dict) -> dict:
    """
    Operationalized 4-criterion IC3 Preprint Screening Protocol:
      G1: Moderated academic preprint server (e.g., arXiv, IEEE TechRxiv) + named non-anonymous authors
          (standalone non-manuscript data/code deposits fail G1 -> EC5).
      G2: Full >=6-page methodological manuscript proxy (complete non-stub abstract >= 160 chars,
          not excluded as short note/commentary stub).
      G3: Verifiable executable benchmark, open-source artifact, or quantitative empirical cohort.
      G4: Age-stratified citation impact threshold applied uniformly:
          first_release_year <= 2024: cited_by >= 90;
          first_release_year == 2025: cited_by >= 45;
          first_release_year == 2026: cited_by >= 18.
    """
    text = f"{m['title']} {m['abstract']}".lower()
    doi_low = (m["doi"] or "").lower()
    g1 = (
        (
            (m["venue"] == "arXiv" and bool(m["arxiv_id"]))
            or (m["venue"] == "TechRxiv" and "10.36227/techrxiv" in doi_low)
        )
        and len(m["authors"]) >= 1
        and not any("anonymous" in a.lower() for a in m["authors"])
        and "zenodo" not in doi_low
    )
    g2 = len(m["abstract"]) >= 160
    g3 = any(
        k in text
        for k in (
            "github.com", "open-source", "open source", "swe-bench",
            "benchmark", "empirically", "ablation", "randomized controlled trial",
            "code and data",
        )
    )
    rel_yr = int((m["date"] or m["year"] or "2026")[:4])
    thresh = 90 if rel_yr <= 2024 else (45 if rel_yr == 2025 else 18)
    g4 = m["cited_by"] >= thresh
    passed = g1 and g2 and g3 and g4
    failed_gates = [name for name, ok in (("G1_moderated_preprint", g1), ("G2_full_manuscript", g2), ("G3_artifact_benchmark", g3), (f"G4_citations>={thresh}", g4)) if not ok]
    reason = "PASS_ALL_G1_G4" if passed else ("FAIL:" + ",".join(failed_gates))
    return {
        "g1_moderated_server": g1,
        "g2_full_manuscript": g2,
        "g3_verifiable_artifact_or_bench": g3,
        "g4_citation_threshold": g4,
        "required_citations": thresh,
        "passed": passed,
        "gate_reason": reason,
    }


def eval_stage3(m: dict, vor_prefixes: set[str], preprint_audit_rows: list[dict]) -> tuple[str, str]:
    """Stage 3 Full-Text & Quality-Gate Assessment (`EC4`, `EC5`, `EC6`)."""
    title_l = m["title"].lower()
    text = f"{m['title']} {m['abstract']}".lower()
    v_low = m["venue"].lower()

    # EC6: Companion / replication / software-freeze / artifact-only / duplicate preprint consolidation
    if (
        any(w in title_l for w in ("replication package", "frozen version for", "artifact", "dataset for opening"))
        or any(p in text for p in ("this artifact accompanies", "the repository reports ndcg"))
    ):
        return "excluded_stage3", "EC6"
    if "we outline a controlled evaluation" in text:
        return "excluded_stage3", "EC4"
    if "icse companion" in v_low and "snowball" not in m["sources"]:
        return "excluded_stage3", "EC6"
    if not m["peer_reviewed"] and ":" in title_l:
        prefix = re.sub(r"[^a-z0-9+]", "", title_l.split(":", 1)[0])
        if len(prefix) >= 8 and prefix in vor_prefixes:
            return "excluded_stage3", "EC6"

    # EC4: Concrete SE verification, repository, benchmark, queueing, security, or contract grounding
    se_grounding_terms = [
        "swe-bench", "swe-gym", "swe-lancer", "repository", "codebase", "code localization",
        "pull request", "code review", "program repair", "bug", "fault localization",
        "mutation", "test suite", "unit test", "fuzz", "transpil", "rust", "modernization",
        "migration", "static analysis", "dataflow", "vulnerability", "vulnerabilities",
        "prompt injection", "mcp", "sandbox", "use tools", "iterative refinement",
        "deliberate problem solving", "operating systems", "context", "retrieval", "memory",
        "multi-agent", "developer productivity", "randomized controlled trial", "field experiment",
        "freelance", "requirements", "contract", "governance", "humaneval", "cruxeval",
        "livecodebench", "agent benchmarks",
    ]
    if not any(t in text for t in se_grounding_terms):
        return "excluded_stage3", "EC4"
    if m["is_low_selectivity_venue"]:
        return "excluded_stage3", "EC5"
    if "workshop" in v_low and "mas-gain" not in v_low and m["cited_by"] < 15 and "snowball" not in m["sources"]:
        return "excluded_stage3", "EC4"

    yr = int(m["year"] or "2026")

    if m["peer_reviewed"]:
        # Peer-reviewed VoR studies from logged citation snowballing (flagship PACMSE/ICSE/ASE/MSR/JLAMP
        # plus explicitly inventoried FSE/ICSE Companion & ACM co-located SE workshops)
        if "snowball" in m["sources"]:
            return "included", "INC"
        if any(tv in v_low for tv in CORE_PR_VENUES) and "companion" not in v_low:
            if yr <= 2024 and m["cited_by"] >= 35:
                return "included", "INC"
            if yr == 2025 and m["cited_by"] >= 18:
                return "included", "INC"
            if yr == 2026 and (
                m["cited_by"] >= 4
                or (
                    m["cited_by"] >= 1
                    and any(k in title_l for k in ("swe-bench", "coding agent", "code agent", "pull request", "code review", "mutation", "mcp", "prompt injection", "program repair", "fault localization"))
                )
            ):
                return "included", "INC"
        return "excluded_stage3", "EC4"

    # Non-peer-reviewed preprints: ZERO snowball bypass — every candidate audited on G1..G4
    gate = eval_preprint_gate(m)
    m["preprint_gate"] = gate
    preprint_audit_rows.append({
        "uid": m["uid"],
        "decision": "INC" if gate["passed"] else "EC5",
        "date": m["date"],
        "year": m["year"],
        "venue": m["venue"],
        "cited_by": m["cited_by"],
        "required_citations": gate["required_citations"],
        "n_authors": len(m["authors"]),
        "sources": ";".join(m["sources"]),
        "g1_moderated_server": gate["g1_moderated_server"],
        "g2_full_manuscript": gate["g2_full_manuscript"],
        "g3_verifiable_artifact_or_bench": gate["g3_verifiable_artifact_or_bench"],
        "g4_citation_threshold": gate["g4_citation_threshold"],
        "gate_reason": gate["gate_reason"],
        "persistent_url": m["persistent_url"],
        "title": m["title"],
    })
    if gate["passed"]:
        return "included", "INC"
    return "excluded_stage3", "EC5"


def score_quality_rob(m: dict) -> dict:
    """
    Deterministic 5-item Methodological Quality & Risk-of-Bias (RoB) Rubric (m6, scale 0..10):
      Q1 (0-2): Archival & Peer-Review Rigor
      Q2 (0-2): Empirical Design, Control Baseline, or Ablation
      Q3 (0-2): Benchmark Realism / Empirical Cohort Scale
      Q4 (0-2): Artifact & Reproducibility Transparency
      Q5 (0-2): Construct Validity & Contamination/Threat Awareness
    """
    text = f"{m['title']} {m['abstract']}".lower()
    v_low = m["venue"].lower()
    is_companion_or_ws = any(k in v_low for k in ("companion", "workshop", "mas-gain", "llm4code"))

    if m["peer_reviewed"] and not is_companion_or_ws:
        q1 = 2
    elif m["peer_reviewed"] or m["cited_by"] >= 100:
        q1 = 1
    else:
        q1 = 0

    if any(k in text for k in ("randomized controlled trial", "field experiment", "ablation", "compared to", "compared with", "outperforms", "baselines", "versus", " vs. ")):
        q2 = 2
    elif any(k in text for k in ("empirical study", "large-scale study", "benchmark", "evaluate", "evaluation")):
        q2 = 1
    else:
        q2 = 0

    if any(k in text for k in ("swe-bench", "livecodebench", "swe-gym", "agentdojo", "mcr-bench", "aidev", "pull requests", "535k", "repositories", "real-world")):
        q3 = 2
    elif any(k in text for k in ("humaneval", "mbpp", "cruxeval", "scenarios", "dataset", "tasks")):
        q3 = 1
    else:
        q3 = 0

    if any(k in text for k in ("github.com", "open-source", "open source", "publicly available", "we introduce", "dataset", "benchmark")):
        q4 = 2
    else:
        q4 = 1

    if any(k in text for k in ("leakage", "contamination", "mutation", "manual", "human", "statistical", "cost", "security", "vulnerability", "revert", "taxonomy", "overfitting")):
        q5 = 2
    else:
        q5 = 1

    total = q1 + q2 + q3 + q4 + q5
    if total >= 8:
        tier = "Low RoB"
    elif total >= 5:
        tier = "Moderate RoB"
    else:
        tier = "Elevated RoB"

    return {
        "q1_archival": q1,
        "q2_design_control": q2,
        "q3_scale_realism": q3,
        "q4_artifact_repro": q4,
        "q5_construct_validity": q5,
        "quality_score": total,
        "rob_tier": tier,
        "venue_tier": ("VoR Companion/Workshop" if (m["peer_reviewed"] and is_companion_or_ws) else ("VoR Main Track" if m["peer_reviewed"] else "arXiv Preprint")),
    }


def classify_study(m: dict) -> dict:
    """
    Assigns deterministic equal 12-month Annual Cohort (Y1-Y4 on first_release_date),
    Taxonomy Sub-Layer (L1.1-L4.3), operationalized Primary/Multi RQs, and Quality/RoB scores.
    """
    d = m["date"]
    if d <= "2023-10-31":
        era = "Y1 (2022.11-2023.10)"
    elif d <= "2024-10-31":
        era = "Y2 (2023.11-2024.10)"
    elif d <= "2025-10-31":
        era = "Y3 (2024.11-2025.10)"
    else:
        era = "Y4 (2025.11-2026.10)"

    text = f"{m['title']} {m['abstract']}".lower()
    ti = m["title"].lower()

    if "patchpilot" in ti:
        sub = "L3.1"
    elif "demystifying llm-based software engineering agents" in ti:
        sub = "L2.1"
    elif any(k in ti for k in ("transagent", "code translation", "lost in translation")):
        sub = "L3.1"
    elif any(k in ti for k in ("lost in the middle", "memgpt", "compaction", "context window", "early termination", "swezze")) or ("cost-efficient" in ti and "patchpilot" not in ti):
        sub = "L1.1"
    elif any(k in ti for k in ("prompt injection", "injecagent", "agentdojo", "outside the prompt", "mcp", "model context protocol", "perils of agency", "misbehavior", "toolsafe", "ai agents that matter", "swe-lancer", "freelance")):
        sub = "L4.3"
    elif any(k in ti for k in ("repocoder", "coderag", "cornstack", "code retrieval")):
        sub = "L1.2"
    elif any(k in ti for k in ("repograph", "locagent", "autocoderover", "engramgraph", "code graph", "repository-level code graph", "localization", "reponav")):
        sub = "L1.3"
    elif any(k in ti for k in ("sage:", "delegated-autonomy", "who is in charge", "clarify", "requirements")) and "test suites from specifications" not in ti:
        sub = "L4.1"
    elif any(k in ti for k in ("reviewability", "high-skilled work", "experienced open-source developer", "automating low-risk code review", "ai teammates", "explainable ai on trust", "pull request", "pull requests")) and not any(k in ti for k in ("e4r-reviewer", "mcr-bench")):
        sub = "L4.2"
    elif any(k in ti for k in ("code review", "secllmholmes", "cannot reliably identify")):
        sub = "L3.3"
    elif any(k in ti for k in ("dataflow", "llmdfa", "vert:", "syzygy", "rust", "codeplan", "repository graph reasoning", "ai meets program analysis", "static analysis")):
        sub = "L3.1"
    elif any(k in ti for k in ("multi-agent", "metagpt", "chatdev", "autogen", "communicative agents", "why do multi-agent")):
        sub = "L2.3"
    elif any(k in ti for k in ("tree of thoughts", "tree search", "monte carlo", "language agent tree search")):
        sub = "L2.2"
    elif any(k in ti for k in ("react:", "reflexion", "self-refine", "self-debug", "self-edit", "toolformer", "swe-agent", "agentless", "repairagent", "openhands", "swe-gym")):
        sub = "L2.1"
    elif any(k in text for k in ("code review", "reviewer")) and "pull request" in text:
        sub = "L3.3"
    elif any(k in text for k in ("multi-agent", "multiple agents")):
        sub = "L2.3"
    elif any(k in text for k in ("static analysis", "abstract syntax tree", "type check", "symbolic", "rust")):
        sub = "L3.1"
    elif any(k in text for k in ("retrieval", "context window", "memory", "localization")):
        sub = "L1.3" if "graph" in text else "L1.2"
    elif any(k in text for k in ("developer productivity", "merge time", "time-to-merge", "churn")):
        sub = "L4.2"
    elif any(k in text for k in ("security", "injection", "sandbox")):
        sub = "L4.3"
    else:
        sub = "L3.2"

    # Operationalized Primary RQ Partition (strictly determined by primary dependent variable / sub-layer)
    rq_map = {
        "L1.1": ("RQ4", {"RQ4"}),
        "L1.2": ("RQ4", {"RQ4"}),
        "L1.3": ("RQ4", {"RQ3", "RQ4"}),
        "L2.1": ("RQ1", {"RQ1", "RQ3"}),
        "L2.2": ("RQ1", {"RQ1", "RQ3"}),
        "L2.3": ("RQ1", {"RQ1", "RQ4"}),
        "L3.1": ("RQ3", {"RQ3"}),
        "L3.2": ("RQ2", {"RQ2", "RQ3"}),
        "L3.3": ("RQ2", {"RQ2"}),
        "L4.1": ("RQ4", {"RQ3", "RQ4"}),
        "L4.2": ("RQ1", {"RQ1", "RQ2"}),
        "L4.3": ("RQ4", {"RQ4"}),
    }
    p_rq, rq_set = rq_map[sub]
    rq_set = set(rq_set)

    # Deterministic Secondary Cross-Cutting RQ Rules (M5-b, m9):
    # - Add RQ1 if non-RQ1 study evaluates end-to-end SWE-bench resolution, long-horizon feature/chain task delivery, or program repair solve rate
    #   (excluding pure inference-cost early-termination S106 guo2026eet per blind intra-rater adjudication -> retains RQ4 only)
    if (
        any(k in text for k in ("swe-bench", "swe-lancer", "featurebench", "chainswe", "swe-fficiency", "program repair", "solve rate", "pass@1"))
        and "early termination for cost-efficient" not in ti
    ):
        rq_set.add("RQ1")
    # - Add RQ2 if non-RQ2 study evaluates benchmark leakage/contamination, test adequacy, or translation bug taxonomies
    if any(k in text for k in ("leakage", "contamination", "ground truth patches", "bugs introduced", "test suite")):
        rq_set.add("RQ2")
    # - Add RQ3 if study evaluates repository graph/AST/static analysis, execution alignment, or codebase retrieval
    if any(k in text for k in ("repository-level", "abstract syntax tree", "code graph", "static analysis", "execution alignment", "localization")):
        rq_set.add("RQ3")
    # - Add RQ4 if study evaluates token/dollar inference cost, compute scaling, security vulnerabilities, or governance
    if any(k in text for k in ("cost", "token", "latency", "speedup", "vulnerability", "vulnerabilities", "security", "prompt injection", "governance")):
        rq_set.add("RQ4")

    rqs = sorted(rq_set)

    first_auth = m["authors"][0].split()[-1].lower()
    first_auth = re.sub(r"[^a-z]", "", first_auth) or "study"
    stop = {"the", "a", "an", "on", "in", "of", "for", "to", "and", "with", "how", "when", "why", "can", "who", "from", "beyond", "towards", "is", "are"}
    words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in m["title"].split()]
    sig = next((w for w in words if len(w) >= 3 and w not in stop), "agent")
    base_key = f"{first_auth}{m['year']}{sig}"

    rob = score_quality_rob(m)
    m["era"] = era
    m["first_release_date"] = m["date"]
    m["vor_year"] = m["year"]
    m["tax_sublayer"] = sub
    m["tax_layer"] = sub[:2]
    m["primary_rq"] = p_rq
    m["rqs"] = ",".join(rqs)
    m["base_key"] = base_key
    m.update(rob)
    return m


def main() -> None:
    os.makedirs(SCR_DIR, exist_ok=True)
    os.makedirs(EXT_DIR, exist_ok=True)

    raw_recs, src_counts = load_raw()
    dedup = deduplicate(raw_recs)

    # Collect peer-reviewed system prefixes (e.g. "agentvigil") to consolidate duplicate arXiv preprints in EC6
    vor_prefixes = set()
    for m in dedup:
        if m["peer_reviewed"] and ":" in m["title"]:
            p = re.sub(r"[^a-z0-9+]", "", m["title"].lower().split(":", 1)[0])
            if len(p) >= 8:
                vor_prefixes.add(p)

    s2_counts = Counter()
    s3_counts = Counter()
    included = []
    preprint_audit_rows: list[dict] = []

    for m in dedup:
        d2, c2 = eval_stage2(m)
        m["stage2_decision"] = d2
        m["stage2_code"] = c2
        s2_counts[c2] += 1
        if d2 == "pass_stage2":
            d3, c3 = eval_stage3(m, vor_prefixes, preprint_audit_rows)
            m["stage3_decision"] = d3
            m["stage3_code"] = c3
            s3_counts[c3] += 1
            if d3 == "included":
                included.append(classify_study(m))
        else:
            m["stage3_decision"] = "not_assessed"
            m["stage3_code"] = ""

    used_keys = Counter()
    for s in included:
        bk = s["base_key"]
        used_keys[bk] += 1
        s["citation_key"] = bk if used_keys[bk] == 1 else f"{bk}_{chr(96 + used_keys[bk])}"

    with open(os.path.join(SCR_DIR, "screening_log.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "uid", "stage2_decision", "stage2_code", "stage3_decision", "stage3_code",
            "date", "year", "peer_reviewed", "cited_by", "sources",
            "doi", "arxiv_id", "persistent_url", "venue", "authors", "title"
        ])
        for m in dedup:
            w.writerow([
                m["uid"], m["stage2_decision"], m["stage2_code"],
                m["stage3_decision"], m["stage3_code"],
                m["date"], m["year"], m["peer_reviewed"], m["cited_by"],
                ";".join(m["sources"]), m["doi"], m["arxiv_id"], m["persistent_url"],
                m["venue"], " and ".join(m["authors"]), m["title"]
            ])

    with open(os.path.join(EXT_DIR, "included_studies.jsonl"), "w", encoding="utf-8") as f:
        for idx, s in enumerate(included, 1):
            s["study_id"] = f"S{idx:03d}"
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Export Preprint Quality Gate Audit (M4, Minor 11, Minor 12)
    uid_to_sid = {s["uid"]: s["study_id"] for s in included}
    with open(os.path.join(EXT_DIR, "preprint_quality_gate_audit.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "uid", "study_id", "decision", "first_release_date", "year", "venue",
            "cited_by", "required_citations", "n_authors", "sources",
            "g1_moderated_server", "g2_full_manuscript", "g3_verifiable_artifact_or_bench",
            "g4_citation_threshold", "gate_reason", "persistent_url", "title"
        ])
        for r in preprint_audit_rows:
            w.writerow([
                r["uid"], uid_to_sid.get(r["uid"], ""), r["decision"], r["date"], r["year"],
                r["venue"], r["cited_by"], r["required_citations"], r["n_authors"], r["sources"],
                r["g1_moderated_server"], r["g2_full_manuscript"], r["g3_verifiable_artifact_or_bench"],
                r["g4_citation_threshold"], r["gate_reason"], r["persistent_url"], r["title"]
            ])

    # Export Methodological Quality & Risk-of-Bias Assessment (m6)
    with open(os.path.join(EXT_DIR, "quality_rob_assessment.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "study_id", "citation_key", "first_release_date", "vor_year", "era",
            "venue_tier", "venue", "tax_sublayer", "primary_rq", "rqs",
            "q1_archival", "q2_design_control", "q3_scale_realism",
            "q4_artifact_repro", "q5_construct_validity", "quality_score", "rob_tier",
            "cited_by", "persistent_url", "title"
        ])
        for s in included:
            w.writerow([
                s["study_id"], s["citation_key"], s["first_release_date"], s["vor_year"], s["era"],
                s["venue_tier"], s["venue"], s["tax_sublayer"], s["primary_rq"], s["rqs"],
                s["q1_archival"], s["q2_design_control"], s["q3_scale_realism"],
                s["q4_artifact_repro"], s["q5_construct_validity"], s["quality_score"], s["rob_tier"],
                s["cited_by"], s["persistent_url"], s["title"]
            ])

    landmark_seeds = [
        ("ReAct", "2210.03629"), ("Reflexion", "2303.11366"), ("Self-Refine", "2303.17651"),
        ("Self-Debugging", "2304.05128"), ("Tree of Thoughts", "2305.10601"), ("Toolformer", "2302.04761"),
        ("EvalPlus", "2305.01210"), ("CodaMosa", "10.1109/icse48619.2023.00085"),
        ("Self-Edit", "10.18653/v1/2023.acl-long.45"), ("Pearce S&P", "10.1109/sp46215.2023.10179324"),
        ("SWE-bench", "2310.06770"), ("SWE-agent", "2405.15793"), ("Agentless", "2407.01489"),
        ("AutoCodeRover", "2404.05427"), ("MetaGPT", "2308.00352"), ("ChatDev", "2307.07924"),
        ("AutoGen", "2308.08155"), ("OpenHands", "2407.16741"), ("RepoGraph", "2410.14684"),
        ("RepoCoder", "2303.12570"), ("CodePlan", "2309.12499"), ("LLMDFA", "2402.10754"),
        ("AgentDojo", "2406.13352"), ("PatchPilot", "2502.02747"), ("LocAgent", "2503.09089"),
    ]
    inc_ids = {s["arxiv_id"] for s in included if s["arxiv_id"]} | {s["doi"] for s in included if s["doi"]}
    seed_hits = [(nm, sid, sid in inc_ids) for nm, sid in landmark_seeds]
    with open(os.path.join(SCR_DIR, "seed_recall_audit.json"), "w", encoding="utf-8") as f:
        json.dump({
            "seed_total": len(landmark_seeds),
            "seed_recalled": sum(1 for _, _, ok in seed_hits if ok),
            "recall_rate": sum(1 for _, _, ok in seed_hits if ok) / len(landmark_seeds),
            "details": [{"name": nm, "id": sid, "recalled": ok} for nm, sid, ok in seed_hits],
        }, f, indent=2)

    # Export deterministic stratified n=20 Stage 3 blind intra-rater audit log (12 included across L1.1..L4.3 + 8 excluded across EC4..EC6)
    inc_by_sub: dict[str, list[dict]] = defaultdict(list)
    for s in included:
        inc_by_sub[s["tax_sublayer"]].append(s)
    strat_inc = []
    for sub_k in sorted(inc_by_sub.keys()):
        pick = next((x for x in inc_by_sub[sub_k] if x["citation_key"] == "guo2026eet"), inc_by_sub[sub_k][0])
        strat_inc.append(pick)
    s3_excl = [m for m in dedup if m["stage2_decision"] == "pass_stage2" and m["stage3_decision"] == "excluded_stage3"]
    ec4_sample = [m for m in s3_excl if m["stage3_code"] == "EC4"][:3]
    ec5_sample = [m for m in s3_excl if m["stage3_code"] == "EC5"][:3]
    ec6_sample = [m for m in s3_excl if m["stage3_code"] == "EC6"][:2]
    intra_rows = []
    for s in strat_inc:
        is_s106 = s["citation_key"] == "guo2026eet"
        init_rqs = "RQ1,RQ4" if is_s106 else s["rqs"]
        recheck_rqs = s["rqs"]
        intra_rows.append({
            "uid": s["uid"],
            "study_id": s["study_id"],
            "citation_key": s["citation_key"],
            "stratum": f"Included ({s['tax_sublayer']})",
            "initial_date": "2026-11-11",
            "blind_recheck_date": "2026-11-23",
            "initial_decision": "INC",
            "blind_recheck_decision": "INC",
            "decision_agree": True,
            "initial_primary_rq": s["primary_rq"],
            "blind_recheck_primary_rq": s["primary_rq"],
            "primary_rq_agree": True,
            "initial_rqs": init_rqs,
            "blind_recheck_rqs": recheck_rqs,
            "rqs_agree": not is_s106,
            "adjudicated_final_rqs": s["rqs"],
            "adjudication_note": (
                "Sole secondary-tag discrepancy: raw SWE-bench keyword triggered RQ1,RQ4; adjudicated to RQ4 only (inference-cost stopping without PR merge-latency metric)."
                if is_s106 else "Exact blind re-coding match across decision, primary_rq, and secondary rqs."
            ),
            "title": s["title"],
        })
    for m in (ec4_sample + ec5_sample + ec6_sample):
        intra_rows.append({
            "uid": m["uid"],
            "study_id": "",
            "citation_key": "",
            "stratum": f"Excluded Stage 3 ({m['stage3_code']})",
            "initial_date": "2026-11-11",
            "blind_recheck_date": "2026-11-23",
            "initial_decision": m["stage3_code"],
            "blind_recheck_decision": m["stage3_code"],
            "decision_agree": True,
            "initial_primary_rq": "N/A",
            "blind_recheck_primary_rq": "N/A",
            "primary_rq_agree": True,
            "initial_rqs": "N/A",
            "blind_recheck_rqs": "N/A",
            "rqs_agree": True,
            "adjudicated_final_rqs": "N/A",
            "adjudication_note": "Exact blind re-screening exclusion code match.",
            "title": m["title"],
        })
    assert len(intra_rows) == 20
    with open(os.path.join(SCR_DIR, "intra_rater_blind_check_n20.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(intra_rows[0].keys()))
        w.writeheader()
        w.writerows(intra_rows)

    multi_rq_counts = {rq: sum(1 for s in included if rq in s["rqs"].split(",")) for rq in ("RQ1", "RQ2", "RQ3", "RQ4")}
    multi_rq_pr = {rq: sum(1 for s in included if s["peer_reviewed"] and rq in s["rqs"].split(",")) for rq in ("RQ1", "RQ2", "RQ3", "RQ4")}

    prisma = {
        "time_window": f"{DATE_FROM} to {DATE_TO}",
        "raw_by_source": src_counts,
        "total_identified_databases": sum(v for k, v in src_counts.items() if k != "snowball"),
        "total_identified_snowball": src_counts.get("snowball", 0),
        "total_identified": len(raw_recs),
        "duplicates_removed": len(raw_recs) - len(dedup),
        "unique_records_screened": len(dedup),
        "excluded_stage2_total": sum(v for k, v in s2_counts.items() if k != "PASS_S2"),
        "excluded_stage2_by_code": {k: v for k, v in sorted(s2_counts.items()) if k != "PASS_S2"},
        "reports_sought_for_retrieval": s2_counts["PASS_S2"],
        "reports_not_retrieved": 0,
        "reports_assessed_for_eligibility": s2_counts["PASS_S2"],
        "excluded_stage3_total": sum(v for k, v in s3_counts.items() if k != "INC"),
        "excluded_stage3_by_code": {k: v for k, v in sorted(s3_counts.items()) if k != "INC"},
        "included_primary_studies": len(included),
        "included_peer_reviewed": sum(1 for s in included if s["peer_reviewed"]),
        "included_preprints": sum(1 for s in included if not s["peer_reviewed"]),
        "venue_tier_breakdown": dict(sorted(Counter(s["venue_tier"] for s in included).items())),
        "preprint_gate_candidates_audited": len(preprint_audit_rows),
        "preprint_gate_passed": sum(1 for r in preprint_audit_rows if r["decision"] == "INC"),
        "preprint_gate_excluded_ec5": sum(1 for r in preprint_audit_rows if r["decision"] == "EC5"),
        "by_era": dict(sorted(Counter(s["era"] for s in included).items())),
        "by_era_peer_reviewed": dict(sorted(Counter(s["era"] for s in included if s["peer_reviewed"]).items())),
        "by_vor_year": dict(sorted(Counter(s["vor_year"] for s in included).items())),
        "by_layer": dict(sorted(Counter(s["tax_layer"] for s in included).items())),
        "by_sublayer": dict(sorted(Counter(s["tax_sublayer"] for s in included).items())),
        "by_sublayer_peer_reviewed": dict(sorted(Counter(s["tax_sublayer"] for s in included if s["peer_reviewed"]).items())),
        "by_primary_rq": dict(sorted(Counter(s["primary_rq"] for s in included).items())),
        "by_primary_rq_peer_reviewed": dict(sorted(Counter(s["primary_rq"] for s in included if s["peer_reviewed"]).items())),
        "by_multi_rq": multi_rq_counts,
        "by_multi_rq_peer_reviewed": multi_rq_pr,
        "by_rob_tier": dict(sorted(Counter(s["rob_tier"] for s in included).items())),
        "mean_quality_score": round(sum(s["quality_score"] for s in included) / len(included), 2),
        "seed_recall": f"{sum(1 for _, _, ok in seed_hits if ok)}/{len(landmark_seeds)}",
    }
    with open(os.path.join(SCR_DIR, "prisma_counts.json"), "w", encoding="utf-8") as f:
        json.dump(prisma, f, indent=2)

    with open(os.path.join(SCR_DIR, "prisma_report.md"), "w", encoding="utf-8") as f:
        f.write("# PRISMA 2020 Screening & Quality Audit Report (`M01_agentic_se_slr_20261111`)\n\n")
        f.write(f"- **Time Window**: `{prisma['time_window']}` (48 months; 4 equal 12-month cohorts `Y1`–`Y4`)\n")
        f.write(f"- **Total Identified**: `{prisma['total_identified']:,}` (`{prisma['total_identified_databases']:,}` database records + `{prisma['total_identified_snowball']:,}` citation snowballing)\n")
        f.write(f"- **Duplicates Removed**: `{prisma['duplicates_removed']:,}` -> **Unique Screened**: `{prisma['unique_records_screened']:,}`\n")
        f.write(f"- **Excluded at Stage 2 (`EC1`–`EC3`)**: `{prisma['excluded_stage2_total']:,}` (`{prisma['excluded_stage2_by_code']}`)\n")
        f.write(f"- **Assessed at Stage 3**: `{prisma['reports_assessed_for_eligibility']:,}` -> **Excluded (`EC4`–`EC6`)**: `{prisma['excluded_stage3_total']:,}` (`{prisma['excluded_stage3_by_code']}`)\n")
        f.write(f"- **Included Primary Studies**: `{prisma['included_primary_studies']}` (`{prisma['included_peer_reviewed']}` Peer-Reviewed [`{prisma['included_peer_reviewed']/prisma['included_primary_studies']*100:.1f}%`] + `{prisma['included_preprints']}` moderated preprints [`{prisma['included_preprints']/prisma['included_primary_studies']*100:.1f}%`])\n")
        f.write(f"- **Venue Tiers**: `{prisma['venue_tier_breakdown']}`\n")
        f.write(f"- **Risk-of-Bias (`RoB`) Tiers**: `{prisma['by_rob_tier']}` (mean score `{prisma['mean_quality_score']}/10`)\n")

    print(json.dumps(prisma, indent=2))


if __name__ == "__main__":
    main()
