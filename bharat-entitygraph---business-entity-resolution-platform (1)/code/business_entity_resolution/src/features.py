"""
Bharat EntityGraph — Business Entity Resolution Platform
Feature Engineering Module
Computes 34-dimensional discriminative pairwise feature representations using RapidFuzz kernels.
"""

from typing import List, Tuple, Dict, Any
import rapidfuzz.distance.Levenshtein as lev
import rapidfuzz.distance.JaroWinkler as jw
import rapidfuzz.fuzz as fuzz

FEATURE_NAMES = [
    # Name Similarity Features (0-10)
    "name_exact_clean",
    "name_exact_core",
    "name_lev_sim",
    "name_jw_sim",
    "name_token_sort",
    "name_token_set",
    "name_token_jaccard",
    "name_token_overlap",
    "name_len_diff",
    "name_len_ratio",
    "name_char_3gram_sim",
    # Address Similarity Features (11-18)
    "addr_has_val",
    "addr_exact_clean",
    "addr_lev_sim",
    "addr_jw_sim",
    "addr_token_sort",
    "addr_token_set",
    "addr_token_jaccard",
    "addr_token_overlap",
    # Structural & Number Features (19-24)
    "postal_exact_match",
    "postal_mismatch",
    "primary_number_match",
    "primary_number_mismatch",
    "common_numbers_count",
    # Cross-Field & Interaction Features (25-33)
    "country_match",
    "cross_prod",
    "cross_min",
    "cross_max",
    "name_high_addr_low",
    "core_exact_no_addr",
    "is_source2",
    "is_source3",
    "shared_signatures_count"
]

def char_ngrams(s: str, n: int = 3) -> set:
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s) - n + 1)}

def extract_pairwise_features(s1_tuple: Tuple[str, str, str, List[str], str, str],
                              target_tuple: Tuple[str, str, str, List[str], str, str],
                              target_id: str,
                              shared_keys_count: int = 1) -> List[float]:
    """
    Computes 34-dim feature vector between pre-normalized S1 and target records.
    Tuple structure: (clean_name, core_name, clean_addr, numbers, postal_code, country)
    """
    s1_cn, s1_core, s1_ca, s1_nums, s1_post, s1_country = s1_tuple
    tgt_cn, tgt_core, tgt_ca, tgt_nums, tgt_post, tgt_country = target_tuple
    
    # 1. Name Features
    name_exact_clean = 1.0 if s1_cn and s1_cn == tgt_cn else 0.0
    name_exact_core = 1.0 if s1_core and s1_core == tgt_core else 0.0
    
    name_lev_sim = lev.normalized_similarity(s1_core, tgt_core) if s1_core and tgt_core else 0.0
    name_jw_sim = jw.similarity(s1_core, tgt_core) if s1_core and tgt_core else 0.0
    name_token_sort = fuzz.token_sort_ratio(s1_core, tgt_core) / 100.0 if s1_core and tgt_core else 0.0
    name_token_set = fuzz.token_set_ratio(s1_core, tgt_core) / 100.0 if s1_core and tgt_core else 0.0
    
    s1_n_toks = set(s1_core.split())
    tgt_n_toks = set(tgt_core.split())
    if s1_n_toks and tgt_n_toks:
        inter = len(s1_n_toks & tgt_n_toks)
        union = len(s1_n_toks | tgt_n_toks)
        min_toks = min(len(s1_n_toks), len(tgt_n_toks))
        name_token_jaccard = inter / union if union > 0 else 0.0
        name_token_overlap = inter / min_toks if min_toks > 0 else 0.0
    else:
        name_token_jaccard = 0.0
        name_token_overlap = 0.0
        
    l1, l2 = len(s1_core), len(tgt_core)
    name_len_diff = abs(l1 - l2)
    name_len_ratio = (min(l1, l2) / max(l1, l2)) if max(l1, l2) > 0 else 0.0
    
    # Character 3-gram Jaccard
    s1_tri = char_ngrams(s1_core, 3)
    tgt_tri = char_ngrams(tgt_core, 3)
    name_char_3gram_sim = (len(s1_tri & tgt_tri) / len(s1_tri | tgt_tri)) if (s1_tri and tgt_tri) else 0.0

    # 2. Address Features
    addr_has_val = 1.0 if s1_ca and tgt_ca else 0.0
    addr_exact_clean = 1.0 if addr_has_val and s1_ca == tgt_ca else 0.0
    
    if addr_has_val:
        addr_lev_sim = lev.normalized_similarity(s1_ca, tgt_ca)
        addr_jw_sim = jw.similarity(s1_ca, tgt_ca)
        addr_token_sort = fuzz.token_sort_ratio(s1_ca, tgt_ca) / 100.0
        addr_token_set = fuzz.token_set_ratio(s1_ca, tgt_ca) / 100.0
        
        s1_a_toks = set(s1_ca.split())
        tgt_a_toks = set(tgt_ca.split())
        a_inter = len(s1_a_toks & tgt_a_toks)
        a_union = len(s1_a_toks | tgt_a_toks)
        a_min = min(len(s1_a_toks), len(tgt_a_toks))
        addr_token_jaccard = a_inter / a_union if a_union > 0 else 0.0
        addr_token_overlap = a_inter / a_min if a_min > 0 else 0.0
    else:
        addr_lev_sim = 0.0
        addr_jw_sim = 0.0
        addr_token_sort = 0.0
        addr_token_set = 0.0
        addr_token_jaccard = 0.0
        addr_token_overlap = 0.0

    # 3. Structural & Number Features
    if s1_post and tgt_post:
        postal_exact_match = 1.0 if s1_post == tgt_post else 0.0
        postal_mismatch = 1.0 if s1_post != tgt_post else 0.0
    else:
        postal_exact_match = 0.0
        postal_mismatch = 0.0
        
    s1_num_set = set(s1_nums)
    tgt_num_set = set(tgt_nums)
    common_nums = s1_num_set & tgt_num_set
    common_numbers_count = float(len(common_nums))
    
    if s1_nums and tgt_nums:
        primary_number_match = 1.0 if s1_nums[0] == tgt_nums[0] else 0.0
        primary_number_mismatch = 1.0 if s1_nums[0] != tgt_nums[0] else 0.0
    else:
        primary_number_match = 0.0
        primary_number_mismatch = 0.0

    # 4. Cross-Field Features
    country_match = 1.0 if s1_country.lower() == tgt_country.lower() else 0.0
    cross_prod = name_jw_sim * addr_jw_sim
    cross_min = min(name_jw_sim, addr_jw_sim)
    cross_max = max(name_jw_sim, addr_jw_sim)
    name_high_addr_low = 1.0 if (name_jw_sim > 0.88 and addr_jw_sim < 0.45) else 0.0
    core_exact_no_addr = 1.0 if (name_exact_core and not addr_has_val) else 0.0
    
    is_source2 = 1.0 if target_id.startswith('S2-') else 0.0
    is_source3 = 1.0 if target_id.startswith('S3-') else 0.0
    shared_signatures_count = float(shared_keys_count)

    return [
        name_exact_clean,
        name_exact_core,
        name_lev_sim,
        name_jw_sim,
        name_token_sort,
        name_token_set,
        name_token_jaccard,
        name_token_overlap,
        name_len_diff,
        name_len_ratio,
        name_char_3gram_sim,
        addr_has_val,
        addr_exact_clean,
        addr_lev_sim,
        addr_jw_sim,
        addr_token_sort,
        addr_token_set,
        addr_token_jaccard,
        addr_token_overlap,
        postal_exact_match,
        postal_mismatch,
        primary_number_match,
        primary_number_mismatch,
        common_numbers_count,
        country_match,
        cross_prod,
        cross_min,
        cross_max,
        name_high_addr_low,
        core_exact_no_addr,
        is_source2,
        is_source3,
        shared_signatures_count
    ]
