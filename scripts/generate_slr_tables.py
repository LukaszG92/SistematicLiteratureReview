"""Regenerate the count-based tables of tqe.tex from data/p4_final_corpus_analyzed.csv.

Usage:  python scripts/generate_slr_tables.py [audit|trends|challenges|corpus]

All numeric cells in the manuscript's trend/challenge tables must come from this
script, never from manual estimates.  `audit` cross-references every \\cite key in
TQE_Template/tqe.tex against the corpus (CSV), the bib file, and
refs_external_allowlist.txt.
"""
import csv, re, sys, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "p4_final_corpus_analyzed.csv"
TEX = ROOT / "TQE_Template" / "tqe.tex"
BIB = ROOT / "TQE_Template" / "references.bib"
ALLOW = ROOT / "refs_external_allowlist.txt"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def load_rows():
    with open(CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_bib_entries():
    """bib key -> {'title': normalized title, 'doi': lowercase doi}"""
    text = BIB.read_text(encoding="utf-8", errors="replace")
    out = {}
    chunks = re.split(r"(?m)^@", text)[1:]
    for ch in chunks:
        m = re.match(r"\w+\{([^,]+),", ch)
        if not m:
            continue
        key = m.group(1).strip()
        t = re.search(r"(?i)\btitle\s*=\s*[{\"]((?:[^{}]|\{[^{}]*\})+?)[}\"]\s*,", ch)
        d = re.search(r"(?i)\bdoi\s*=\s*[{\"]([^}\"]+)[}\"]", ch)
        out[key] = {
            "title": norm(re.sub(r"[{}]", "", t.group(1))) if t else "",
            "doi": d.group(1).strip().lower() if d else "",
        }
    return out


def load_bib_titles():
    return {k: v["title"] for k, v in load_bib_entries().items()}


def corpus_bib_keys():
    """Map each CSV row title to its bib key (DOI match first, then title)."""
    rows, bib = load_rows(), load_bib_entries()
    by_doi = {v["doi"]: k for k, v in bib.items() if v["doi"]}
    key_by_title = {}
    for r in rows:
        doi = r["DOI"].strip().lower()
        if doi and doi in by_doi:
            key_by_title[r["Title"]] = by_doi[doi]
            continue
        t = norm(r["Title"])
        hits = [k for k, v in bib.items()
                if v["title"] == t or (len(t) > 25 and (t in v["title"] or v["title"] in t))]
        if not hits:
            from difflib import SequenceMatcher
            scored = [(SequenceMatcher(None, t, v["title"]).ratio(), k)
                      for k, v in bib.items() if v["title"]]
            best = max(scored)
            if best[0] > 0.75:
                hits = [best[1]]
        key_by_title[r["Title"]] = hits[0] if hits else None
    return key_by_title


def cited_keys():
    text = TEX.read_text(encoding="utf-8", errors="replace")
    keys = set()
    for m in re.finditer(r"\\cite\{([^}]+)\}", text):
        keys.update(k.strip() for k in m.group(1).split(","))
    return keys


def audit():
    corpus_keys = {v for v in corpus_bib_keys().values() if v}
    allow = set()
    if ALLOW.exists():
        for line in ALLOW.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                allow.add(line.split()[0])
    bib = set(load_bib_titles().keys())
    print(f"corpus rows mapped to bib keys: {len(corpus_keys)}/125")
    unmatched = [t for t, k in corpus_bib_keys().items() if not k]
    for t in unmatched:
        print("  UNMAPPED CSV TITLE:", t[:80])
    print()
    for k in sorted(cited_keys()):
        status = ("CORPUS" if k in corpus_keys else
                  "ALLOWLIST" if k in allow else
                  "MISSING-FROM-BIB" if k not in bib else
                  "EXTERNAL-NOT-ALLOWLISTED")
        if status != "CORPUS":
            print(f"  {status:26s} {k}")


def trends():
    rows = load_rows()
    n = len(rows)
    fields = ["encoding_bottleneck", "quantum_advantage_claimed", "scalability_discussed",
              "barren_plateaus", "qubit_scaling_tested", "execution",
              "classical_baseline", "code_available"]
    for f in fields:
        c = Counter(r[f] for r in rows)
        cells = "; ".join(f"{v}: {k} ({100*k/n:.1f}\\%)" for v, k in c.most_common())
        print(f"{f}: {cells}")


def challenges():
    rows = load_rows()
    n = len(rows)
    def cnt(pred): return sum(1 for r in rows if pred(r))
    print("bottleneck explicit+implicit:", cnt(lambda r: r["encoding_bottleneck"] in ("explicit", "implicit")))
    print("no classical baseline:", cnt(lambda r: r["classical_baseline"] == "no"))
    print("advantage yes:", cnt(lambda r: r["quantum_advantage_claimed"] == "yes"),
          "conditional:", cnt(lambda r: r["quantum_advantage_claimed"] == "conditional"),
          "no:", cnt(lambda r: r["quantum_advantage_claimed"] == "no"))
    print("barren absent:", cnt(lambda r: r["barren_plateaus"] == "absent"),
          "mentioned:", cnt(lambda r: r["barren_plateaus"] == "mentioned"),
          "discussed:", cnt(lambda r: r["barren_plateaus"] == "discussed"))
    print("noiseless only:", cnt(lambda r: r["execution"] == "simulation_noiseless"))
    print("qubit scaling untested:", cnt(lambda r: r["qubit_scaling_tested"] == "no"))
    print("scalability not discussed:", cnt(lambda r: r["scalability_discussed"] == "no"))
    print("code unavailable:", cnt(lambda r: r["code_available"] == "no"))
    print("n =", n)


def corpus_table():
    """Write TQE_Template/corpus_table.tex: full corpus classification (Task D)."""
    rows, keymap = load_rows(), corpus_bib_keys()
    rows.sort(key=lambda r: (r["model_family"], r["encoding"], r["Publication Year"]))
    def esc(s): return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
    body_rows = []
    for r in rows:
        k = keymap.get(r["Title"]) or "??"
        qub = r["qubit_count"] if r["qubit_count"] not in ("", "NR") else "NR"
        ds = esc(r["dataset"].split(";")[0].strip())[:30]
        hb = esc((r["hardware_backend"].split(";")[0].strip() or "NA"))[:22]
        body_rows.append(
            f"\\cite{{{k}}} & {esc(r['model_family'])} & {esc(r['encoding'])} & {qub} & {ds} & {hb} \\\\")
    chunks = [body_rows[i:i + 42] for i in range(0, len(body_rows), 42)]
    parts = []
    for i, ch in enumerate(chunks, 1):
        parts.append(
            "\\begin{table*}[p]\n"
            f"\\caption{{Classification of the final primary corpus under the encoding comparison framework (part {i} of {len(chunks)}): "
            "study, model family, encoding family, qubit count, primary dataset, and hardware backend. "
            "Generated from the released extraction sheet by scripts/generate\\_slr\\_tables.py.}\n"
            f"\\label{{tab:corpus_classification_{i}}}\n"
            "\\centering\n\\scriptsize\n"
            "\\begin{tabular}{@{}l l l c p{0.28\\textwidth} l@{}}\n\\hline\n"
            "\\textbf{Study} & \\textbf{Model family} & \\textbf{Encoding} & \\textbf{Qubits} & \\textbf{Primary dataset} & \\textbf{Backend} \\\\\n\\hline\n"
            + "\n".join(ch) +
            "\n\\hline\n\\end{tabular}\n\\end{table*}\n")
    out = ROOT / "TQE_Template" / "corpus_table.tex"
    out.write_text("% Auto-generated by scripts/generate_slr_tables.py corpus -- do not edit by hand.\n\n"
                   + "\n".join(parts), encoding="utf-8")
    print("wrote", out, f"({len(body_rows)} rows, {len(chunks)} tables)")


if __name__ == "__main__":
    {"audit": audit, "trends": trends, "challenges": challenges,
     "corpus": corpus_table}[sys.argv[1] if len(sys.argv) > 1 else "audit"]()
