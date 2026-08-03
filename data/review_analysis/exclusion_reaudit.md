# Exclusion re-audit candidates

Basis: `data/inclusion_exclusion_criteria.txt` and `TQE_Template/tqe.tex` eligibility criteria. A paper must satisfy all inclusion criteria, especially NLP task grounding, genuine circuit simulation/hardware execution, identified text/text-derived quantum encoding, and 2021-2026 time window.

## Summary

- Recommended exclusions from the analyzed corpus: 12.
- Retain but correct metadata: 1.
- Main failure modes: no executed/simulated quantum circuit, theoretical/toolkit/survey-like contribution, no text-to-quantum encoding, or 2020 publication outside the stated window.

## Recommended exclusions

### A QUANTUM CIRCUIT-BASED COMPRESSION PERSPECTIVE FOR PARAMETER-EFFICIENT LEARNING (2025)

- Criteria: IC3; exclusion basis: EC2 / outside encoding scope; confidence: high.

- Evidence: Paper uses quantum parameter generation/adaptation to produce PEFT weights for GPT-2/Gemma-2. The analyzed notes state NLP data are never encoded into qubits and encoding is NR; the paper itself frames QPA as avoiding input data encoding and quantum inference.

- Action: Remove from primary encoding-in-QNLP corpus, or retain only as related QML-for-LLM context.

### Quantum word embedding for machine learning (2024)

- Criteria: IC2; exclusion basis: EC9 / EC10; confidence: high.

- Evidence: Analyzed execution is NA and model_family is quantum_inspired. The PDF abstract says it proposes a finite-automaton QWE algorithm and reports numerical results, but no simulated/executed quantum circuit is evidenced. Includes non-NLP biology applications.

- Action: Remove from primary corpus.

### Quantum Algorithms for Compositional Text Processing (2024)

- Criteria: IC2; exclusion basis: EC10 / EC11; confidence: high.

- Evidence: Analyzed execution is NA. PDF says it proposes QDisCoCirc and outlines evaluation on near-term processors, with empirical verification left to future work/elsewhere. No primary simulation or hardware evaluation in this paper.

- Action: Remove from primary corpus; discuss as theoretical/future-work background if needed.

### Harnessing Quantum Computing to Optimize Reinforcement Learning for NLP Tasks (2025)

- Criteria: IC2, IC3; exclusion basis: EC4 / EC11; confidence: high.

- Evidence: Analyzed notes say no dataset or implemented experiment identified; framework is NR and execution is NA. PDF appears to present mathematical workflow/results without verifiable circuit framework or reproducible quantum simulation evidence.

- Action: Remove from primary corpus.

### Application of Quantum Natural Language Processing for Language Translation (2021)

- Criteria: IC2; exclusion basis: EC10 / EC11; confidence: high.

- Evidence: Analyzed execution is NA and notes say theoretical/proposed only. PDF abstract says “we propose a protocol” and frames the method as paving the way; no executed simulation/hardware experiment is identified.

- Action: Remove from primary corpus; retain as theoretical background if useful.

### Quantum computations for disambiguation and question answering (2022)

- Criteria: IC2; exclusion basis: EC10 / EC11; confidence: medium-high.

- Evidence: Analyzed execution is NA and framework NR. PDF develops a grammar-to-quantum framework and Grover-style QA/disambiguation pipeline, but I did not find evidence of an evaluated circuit simulation or hardware run.

- Action: Remove from primary corpus unless a later full-text check finds actual simulation results.

### DisCoPy: Monoidal categories in python (2021)

- Criteria: IC1; exclusion basis: EC12-like toolkit/software paper; confidence: high.

- Evidence: Analyzed nlp_task is none. PDF describes the architecture of the DisCoPy Python package; it is a software/toolkit contribution, not a primary NLP-task evaluation paper.

- Action: Remove from primary corpus; cite as tooling/reference material.

### Variational Quantum Classifiers for Natural-Language Text (2023)

- Criteria: IC2; exclusion basis: EC10 / EC12-like theoretical proposal; confidence: high.

- Evidence: Analyzed execution is NA and notes say no experiments. PDF abstract says it discusses potential approaches to VQTCs rather than reporting a new evaluated model.

- Action: Remove from primary corpus; cite as conceptual background if needed.

### Category Theory for Quantum Natural Language Processing (2022)

- Criteria: IC1; exclusion basis: EC12; confidence: high.

- Evidence: Analyzed nlp_task is none and execution is NA. PDF is a thesis introducing and surveying QNLP/category-theoretic models and DisCoPy; it is not a single primary experimental NLP study.

- Action: Remove from primary corpus; cite as background/reference.

### A hybrid classical-quantum workflow for natural language processing (2020)

- Criteria: IC7; exclusion basis: time window violation; confidence: high.

- Evidence: Formal criteria define the time window as 2021-2026 inclusive. This row is 2020, even though it otherwise appears relevant and simulated.

- Action: Remove from primary corpus or explicitly amend criteria/time window if it must be retained.

### Grammar-Aware Question-Answering on Quantum Computers (2020)

- Criteria: IC7; exclusion basis: EC6 duplicate/superseded likely; confidence: high.

- Evidence: Formal criteria define 2021-2026 inclusive. This 2020 preprint also appears superseded by the 2023 Quantum Machine Intelligence article “Grammar-aware sentence classification on quantum computers,” which is already in the corpus.

- Action: Remove 2020 preprint; retain the 2023 journal article.

### Foundations for Near-Term Quantum Natural Language Processing (2020)

- Criteria: IC2, IC7; exclusion basis: EC12 / theoretical-expository; confidence: high.

- Evidence: Formal criteria define 2021-2026 inclusive. Analyzed execution is NA and notes call it a foundational manifesto with no original experiments. PDF abstract explicitly describes an expository foundations paper.

- Action: Remove from primary corpus; cite as background.

## Retain but correct

### Experimentation Analysis of VQC and QSVM on Sentence Classification in Quantum Paradigm (2024)

- Evidence: CSV encoding is NR, but PDF pseudocode says classical data are mapped to quantum states using ZZFeatureMap for QSVM and reports Qiskit simulation/hardware context. This satisfies IC3 at least for the QSVM part.

- Action: Do not exclude; correct encoding to structured_feature_map or add notes that QSVM uses ZZFeatureMap while VQC encoding is less explicit.
