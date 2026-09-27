# Bharat EntityGraph
### "Reconstructing Business Identity from Fragmented Data"
**Amazon ML Challenge 2026 Submission Platform**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Model: LightGBM](https://img.shields.io/badge/model-LightGBM%20GBDT-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![Validation Macro F0.5: 0.9869](https://img.shields.io/badge/Validation%20Macro%20F0.5-0.9869-success.svg)](models/model_metadata.json)
[![Validation Precision: 99.76%](https://img.shields.io/badge/Precision-99.76%25-blueviolet.svg)](models/model_metadata.json)
[![Submission Status: PASS](https://img.shields.io/badge/Submission%20Validator-PASS-success.svg)](output/matching_results.tsv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Overview
Bharat EntityGraph is an enterprise-grade Business Entity Resolution engine and identity intelligence system built for the Amazon ML Challenge 2026. The platform resolves fragmented business records across heterogeneous vendor catalogs without common identifiers, optimizing specifically for precision-heavy Macro $F_{0.5}$ evaluation.

### Core Architecture:
1. **Conservative Multi-Lingual Normalization:** Unifies Indian commercial patterns, US corporate formats, and European open-set entities (France) without over-collapsing distinct businesses.
2. **Multi-Strategy Compound Blocking:** Inverted index union combining exact core brand signatures, sorted bigrams, PIN/ZIP codes, primary street numbers, and character 3-grams with frequency capping to achieve **97.91% candidate recall**.
3. **Discriminative Pairwise Feature Engineering:** 33 RapidFuzz-powered lexical, phonological, structural, numeric, and cross-field interaction features.
4. **LightGBM Decision Tree Matcher:** Trained on mined hard negatives with calibrated log-loss (<100K parameters, MIT/Apache 2.0 license).
5. **Macro $F_{0.5}$ Dual-Thresholding & 1-to-1 Target Exclusivity:** Enforces bipartite target exclusivity to eliminate duplicate false merges while safeguarding true singletons.

---

## 2. Validation Benchmark Scores

| Metric | Measured Score | Description |
| :--- | :--- | :--- |
| **Macro $F_{0.5}$** | **0.9869** | Official challenge competition metric |
| **Precision** | **99.76%** | False positive avoidance ($2\times$ weight in $F_{0.5}$) |
| **Recall** | **97.44%** | True positive linkage recovery |
| **Macro $F_1$** | **0.9798** | Harmonic balance between Precision and Recall |
| **Candidate Recall** | **97.91%** | Upper bound recall achieved by blocking |
| **Singleton Accuracy** | **100.00%** | Accurate preservation of unlinked businesses |
| **False Positives** | **1 / 420** | Strictly controlled under bipartite target exclusivity |

---

## 3. End-to-End Reproduction Guide

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train model and optimize Macro F0.5 thresholds
python3 train.py

# 3. Run full test inference and generate official TSVs
python3 code/business_entity_resolution/src/main.py \
    --test-dir dataset/test \
    --output-dir output

# 4. Run official competition submission validator
python3 utils/validate_submission.py \
    --matching output/matching_results.tsv \
    --candidate output/candidate_pairs.tsv \
    --test-dir dataset/test \
    --check-ids
```

Output:
```text
PASS — no blocking issues found. Safe to submit.
```

---

## 4. Package Artifacts
The final submission archive `bharat_entitygraph_submission.zip` contains:
```text
output/
  matching_results.tsv
  candidate_pairs.tsv
code/
  business_entity_resolution/
    src/
    README.md
    requirements.txt
Documentation_template.md
README.md
requirements.txt
```
