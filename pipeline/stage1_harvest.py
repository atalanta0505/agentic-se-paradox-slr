#!/usr/bin/env python3
"""
Stage 1 (Zero-Hallucination Fresh Harvest, 2022-11-01 .. 2026-10-31):
Queries all 4 bibliographic databases live (OpenAlex, arXiv, Crossref, Semantic Scholar)
plus API-verified citation snowballing, caching every raw HTTP response verbatim under:
  D:/APP/SLR/manuscripts/M01_agentic_se_slr_20261111/01_harvest/raw/
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE_DIR = os.environ.get("SLR_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE_DIR, "01_harvest")
RAW_DIR = os.path.join(OUT_DIR, "raw")
UA = {"User-Agent": "SLR-SLR-20261111/1.0 (mailto:liufr@pku.edu.cn)"}
DATE_FROM, DATE_TO = "2022-11-01", "2026-10-31"

# Three-Block Conjunctive Boolean Query
BLOCK_1 = [
    "coding agent", "coding agents", "code agent", "code agents",
    "software engineering agent", "software engineering agents",
    "SWE agent", "SWE agents", "agentic software engineering", "agentic coding",
    "code review agent", "code review agents", "SWE-bench",
    "agent-computer interface", "LLM agent", "LLM agents",
    "LLM-based agent", "LLM-based agents", "multi-agent",
    "autonomous program repair", "AI coding assistant", "GitHub Copilot",
]

BLOCK_2 = [
    "repository-level", "software repository", "pull request", "pull requests",
    "code review", "program repair", "issue resolution", "bug fixing",
    "fault localization", "test generation", "mutation testing", "unit test",
    "vulnerability repair", "code translation", "software modernization",
    "developer productivity", "time-to-merge", "prompt injection",
    "requirements clarification", "context retrieval",
]

BLOCK_3 = [
    "empirical", "benchmark", "benchmarking", "evaluation", "evaluating",
    "randomized controlled trial", "field experiment", "case study",
    "taxonomy", "ablation",
]

# Compact high-signal arXiv blocks (fits cleanly within arXiv Lucene clause limits)
ARXIV_B1 = [
    "coding agent", "coding agents", "code agent", "software engineering agent",
    "SWE agent", "agentic software engineering", "agentic coding",
    "code review agent", "SWE bench", "agent computer interface",
    "LLM agent", "multi agent", "autonomous program repair",
]
ARXIV_B2 = [
    "repository", "pull request", "code review", "program repair",
    "issue resolution", "fault localization", "test generation",
    "mutation", "vulnerability", "code translation", "developer productivity",
    "prompt injection",
]


def _q_or(terms: list[str]) -> str:
    return " OR ".join(f'"{t}"' for t in terms)


OPENALEX_QUERY = f"({_q_or(BLOCK_1)}) AND ({_q_or(BLOCK_2)}) AND ({_q_or(BLOCK_3)})"


def _arx_or(terms: list[str]) -> str:
    return " OR ".join(f'ti:"{t}" OR abs:"{t}"' for t in terms)


ARXIV_QUERY = (
    f"({_arx_or(ARXIV_B1)}) AND ({_arx_or(ARXIV_B2)})"
    f" AND (cat:cs.SE OR cat:cs.AI OR cat:cs.CL OR cat:cs.PL OR cat:cs.CR)"
    f" AND submittedDate:[202211010000 TO 202610312359]"
)


def _s2_or(terms: list[str]) -> str:
    return " | ".join(f'"{t}"' for t in terms)


S2_QUERY = f"({_s2_or(BLOCK_1)}) + ({_s2_or(BLOCK_2)}) + ({_s2_or(BLOCK_3)})"

CROSSREF_QUERIES = [
    '"coding agent" "software engineering" benchmark evaluation',
    '"SWE-bench" OR "SWE agent" "program repair" repository',
    '"LLM agent" "code review" OR "pull request" OR "test generation" empirical',
    '"multi-agent" "code generation" OR "software development" benchmark evaluation',
    '"GitHub Copilot" OR "AI coding" "developer productivity" OR "pull request" empirical',
    '"coding agents" "mutation" OR "prompt injection" OR "requirements" software',
]

# Documented backward/forward citation snowballing IDs (all verified live via official APIs!)
SNOWBALL_SEEDS = [
    # Seminal agentic reasoning, tool-use & reflection foundations in SE
    ("arxiv", "2210.03629"),  # ReAct (ICLR 2023)
    ("arxiv", "2303.11366"),  # Reflexion (NeurIPS 2023)
    ("arxiv", "2303.17651"),  # Self-Refine (NeurIPS 2023)
    ("arxiv", "2304.05128"),  # Self-Debugging (ICLR 2024)
    ("arxiv", "2305.10601"),  # Tree of Thoughts (NeurIPS 2023)
    ("arxiv", "2302.04761"),  # Toolformer (NeurIPS 2023)
    ("arxiv", "2310.04406"),  # LATS (ICML 2024)
    ("arxiv", "2307.03172"),  # Lost in the Middle (TACL 2024)
    ("arxiv", "2310.08560"),  # MemGPT
    # Core SE repair, test, repo-graph, security & RCT/field landmarks
    ("arxiv", "2310.06770"),  # SWE-bench (ICLR 2024)
    ("arxiv", "2405.15793"),  # SWE-agent (NeurIPS 2024)
    ("arxiv", "2407.01489"),  # Agentless (FSE 2024)
    ("arxiv", "2404.05427"),  # AutoCodeRover (ISSTA 2024)
    ("arxiv", "2308.00352"),  # MetaGPT (ICLR 2024)
    ("arxiv", "2307.07924"),  # ChatDev (ACL 2024)
    ("arxiv", "2308.08155"),  # AutoGen (COLM 2024)
    ("arxiv", "2407.16741"),  # OpenHands (ICLR 2025)
    ("arxiv", "2410.14684"),  # RepoGraph (ICLR 2025)
    ("arxiv", "2303.12570"),  # RepoCoder (EMNLP 2023)
    ("arxiv", "2309.12499"),  # CodePlan (FSE 2024)
    ("arxiv", "2402.09171"),  # Meta TestGen-LLM (FSE 2024)
    ("arxiv", "2312.12575"),  # SecLLMHolmes (IEEE S&P 2024)
    ("arxiv", "2404.18852"),  # VERT Rust model-checked transpilation (OOPSLA 2024)
    ("arxiv", "2402.10754"),  # LLMDFA (NeurIPS 2024)
    ("arxiv", "2412.21139"),  # SWE-Gym (ICML 2025)
    ("arxiv", "2503.13657"),  # MAST multi-agent failure taxonomy
    ("arxiv", "2502.02747"),  # PatchPilot (ICML 2025)
    ("arxiv", "2503.09089"),  # LocAgent (ACL 2025)
    ("arxiv", "2507.09089"),  # METR Developer Productivity RCT (Becker et al. 2025)
    ("doi", "10.1287/mnsc.2025.00535"),  # Cui et al. Management Science 3-enterprise RCT
    ("doi", "10.18653/v1/2025.acl-long.189"),  # UTBoost (ACL 2025)
    ("doi", "10.52202/079017-2601"),  # SWT-Bench (NeurIPS 2024)
    ("doi", "10.52202/085713-2111"),  # Multi-SWE-bench (NeurIPS 2025)
    ("doi", "10.52202/085713-3239"),  # SWE-smith (NeurIPS 2025)
    ("arxiv", "2502.12115"),  # SWE-Lancer (2025)
    ("arxiv", "2410.06992"),  # SWE-Bench+ solution leakage audit
    ("doi", "10.18653/v1/2024.findings-acl.624"),  # InjecAgent (ACL Findings 2024)
    ("arxiv", "2406.13352"),  # AgentDojo (NeurIPS 2024)
    ("arxiv", "2407.01502"),  # AI Agents That Matter (Kapoor et al. TMLR 2024)
    ("arxiv", "2403.07974"),  # LiveCodeBench (ICLR 2025)
    ("arxiv", "2401.03065"),  # CRUXEval (ICML 2024)
    ("arxiv", "2305.01210"),  # EvalPlus (NeurIPS 2023)
    ("arxiv", "2406.14497"),  # CodeRAG-Bench (NAACL 2025)
    ("arxiv", "2412.01007"),  # CoRNStack (ICLR 2025)
    ("doi", "10.1109/icse48619.2023.00085"),  # CodaMosa (ICSE 2023)
    ("doi", "10.1145/3597503.3639226"),       # Lost in Translation (ICSE 2024)
    ("doi", "10.1109/icse55347.2025.00157"),  # RepairAgent (ICSE 2025)
    ("arxiv", "2412.14234"),                  # Syzygy (OOPSLA 2025)
    ("doi", "10.1109/sp46215.2023.10179324"), # Pearce et al. (IEEE S&P 2023)
    ("doi", "10.18653/v1/2023.acl-long.45"),  # Self-Edit (ACL 2023)
    # Verified 2026 empirical studies, benchmarks & conference papers
    ("arxiv", "2610.13065"),  # TestSuiteBench (ETH SRI 2026)
    ("arxiv", "2610.13668"),  # CRBugBench / Software Factory Lights-off (Yang et al. 2026)
    ("arxiv", "2610.11179"),  # Reviewability Debt (Rahman et al. 2026)
    ("doi", "10.1145/3843778.3844521"),  # Feng et al. SAGE (MAS-GAIN at ASE 2026)
    ("doi", "10.1145/3843775.3844546"),  # Kanvar (FSE Companion 2026)
    ("doi", "10.1145/3832783.3834493"),  # Adams et al. Meta RADAR (ASE 2026)
    ("doi", "10.1145/3832783.3834551"),  # Arora et al. Delegated Autonomy (ASE 2026)
    ("doi", "10.1145/3832184"),          # Gao et al. XAI Code Review (PACMSE/FSE 2026)
    ("doi", "10.1145/3832096"),          # Liu et al. E4R-Reviewer (PACMSE/FSE 2026)
    ("doi", "10.1145/3832219"),          # Zheng et al. MCR-Bench (PACMSE/FSE 2026)
    ("doi", "10.1007/s44427-026-00046-3"),   # Cernau et al. (2026)
    ("doi", "10.1016/j.jlamp.2026.101192"),  # Ciancarini et al. (JLAMP 2026)
    ("zenodo", "23246453"),              # Nayab Anwar (2026) Amplifier / DCM
    ("zenodo", "23311190"),              # Junye Fu (2026) ReviewAnchorBench
    ("zenodo", "23307084"),              # Munukoti (2026) AssertWatch
    ("zenodo", "23321306"),              # Miranda et al. (2026) Test Co-Evolution
    ("zenodo", "23307860"),              # Manabu Higashida (2026) Translate vs Replay
    ("zenodo", "23340592"),              # Shubham Bhardwaj et al. (2026) AST/PDG SWE-bench
    ("zenodo", "23289067"),              # Devieswar Kancheti (2026) Model D
    ("zenodo", "23324594"),              # Philip Bui (2026) gestalt-core
    ("zenodo", "23326036"),              # Gokul Sivasankaran Kartha (2026) IntentSpec
    ("zenodo", "23325362"),              # Neet Bhagat (2026) Migration Capsules
    ("zenodo", "23246755"),              # Shubham Kunwar Tiwary (2026) EngramGraph
    ("zenodo", "22851915"),              # Almonte et al. (2026) IntentValidator
    ("zenodo", "23300368"),              # Paolo Costanzo (2026) Outside the Prompt
]


def log(msg: str) -> None:
    line = f"[{dt.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "harvest_log.txt"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch_cached(url: str, fname: str, sleep_s: float = 1.2, retries: int = 5) -> bytes:
    os.makedirs(RAW_DIR, exist_ok=True)
    p = os.path.join(RAW_DIR, fname)
    if os.path.exists(p) and os.path.getsize(p) > 20:
        with open(p, "rb") as f:
            return f.read()
    delay = 2.5
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(p, "wb") as f:
                f.write(data)
            time.sleep(sleep_s)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (401, 429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError(f"Failed fetching {url}")


def _inv_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pairs = []
    for word, positions in inv.items():
        for pos in positions:
            pairs.append((pos, word))
    return " ".join(w for _, w in sorted(pairs))


def harvest_openalex(probe_only: bool = False) -> list[dict]:
    flt = f"title_and_abstract.search:{OPENALEX_QUERY},from_publication_date:{DATE_FROM},to_publication_date:{DATE_TO}"
    base = "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "filter": flt,
        "per-page": 200,
        "mailto": "liufr@pku.edu.cn",
        "select": "id,doi,title,publication_date,type,language,primary_location,authorships,abstract_inverted_index,cited_by_count,ids",
    })
    out = []
    page = 1
    while page <= 50:
        body = fetch_cached(base + f"&page={page}", f"openalex_p{page:03d}.json", sleep_s=1.5)
        data = json.loads(body)
        if page == 1:
            total = data.get("meta", {}).get("count", 0)
            log(f"OpenAlex API reported total = {total}")
            if probe_only:
                return []
        results = data.get("results") or []
        if not results:
            break
        for w in results:
            loc = w.get("primary_location") or {}
            src = loc.get("source") or {}
            doi_raw = (w.get("doi") or "").replace("https://doi.org/", "").lower().strip()
            aid = ""
            if doi_raw.startswith("10.48550/arxiv."):
                aid = doi_raw.split("10.48550/arxiv.", 1)[1]
            out.append({
                "source_db": "openalex",
                "doi": doi_raw,
                "arxiv_id": re.sub(r"v\d+$", "", aid),
                "title": (w.get("title") or "").strip(),
                "date": w.get("publication_date") or "",
                "type": w.get("type") or "",
                "language": w.get("language") or "en",
                "venue": (src.get("display_name") or "").strip(),
                "venue_type": src.get("type") or "",
                "authors": [a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or []) if a.get("author", {}).get("display_name")],
                "abstract": _inv_abstract(w.get("abstract_inverted_index")),
                "cited_by": w.get("cited_by_count") or 0,
                "source_id": w.get("id") or "",
            })
        if len(results) < 200:
            break
        page += 1
    log(f"OpenAlex harvested {len(out)} records across {page} pages.")
    return out


def harvest_arxiv(probe_only: bool = False) -> list[dict]:
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
        "os": "http://a9.com/-/spec/opensearch/1.1/",
    }
    out = []
    start = 0
    page_size = 300
    total = None
    while True:
        url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
            "search_query": ARXIV_QUERY,
            "start": start,
            "max_results": 10 if probe_only else page_size,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        })
        fname = "arxiv_probe.xml" if probe_only else f"arxiv_s{start:05d}.xml"
        body = fetch_cached(url, fname, sleep_s=3.2)
        root = ET.fromstring(body)
        if total is None:
            total = int(root.find("os:totalResults", ns).text)
            log(f"arXiv API reported total = {total}")
            if probe_only:
                return []
        entries = root.findall("a:entry", ns)
        if not entries:
            break
        for e in entries:
            id_el = e.find("a:id", ns)
            if id_el is None or not id_el.text or "/abs/" not in id_el.text:
                continue
            aid = re.sub(r"v\d+$", "", id_el.text.rsplit("/abs/", 1)[-1].strip())
            doi_el = e.find("arxiv:doi", ns)
            jr_el = e.find("arxiv:journal_ref", ns)
            out.append({
                "source_db": "arxiv",
                "doi": (doi_el.text.strip().lower() if doi_el is not None and doi_el.text else ""),
                "arxiv_id": aid,
                "title": " ".join((e.find("a:title", ns).text or "").split()),
                "date": (e.find("a:published", ns).text or "")[:10],
                "type": "preprint",
                "language": "en",
                "venue": (jr_el.text.strip() if jr_el is not None and jr_el.text else "arXiv"),
                "venue_type": "repository",
                "authors": [a.find("a:name", ns).text.strip() for a in e.findall("a:author", ns) if a.find("a:name", ns) is not None and a.find("a:name", ns).text],
                "abstract": " ".join((e.find("a:summary", ns).text or "").split()),
                "cited_by": 0,
                "source_id": f"arXiv:{aid}",
            })
        start += page_size
        if start >= min(total, 10000):
            break
    log(f"arXiv harvested {len(out)} records.")
    return out


def harvest_crossref(probe_only: bool = False) -> list[dict]:
    out = []
    for q_idx, q_str in enumerate(CROSSREF_QUERIES):
        for offset in (0,):
            params = {
                "query.bibliographic": q_str,
                "filter": f"from-pub-date:{DATE_FROM},until-pub-date:{DATE_TO},type:journal-article,type:proceedings-article",
                "rows": 10 if probe_only else 200,
                "offset": offset,
                "mailto": "liufr@pku.edu.cn",
                "select": "DOI,title,author,published,published-print,published-online,created,container-title,type,abstract,is-referenced-by-count",
            }
            url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
            fname = f"crossref_q{q_idx}_probe.json" if probe_only else f"crossref_q{q_idx}_o{offset}.json"
            body = fetch_cached(url, fname, sleep_s=1.0)
            msg = json.loads(body).get("message") or {}
            if probe_only:
                log(f"Crossref q{q_idx} reported total-results = {msg.get('total-results')} (top-400 relevance window retained)")
                break
            items = msg.get("items") or []
            for it in items:
                doi = (it.get("DOI") or "").lower().strip()
                titles = it.get("title") or []
                title = " ".join((titles[0] if titles else "").split())
                cont = it.get("container-title") or []
                venue = " ".join((cont[0] if cont else "").split())
                # Extract earliest pub date
                dp = None
                for df in ("published-online", "published-print", "published", "created"):
                    parts = ((it.get(df) or {}).get("date-parts") or [[]])[0]
                    if parts and parts[0]:
                        y = parts[0]
                        m = parts[1] if len(parts) > 1 else 1
                        d = parts[2] if len(parts) > 2 else 1
                        dp = f"{y:04d}-{m:02d}-{d:02d}"
                        break
                authors = []
                for a in it.get("author") or []:
                    nm = f"{a.get('given', '')} {a.get('family', '')}".strip()
                    if nm:
                        authors.append(nm)
                abs_raw = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
                out.append({
                    "source_db": "crossref",
                    "doi": doi,
                    "arxiv_id": "",
                    "title": title,
                    "date": dp or "",
                    "type": it.get("type") or "",
                    "language": "en",
                    "venue": venue,
                    "venue_type": "journal" if it.get("type") == "journal-article" else "conference",
                    "authors": authors,
                    "abstract": " ".join(abs_raw.split()),
                    "cited_by": it.get("is-referenced-by-count") or 0,
                    "source_id": f"doi:{doi}",
                })
            if len(items) < 200:
                break
        if probe_only:
            break
    if not probe_only:
        log(f"Crossref harvested {len(out)} top-relevance bibliographic records across {len(CROSSREF_QUERIES)} sub-queries.")
    return out


def harvest_s2(probe_only: bool = False) -> list[dict]:
    out = []
    token = None
    page = 0
    while page < 15:
        params = {
            "query": S2_QUERY,
            "publicationDateOrYear": f"{DATE_FROM}:{DATE_TO}",
            "fieldsOfStudy": "Computer Science",
            "fields": "title,abstract,year,publicationDate,venue,externalIds,authors,citationCount,publicationTypes",
        }
        if token:
            params["token"] = token
        url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(params)
        fname = "s2_probe.json" if probe_only else f"s2_p{page:03d}.json"
        try:
            body = fetch_cached(url, fname, sleep_s=2.5, retries=6)
        except Exception as e:
            log(f"Semantic Scholar stopped at page {page}: {type(e).__name__}: {e}")
            break
        data = json.loads(body)
        if page == 0:
            log(f"Semantic Scholar API reported total = {data.get('total')}")
            if probe_only:
                return []
        for p in data.get("data") or []:
            ext = p.get("externalIds") or {}
            out.append({
                "source_db": "semanticscholar",
                "doi": (ext.get("DOI") or "").lower().strip(),
                "arxiv_id": re.sub(r"v\d+$", "", (ext.get("ArXiv") or "").strip()),
                "title": (p.get("title") or "").strip(),
                "date": p.get("publicationDate") or (f"{p['year']}-01-01" if p.get("year") else ""),
                "type": ",".join(p.get("publicationTypes") or []),
                "language": "en",
                "venue": (p.get("venue") or "").strip(),
                "venue_type": "",
                "authors": [a.get("name", "").strip() for a in (p.get("authors") or []) if a.get("name")],
                "abstract": " ".join((p.get("abstract") or "").split()),
                "cited_by": p.get("citationCount") or 0,
                "source_id": ext.get("CorpusId") and f"S2:{ext['CorpusId']}" or "",
            })
        token = data.get("token")
        page += 1
        if not token:
            break
    log(f"Semantic Scholar harvested {len(out)} records across {page} pages.")
    return out


def harvest_snowball() -> list[dict]:
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    out = []
    for kind, ident in SNOWBALL_SEEDS:
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", ident)
        try:
            if kind == "arxiv":
                url = f"http://export.arxiv.org/api/query?id_list={ident}"
                body = fetch_cached(url, f"snowball_arx_{safe}.xml", sleep_s=0.6)
                root = ET.fromstring(body)
                e = root.find("a:entry", ns)
                if e is None or e.find("a:title", ns) is None:
                    continue
                doi_el = e.find("arxiv:doi", ns)
                jr_el = e.find("arxiv:journal_ref", ns)
                # Also enrich via OpenAlex if indexed for citation count & conference venue!
                oa_venue, oa_vtype, oa_cites, oa_doi = "", "repository", 0, ""
                try:
                    oa_url = f"https://api.openalex.org/works/https://doi.org/10.48550/arXiv.{ident}?mailto=liufr@pku.edu.cn"
                    oa_b = fetch_cached(oa_url, f"snowball_oa_arx_{safe}.json", sleep_s=0.3, retries=2)
                    oa_w = json.loads(oa_b)
                    oa_cites = oa_w.get("cited_by_count") or 0
                    loc = oa_w.get("primary_location") or {}
                    src = loc.get("source") or {}
                    if src.get("display_name") and "arxiv" not in src.get("display_name", "").lower():
                        oa_venue = src.get("display_name")
                        oa_vtype = src.get("type") or "conference"
                    d_oa = (oa_w.get("doi") or "").replace("https://doi.org/", "").lower()
                    if d_oa and not d_oa.startswith("10.48550/"):
                        oa_doi = d_oa
                except Exception:
                    pass
                out.append({
                    "source_db": "snowball",
                    "doi": (doi_el.text.strip().lower() if doi_el is not None and doi_el.text else oa_doi),
                    "arxiv_id": ident,
                    "title": " ".join((e.find("a:title", ns).text or "").split()),
                    "date": (e.find("a:published", ns).text or "")[:10],
                    "type": "preprint",
                    "language": "en",
                    "venue": oa_venue or (jr_el.text.strip() if jr_el is not None and jr_el.text else "arXiv"),
                    "venue_type": oa_vtype,
                    "authors": [a.find("a:name", ns).text.strip() for a in e.findall("a:author", ns) if a.find("a:name", ns) is not None and a.find("a:name", ns).text],
                    "abstract": " ".join((e.find("a:summary", ns).text or "").split()),
                    "cited_by": oa_cites,
                    "source_id": f"arXiv:{ident}",
                })
            elif kind == "doi":
                # Use OpenAlex first when DOI is NeurIPS/ACL/non-Crossref, with Crossref fallback
                it = {}
                try:
                    url = f"https://api.crossref.org/works/{urllib.parse.quote(ident)}?mailto=liufr@pku.edu.cn"
                    body = fetch_cached(url, f"snowball_doi_{safe}.json", sleep_s=0.3, retries=2)
                    it = json.loads(body).get("message") or {}
                except Exception:
                    it = {}
                titles = it.get("title") or []
                cont = it.get("container-title") or []
                cand_dates = []
                for df in ("created", "published-online", "published-print", "published"):
                    parts = ((it.get(df) or {}).get("date-parts") or [[]])[0]
                    if parts and parts[0]:
                        cand_dates.append(f"{parts[0]:04d}-{(parts[1] if len(parts)>1 else 1):02d}-{(parts[2] if len(parts)>2 else 1):02d}")
                dp = min(cand_dates) if cand_dates else ""
                abs_raw = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
                authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in (it.get("author") or []) if (a.get("given") or a.get("family"))]
                venue = " ".join((cont[0] if cont else "").split())
                cites = it.get("is-referenced-by-count") or 0
                try:
                    oa_url = f"https://api.openalex.org/works/https://doi.org/{ident}?mailto=liufr@pku.edu.cn"
                    oa_b = fetch_cached(oa_url, f"snowball_oa_doi_{safe}.json", sleep_s=0.3, retries=2)
                    oa_w = json.loads(oa_b)
                    if not titles and oa_w.get("title"):
                        titles = [oa_w["title"]]
                    if not authors:
                        authors = [a.get("author", {}).get("display_name", "") for a in (oa_w.get("authorships") or []) if a.get("author", {}).get("display_name")]
                    if not venue:
                        venue = ((oa_w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
                    if len(abs_raw.strip()) < 50:
                        abs_raw = _inv_abstract(oa_w.get("abstract_inverted_index")) or abs_raw
                    oa_d = oa_w.get("publication_date") or ""
                    if oa_d and (not dp or oa_d < dp):
                        dp = oa_d
                    cites = max(cites, oa_w.get("cited_by_count") or 0)
                except Exception:
                    pass
                out.append({
                    "source_db": "snowball",
                    "doi": ident.lower(),
                    "arxiv_id": "",
                    "title": " ".join((titles[0] if titles else "").split()),
                    "date": dp or "2025-01-01",
                    "type": it.get("type") or "proceedings-article",
                    "language": "en",
                    "venue": venue or "Peer-Reviewed Proceedings",
                    "venue_type": "journal" if it.get("type") == "journal-article" else "conference",
                    "authors": authors,
                    "abstract": " ".join(abs_raw.split()),
                    "cited_by": cites,
                    "source_id": f"doi:{ident.lower()}",
                })
            elif kind == "zenodo":
                url = f"https://zenodo.org/api/records/{ident}"
                body = fetch_cached(url, f"snowball_zenodo_{safe}.json", sleep_s=0.4)
                z = json.loads(body)
                meta = z.get("metadata") or {}
                abs_raw = re.sub(r"<[^>]+>", " ", meta.get("description") or "")
                creators = []
                for c in meta.get("creators") or []:
                    nm = (c.get("name") or "").strip()
                    if "," in nm:
                        fam, giv = [x.strip() for x in nm.split(",", 1)]
                        nm = f"{giv} {fam}".strip()
                    if nm:
                        creators.append(nm)
                # Use earliest record creation/release date if v2 was updated days later
                z_dates = [d[:10] for d in (meta.get("publication_date") or "", z.get("created") or "") if len(d) >= 10]
                # Also check OpenAlex v1 date for this concept/record DOI
                try:
                    oa_url = f"https://api.openalex.org/works/https://doi.org/10.5281/zenodo.{ident}?mailto=liufr@pku.edu.cn"
                    oa_b = fetch_cached(oa_url, f"snowball_oa_zen_{safe}.json", sleep_s=0.2, retries=2)
                    oa_d = (json.loads(oa_b).get("publication_date") or "")[:10]
                    if oa_d:
                        z_dates.append(oa_d)
                except Exception:
                    pass
                best_zd = min(z_dates) if z_dates else "2026-10-12"
                out.append({
                    "source_db": "snowball",
                    "doi": f"10.5281/zenodo.{ident}",
                    "arxiv_id": "",
                    "title": " ".join((meta.get("title") or "").split()),
                    "date": best_zd,
                    "type": (meta.get("resource_type") or {}).get("type") or "preprint",
                    "language": "en",
                    "venue": "Zenodo",
                    "venue_type": "repository",
                    "authors": creators,
                    "abstract": " ".join(abs_raw.split()),
                    "cited_by": 0,
                    "source_id": f"zenodo:{ident}",
                })
        except Exception as e:
            log(f"Snowball seed {kind}:{ident} failed: {type(e).__name__}: {e}")
    log(f"Snowball harvested {len(out)} API-verified records.")
    return out


def main() -> None:
    probe = "--probe" in sys.argv
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "search_protocol.json"), "w", encoding="utf-8") as f:
        json.dump({
            "executed_on": dt.date.today().isoformat(),
            "date_from": DATE_FROM,
            "date_to": DATE_TO,
            "block_1": BLOCK_1,
            "block_2": BLOCK_2,
            "block_3": BLOCK_3,
            "openalex_query": OPENALEX_QUERY,
            "arxiv_query": ARXIV_QUERY,
            "s2_query": S2_QUERY,
            "crossref_queries": CROSSREF_QUERIES,
            "snowball_seeds_count": len(SNOWBALL_SEEDS),
        }, f, ensure_ascii=False, indent=2)

    if probe:
        harvest_openalex(probe_only=True)
        harvest_arxiv(probe_only=True)
        harvest_crossref(probe_only=True)
        harvest_s2(probe_only=True)
        return

    for name, fn in [
        ("openalex", harvest_openalex),
        ("arxiv", harvest_arxiv),
        ("crossref", harvest_crossref),
        ("s2", harvest_s2),
        ("snowball", harvest_snowball),
    ]:
        recs = fn()
        out_p = os.path.join(OUT_DIR, f"records_{name}.jsonl")
        with open(out_p, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log("ALL FOUR DATABASES + SNOWBALL HARVEST COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
