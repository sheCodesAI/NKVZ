"""
Bharat EntityGraph — Business Entity Resolution Platform
Official Evaluation Module
Implements Macro F0.5 per Source 1 entity with strict singleton handling.
"""

from typing import Dict, Set, List
import numpy as np

def compute_entity_f05(true_set: Set[str], pred_set: Set[str]) -> float:
    """
    Computes F_0.5 score for a single Source 1 entity:
    F_0.5 = (1.25 * Precision * Recall) / (0.25 * Precision + Recall)
    
    Singleton logic:
    - True empty, Pred empty -> 1.0 (True Negative)
    - True empty, Pred non-empty -> 0.0 (False Positive)
    - True non-empty, Pred empty -> 0.0 (False Negative)
    """
    is_true_empty = len(true_set) == 0
    is_pred_empty = len(pred_set) == 0

    if is_true_empty:
        return 1.0 if is_pred_empty else 0.0

    if is_pred_empty:
        return 0.0

    tp = len(true_set & pred_set)
    if tp == 0:
        return 0.0

    precision = tp / len(pred_set)
    recall = tp / len(true_set)

    denom = 0.25 * precision + recall
    if denom == 0:
        return 0.0

    return (1.25 * precision * recall) / denom

def evaluate_resolution_predictions(ground_truth: Dict[str, Set[str]], 
                                    predictions: Dict[str, Set[str]]) -> Dict[str, float]:
    """
    Evaluates entity resolution predictions against ground truth.
    Returns:
    - macro_f05
    - precision
    - recall
    - macro_f1
    - singleton_accuracy
    - total_tp, total_fp, total_fn
    """
    f05_scores = []
    f1_scores = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_true_links = 0
    total_pred_links = 0
    
    singleton_total = 0
    singleton_correct = 0
    
    all_s1 = sorted(list(ground_truth.keys()))
    
    for s1_id in all_s1:
        true_set = ground_truth[s1_id]
        pred_set = predictions.get(s1_id, set())
        
        f05 = compute_entity_f05(true_set, pred_set)
        f05_scores.append(f05)
        
        tp = len(true_set & pred_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_true_links += len(true_set)
        total_pred_links += len(pred_set)
        
        if len(true_set) == 0:
            singleton_total += 1
            if len(pred_set) == 0:
                singleton_correct += 1
        else:
            if len(pred_set) > 0 and tp > 0:
                p = tp / len(pred_set)
                r = tp / len(true_set)
                f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
            else:
                f1 = 0.0
            f1_scores.append(f1)
            
    macro_f05 = float(np.mean(f05_scores)) if f05_scores else 0.0
    macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
    precision = total_tp / total_pred_links if total_pred_links > 0 else 1.0
    recall = total_tp / total_true_links if total_true_links > 0 else 0.0
    singleton_acc = singleton_correct / singleton_total if singleton_total > 0 else 1.0
    
    return {
        "macro_f05": macro_f05,
        "precision": precision,
        "recall": recall,
        "macro_f1": macro_f1,
        "singleton_accuracy": singleton_acc,
        "total_singletons": singleton_total,
        "correct_singletons": singleton_correct,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "total_entities_evaluated": len(all_s1)
    }
