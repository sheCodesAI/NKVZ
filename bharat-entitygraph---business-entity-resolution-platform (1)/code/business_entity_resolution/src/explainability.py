"""
Bharat EntityGraph — Business Entity Resolution Platform
Explainability & Evidence Layer
Provides feature attribution, human-in-the-loop confidence triage, and diagnostic explanations.
"""

from typing import Dict, List, Any
import rapidfuzz.distance.JaroWinkler as jw
import rapidfuzz.distance.Levenshtein as lev
import rapidfuzz.fuzz as fuzz

def generate_pair_explanation(
    s1_name: str, s1_addr: str, s1_country: str,
    tgt_name: str, tgt_addr: str, tgt_country: str,
    confidence: float, threshold: float = 0.70
) -> Dict[str, Any]:
    """Generates a complete, interpretable explainability card for a candidate pair."""
    name_jw = jw.similarity(s1_name.lower(), tgt_name.lower())
    addr_jw = jw.similarity(s1_addr.lower(), tgt_addr.lower())
    token_sort = fuzz.token_sort_ratio(s1_name.lower(), tgt_name.lower()) / 100.0
    
    country_match = s1_country.lower() == tgt_country.lower()
    
    evidence_items = []
    if name_jw > 0.85:
        evidence_items.append(f"Strong Name Similarity ({name_jw:.2f})")
    elif name_jw > 0.65:
        evidence_items.append(f"Moderate Name Similarity ({name_jw:.2f})")
    else:
        evidence_items.append(f"Low Name Similarity ({name_jw:.2f})")
        
    if addr_jw > 0.80:
        evidence_items.append(f"Strong Address Alignment ({addr_jw:.2f})")
    elif addr_jw > 0.50:
        evidence_items.append(f"Partial Address Match ({addr_jw:.2f})")
        
    if country_match:
        evidence_items.append(f"Country Agreement: {s1_country}")
    else:
        evidence_items.append(f"Country Discrepancy: {s1_country} vs {tgt_country}")
        
    if confidence >= 0.80:
        status = "AUTO_ACCEPTED"
        badge_color = "emerald"
    elif confidence >= threshold:
        status = "ACCEPTED"
        badge_color = "blue"
    elif confidence >= 0.45:
        status = "REVIEW_REQUIRED"
        badge_color = "amber"
    else:
        status = "REJECTED"
        badge_color = "rose"

    return {
        "confidence": round(confidence, 4),
        "status": status,
        "badge_color": badge_color,
        "name_jw": round(name_jw, 3),
        "addr_jw": round(addr_jw, 3),
        "token_sort": round(token_sort, 3),
        "country_match": country_match,
        "evidence_list": evidence_items,
        "decision_summary": f"{status} (Score: {confidence:.2f}, Threshold: {threshold:.2f})"
    }
