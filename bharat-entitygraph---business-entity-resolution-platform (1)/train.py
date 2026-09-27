#!/usr/bin/env python3
"""
Bharat EntityGraph — Training and Threshold Optimization Pipeline
Amazon ML Challenge 2026
Trains Gradient Boosted Entity Matcher on mined hard negatives and calibrates Macro F0.5 thresholds.
"""

import os
import sys
import time
import json
import random
import argparse
import collections
import numpy as np

# Add src to path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "code", "business_entity_resolution", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import normalization as norm
from blocking import MultiStrategyInvertedIndex
from features import extract_pairwise_features, FEATURE_NAMES
from model import BharatEntityMatcher
from evaluation import evaluate_resolution_predictions, compute_entity_f05
from thresholding import optimize_thresholds, apply_decision_rules_and_conflict_resolution
from data_loader import load_records_tsv, load_ground_truth_tsv

def run_training_pipeline(
    train_dir: str = "dataset/train",
    model_out: str = "models/bharat_entity_matcher.joblib",
    meta_out: str = "models/model_metadata.json",
    val_split_ratio: float = 0.20,
    seed: int = 42
):
    print("=================================================================")
    print("  BHARAT ENTITYGRAPH: MODEL TRAINING & THRESHOLD OPTIMIZATION")
    print("  Amazon ML Challenge 2026 — Macro F0.5 Evaluation")
    print("=================================================================")
    random.seed(seed)
    np.random.seed(seed)
    
    t_start = time.time()
    
    # 1. Ingest Training Sources
    s1_file = os.path.join(train_dir, "train_source1.tsv")
    s2_file = os.path.join(train_dir, "train_source2.tsv")
    s3_file = os.path.join(train_dir, "train_source3.tsv")
    gt_file = os.path.join(train_dir, "train_ground_truth.tsv")

    print("\n[Step 1/5] Loading training records & ground truth...")
    s1_records = load_records_tsv(s1_file)
    s2_records = load_records_tsv(s2_file)
    s3_records = load_records_tsv(s3_file)
    ground_truth = load_ground_truth_tsv(gt_file)
    
    print(f"Loaded: S1 = {len(s1_records):,}, S2 = {len(s2_records):,}, S3 = {len(s3_records):,}")
    print(f"Ground Truth pairs loaded: {len(ground_truth):,} reference entities")

    # Combine S2 and S3 target sets partitioned by country
    target_by_country = collections.defaultdict(dict)
    all_targets = {}
    for tid, rec in s2_records.items():
        target_by_country[rec[2]][tid] = rec
        all_targets[tid] = rec
    for tid, rec in s3_records.items():
        target_by_country[rec[2]][tid] = rec
        all_targets[tid] = rec

    # 2. Stratified Entity-Level Validation Split
    print("\n[Step 2/5] Creating held-out entity-level validation split...")
    all_s1_ids = sorted(list(s1_records.keys()))
    random.shuffle(all_s1_ids)
    
    n_val = int(len(all_s1_ids) * val_split_ratio)
    val_s1_set = set(all_s1_ids[:n_val])
    train_s1_ids = all_s1_ids[n_val:]
    
    print(f"Split: {len(train_s1_ids):,} Train S1 entities | {len(val_s1_set):,} Validation S1 entities")

    # 3. Mine Candidates and Extract Features for Training & Validation
    print("\n[Step 3/5] Inverted Index Blocking & Hard Negative Mining...")
    
    # Build Inverted Index per country
    indexes = {}
    for country, targets in target_by_country.items():
        idx = MultiStrategyInvertedIndex(max_key_frequency=500)
        idx.index_target_records(targets)
        indexes[country] = idx
        print(f"  Indexed {country}: {len(targets):,} targets")

    # Helper to precompute normalized record
    def get_norm_tuple(name, addr, country):
        cn, core_n, _ = norm.normalize_name(name)
        ca, nums, post, _ = norm.normalize_address(addr, country)
        return (cn, core_n, ca, nums, post, country)

    train_X = []
    train_y = []

    # Mining Training Pairs (True Positives + Inverted Index Negatives)
    for s1_id in train_s1_ids:
        raw_name, raw_addr, country = s1_records[s1_id]
        s1_tuple = get_norm_tuple(raw_name, raw_addr, country)
        idx = indexes.get(country)
        if not idx:
            continue
            
        true_matches = ground_truth.get(s1_id, set())
        candidates = idx.retrieve_candidates(s1_id, raw_name, raw_addr, country, top_k=25)
        cand_ids = {c[0] for c in candidates}
        cand_dict = dict(candidates)

        # Include all true positives even if missed by blocking (to train strong weights)
        for true_id in true_matches:
            if true_id in all_targets:
                tgt_tuple = get_norm_tuple(all_targets[true_id][0], all_targets[true_id][1], country)
                support = cand_dict.get(true_id, 1)
                feats = extract_pairwise_features(s1_tuple, tgt_tuple, true_id, shared_keys_count=support)
                train_X.append(feats)
                train_y.append(1)

        # Include mined hard negatives from blocking
        for cand_id, support in candidates:
            if cand_id not in true_matches and cand_id in all_targets:
                tgt_tuple = get_norm_tuple(all_targets[cand_id][0], all_targets[cand_id][1], country)
                feats = extract_pairwise_features(s1_tuple, tgt_tuple, cand_id, shared_keys_count=support)
                train_X.append(feats)
                train_y.append(0)

    train_X = np.array(train_X, dtype=np.float32)
    train_y = np.array(train_y, dtype=np.int32)
    print(f"Training dataset constructed: {len(train_y):,} pairs ({np.sum(train_y == 1):,} positives, {np.sum(train_y == 0):,} hard negatives)")

    # 4. Train BharatEntityMatcher
    print("\n[Step 4/5] Fitting LightGBM / GBDT Pairwise Matcher...")
    matcher = BharatEntityMatcher(n_estimators=300, learning_rate=0.05, max_depth=6, scale_pos_weight=1.0)
    matcher.fit(train_X, train_y)
    matcher.save(model_out)
    print(f"Model trained and saved to: {model_out}")

    # 5. Evaluate and Calibrate Thresholds on Held-Out Validation Split
    print("\n[Step 5/5] Scoring Validation Set & Calibrating Dual Thresholds...")
    val_gt = {s1_id: ground_truth.get(s1_id, set()) for s1_id in val_s1_set}
    val_scored_pairs = [] # (s1_id, cand_id, prob)
    val_s1_cand_probs = collections.defaultdict(list)
    val_cand_recall_hits = 0
    val_total_links = 0

    for s1_id in val_s1_set:
        raw_name, raw_addr, country = s1_records[s1_id]
        s1_tuple = get_norm_tuple(raw_name, raw_addr, country)
        idx = indexes.get(country)
        true_matches = val_gt[s1_id]
        val_total_links += len(true_matches)
        
        candidates = idx.retrieve_candidates(s1_id, raw_name, raw_addr, country, top_k=35)
        cand_ids = {c[0] for c in candidates}
        val_cand_recall_hits += len(true_matches & cand_ids)

        if not candidates:
            continue

        c_feats = []
        c_ids = []
        for cand_id, support in candidates:
            if cand_id in all_targets:
                tgt_tuple = get_norm_tuple(all_targets[cand_id][0], all_targets[cand_id][1], country)
                feats = extract_pairwise_features(s1_tuple, tgt_tuple, cand_id, shared_keys_count=support)
                c_feats.append(feats)
                c_ids.append(cand_id)

        if c_feats:
            probs = matcher.predict_proba(np.array(c_feats, dtype=np.float32))
            for cid, p in zip(c_ids, probs):
                val_scored_pairs.append((s1_id, cid, float(p)))
                val_s1_cand_probs[s1_id].append((cid, float(p)))

    cand_recall = val_cand_recall_hits / val_total_links if val_total_links > 0 else 1.0
    print(f"Validation Candidate Blocking Recall: {cand_recall*100:.2f}% ({val_cand_recall_hits:,}/{val_total_links:,} links covered)")

    # Grid search for optimal source-aware thresholds
    best_s2, best_s3, best_f05 = optimize_thresholds(val_scored_pairs, val_gt)
    print(f"Optimal Calibrated Thresholds: tau_S2 = {best_s2:.2f}, tau_S3 = {best_s3:.2f}")

    # Generate final validation predictions with exclusivity resolution
    val_preds_dict = apply_decision_rules_and_conflict_resolution(
        val_s1_cand_probs,
        s2_threshold=best_s2,
        s3_threshold=best_s3,
        enforce_target_exclusivity=True
    )
    # Convert list to set for evaluation
    val_preds_set = {k: set(v) for k, v in val_preds_dict.items()}

    final_metrics = evaluate_resolution_predictions(val_gt, val_preds_set)
    print("\n=================================================================")
    print("  FINAL VALIDATION BENCHMARK RESULTS")
    print("=================================================================")
    print(f"  • Validation Macro F0.5 : {final_metrics['macro_f05']:.4f}")
    print(f"  • Precision             : {final_metrics['precision']*100:.2f}%")
    print(f"  • Recall                : {final_metrics['recall']*100:.2f}%")
    print(f"  • Macro F1              : {final_metrics['macro_f1']:.4f}")
    print(f"  • Singleton Accuracy    : {final_metrics['singleton_accuracy']*100:.2f}% ({final_metrics['correct_singletons']}/{final_metrics['total_singletons']})")
    print(f"  • True Positives        : {final_metrics['total_tp']:,}")
    print(f"  • False Positives       : {final_metrics['total_fp']:,}")
    print(f"  • False Negatives       : {final_metrics['total_fn']:,}")
    print(f"  • Candidate Recall      : {cand_recall*100:.2f}%")
    print("=================================================================")

    meta = {
        "model_type": matcher.model_type,
        "n_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "optimal_s2_threshold": best_s2,
        "optimal_s3_threshold": best_s3,
        "validation_macro_f05": final_metrics['macro_f05'],
        "validation_precision": final_metrics['precision'],
        "validation_recall": final_metrics['recall'],
        "validation_macro_f1": final_metrics['macro_f1'],
        "candidate_recall": cand_recall,
        "singleton_accuracy": final_metrics['singleton_accuracy'],
        "false_positives": final_metrics['total_fp'],
        "false_negatives": final_metrics['total_fn'],
        "train_pairs_count": len(train_y),
        "val_entities_count": len(val_s1_set),
        "train_runtime_seconds": round(time.time() - t_start, 2)
    }

    os.makedirs(os.path.dirname(os.path.abspath(meta_out)), exist_ok=True)
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata exported to: {meta_out}")

    return final_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Bharat EntityGraph Model")
    parser.add_argument("--train-dir", default="dataset/train")
    parser.add_argument("--model-out", default="models/bharat_entity_matcher.joblib")
    parser.add_argument("--meta-out", default="models/model_metadata.json")
    args = parser.parse_args()

    run_training_pipeline(
        train_dir=args.train_dir,
        model_out=args.model_out,
        meta_out=args.meta_out
    )
