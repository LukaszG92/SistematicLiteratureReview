#!/usr/bin/env python3
"""
Iterative citation snowballing (backward + forward) via OpenAlex API,
with dedup against the existing SLR corpus (DOI + fuzzy title match).

No CLI flags — edit the CONFIG block below if you need to change anything,
then just run:

    python snowball_openalex.py

Method: Wohlin-style iterative snowballing.
- backward = references of each seed (survey papers in SEEDS_CSV)
- forward  = works citing each seed (OpenAlex `cites:` filter)
- each round, newly found items become seeds for the next round
- stops at ROUNDS or at saturation (no new items)

Dedup: normalized DOI match, then token-set fuzzy title match.

Requires: requests, pandas  (pip install requests pandas)
"""

import csv
import os
import re
import sys
import time
from difflib import SequenceMatcher

import pandas as pd
import requests

# ============================== CONFIG ==============================

SEEDS_CSV = "data/p1_included_surveys.csv"        # included surveys, one row = one seed
SEEDS_CSV_DOI_COL = "DOI"

CORPUS_CSV = "data/p0_full_corpus.csv"  # full original corpus, for dedup
CORPUS_DOI_COL = "DOI"
CORPUS_TITLE_COL = "Title"

OUT_CSV = "snowball_candidates.csv"
SOURCE_PHASE = "snowballing_included_surveys"  # tag for PRISMA bookkeeping

ROUNDS = 2
YEAR_MIN = 2019
YEAR_MAX = 2026
MAX_FORWARD_PER_SEED = 300     # cap on citing works fetched per seed (lowered
                                # to contain round-2 blowup on highly-cited hubs)
TITLE_SIM_THRESHOLD = 0.90

# Topical inclusion filter for round >= 2 findings. Round-1 candidates
# (found directly from the verified survey seeds, backward or forward) are
# ALWAYS kept unfiltered and trusted — that set is small (a few hundred) and
# high-precision. Candidates first discovered in round 2 (or later, if you
# ever raise ROUNDS) are NOT verified in-topic themselves, so without a
# filter the final round dumps everything it finds straight into the output
# with no gate at all (an expansion-only filter has zero effect on the last
# round, since there's no round N+1 left to gate). This filter decides
# whether a round>=2 candidate is kept in the output CSV at all.
TOPICAL_FILTER_ENABLED = True
TOPICAL_MUST_CONTAIN = ["quantum"]
TOPICAL_MUST_CONTAIN_ANY = [
    "language", "nlp", "text", "linguistic", "sentiment",
    "word embedding", "discocat", "lambeq",
]

MAILTO = ""   # put your email here to join OpenAlex's polite pool (optional
              # but recommended: higher rate limits, more reliable requests)

# ======================================================================

API = "https://api.openalex.org"


# ----------------------------- helpers -----------------------------

def norm_doi(doi):
    if not doi or not isinstance(doi, str):
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi)
    return doi or None


def norm_title(title):
    if not title or not isinstance(title, str):
        return ""
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return " ".join(sorted(t.split()))  # token-set normalization


def title_sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def passes_topical_filter(rec):
    """Should this candidate be kept in the output at all?
    Round 1 (found directly from verified survey seeds) is always kept.
    Round >= 2 must pass the lexical topical check."""
    if not TOPICAL_FILTER_ENABLED:
        return True
    if rec["round"] == 1:
        return True
    text = f"{rec['title']} {rec['abstract']}".lower()
    if not all(term in text for term in TOPICAL_MUST_CONTAIN):
        return False
    return any(term in text for term in TOPICAL_MUST_CONTAIN_ANY)


def get(session, url, params, retries=6):
    params = dict(params or {})
    if MAILTO:
        params["mailto"] = MAILTO
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            time.sleep(min(2 ** attempt, 30))
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(2 ** attempt, 30))
            continue
        r.raise_for_status()
    raise RuntimeError(f"Failed after {retries} retries: {url}")


def paginate(session, url, params, max_records=2000):
    """Cursor pagination over an OpenAlex list endpoint."""
    out, cursor = [], "*"
    params = dict(params or {})
    params["per-page"] = 200
    while cursor and len(out) < max_records:
        params["cursor"] = cursor
        data = get(session, url, params)
        out.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")
        time.sleep(0.15)
    return out


def work_record(w, found_via, seed_id, round_n):
    inv = w.get("abstract_inverted_index")
    abstract = ""
    if inv:
        pos = {}
        for token, idxs in inv.items():
            for i in idxs:
                pos[i] = token
        abstract = " ".join(pos[i] for i in sorted(pos))
    auths = "; ".join(
        a.get("author", {}).get("display_name", "")
        for a in (w.get("authorships") or [])[:12]
    )
    loc = (w.get("primary_location") or {}).get("source") or {}
    return {
        "openalex_id": w.get("id", "").replace("https://openalex.org/", ""),
        "doi": norm_doi(w.get("doi")),
        "title": w.get("title") or w.get("display_name") or "",
        "authors": auths,
        "venue": loc.get("display_name", ""),
        "year": w.get("publication_year"),
        "type": w.get("type"),
        "cited_by_count": w.get("cited_by_count"),
        "abstract": abstract,
        "found_via": found_via,          # backward | forward
        "seed": seed_id,
        "round": round_n,
        "source_phase": SOURCE_PHASE,
    }


# --------------------------- snowballing ---------------------------

def resolve_seeds(session, dois):
    """DOI -> OpenAlex work objects."""
    works = []
    for doi in dois:
        try:
            w = get(session, f"{API}/works/doi:{doi}", {})
            works.append(w)
            print(f"  seed ok: {doi} -> {w['id']}")
        except Exception as e:
            print(f"  seed FAILED ({doi}): {e}", file=sys.stderr)
        time.sleep(0.15)
    return works


def backward(session, work):
    """References of a work. referenced_works gives IDs; batch-fetch them."""
    ids = work.get("referenced_works") or []
    out = []
    for i in range(0, len(ids), 50):
        batch = "|".join(x.replace("https://openalex.org/", "") for x in ids[i:i + 50])
        data = get(session, f"{API}/works",
                   {"filter": f"openalex_id:{batch}", "per-page": 50})
        out.extend(data.get("results", []))
        time.sleep(0.15)
    return out


def forward(session, work):
    """Works citing this work."""
    wid = work["id"].replace("https://openalex.org/", "")
    return paginate(session, f"{API}/works",
                    {"filter": f"cites:{wid}"}, max_records=MAX_FORWARD_PER_SEED)


def load_seed_dois():
    df = pd.read_csv(SEEDS_CSV)
    if SEEDS_CSV_DOI_COL not in df.columns:
        raise SystemExit(
            f"Column '{SEEDS_CSV_DOI_COL}' not found in {SEEDS_CSV}. "
            f"Available columns: {list(df.columns)}"
        )
    dois = [norm_doi(d) for d in df[SEEDS_CSV_DOI_COL] if isinstance(d, str)]
    missing = df[SEEDS_CSV_DOI_COL].isna().sum()
    if missing:
        print(f"WARNING: {missing} row(s) in {SEEDS_CSV} have no DOI and will "
              f"be skipped as seeds — resolve manually if needed.", file=sys.stderr)
    return [d for d in dois if d]


def save_checkpoint(candidates, path):
    if not candidates:
        return
    df = pd.DataFrame(candidates.values())
    df = df.sort_values(["round", "cited_by_count"], ascending=[True, False])
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def main():
    # --- load existing corpus for dedup
    corpus = pd.read_csv(CORPUS_CSV)
    known_dois = {norm_doi(d) for d in corpus.get(CORPUS_DOI_COL, pd.Series()) if norm_doi(d)}
    known_titles = {norm_title(t) for t in corpus.get(CORPUS_TITLE_COL, pd.Series()) if isinstance(t, str)}
    print(f"Corpus: {len(corpus)} rows, {len(known_dois)} DOIs, {len(known_titles)} titles")

    def is_known(rec):
        if rec["doi"] and rec["doi"] in known_dois:
            return True
        nt = norm_title(rec["title"])
        if not nt:
            return False
        if nt in known_titles:
            return True
        # fuzzy: only compare against titles with similar length (cheap prefilter)
        return any(
            abs(len(nt) - len(kt)) < 25 and title_sim(nt, kt) >= TITLE_SIM_THRESHOLD
            for kt in known_titles
        )

    # --- seeds
    seed_dois = load_seed_dois()
    print(f"Seeds: {len(seed_dois)} DOIs from {SEEDS_CSV}")

    # --- resume from a previous checkpoint if present
    candidates = {}
    if os.path.exists(OUT_CSV):
        prev = pd.read_csv(OUT_CSV)
        for _, row in prev.iterrows():
            candidates[row["openalex_id"]] = row.to_dict()
        print(f"Resuming: loaded {len(candidates)} candidates from existing {OUT_CSV}")

    session = requests.Session()
    session.headers["User-Agent"] = "qnlp-slr-snowballing"

    seeds = resolve_seeds(session, seed_dois)

    seen_ids = {w["id"] for w in seeds} | {
        f"https://openalex.org/{oid}" for oid in candidates
    }          # OpenAlex IDs already processed/queued

    frontier = seeds
    for rnd in range(1, ROUNDS + 1):
        print(f"\n=== Round {rnd}: {len(frontier)} seeds ===")
        next_frontier = []
        skipped_expansion = 0
        total = len(frontier)
        for i, w in enumerate(frontier, 1):
            wid = w["id"].replace("https://openalex.org/", "")
            title = (w.get("title") or "")[:60]
            print(f"[{rnd}] ({i}/{total}) {wid} {title}")

            try:
                found = [("backward", x) for x in backward(session, w)]
                found += [("forward", x) for x in forward(session, w)]
            except Exception as e:
                print(f"    !! seed failed, skipping ({e})", file=sys.stderr)
                save_checkpoint(candidates, OUT_CSV)
                continue

            for via, x in found:
                if x["id"] in seen_ids:
                    continue
                seen_ids.add(x["id"])
                rec = work_record(x, via, wid, rnd)
                # filters
                y = rec["year"] or 0
                if not (YEAR_MIN <= y <= YEAR_MAX):
                    continue
                if rec["type"] in ("paratext", "erratum", "editorial", "letter"):
                    continue
                if is_known(rec):
                    continue
                if not passes_topical_filter(rec):
                    skipped_expansion += 1
                    continue
                candidates[rec["openalex_id"]] = rec
                next_frontier.append(x)
            print(f"    -> {len(candidates)} candidates total so far")
            save_checkpoint(candidates, OUT_CSV)
        print(f"Round {rnd} done. New candidates so far: {len(candidates)}")
        print(f"  ({skipped_expansion} candidates from this round dropped — "
              f"failed the topical filter, not saved to output)")
        if not next_frontier:
            print("Saturation reached.")
            break
        frontier = next_frontier

    # --- output
    if not candidates:
        print("No new candidates found.")
        return
    df = pd.DataFrame(candidates.values())
    df = df.sort_values(["round", "cited_by_count"], ascending=[True, False])
    df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"\nWrote {len(df)} candidates -> {OUT_CSV}")
    print(df["found_via"].value_counts().to_string())
    print(df["round"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()