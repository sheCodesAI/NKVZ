"""
Bharat EntityGraph — Business Entity Resolution Platform
Data Loader Module
Robust tab-separated (.tsv) reader supporting streaming and country partitioning.
"""

import os
from typing import Dict, List, Tuple, Generator, Set

def load_records_tsv(path: str, country_filter: str = None) -> Dict[str, Tuple[str, str, str]]:
    """
    Reads TSV with header: entity_id, business_name, business_address, country.
    Returns: dict of entity_id -> (business_name, business_address, country)
    """
    records = {}
    if not os.path.exists(path):
        return records
        
    with open(path, 'r', encoding='utf-8') as f:
        header = f.readline().rstrip('\r\n').split('\t')
        for line in f:
            line = line.rstrip('\r\n')
            if not line:
                continue
            parts = line.split('\t')
            eid = parts[0]
            name = parts[1] if len(parts) > 1 else ''
            addr = parts[2] if len(parts) > 2 else ''
            country = parts[3] if len(parts) > 3 else ''
            
            if country_filter is None or country == country_filter:
                records[eid] = (name, addr, country)
                
    return records

def load_ground_truth_tsv(path: str) -> Dict[str, Set[str]]:
    """
    Reads ground truth TSV: source1_entity_id, matched_entity_ids.
    Returns: dict of source1_entity_id -> set of matched_entity_ids
    """
    gt = {}
    if not os.path.exists(path):
        return gt
        
    with open(path, 'r', encoding='utf-8') as f:
        f.readline() # Header
        for line in f:
            line = line.rstrip('\r\n')
            if not line:
                continue
            parts = line.split('\t')
            s1_id = parts[0]
            mids = parts[1].split(',') if len(parts) > 1 and parts[1].strip() else []
            gt[s1_id] = set(mids)
            
    return gt

def stream_source1_entities(path: str) -> Generator[Tuple[str, str, str, str], None, None]:
    """Yields (entity_id, business_name, business_address, country) line by line."""
    with open(path, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            line = line.rstrip('\r\n')
            if not line:
                continue
            parts = line.split('\t')
            eid = parts[0]
            name = parts[1] if len(parts) > 1 else ''
            addr = parts[2] if len(parts) > 2 else ''
            country = parts[3] if len(parts) > 3 else ''
            yield eid, name, addr, country
