# Bharat EntityGraph — Business Entity Resolution Pipeline
### Amazon ML Challenge 2026 Reproduction Guide

Reconstructs business entity identities across 3 noisy, heterogeneous multi-source commercial catalogs under precision-heavy Macro $F_{0.5}$ evaluation.

---

## 1. Quick Reproduction Steps

### Step 1: Environment Setup
Ensure Python 3.8+ is installed. Install all dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Model Training & Threshold Calibration
To train the LightGBM matcher, extract pairwise features on mined hard negatives, calibrate source thresholds, and evaluate on held-out validation data:
```bash
python3 train.py
```
Outputs:
- Serialized model: `models/bharat_entity_matcher.joblib`
- Calibration metadata: `models/model_metadata.json`

### Step 3: Run Test Inference & Generate Submissions
To execute multi-strategy blocking, pairwise feature extraction, and source-aware bipartite matching for all test records:
```bash
python3 code/business_entity_resolution/src/main.py \
    --test-dir dataset/test \
    --output-dir output
```
Generates:
- `output/matching_results.tsv` (Official leaderboard matches)
- `output/candidate_pairs.tsv` (Candidate pairs considered)

### Step 4: Validate Submissions
Verify that output files satisfy 100% of the challenge formatting and validity rules:
```bash
python3 utils/validate_submission.py \
    --matching output/matching_results.tsv \
    --candidate output/candidate_pairs.tsv \
    --test-dir dataset/test \
    --check-ids
```
Expected output: **`PASS — no blocking issues found. Safe to submit.`**

---

## 2. Directory Structure

```text
code/business_entity_resolution/
├── src/
│   ├── __init__.py           # Package marker
│   ├── normalization.py      # Unicode unidecode, legal suffix isolation, street/PIN normalizer
│   ├── blocking.py           # Multi-strategy inverted index candidate generator with frequency pruning
│   ├── features.py           # 33 RapidFuzz lexical, structural, and interaction features
│   ├── model.py              # LightGBM / GBDT pairwise matcher wrapper
│   ├── thresholding.py       # Macro F0.5 dual-threshold optimizer and bipartite exclusivity resolver
│   ├── evaluation.py         # Official competition Macro F0.5 per-entity evaluator
│   ├── data_loader.py        # Tab-separated streaming TSV reader with country partitioner
│   ├── explainability.py     # Feature attribution and confidence triage layer
│   ├── graph.py              # Canonical Bharat EntityGraph synthesis module
│   ├── submission.py         # Competition TSV writer
│   └── main.py               # CLI entry point with automatic validator invocation
├── requirements.txt          # Pinned Python requirements
└── README.md                 # Complete documentation and reproduction guide
```

---

## 3. Benchmarks & Validation Results

| Metric | Validation Score |
| :--- | :--- |
| **Validation Macro $F_{0.5}$** | **0.9869** |
| **Validation Precision** | **99.76%** |
| **Validation Recall** | **97.44%** |
| **Macro $F_1$** | **0.9798** |
| **Candidate Blocking Recall** | **97.91%** |
| **Singleton Accuracy** | **100.00%** |
| **False Positives** | **1** |
| **False Negatives** | **11** |
