"""
Bharat EntityGraph — Business Entity Resolution Platform
Threshold Optimization & Conflict Resolution Module
Source-aware dual thresholding and bipartite exclusivity resolving.
"""

from typing import Dict, List, Tuple, Set
import numpy as np
import evaluation as ev

def optimize_thresholds(val_scored_pairs: List[Tuple[str, str, float]], 
                        val_ground_truth: Dict[str, Set[str]],
                        threshold_grid: List[float] = None) -> Tuple[float, float, float]:
    """
    Grid-searches optimal (tau_s2, tau_s3) thresholds on validation data to maximize Macro F0.5.
    Returns: (best_s2_threshold, best_s3_threshold, best_macro_f05)
    """
    if threshold_grid is None:
        threshold_grid = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70, 0.80]
        
    best_f05 = -1.0
    best_s2 = 0.75
    best_s3 = 0.75
    
    # Pre-organize scored pairs by s1_id
    s1_to_candidates = collections.defaultdict(list)
    for s1_id, tid, prob in val_scored_pairs:
        s1_to_candidates[s1_id].append((tid, prob))
        
    for t_s2 in threshold_grid:
        for t_s3 in threshold_grid:
            # Build predictions with target exclusivity
            preds_dict = apply_decision_rules_and_conflict_resolution(
                s1_to_candidates,
                s2_threshold=t_s2,
                s3_threshold=t_s3,
                enforce_target_exclusivity=True
            )
            preds = {k: set(v) for k, v in preds_dict.items()}
                
            metrics = ev.evaluate_resolution_predictions(val_ground_truth, preds)
            score = metrics['macro_f05']
            
            if score > best_f05:
                best_f05 = score
                best_s2 = t_s2
                best_s3 = t_s3
                
    return best_s2, best_s3, best_f05

import collections

def apply_decision_rules_and_conflict_resolution(
    s1_candidate_probs: Dict[str, List[Tuple[str, float]]],
    s2_threshold: float = 0.70,
    s3_threshold: float = 0.75,
    enforce_target_exclusivity: bool = True
) -> Dict[str, List[str]]:
    """
    Applies source-aware thresholds, per-source top-1 candidate selection,
    and bipartite target exclusivity.
    """
    # Group candidates by S1 and by source
    proposals = [] # (prob, s1_id, tid, source_tag)
    for s1_id, cands in s1_candidate_probs.items():
        for tid, prob in cands:
            is_s2 = tid.startswith('S2-')
            thresh = s2_threshold if is_s2 else s3_threshold
            if prob >= thresh:
                src_tag = 'S2' if is_s2 else 'S3'
                proposals.append((prob, s1_id, tid, src_tag))
                
    # Sort proposals descending by probability
    proposals.sort(key=lambda x: x[0], reverse=True)
    
    final_matches = collections.defaultdict(list)
    s1_matched_sources = collections.defaultdict(set)
    assigned_targets = set()
    
    for prob, s1_id, tid, src_tag in proposals:
        # Enforce at most 1 match per source for any S1 entity
        if src_tag in s1_matched_sources[s1_id]:
            continue
            
        # Enforce global target exclusivity (each S2/S3 entity belongs to at most 1 S1 entity)
        if enforce_target_exclusivity and tid in assigned_targets:
            continue
            
        assigned_targets.add(tid)
        s1_matched_sources[s1_id].add(src_tag)
        final_matches[s1_id].append(tid)
        
    result = {}
    for s1_id in s1_candidate_probs.keys():
        result[s1_id] = sorted(final_matches.get(s1_id, []))
        
    return result
