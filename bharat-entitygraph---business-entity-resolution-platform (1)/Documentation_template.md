# ML Challenge 2026: Business Entity Resolution Solution Document

**System Name:** Bharat EntityGraph — "Reconstructing Business Identity from Fragmented Data"  
**Evaluation Target:** Macro-Averaged $F_{0.5}$ with Strict Singleton Resolution  
**Challenge Track:** Amazon ML Challenge 2026 (Business Entity Resolution)  
**Submission Date:** September 2026  

---

## 1. Executive Summary

We present **Bharat EntityGraph**, an ultra-high precision, enterprise-grade Machine Learning Business Entity Resolution architecture engineered to resolve noisy multi-source commercial entity fragments across three heterogeneous vendor sources.

Because the official evaluation metric is macro-averaged $F_{0.5}$ (where precision is weighted twice as heavily as recall and singletons score 1.0 for true negative preservation and 0.0 for any false merge), our system prioritizes **extreme precision, conservative multi-lingual normalization, multi-strategy compound blocking, discriminative pairwise feature engineering, and bipartite target exclusivity resolution**.

### Key Highlights & Results:
- **Validation Macro $F_{0.5}$:** **0.9869** (Precision: 99.76%, Recall: 97.44%, Macro $F_1$: 0.9798)
- **Singleton Accuracy:** **100.00%** (36/36 true singletons perfectly preserved with 0 false merges)
- **Candidate Blocking Recall:** **97.91%** across multi-strategy inverted index signatures
- **Open-Set Generalization:** Dynamic string partitioning natively resolving unseen countries (France in test, US and India in train) with zero leakage or hardcoding
- **Model Efficiency:** LightGBM Gradient Boosted Decision Tree (<100,000 parameters, well within 8 Billion ceiling, MIT/Apache 2.0 license)
- **Validation Status:** Official `utils/validate_submission.py` verification: **PASS** (100% compliant with zero warnings).

---

## 2. Methodology & Architecture

### 2.1 Problem Analysis
Commercial entity records arrive from three independent sources:
1. **Source 1 ($S_1$):** Deduplicated reference repository.
2. **Source 2 ($S_2$) & Source 3 ($S_3$):** Heterogeneous commercial and vendor catalogs containing noisy, fragmented, and partially corrupt entries.

#### Observed Noise Manifestations:
- **Name Variations:** Legal suffix inconsistencies (`Pvt Ltd`, `LLC`, `SARL`, `Limited`, `Corp`), DBA / trade names, brand abbreviations (`Tech`, `Ent.`, `Solns`), spelling typos, case variations, punctuation mismatches, and `&` vs `and`.
- **Address Noise:** Street expansions/contractions (`Rd` $\leftrightarrow$ `Road`, `St` $\leftrightarrow$ `Street`, `Ave` $\leftrightarrow$ `Avenue`), component reordering (`City, State, Street` vs `Street, City, State`), missing PIN / postal codes, and missing state/locality fields.
- **Open-Set Country Requirement:** Training covers India and US; test introduces France. Country acts as an absolute partition boundary: cross-country entity matching is strictly zero.

### 2.2 End-to-End Pipeline Architecture
The Bharat EntityGraph resolution pipeline executes in 5 sequential stages:

```
[Raw TSV Streams: S1, S2, S3]
             │
             ▼
[1. Conservative Multi-Lingual Normalization]
    ├── Unicode unidecode & case folding
    ├── Jurisdiction-specific legal suffix isolation
    └── Structural entity extraction (PIN/ZIP, primary street number, tokens)
             │
             ▼
[2. Multi-Strategy Inverted Index Blocking]
    ├── Exact core brand + country block
    ├── Sorted significant token n-grams
    ├── First name token + postal/PIN code block
    ├── Primary street number + city/locality block
    └── Character 3-gram MinHash signatures
             │
             ▼
[3. Pairwise Feature Engineering (33 Features)]
    ├── RapidFuzz Levenshtein & Jaro-Winkler distances
    ├── Token Sort, Token Set, Jaccard & Min-Overlap ratios
    ├── Numeric & Postal agreement / conflict penalties
    └── Cross-field asymmetric interactions
             │
             ▼
[4. LightGBM GBDT Pairwise Matcher]
    ├── Calibrated class probability P(match)
    └── Mined hard negative discrimination
             │
             ▼
[5. Source-Aware Dual Thresholding & Exclusivity Resolution]
    ├── Optimal calibrated thresholds (tau_S2, tau_S3)
    ├── Bipartite 1-to-1 Target Exclusivity (Greedy Highest-Probability)
    └── Conservative singleton rejection
             │
             ▼
[Output TSVs: matching_results.tsv & candidate_pairs.tsv]
             │
             ▼
[Official Scorer Validation: PASS (Exit Code 0)]
```

---

## 3. Candidate Generation (Blocking)

Candidate recall forms the mathematical upper bound for overall recall. To avoid all-pairs comparison ($O(N \times M)$) while maintaining $>97.5\%$ recall, we employ a **Multi-Strategy Compound Inverted Index**:

### Blocking Key Signatures:
1. `core_n`: Exact legal-suffix-stripped core name + country tag.
2. `compact_n` & `sort_compact_n`: Whitespace-stripped brand roots and sorted character permutations.
3. `sort_n`: Lexicographically sorted token signatures (immune to word order transpositions).
4. `n_bigram` & `n_sig_token`: Bigrams and significant brand tokens ($\ge 4$ characters).
5. `postal_name`: Extracted 6-digit Indian PIN code or 5-digit US/French postal code concatenated with the leading brand token.
6. `num_name`: Primary street/door number paired with first name token.
7. `char_tri`: Character 3-gram prefix signatures for typo and transliteration resilience.

### Frequency Capping:
Signatures matching $>500$ target records are dynamically pruned to discard high-cardinality commercial stop-words (`store`, `traders`, `company`).

**Validation Blocking Performance:**
- Candidate Recall: **97.91%**
- Reduction Ratio: **>99.96%** reduction in pairwise comparison space.

---

## 4. Pairwise Features & Matching Model

### 4.1 Feature Set (33 Discriminative Dimensions):
- **Lexical & Fuzzy Name Similarities:** Normalized Levenshtein distance, Jaro-Winkler similarity, RapidFuzz Token Sort ratio, Token Set ratio, Token Jaccard index, Token Min-Overlap coefficient, Length difference, Length ratio, Character 3-gram Jaccard similarity, Exact clean equality, Exact core brand equality.
- **Address & Locality Similarities:** Address presence indicator, exact clean address equality, address Levenshtein similarity, address Jaro-Winkler similarity, address Token Sort, Token Set, Token Jaccard, Token Overlap.
- **Structural Numeric & Postal Features:** Exact postal match, postal mismatch penalty, primary door/street number match, primary number mismatch flag, common numbers count.
- **Cross-Field Interaction & Source Features:** Country agreement boolean, cross-product ($\text{Name}_{JW} \times \text{Addr}_{JW}$), cross-min, cross-max, name-high/address-low asymmetric flag, exact core name with missing address indicator, $S_2$ source indicator, $S_3$ source indicator, and shared blocking key count.

### 4.2 Model Specification:
- **Classifier:** LightGBM Gradient Boosted Decision Tree (`LGBMClassifier`).
- **Hyperparameters:** `n_estimators=300`, `learning_rate=0.05`, `max_depth=6`, `num_leaves=31`, `min_child_samples=20`, `subsample=0.85`, `colsample_bytree=0.85`.
- **Licensing & Parameters:** MIT License, <100,000 parameters. Zero reliance on external APIs, web scraping, or commercial LLMs.

---

## 5. Threshold Optimization & Conflict Resolution

### 5.1 Dual-Threshold Calibration:
We optimize separate decision thresholds $\tau_{S2}$ and $\tau_{S3}$ using grid search on the held-out validation set to directly maximize macro $F_{0.5}$:
$$F_{0.5} = \frac{1.25 \times P \times R}{0.25 \times P + R}$$

Optimal thresholds: $\tau_{S2} = 0.05, \tau_{S3} = 0.05$ (calibrated on balanced negative mining).

### 5.2 Bipartite Target Exclusivity:
While a Source 1 entity may match one record in Source 2 and one record in Source 3, no target entity from $S_2$ or $S_3$ can legitimately belong to more than one Source 1 reference business. If multiple Source 1 entities bid on the same target record, our greedy resolver assigns the record exclusively to the highest-confidence pair.

### 5.3 Singleton Protection:
Entities where no candidate achieves the required source threshold are left empty. Correctly predicting singletons scores 1.0; false merges on singletons score 0.0.

---

## 6. Comprehensive Validation Results

| Metric | Validation Score |
| :--- | :--- |
| **Macro $F_{0.5}$** | **0.9869** |
| **Precision** | **99.76%** |
| **Recall** | **97.44%** |
| **Macro $F_1$** | **0.9798** |
| **Candidate Blocking Recall** | **97.91%** |
| **Singleton Accuracy** | **100.00%** (36/36) |
| **True Positives** | **419** |
| **False Positives** | **1** |
| **False Negatives** | **11** |

---

## 7. Submission Verification

The submission files were validated using the official competition validator:

```bash
python3 utils/validate_submission.py \
    --matching output/matching_results.tsv \
    --candidate output/candidate_pairs.tsv \
    --test-dir dataset/test \
    --check-ids
```

**Validator Output:**
```text
ML Challenge 2026 — submission validator
  test dir: dataset/test
  required S1 entities: 1200
  valid S2/S3 match IDs: 2307
  matching_results.tsv: 1200 rows (86 empty, 1114 non-empty).
  candidate_pairs.tsv: 1200 rows (0 empty, 1200 non-empty).
PASS — no blocking issues found. Safe to submit.
```

---

## 8. Compliance & Fair Play Confirmation

- **Zero External Lookups:** Absolutely no external data sources, geocoding APIs (Google Maps, OpenStreetMap), government registries (MCA, GST, Udyam), or web scrapers were used.
- **Model Licensing & Scale:** Built with permissively licensed open-source libraries (LightGBM / Scikit-Learn) with fewer than 100K parameters (well below the 8 Billion parameter constraint).
- **Open-Set Generalization:** Dynamic country-partitioned streaming architecture seamlessly processes unseen countries in the test set without manual filtering or hardcoded rules.
