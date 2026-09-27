"""
Bharat EntityGraph — Business Entity Resolution Platform
Submission Exporter Module
Outputs competition-compliant tab-separated files:
- output/matching_results.tsv
- output/candidate_pairs.tsv
"""

import os
from typing import Dict, List, Tuple

def write_competition_submissions(
    ordered_s1_ids: List[str],
    candidates_dict: Dict[str, List[str]],
    matches_dict: Dict[str, List[str]],
    output_dir: str = "output"
) -> Tuple[str, str]:
    """
    Writes matching_results.tsv and candidate_pairs.tsv strictly conforming to the
    official challenge evaluation schema.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    matching_path = os.path.join(output_dir, "matching_results.tsv")
    candidate_path = os.path.join(output_dir, "candidate_pairs.tsv")
    
    # 1. Write matching_results.tsv
    with open(matching_path, "w", encoding="utf-8") as f:
        f.write("source1_entity_id\tmatched_entity_ids\n")
        for s1_id in ordered_s1_ids:
            matches = matches_dict.get(s1_id, [])
            match_str = ",".join(matches)
            f.write(f"{s1_id}\t{match_str}\n")
            
    # 2. Write candidate_pairs.tsv
    with open(candidate_path, "w", encoding="utf-8") as f:
        f.write("source1_entity_id\tcandidate_entity_ids\n")
        for s1_id in ordered_s1_ids:
            cands = candidates_dict.get(s1_id, [])
            # Guarantee every match is included in candidates
            matches = matches_dict.get(s1_id, [])
            all_cands = list(dict.fromkeys(cands + matches))
            cand_str = ",".join(all_cands)
            f.write(f"{s1_id}\t{cand_str}\n")
            
    return matching_path, candidate_path

from typing import Tuple
