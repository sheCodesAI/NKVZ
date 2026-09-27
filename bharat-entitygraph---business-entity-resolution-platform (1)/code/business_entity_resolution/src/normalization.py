"""
Bharat EntityGraph — Business Entity Resolution Platform
Normalization Module
Conservative, multi-lingual normalization tailored for Indian, US, and European business records.
"""

import re
import unicodedata
import text_unidecode

# Universal & Jurisdiction-Specific Legal Suffixes
LEGAL_SUFFIXES = {
    # Indian Corporate & Commercial
    'pvt', 'private', 'ltd', 'limited', 'enterprises', 'enterprise', 'industries', 'industry',
    'bhandar', 'emporium', 'traders', 'trading', 'works', 'stores', 'store', 'depot',
    'corporation', 'corp', 'solutions', 'solution', 'technologies', 'technology', 'services', 'service',
    'holdings', 'holding', 'ventures', 'associates', 'consulting', 'group', 'company', 'co',
    # US Corporate
    'inc', 'incorporated', 'llc', 'llp', 'pllc', 'pc', 'corp',
    # European / French (Open-Set Test Domain)
    'sarl', 'sas', 'sasu', 'sci', 'sa', 'snc', 'eurl', 'ste', 'sté', 'gie', 'ei', 'eirl',
    'scp', 'selarl', 'earl', 'scic', 'sem', 'groupe', 'compagnie', 'cie'
}

ARTICLES_AND_PREPOSITIONS = {
    'the', 'a', 'an', 'and', 'of', 'for', 'in', 'at',
    'le', 'la', 'les', 'l', 'un', 'une', 'du', 'des', 'de', 'd', 'au', 'aux',
    'shree', 'sri', 'm/s', 'messrs'
}

STREET_ABBREVIATIONS = {
    # English / Global
    'rd': 'road', 'st': 'street', 'ave': 'avenue', 'blvd': 'boulevard',
    'dr': 'drive', 'ct': 'court', 'ln': 'lane', 'pl': 'place', 'sq': 'square',
    'pkwy': 'parkway', 'hwy': 'highway', 'fl': 'floor', 'ste': 'suite', 'apt': 'apartment',
    'bldg': 'building', 'no': 'number', 'nr': 'near', 'opp': 'opposite', 'bhnd': 'behind',
    'sec': 'sector', 'ph': 'phase',
    # French
    'r': 'rue', 'av': 'avenue', 'bd': 'boulevard', 'ch': 'chemin', 'imp': 'impasse',
    'all': 'allee', 'rte': 'route', 'crs': 'cours', 'qu': 'quai', 'pass': 'passage',
    'bat': 'batiment', 'res': 'residence', 'zi': 'zone industrielle', 'za': 'zone activite'
}

SPLIT_DIGIT_LETTER = re.compile(r'(\d+)\s*([a-zA-Z]+)')
NUMBER_RE = re.compile(r'\b\d+\b')
POSTAL_IN_RE = re.compile(r'\b([1-9][0-9]{5})\b')
POSTAL_US_RE = re.compile(r'\b([0-9]{5})(?:-[0-9]{4})?\b')
POSTAL_FR_RE = re.compile(r'\b(0[1-9]|[1-8]\d|9[0-8])\d{3}\b')
PUNCT_RE = re.compile(r'[^a-zA-Z0-9\s]')
MULTI_SPACE_RE = re.compile(r'\s+')
URL_RE = re.compile(r'https?://(?:www\.)?')
DOMAIN_RE = re.compile(r'\.(com|org|net|in|co|io|fr)\b')

def clean_text(s: str) -> str:
    """Conservative Unicode unidecode, lowercase, and punctuation stripping."""
    if not s or s.lower() == 'null':
        return ''
    s = text_unidecode.unidecode(s)
    s = s.lower()
    s = URL_RE.sub('', s)
    s = DOMAIN_RE.sub(' ', s)
    s = SPLIT_DIGIT_LETTER.sub(r'\1 \2', s)
    s = PUNCT_RE.sub(' ', s)
    s = MULTI_SPACE_RE.sub(' ', s).strip()
    return s

def normalize_name(name: str):
    """
    Produces:
    - cleaned_name: lowercase cleaned string
    - core_name: name stripped of legal suffixes and leading articles
    - tokens: list of clean tokens
    """
    cleaned = clean_text(name)
    if not cleaned:
        return '', '', []
    tokens = cleaned.split()
    
    # Strip legal suffixes
    core = [t for t in tokens if t not in LEGAL_SUFFIXES]
    if not core:
        core = tokens
        
    # Strip leading honorifics / articles for core comparison
    if len(core) > 1 and core[0] in ARTICLES_AND_PREPOSITIONS:
        core = core[1:]
        
    core_name = ' '.join(core)
    return cleaned, core_name, tokens

def extract_postal_code(addr: str, country: str = None) -> str:
    """Extracts standard postal / PIN code based on country or general pattern."""
    if not addr:
        return ''
    if country == 'India':
        m = POSTAL_IN_RE.search(addr)
        if m:
            return m.group(1)
    elif country == 'US':
        m = POSTAL_US_RE.search(addr)
        if m:
            return m.group(1)
    elif country == 'France':
        m = POSTAL_FR_RE.search(addr)
        if m:
            return m.group(0)
    # General fallback
    m = re.search(r'\b\d{5,6}\b', addr)
    return m.group(0) if m else ''

def normalize_address(addr: str, country: str = None):
    """
    Produces:
    - cleaned_addr: normalized expanded address string
    - numbers: list of numeric tokens (building numbers, flats, pincodes)
    - postal_code: extracted postal / PIN code
    - tokens: list of address tokens
    """
    cleaned = clean_text(addr)
    if not cleaned:
        return '', [], '', []
        
    raw_tokens = cleaned.split()
    expanded_tokens = [STREET_ABBREVIATIONS.get(t, t) for t in raw_tokens]
    cleaned_addr = ' '.join(expanded_tokens)
    
    numbers = NUMBER_RE.findall(cleaned)
    postal_code = extract_postal_code(addr, country)
    
    return cleaned_addr, numbers, postal_code, expanded_tokens
