"""
Bharat EntityGraph — Business Entity Resolution Platform
Entity Graph Reconstruction Module
Reconstructs canonical business identities and multi-source evidence graphs from resolution decisions.
"""

from typing import Dict, List, Any, Tuple

def reconstruct_canonical_entity(
    s1_id: str,
    s1_record: Tuple[str, str, str],
    matched_targets: List[Tuple[str, Tuple[str, str, str], float]],
    unresolved_cands: List[Tuple[str, Tuple[str, str, str], float]] = None
) -> Dict[str, Any]:
    """
    Synthesizes a Canonical Business Node and its star-topology resolution graph.
    s1_record: (name, address, country)
    matched_targets: [(tgt_id, (name, addr, country), confidence), ...]
    """
    s1_name, s1_addr, s1_country = s1_record
    
    # Derive canonical attributes
    canonical_name = s1_name
    canonical_addr = s1_addr
    
    # Calculate aggregate confidence
    if matched_targets:
        avg_conf = sum(t[2] for t in matched_targets) / len(matched_targets)
    else:
        avg_conf = 1.0 # True singleton confidence
        
    nodes = [
        {
            "id": s1_id,
            "label": s1_name,
            "source": "Source 1 (Reference)",
            "type": "reference",
            "address": s1_addr,
            "country": s1_country
        }
    ]
    
    edges = []
    
    for tgt_id, (t_name, t_addr, t_country), conf in matched_targets:
        src = "Source 2" if tgt_id.startswith("S2-") else "Source 3"
        nodes.append({
            "id": tgt_id,
            "label": t_name,
            "source": src,
            "type": "match",
            "address": t_addr,
            "country": t_country,
            "confidence": round(conf, 4)
        })
        edges.append({
            "source": s1_id,
            "target": tgt_id,
            "confidence": round(conf, 4),
            "status": "ACCEPTED"
        })
        
    alternatives = []
    if unresolved_cands:
        for c_id, (c_name, c_addr, c_country), conf in unresolved_cands:
            src = "Source 2" if c_id.startswith("S2-") else "Source 3"
            alternatives.append({
                "id": c_id,
                "label": c_name,
                "source": src,
                "address": c_addr,
                "confidence": round(conf, 4),
                "reason": "Below decision threshold"
            })

    return {
        "canonical_id": f"CANONICAL-{s1_id.replace('S1-', '')}",
        "canonical_name": canonical_name,
        "canonical_address": canonical_addr,
        "country": s1_country,
        "is_singleton": len(matched_targets) == 0,
        "match_count": len(matched_targets),
        "overall_confidence": round(avg_conf, 4),
        "graph_nodes": nodes,
        "graph_edges": edges,
        "alternatives": alternatives
    }
