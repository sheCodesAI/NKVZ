#!/usr/bin/env python3
"""
Bharat EntityGraph — End-to-End Business Entity Resolution CLI Driver
Amazon ML Challenge 2026 Submission Pipeline
"""

import os
import sys
import time
import json
import argparse
import subprocess
import collections
from typing import Dict, List, Tuple

# Path resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import normalization as norm
from blocking import MultiStrategyInvertedIndex
from features import extract_pairwise_features, FEATURE_NAMES
from model import BharatEntityMatcher
from thresholding import apply_decision_rules_and_conflict_resolution
from data_loader import load_records_tsv, stream_source1_entities
from submission import write_competition_submissions

def run_entity_resolution_inference(
    test_dir: str = "dataset/test",
    output_dir: str = "output",
    model_path: str = "models/bharat_entity_matcher.joblib",
    meta_path: str = "models/model_metadata.json",
    top_k_candidates: int = 35
) -> Dict[str, any]:
    """Runs complete, deterministic inference over all test Source 1 entities."""
    t_start = time.time()
    os.makedirs(output_dir, exist_ok=True)
    
    print("=================================================================")
    print("  BHARAT ENTITYGRAPH: BUSINESS ENTITY RESOLUTION INFERENCE")
    print("  Amazon ML Challenge 2026 — Macro F0.5 Optimized Pipeline")
    print("=================================================================")
    print(f"Test Directory   : {test_dir}")
    print(f"Output Directory : {output_dir}")
    print(f"Model Path       : {model_path}")

    # 1. Load Model and Decision Thresholds
    s2_threshold = 0.70
    s3_threshold = 0.75
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            s2_threshold = meta.get("optimal_s2_threshold", 0.70)
            s3_threshold = meta.get("optimal_s3_threshold", 0.75)
    print(f"Decision Thresholds: tau_S2 = {s2_threshold:.2f}, tau_S3 = {s3_threshold:.2f}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Please run train.py first.")

    model = BharatEntityMatcher.load(model_path)

    # 2. Read Test Sources
    s1_path = os.path.join(test_dir, "test_source1.tsv")
    s2_path = os.path.join(test_dir, "test_source2.tsv")
    s3_path = os.path.join(test_dir, "test_source3.tsv")

    print("\n[Phase 1/4] Ingesting test records & partitioning by country...")
    # Load all Source 1 entities in exact order
    ordered_s1_ids = []
    country_s1_records = collections.defaultdict(list)
    s1_record_map = {}
    
    for eid, name, addr, country in stream_source1_entities(s1_path):
        ordered_s1_ids.append(eid)
        country_s1_records[country].append((eid, name, addr, country))
        s1_record_map[eid] = (name, addr, country)
        
    print(f"Total Test Source 1 Entities: {len(ordered_s1_ids):,}")
    for c, records in country_s1_records.items():
        print(f"  • {c:<10}: {len(records):,} entities ({len(records)/len(ordered_s1_ids)*100:.1f}%)")

    # Load targets (S2 and S3)
    s2_records = load_records_tsv(s2_path)
    s3_records = load_records_tsv(s3_path)
    print(f"Target Records Loaded: S2 = {len(s2_records):,}, S3 = {len(s3_records):,}")

    # Combine targets partitioned by country
    target_by_country = collections.defaultdict(dict)
    for tid, rec in s2_records.items():
        target_by_country[rec[2]][tid] = rec
    for tid, rec in s3_records.items():
        target_by_country[rec[2]][tid] = rec

    # 3. Candidate Generation & Feature Scoring per Country
    print("\n[Phase 2/4] Multi-strategy blocking & pairwise feature scoring...")
    all_candidates_dict = collections.defaultdict(list)
    all_s1_candidate_probs = collections.defaultdict(list)
    
    total_candidate_pairs = 0
    country_breakdown = {}

    for country, s1_list in country_s1_records.items():
        c_t0 = time.time()
        c_targets = target_by_country.get(country, {})
        print(f"\nProcessing Country: {country} ({len(s1_list):,} S1 entities, {len(c_targets):,} target records)...")

        # Build country-partitioned inverted index
        index = MultiStrategyInvertedIndex(max_key_frequency=500)
        n_keys, n_pruned = index.index_target_records(c_targets)
        print(f"  Indexed {len(c_targets):,} records -> {n_keys:,} signatures ({n_pruned} stop-keys pruned)")

        # Precompute normalized representation for S1
        s1_preprocessed = {}
        for eid, name, addr, c_name in s1_list:
            cn, core_n, _ = norm.normalize_name(name)
            ca, nums, post, _ = norm.normalize_address(addr, c_name)
            s1_preprocessed[eid] = (cn, core_n, ca, nums, post, c_name)

        # Retrieve candidates and extract features in batches
        feature_batch = []
        pair_batch = [] # (s1_id, cand_id)

        c_pairs_count = 0
        for eid, name, addr, c_name in s1_list:
            candidates = index.retrieve_candidates(eid, name, addr, c_name, top_k=top_k_candidates)
            c_ids = [c[0] for c in candidates]
            all_candidates_dict[eid] = c_ids
            c_pairs_count += len(c_ids)

            s1_tuple = s1_preprocessed[eid]
            for cand_id, shared_support in candidates:
                tgt_tuple = index.target_cache[cand_id]
                feats = extract_pairwise_features(s1_tuple, tgt_tuple, cand_id, shared_keys_count=shared_support)
                feature_batch.append(feats)
                pair_batch.append((eid, cand_id))

        total_candidate_pairs += c_pairs_count
        print(f"  Generated {c_pairs_count:,} candidate pairs (avg {c_pairs_count/len(s1_list):.1f} / entity)")

        # Model Inference
        if feature_batch:
            import numpy as np
            X = np.array(feature_batch, dtype=np.float32)
            probs = model.predict_proba(X)
            
            for (eid, cand_id), prob in zip(pair_batch, probs):
                all_s1_candidate_probs[eid].append((cand_id, float(prob)))

        c_elapsed = time.time() - c_t0
        country_breakdown[country] = {
            "s1_count": len(s1_list),
            "target_count": len(c_targets),
            "candidate_pairs": c_pairs_count,
            "runtime_sec": round(c_elapsed, 2)
        }

    # 4. Global Decision & Target Exclusivity Resolution
    print("\n[Phase 3/4] Threshold filtering & bipartite target exclusivity resolution...")
    matches_dict = apply_decision_rules_and_conflict_resolution(
        all_s1_candidate_probs,
        s2_threshold=s2_threshold,
        s3_threshold=s3_threshold,
        enforce_target_exclusivity=True
    )

    # Compute quick stats
    total_matched_entities = sum(1 for mids in matches_dict.values() if mids)
    total_singletons = len(ordered_s1_ids) - total_matched_entities
    total_links = sum(len(mids) for mids in matches_dict.values())
    total_s2 = sum(sum(1 for m in mids if m.startswith('S2-')) for mids in matches_dict.values())
    total_s3 = sum(sum(1 for m in mids if m.startswith('S3-')) for mids in matches_dict.values())

    print(f"\nInference Summary:")
    print(f"  • Total S1 Entities   : {len(ordered_s1_ids):,}")
    print(f"  • Singletons (No Match): {total_singletons:,} ({total_singletons/len(ordered_s1_ids)*100:.2f}%)")
    print(f"  • Entities with Matches: {total_matched_entities:,} ({total_matched_entities/len(ordered_s1_ids)*100:.2f}%)")
    print(f"  • Total Links Resolved : {total_links:,} (S2: {total_s2:,}, S3: {total_s3:,})")
    print(f"  • Total Candidates Fed : {total_candidate_pairs:,}")

    # 5. Export TSV Submissions
    print("\n[Phase 4/4] Writing official submission files...")
    matching_tsv, candidate_tsv = write_competition_submissions(
        ordered_s1_ids=ordered_s1_ids,
        candidates_dict=all_candidates_dict,
        matches_dict=matches_dict,
        output_dir=output_dir
    )
    print(f"  ✓ Written: {matching_tsv}")
    print(f"  ✓ Written: {candidate_tsv}")

    # 6. Run Official Validator
    validator_path = "utils/validate_submission.py"
    val_status = "UNKNOWN"
    val_output = ""
    if os.path.exists(validator_path):
        print("\n=== Running Official Challenge Validator ===")
        val_cmd = [
            sys.executable, validator_path,
            "--matching", matching_tsv,
            "--candidate", candidate_tsv,
            "--test-dir", test_dir
        ]
        res = subprocess.run(val_cmd, capture_output=True, text=True)
        val_output = res.stdout + res.stderr
        print(val_output.strip())
        val_status = "PASS" if res.returncode == 0 else "FAIL"
        print(f"Validator Status: {val_status}")

    total_time = time.time() - t_start
    summary_report = {
        "status": "SUCCESS",
        "validator_status": val_status,
        "runtime_seconds": round(total_time, 2),
        "total_s1_entities": len(ordered_s1_ids),
        "total_singletons": total_singletons,
        "singleton_rate": round(total_singletons / len(ordered_s1_ids), 4),
        "total_matched_links": total_links,
        "total_s2_matches": total_s2,
        "total_s3_matches": total_s3,
        "total_candidates": total_candidate_pairs,
        "s2_threshold": s2_threshold,
        "s3_threshold": s3_threshold,
        "country_breakdown": country_breakdown
    }

    report_path = os.path.join(output_dir, "inference_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    return summary_report

def main():
    parser = argparse.ArgumentParser(description="Bharat EntityGraph Inference CLI")
    parser.add_argument("--test-dir", default="dataset/test", help="Path to test dataset")
    parser.add_argument("--output-dir", default="output", help="Path to output directory")
    parser.add_argument("--model-path", default="models/bharat_entity_matcher.joblib", help="Path to model")
    parser.add_argument("--meta-path", default="models/model_metadata.json", help="Path to metadata")
    args = parser.parse_args()

    run_entity_resolution_inference(
        test_dir=args.test_dir,
        output_dir=args.output_dir,
        model_path=args.model_path,
        meta_path=args.meta_path
    )

if __name__ == "__main__":
    main()
