"""Helpers for the academic rewrite: key snapshots and per-section prose metrics."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXS = [ROOT / "TQE_Template" / "tqe.tex", ROOT / "TQE_Template" / "corpus_table.tex"]


def keys():
    ks, occ = set(), 0
    for f in TEXS:
        t = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\\cite\{([^}]+)\}", t):
            for k in m.group(1).split(","):
                ks.add(k.strip())
                occ += 1
    return ks, occ


def snapshot(name):
    ks, occ = keys()
    (ROOT / name).write_text("\n".join(sorted(ks)) + "\n", encoding="utf-8")
    print(f"{name}: {len(ks)} unique keys, {occ} occurrences")


def strip_tex(t):
    t = re.sub(r"(?s)\\begin\{table\*?\}.*?\\end\{table\*?\}", " ", t)
    t = re.sub(r"(?s)\\begin\{equation\}.*?\\end\{equation\}", " EQN. ", t)
    t = re.sub(r"\\Figure\[[^]]*\]\([^)]*\)\[[^]]*\]\{[^}]*\}\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", " ", t)
    t = re.sub(r"%.*", "", t)
    t = re.sub(r"\\(sub)*section\{[^}]*\}", " ", t)
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = re.sub(r"\\cite\{[^}]*\}", "[c]", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^]]*\])?(\{[^{}]*\})?", " ", t)
    t = re.sub(r"[{}$~]", " ", t)
    return t


def section_metrics(pattern):
    t = TEXS[0].read_text(encoding="utf-8", errors="replace")
    m = re.search(pattern, t, re.S)
    if not m:
        print("section not found"); return
    body = strip_tex(m.group(0))
    words = re.findall(r"[A-Za-z0-9'\-]+", body)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.split()) > 3]
    lens = sorted(len(s.split()) for s in sents)
    med = lens[len(lens)//2] if lens else 0
    print(f"words={len(words)} sentences={len(sents)} median={med} max={max(lens) if lens else 0} over45={sum(1 for x in lens if x>45)} over60={sum(1 for x in lens if x>60)}")


if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        snapshot(sys.argv[2])
    elif sys.argv[1] == "section":
        section_metrics(sys.argv[2])
