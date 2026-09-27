"""
Bharat EntityGraph — Business Entity Resolution Platform
Multi-Strategy Compound Blocking Module
Maximizes candidate recall ceiling while maintaining strict candidate reduction ratios.
"""

import collections
from typing import Dict, List, Set, Tuple
import normalization as norm

COMMON_ADDR_STOPWORDS = {
    'street', 'road', 'avenue', 'boulevard', 'drive', 'court', 'lane', 'place',
    'circle', 'way', 'trail', 'parkway', 'highway', 'suite', 'floor', 'apartment',
    'building', 'room', 'number', 'near', 'opposite', 'behind', 'block', 'sector',
    'phase', 'plot', 'flat', 'door', 'fl', 'no', 'unit', 'north', 'south', 'east', 'west',
    'india', 'us', 'usa', 'state', 'district', 'city', 'nagar', 'colony', 'marg', 'gali',
    'bazaar', 'chowk', 'france', 'rue', 'avenue', 'boulevard', 'chemin', 'cours', 'quai'
}

def extract_blocking_signatures(clean_name: str, core_name: str, clean_addr: str, 
                                numbers: List[str], postal: str, country: str) -> Set[Tuple[str, str]]:
    """Generates rich, complementary multi-attribute blocking signatures."""
    keys = set()
    n_tokens = core_name.split()
    a_tokens = clean_addr.split()
    c_tag = country.lower() if country else 'global'
    
    # 1. Exact core brand name + country
    if len(core_name) >= 3:
        keys.add(('core_n', f"{core_name}_{c_tag}"))
        
    # 2. Compact name (no whitespace) + country
    compact = ''.join(n_tokens)
    if len(compact) >= 4:
        keys.add(('compact_n', f"{compact}_{c_tag}"))
        keys.add(('sort_compact_n', f"{''.join(sorted(n_tokens))}_{c_tag}"))
        
    # 3. Sorted Name Tokens (handles word transposition) + country
    if len(n_tokens) >= 2:
        sorted_name = ' '.join(sorted(n_tokens))
        keys.add(('sort_n', f"{sorted_name}_{c_tag}"))
        # First 2 tokens bigram
        keys.add(('n_bigram', f"{n_tokens[0]}_{n_tokens[1]}_{c_tag}"))
    elif len(n_tokens) == 1 and len(n_tokens[0]) >= 3:
        keys.add(('n_single', f"{n_tokens[0]}_{c_tag}"))
        
    # 4. Significant distinct name tokens + country
    for t in n_tokens:
        if len(t) >= 4 and t not in norm.LEGAL_SUFFIXES and t not in norm.ARTICLES_AND_PREPOSITIONS:
            keys.add(('n_sig_token', f"{t}_{c_tag}"))
            
    # 5. Postal / PIN code + First Name Token
    if postal and n_tokens:
        keys.add(('postal_name', f"{postal}_{n_tokens[0]}"))
        if len(n_tokens) >= 2:
            keys.add(('postal_name2', f"{postal}_{n_tokens[1]}"))
            
    # 6. Primary Street/Building Number + First Name Token
    if numbers and n_tokens:
        primary_num = numbers[0]
        keys.add(('num_name', f"{primary_num}_{n_tokens[0]}_{c_tag}"))
        
    # 7. Character 3-Gram Signatures for Typo & Transliteration Resilience
    if len(core_name) >= 6:
        # First 3-gram and second 3-gram prefix
        tri1 = core_name[:3]
        tri2 = core_name[3:6]
        keys.add(('char_tri', f"{tri1}_{tri2}_{c_tag}"))
        
    # 8. Rare address tokens + Name token
    sig_addr = [w for w in a_tokens if w not in COMMON_ADDR_STOPWORDS and len(w) >= 4 and not w.isdigit()]
    if sig_addr and n_tokens:
        for aw in sig_addr[:2]:
            keys.add(('addr_name', f"{aw}_{n_tokens[0]}_{c_tag}"))
            
    return keys

class MultiStrategyInvertedIndex:
    """Inverted index with token-frequency bounding to guarantee fast, high-recall blocking."""
    
    def __init__(self, max_key_frequency: int = 400):
        self.max_key_frequency = max_key_frequency
        self.index: Dict[Tuple[str, str], List[str]] = collections.defaultdict(list)
        self.target_cache: Dict[str, Tuple[str, str, str, List[str], str, str]] = {}
        
    def index_target_records(self, target_records: Dict[str, Tuple[str, str, str]]):
        """Indexes target records (S2 and S3)."""
        for tid, (raw_name, raw_addr, country) in target_records.items():
            cn, core_n, _ = norm.normalize_name(raw_name)
            ca, nums, postal, _ = norm.normalize_address(raw_addr, country)
            self.target_cache[tid] = (cn, core_n, ca, nums, postal, country)
            
            keys = extract_blocking_signatures(cn, core_name=core_n, clean_addr=ca, 
                                              numbers=nums, postal=postal, country=country)
            for k in keys:
                self.index[k].append(tid)
                
        # Frequency pruning for high-cardinality stop-keys
        pruned_count = 0
        for k in list(self.index.keys()):
            if len(self.index[k]) > self.max_key_frequency:
                del self.index[k]
                pruned_count += 1
                
        return len(self.index), pruned_count

    def retrieve_candidates(self, s1_id: str, raw_name: str, raw_addr: str, 
                            country: str, top_k: int = 35) -> List[Tuple[str, int]]:
        """
        Retrieves top candidate target entity IDs ranked by shared key support.
        Returns list of (candidate_id, shared_key_count).
        """
        cn, core_n, _ = norm.normalize_name(raw_name)
        ca, nums, postal, _ = norm.normalize_address(raw_addr, country)
        keys = extract_blocking_signatures(cn, core_name=core_n, clean_addr=ca, 
                                          numbers=nums, postal=postal, country=country)
                                          
        cand_counts = collections.Counter()
        for k in keys:
            if k in self.index:
                cand_counts.update(self.index[k])
                
        if not cand_counts:
            return []
            
        # Return top_k candidates with highest shared signature support
        return cand_counts.most_common(top_k)
