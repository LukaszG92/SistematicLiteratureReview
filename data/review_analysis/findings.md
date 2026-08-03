# Review Analysis Findings

Corpus: 127 papers, 2021-2026.
Publication volume peaks in 2025 with 42 papers; 2026 has 27 papers in the current corpus.

## Major Findings

- The review is now split across vqc (51 papers, 40.2%), compositional (30, 23.6%), recurrent_nn (11, 8.7%), hybrid_nn (9, 7.1%), and quantum_transformer (14, 11.0%). Because some papers compare multiple model families, these are family mentions over a 127-paper corpus.
- Encoding choices are concentrated after multi-label encoding correction: angle (56 mentions, 44.1% of papers), amplitude (34, 26.8%), and syntactic (30, 23.6%) dominate. Percentages are over the 127-paper corpus, so categories can overlap.
- Structured feature maps merge IQP, ZZFeatureMap, ZFeatureMap, PauliFeatureMap, and Pauli-Y variants into one family (10 mentions, 7.9%), with exact variants retained in `encoding_notes`.
- The heatmap remains strongly structured by design pattern: compositional models mostly use syntactic encoding (29/30 model-encoding mentions), while VQC papers are concentrated in angle (28) and amplitude (19) encodings.
- The residual hybrid_nn bucket is now small and mixed: mostly angle-based fusion or sequence-adjacent hybrids (5 angle mentions, 2 amplitude mentions), plus single data-reuploading and hybrid-embed cases. Recurrent_nn papers cluster in angle-based QLSTM/QRNN-style models (9 angle, 2 amplitude).
- Quantum transformer work is a recent growth category: 14 papers overall, mostly angle encoding (9) with amplitude as the secondary choice (4).
- After removing out-of-window and theoretical/toolkit-only works, the corpus starts in 2021 and shifts from early compositional QNLP toward broader applied VQC, hybrid, and transformer architectures after 2023.
- Execution remains simulation-heavy: simulation_noiseless (96, 75.6%) dominates; real_hardware-only studies remain rare (2).

## Top Model-Encoding Combinations

- compositional + syntactic: 29 papers
- vqc + angle: 28 papers
- vqc + amplitude: 19 papers
- recurrent_nn + angle: 9 papers
- quantum_transformer + angle: 9 papers
- hybrid_nn + angle: 5 papers
- quantum_kernel + amplitude: 5 papers
- vqc + structured_feature_map: 5 papers
- quantum_kernel + structured_feature_map: 4 papers
- quantum_transformer + amplitude: 4 papers
- hybrid_nn + amplitude: 2 papers
- quantum_kernel + angle: 2 papers
- recurrent_nn + amplitude: 2 papers
- vqc + data_reuploading: 2 papers
- vqc + hybrid_embed: 2 papers

## Temporal Pattern

- 2021-2022: small corpus, mostly compositional/syntactic QNLP and early hybrid neural work.
- 2023: transition year with VQC, hybrid, kernel, and transformer approaches all present.
- 2024-2025: expansion phase, especially VQC/angle, VQC/amplitude, recurrent architectures, and quantum transformer designs.
- 2026: still incomplete-year coverage, but current papers are concentrated in VQC, recurrent_nn, and quantum transformer designs.

## Generated Artifacts

- `model_family_x_encoding_counts.csv`
- `model_family_x_encoding_row_pct.csv`
- `model_family_x_encoding_heatmap_counts.png`
- `model_family_x_encoding_heatmap_row_pct.png`
- `year_x_model_family_counts.csv`
- `year_x_encoding_counts.csv`
- `year_x_model_family_stacked.png`
- `year_x_encoding_stacked.png`
- `year_x_model_family_lines.png`
- `year_x_encoding_lines.png`
