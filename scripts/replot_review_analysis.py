#!/usr/bin/env python3
"""Rebuild review-analysis tables and figures from the analyzed corpus."""

from __future__ import annotations

import collections
import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "p4_final_corpus_analyzed.csv"
OUT_DIR = ROOT / "data" / "review_analysis"
FIG_DIR = ROOT / "TQE_Template" / "figures"

# --- Task and dataset normalization -----------------------------------------

TASK_FAMILY_MAP = {
    "sentiment_analysis": "sentiment classification",
    "sentiment_classification": "sentiment classification",
    "text_classification": "other classification",
    "sentence_classification": "other classification",
    "medical_text_classification": "other classification",
    "misinformation_detection": "other classification",
    "emotion_recognition": "other classification",
    "other:vulnerability_detection": "other classification",
    "other:ai_text_detection": "other classification",
    "other:humor_detection": "other classification",
    "other:sarcasm_detection": "other classification",
    "other:language_identification": "other classification",
    "other:steganalysis": "other classification",
    "semantic_similarity": "similarity & disambiguation",
    "word_sense_disambiguation": "similarity & disambiguation",
    "other:coreference_resolution": "similarity & disambiguation",
    "other:pronoun_resolution": "similarity & disambiguation",
    "named_entity_recognition": "sequence labeling",
    "other:POS_tagging": "sequence labeling",
    "question_answering": "QA & retrieval",
    "information_retrieval": "QA & retrieval",
    "other:query_estimation": "QA & retrieval",
    "language_modeling": "generation & LM",
    "machine_translation": "generation & LM",
    "dialogue": "generation & LM",
    "other:code_generation": "generation & LM",
    "music_or_multimodal": "other",
    "regression": "other",
    "other:topic_modeling": "other",
    "other:storyline_extraction": "other",
    "other:knowledge_graph_construction": "other",
}

TASK_FAMILY_ORDER = [
    "sentiment classification",
    "other classification",
    "similarity & disambiguation",
    "sequence labeling",
    "QA & retrieval",
    "generation & LM",
    "other",
]

DATASET_ALIASES = {
    "IMDB": "IMDb",
    "IMDb": "IMDb",
    "IMDB Movie Reviews": "IMDb",
    "IMDb sentence-polarity movie reviews": "IMDb",
    "MC": "MC (lambeq)",
    "MC (Meaning Classification)": "MC (lambeq)",
    "lambeq (MC)": "MC (lambeq)",
    "LambeqMC": "MC (lambeq)",
    "Meaning Classification (Lorenz et al.)": "MC (lambeq)",
    "mc data (IT vs food topic)": "MC (lambeq)",
    "RP": "RP (lambeq)",
    "RP (Relative Pronoun)": "RP (lambeq)",
    "LambeqRP": "RP (lambeq)",
    "Amazon": "Amazon reviews",
    "Amazon reviews": "Amazon reviews",
    "Amazon Cell Phones reviews (Kotzias et al.)": "Amazon reviews",
    "SST-2": "SST-2",
    "SST2": "SST-2",
    "20 Newsgroups": "20 Newsgroups",
    "20 Newsgroups (binary subset)": "20 Newsgroups",
    "20NewsGroup": "20 Newsgroups",
    "ItaCoLa (Italian Corpus of Linguistic Acceptability)": "ItaCoLa",
    "SMS spam/ham": "SMS Spam Collection",
    "SentiPolc Italian sentiment dataset": "SentiPolc",
    "SARD (Software Assurance Reference Dataset)": "SARD",
    "IMDB database (SQL queries)": "IMDb-SQL (SQL2Circuits)",
    "custom restaurant domain sentences (29-word vocabulary)": "restaurant-domain sentences (SimpleSA)",
    "restaurant domain sentences (29-word vocabulary": "restaurant-domain sentences (SimpleSA)",
    "restaurant domain sentences (same 29-word vocabulary as SimpleSA paper)": "restaurant-domain sentences (SimpleSA)",
    "custom restaurant domain sentences (expanded": "restaurant-domain sentences (SimpleSA)",
    "restaurant sentiment dataset": "restaurant-domain sentences (SimpleSA)",
    "50 hand-crafted sentences (simple declarative": "custom hand-crafted sentences",
    "synthetic (pattern reproduction": "synthetic tasks",
    "synthetic data": "synthetic tasks",
    "synthetic datasets": "synthetic tasks",
}

# Continuation fragments produced by semicolons inside parentheses, and
# entries with no recoverable dataset identity.
DATASET_DROP = {
    "4-5 words/sentence)",
    "42-word vocabulary)",
    "passive)",
    "interrogative",
    "Needle in Haystack)",
    "fourth rating-score dataset NR",
}


def paper_task_families(raw: object) -> list[str]:
    """Task families of one study.

    A study counts as "other" only when none of its labels resolves to a named
    family. A minor secondary label with no family of its own (regression,
    storyline extraction, knowledge-graph construction) does not drag a study
    that already has a family into the residual.
    """
    families = []
    for label in str(raw).split(";"):
        label = label.strip()
        if not label or label in ("NR", "NA"):
            continue
        fam = TASK_FAMILY_MAP.get(label, "other")
        if fam != "other" and fam not in families:
            families.append(fam)
    return families or ["other"]


def paper_datasets(raw: object) -> list[str]:
    names = []
    for part in str(raw).split(";"):
        part = part.strip()
        if not part or part in ("NR", "NA") or part in DATASET_DROP:
            continue
        name = DATASET_ALIASES.get(part, part)
        if name not in names:
            names.append(name)
    return names


def read_corpus() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def pretty_label(value: object) -> str:
    return str(value).replace("_", "\n")


def save_bar(series: pd.Series, out_path: Path, title: str, xlabel: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    series.plot(kind="bar", ax=ax, color="#2a6fdb")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_stacked_bars(table: pd.DataFrame, out_path: Path, title: str, ylabel: str) -> None:
    years = list(table.index)
    cols = list(table.columns)
    fig, ax = plt.subplots(figsize=(13, 6.5))
    bottom = pd.Series([0] * len(table), index=table.index, dtype=float)
    palette = plt.cm.tab20.colors
    for i, col in enumerate(cols):
        vals = table[col].fillna(0).astype(float)
        ax.bar(years, vals, bottom=bottom.values, label=col, color=palette[i % len(palette)])
        bottom += vals
    ax.set_title(title)
    ax.set_xlabel("Publication Year")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        [pretty_label(col) for col in cols],
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=8,
        title="Legend",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_lines(table: pd.DataFrame, out_path: Path, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    palette = plt.cm.tab20.colors
    for i, col in enumerate(table.columns):
        ax.plot(
            table.index,
            table[col].fillna(0),
            marker="o",
            linewidth=1.8,
            label=pretty_label(col),
            color=palette[i % len(palette)],
        )
    ax.set_title(title)
    ax.set_xlabel("Publication Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, title="Legend")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_heatmap(table: pd.DataFrame, out_path: Path, title: str, fmt: str = "d") -> None:
    n_rows, n_cols = table.shape
    fig_w = max(10.0, 1.25 * n_cols + 4.0)
    fig_h = max(4.5, 0.7 * n_rows + 2.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    data = table.fillna(0).values.astype(float)
    vmax = data.max() if data.size else 1.0
    im = ax.imshow(data, aspect="auto", cmap="Blues", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels([pretty_label(col) for col in table.columns], rotation=0, ha="center", fontsize=9)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels([pretty_label(idx) for idx in table.index], fontsize=9)
    ax.set_title(title)
    ax.set_xticks([x - 0.5 for x in range(1, len(table.columns))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(table.index))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if val == 0:
                continue
            if fmt == "d":
                text = f"{int(val)}"
            else:
                text = f"{val:.1f}%"
            color = "white" if vmax and val >= vmax * 0.6 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=9, color=color)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_paper_heatmap(table: pd.DataFrame, out_path: Path, xlabel: str, ylabel: str) -> None:
    """Publication-style heatmap (no title, PDF) used for the encoding cross-tab figures."""
    data = table.fillna(0).values.astype(float)
    vmax = data.max() if data.size else 1.0
    fig, ax = plt.subplots(figsize=(9.0, 0.55 * len(table.index) + 1.8))
    im = ax.imshow(data, aspect="auto", cmap="Blues", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns, rotation=30, ha="right", fontsize=10)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels(table.index, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_xticks([x - 0.5 for x in range(1, len(table.columns))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(table.index))], minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = int(data[i, j])
            color = "white" if vmax and val >= vmax * 0.6 else "black"
            ax.text(j, i, str(val), ha="center", va="center", fontsize=9, color=color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Number of studies", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def save_paper_stacked(table: pd.DataFrame, out_path: Path, ylabel: str, n_minor: int = 0) -> None:
    """Publication-style stacked bars in the Blues palette of the heatmaps.

    Shades run dark (bottom of the stack) to light (top), so adjacent segments
    always contrast. The last ``n_minor`` columns are drawn in greys so that
    thin minority segments are not confused with the pale blues.
    """
    n_major = len(table.columns) - n_minor
    shades = list(plt.cm.Blues([0.95 - 0.65 * i / max(n_major - 1, 1) for i in range(n_major)]))
    shades += list(plt.cm.Greys([0.6 - 0.35 * i / max(n_minor - 1, 1) for i in range(n_minor)]))
    years = [str(y) for y in table.index]
    totals = table.sum(axis=1).values
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bottom = pd.Series(0.0, index=table.index)
    for col, shade in zip(table.columns, shades):
        vals = table[col].astype(float)
        ax.bar(years, vals, bottom=bottom.values, width=0.72, label=col,
               color=shade, edgecolor="white", linewidth=0.8)
        bottom += vals
    for x, total in zip(years, totals):
        ax.text(x, total + 0.6, f"{int(total)}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_ylim(0, totals.max() * 1.12)
    ax.set_xlabel("Publication year", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(labelsize=10)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    # Legend listed top-to-bottom in the same order as the stack.
    ax.legend(handles[::-1], labels[::-1], fontsize=8, loc="upper left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def task_dataset_analyses(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    total = len(df)
    df = df.copy()
    df["task_families"] = df["nlp_task"].apply(paper_task_families)
    df["datasets_norm"] = df["dataset"].apply(paper_datasets)

    # (1) Task family distribution (papers counted once per family).
    fam_counts = collections.Counter(f for fams in df["task_families"] for f in fams)
    fam_df = pd.DataFrame(
        [(f, fam_counts.get(f, 0), round(fam_counts.get(f, 0) / total * 100, 1)) for f in TASK_FAMILY_ORDER],
        columns=["task_family", "papers", "share_pct"],
    )
    fam_df.to_csv(OUT_DIR / "task_family_counts.csv", index=False)

    # (2) Encoding family x task family crosstab.
    enc_order = [
        ("angle", "Angle"),
        ("amplitude", "Amplitude"),
        ("syntactic", "Syntactic/DisCoCat"),
        ("structured_feature_map", "Structured feature map"),
        ("data_reuploading", "Data re-uploading"),
        ("hybrid_embed", "Hybrid embedding"),
        ("other:hamiltonian", "Hamiltonian/observable"),
    ]
    enc_task = pd.DataFrame(0, index=[lbl for _, lbl in enc_order], columns=TASK_FAMILY_ORDER)
    enc_labels = dict(enc_order)
    for _, row in df.iterrows():
        enc = enc_labels.get(str(row["encoding"]).strip())
        if enc is None:
            continue
        for fam in row["task_families"]:
            enc_task.loc[enc, fam] += 1
    enc_task.to_csv(OUT_DIR / "encoding_x_task_family_counts.csv")
    save_paper_heatmap(
        enc_task,
        FIG_DIR / "encoding_by_task_family.pdf",
        "NLP task family",
        "Encoding family",
    )

    # (2b) Encoding family x model family crosstab (same layout as (2)).
    model_order = [
        ("vqc", "VQC"),
        ("compositional", "Compositional"),
        ("hybrid_nn", "Hybrid NN"),
        ("quantum_transformer", "Quantum transformer"),
        ("quantum_kernel", "Quantum kernel"),
        ("recurrent_nn", "Recurrent NN"),
    ]
    model_labels = dict(model_order)
    enc_model = pd.DataFrame(0, index=[lbl for _, lbl in enc_order], columns=[lbl for _, lbl in model_order])
    for _, row in df.iterrows():
        enc = enc_labels.get(str(row["encoding"]).strip())
        model = model_labels.get(str(row["model_family"]).strip())
        if enc is None or model is None:
            continue
        enc_model.loc[enc, model] += 1
    enc_model.to_csv(OUT_DIR / "encoding_x_model_family_counts.csv")
    save_paper_heatmap(
        enc_model,
        FIG_DIR / "encoding_by_model_family.pdf",
        "Model family",
        "Encoding family",
    )

    # (2c) Encoding family and model family by year (stacked bars, paper figures).
    years = sorted(df["Publication Year"].unique())
    year_enc = pd.DataFrame(0, index=years, columns=[lbl for _, lbl in enc_order])
    year_model = pd.DataFrame(0, index=years, columns=[model_labels[k] for k in (
        "compositional", "vqc", "hybrid_nn", "quantum_transformer", "quantum_kernel", "recurrent_nn")])
    for _, row in df.iterrows():
        enc = enc_labels.get(str(row["encoding"]).strip())
        model = model_labels.get(str(row["model_family"]).strip())
        if enc is not None:
            year_enc.loc[row["Publication Year"], enc] += 1
        if model is not None:
            year_model.loc[row["Publication Year"], model] += 1
    save_paper_stacked(year_enc, FIG_DIR / "encoding_by_year.pdf", "Number of studies (per encoding family)", n_minor=3)
    save_paper_stacked(year_model, FIG_DIR / "model_family_by_year.pdf", "Number of studies (per model family)", n_minor=2)

    # (3) Dataset reuse after alias normalization.
    ds_counts = collections.Counter(d for names in df["datasets_norm"] for d in names)
    reuse = pd.DataFrame(sorted(ds_counts.items(), key=lambda kv: (-kv[1], kv[0])), columns=["dataset", "papers"])
    reuse.to_csv(OUT_DIR / "dataset_reuse_counts.csv", index=False)
    summary = pd.DataFrame(
        {
            "metric": [
                "distinct datasets (normalized)",
                "datasets used by exactly 1 paper",
                "datasets used by >=2 papers",
                "datasets used by >=4 papers",
                "papers using at least one shared (>=2 papers) dataset",
                "papers with no usable dataset name (NR/NA only)",
            ],
            "value": [
                len(ds_counts),
                sum(1 for c in ds_counts.values() if c == 1),
                sum(1 for c in ds_counts.values() if c >= 2),
                sum(1 for c in ds_counts.values() if c >= 4),
                int(df["datasets_norm"].apply(lambda names: any(ds_counts[d] >= 2 for d in names)).sum()),
                int(df["datasets_norm"].apply(len).eq(0).sum()),
            ],
        }
    )
    summary.to_csv(OUT_DIR / "dataset_reuse_summary.csv", index=False)

    # (4) Dataset size vs qubit count, colored by encoding family.
    scat = df.copy()
    scat["size_num"] = pd.to_numeric(scat["dataset_size"], errors="coerce")
    scat["qubits_num"] = pd.to_numeric(scat["qubit_count"], errors="coerce")
    scat = scat.dropna(subset=["size_num", "qubits_num"])
    scat[["Author", "Publication Year", "encoding", "size_num", "qubits_num"]].to_csv(
        OUT_DIR / "dataset_size_vs_qubits.csv", index=False
    )
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    palette = plt.cm.tab10.colors
    for i, (enc, lbl) in enumerate(enc_order):
        sub = scat[scat["encoding"].str.strip() == enc]
        if sub.empty:
            continue
        ax.scatter(sub["size_num"], sub["qubits_num"], s=45, alpha=0.8, color=palette[i % 10], label=lbl)
    ax.set_xscale("log")
    ax.set_xlabel("Dataset size (examples, log scale)", fontsize=11)
    ax.set_ylabel("Qubit count", fontsize=11)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dataset_size_vs_qubits.pdf", bbox_inches="tight")
    plt.close(fig)

    # (5) Within-benchmark comparison cells (datasets used by >= 4 papers).
    cell_rows = []
    shared = {d for d, c in ds_counts.items() if c >= 4}
    for _, row in df.iterrows():
        for d in row["datasets_norm"]:
            if d in shared:
                cell_rows.append(
                    {
                        "dataset": d,
                        "author": str(row["Author"]).split(";")[0],
                        "year": row["Publication Year"],
                        "encoding": row["encoding"],
                        "model_family": row["model_family"],
                        "qubit_count": row["qubit_count"],
                        "execution": row["execution"],
                        "primary_metric": row["primary_metric"],
                        "best_result": row["best_result"],
                    }
                )
    pd.DataFrame(cell_rows).sort_values(["dataset", "year", "author"]).to_csv(
        OUT_DIR / "shared_benchmark_cells.csv", index=False
    )

    # (6) Task family by year (stacked bars, paper figure).
    year_fam = pd.DataFrame(0, index=sorted(df["Publication Year"].unique()), columns=TASK_FAMILY_ORDER)
    for _, row in df.iterrows():
        for fam in row["task_families"]:
            year_fam.loc[row["Publication Year"], fam] += 1
    year_fam.to_csv(OUT_DIR / "year_x_task_family_counts.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bottom = pd.Series(0.0, index=year_fam.index)
    palette = plt.cm.tab10.colors
    for i, fam in enumerate(TASK_FAMILY_ORDER):
        ax.bar(year_fam.index, year_fam[fam], bottom=bottom.values, label=fam, color=palette[i % 10])
        bottom += year_fam[fam]
    ax.set_xlabel("Publication year", fontsize=11)
    ax.set_ylabel("Number of studies (per task family)", fontsize=11)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "task_family_by_year.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = read_corpus()
    total = len(df)

    family_order = list(df["model_family"].value_counts().index)
    encoding_order = list(df["encoding"].value_counts().index)

    family_counts = (
        df["model_family"]
        .value_counts()
        .rename_axis("model_family")
        .reset_index(name="count")
    )
    family_counts["share_pct"] = (family_counts["count"] / total * 100).round(1)
    family_counts.to_csv(OUT_DIR / "model_family_counts.csv", index=False)

    encoding_counts = (
        df["encoding"]
        .value_counts()
        .rename_axis("encoding")
        .reset_index(name="count")
    )
    encoding_counts["share_pct"] = (encoding_counts["count"] / total * 100).round(1)
    encoding_counts.to_csv(OUT_DIR / "encoding_counts.csv", index=False)

    year_counts = (
        df["Publication Year"]
        .value_counts()
        .sort_index()
        .rename_axis("year")
        .reset_index(name="count")
    )
    year_counts.to_csv(OUT_DIR / "year_counts.csv", index=False)

    qadv_counts = (
        df["quantum_advantage_claimed"]
        .value_counts()
        .rename_axis("quantum_advantage_claimed")
        .reset_index(name="count")
    )
    qadv_counts.to_csv(OUT_DIR / "quantum_advantage_claimed_counts.csv", index=False)

    exec_counts = (
        df["execution"]
        .value_counts()
        .rename_axis("execution")
        .reset_index(name="count")
    )
    exec_counts.to_csv(OUT_DIR / "execution_counts.csv", index=False)

    baseline_counts = (
        df["classical_baseline"]
        .value_counts()
        .rename_axis("classical_baseline")
        .reset_index(name="count")
    )
    baseline_counts.to_csv(OUT_DIR / "classical_baseline_counts.csv", index=False)

    code_counts = (
        df["code_available"]
        .value_counts()
        .rename_axis("code_available")
        .reset_index(name="count")
    )
    code_counts.to_csv(OUT_DIR / "code_available_counts.csv", index=False)

    scalability_counts = (
        df["scalability_discussed"]
        .value_counts()
        .rename_axis("scalability_discussed")
        .reset_index(name="count")
    )
    scalability_counts.to_csv(OUT_DIR / "scalability_discussed_counts.csv", index=False)

    bottleneck_counts = (
        df["encoding_bottleneck"]
        .value_counts()
        .rename_axis("encoding_bottleneck")
        .reset_index(name="count")
    )
    bottleneck_counts.to_csv(OUT_DIR / "encoding_bottleneck_counts.csv", index=False)

    barren_counts = (
        df["barren_plateaus"]
        .value_counts()
        .rename_axis("barren_plateaus")
        .reset_index(name="count")
    )
    barren_counts.to_csv(OUT_DIR / "barren_plateaus_counts.csv", index=False)

    family_x_encoding = pd.crosstab(df["model_family"], df["encoding"]).reindex(index=family_order, columns=encoding_order, fill_value=0)
    family_x_encoding.to_csv(OUT_DIR / "model_family_x_encoding_counts.csv")

    row_pct = family_x_encoding.div(family_x_encoding.sum(axis=1), axis=0).fillna(0) * 100
    row_pct.round(1).to_csv(OUT_DIR / "model_family_x_encoding_row_pct.csv")

    top_combos = (
        df.groupby(["model_family", "encoding"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "model_family", "encoding"], ascending=[False, True, True])
    )
    top_combos.to_csv(OUT_DIR / "top_model_encoding_combinations.csv", index=False)

    year_family = pd.crosstab(df["Publication Year"], df["model_family"]).sort_index()
    year_encoding = pd.crosstab(df["Publication Year"], df["encoding"]).sort_index()
    year_family.to_csv(OUT_DIR / "year_x_model_family_counts.csv")
    year_encoding.to_csv(OUT_DIR / "year_x_encoding_counts.csv")

    save_bar(
        year_counts.set_index("year")["count"],
        OUT_DIR / "yearly_publication_counts.png",
        "Publications per Year",
        "Year",
        "Count",
    )
    save_heatmap(
        family_x_encoding,
        OUT_DIR / "model_family_x_encoding_heatmap_counts.png",
        "Model Family x Encoding Counts",
        fmt="d",
    )
    save_heatmap(
        row_pct,
        OUT_DIR / "model_family_x_encoding_heatmap_row_pct.png",
        "Model Family x Encoding Row %",
        fmt=".1f",
    )
    save_stacked_bars(
        year_family,
        OUT_DIR / "year_x_model_family_stacked.png",
        "Publications by Year and Model Family",
        "Count",
    )
    save_stacked_bars(
        year_encoding,
        OUT_DIR / "year_x_encoding_stacked.png",
        "Publications by Year and Encoding",
        "Count",
    )
    save_lines(
        year_family,
        OUT_DIR / "year_x_model_family_lines.png",
        "Publications by Year and Model Family",
        "Count",
    )
    save_lines(
        year_encoding,
        OUT_DIR / "year_x_encoding_lines.png",
        "Publications by Year and Encoding",
        "Count",
    )

    task_dataset_analyses(df)


if __name__ == "__main__":
    main()
