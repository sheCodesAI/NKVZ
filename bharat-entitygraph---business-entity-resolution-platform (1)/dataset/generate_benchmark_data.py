#!/usr/bin/env python3
"""
Generate realistic challenge dataset for training, validation, and testing.
Strictly follows official Amazon ML Challenge 2026 specifications:
- Tab-separated (.tsv)
- Columns: entity_id, business_name, business_address, country
- Source prefixes: S1-, S2-, S3-
- Open-set: Train = {US, India}, Test = {US, India, France}
- Noise patterns: abbreviations, legal suffixes, typos, transliteration, missing PINs, landmarks
- Ground truth: source1_entity_id, matched_entity_ids (comma-separated, empty for singletons)
"""

import os
import random
import sys

random.seed(42)

TRAIN_DIR = "dataset/train"
TEST_DIR = "dataset/test"
os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(TEST_DIR, exist_ok=True)

# Sample base entities for India
INDIA_NAMES = [
    ("Reliance Retail", "Pvt Ltd", "Retail"),
    ("Tata Consultancy Services", "Limited", "IT"),
    ("Infosys Technologies", "Ltd", "Software"),
    ("State Bank of India", "", "Banking"),
    ("HDFC Bank", "Ltd", "Banking"),
    ("ICICI Securities", "Private Limited", "Finance"),
    ("Mahindra & Mahindra", "Financial Services", "Automobile"),
    ("Larsen & Toubro", "Infotech Ltd", "Engineering"),
    ("Adani Enterprises", "Ltd", "Trading"),
    ("Bharti Airtel", "Enterprises", "Telecom"),
    ("Wipro Consumer Care", "and Lighting", "FMCG"),
    ("Bajaj Auto", "Holdings Ltd", "Automobile"),
    ("Sun Pharmaceutical", "Industries Ltd", "Pharma"),
    ("Apollo Hospitals", "Enterprise Ltd", "Healthcare"),
    ("Godrej Consumer Products", "Ltd", "FMCG"),
    ("Dabur India", "Limited", "Healthcare"),
    ("Maruti Suzuki", "India Limited", "Automobile"),
    ("Hindustan Unilever", "Trading Co", "FMCG"),
    ("Asian Paints", "Colour Solutions", "Paints"),
    ("Titan Company", "Enterprises", "Retail"),
    ("Shree Ganesh Kirana", "Store", "Grocery"),
    ("Sri Laxmi Textiles", "and Sarees", "Garments"),
    ("Patel Brothers Provision", "Bhandar", "Wholesale"),
    ("Sharma Sweet House", "& Restaurant", "Food"),
    ("Krishna Medical", "and General Stores", "Pharmacy"),
    ("Om Sai Digital Printing", "Services", "Printing"),
    ("Shree Balaji Udyog", "Pvt Ltd", "Manufacturing"),
    ("Apex Diagnostic Centre", "& Path Lab", "Healthcare"),
    ("Venkateshwara Hardware", "and Electricals", "Hardware"),
    ("Gupta Book Depot", "and Stationers", "Retail"),
    ("Swastik Auto Spares", "Works", "Automotive"),
    ("Radha Raman Handlooms", "Emporium", "Textiles"),
    ("Kailash Parbat Pure Veg", "Restaurant", "Hospitality"),
    ("Ambika Jewellers", "Private Limited", "Jewellery"),
    ("Royal Enfield Service", "Centre", "Automotive"),
]

INDIA_ADDRS = [
    ("Plot 42, Electronic City Phase 1", "Bengaluru", "Karnataka", "560100"),
    ("12/A, Nariman Point, Express Towers", "Mumbai", "Maharashtra", "400021"),
    ("Near SBI ATM, Gali No 4, Karol Bagh", "New Delhi", "Delhi", "110005"),
    ("Shop 15, Sector 18 Market", "Noida", "Uttar Pradesh", "201301"),
    ("Opposite City Railway Station, M.G. Road", "Pune", "Maharashtra", "411001"),
    ("Behind Nexus Mall, Koramangala 5th Block", "Bengaluru", "Karnataka", "560095"),
    ("45-B, Anna Salai, Mount Road", "Chennai", "Tamil Nadu", "600002"),
    ("G-10, Ground Floor, Banjara Hills Road No 12", "Hyderabad", "Telangana", "560034"),
    ("Chowk Bazaar, Near Ghanta Ghar", "Surat", "Gujarat", "395003"),
    ("104, Civil Lines, Near Bus Stand", "Jaipur", "Rajasthan", "302006"),
    ("Door No 8-2-293, Jubilee Hills", "Hyderabad", "Telangana", "500033"),
    ("Shop 8, New Market Area", "Bhopal", "Madhya Pradesh", "462001"),
    ("22, Park Street, 3rd Floor", "Kolkata", "West Bengal", "700016"),
    ("NH-8, Near Toll Plaza, Udyog Vihar Phase 4", "Gurugram", "Haryana", "122015"),
    ("Near Old High Court, Mall Road", "Shimla", "Himachal Pradesh", "171001"),
]

# Sample base entities for US
US_NAMES = [
    ("Acme Industrial Solutions", "LLC", "Manufacturing"),
    ("Apex Global Logistics", "Inc.", "Supply Chain"),
    ("Beacon Financial Group", "Corp", "Finance"),
    ("Cascade Software Labs", "Technologies", "Tech"),
    ("Delta Healthcare Partners", "P.C.", "Medical"),
    ("Evergreen Valley Dental", "Associates", "Dental"),
    ("Frontier Energy Systems", "Corporation", "Energy"),
    ("Golden Gate Capital", "Holdings LLC", "Private Equity"),
    ("Horizon Media Group", "Enterprises", "Marketing"),
    ("Ironclad Security Services", "Inc", "Security"),
    ("Juniper Ridge Construction", "Co.", "Construction"),
    ("Keystone Property Management", "LLC", "Real Estate"),
    ("Liberty Auto Body", "& Repair", "Automotive"),
    ("Magnolia Bakery and Cafe", "", "Food"),
    ("Nexus Cloud Technologies", "Corporation", "Cloud"),
    ("Olympic Mountain Sports", "LLC", "Retail"),
    ("Pacific Coast BioLabs", "Inc.", "Biotech"),
    ("Quantum Leap Robotics", "LLC", "Robotics"),
    ("Redwood Wealth Management", "Group", "Finance"),
    ("Summit View Veterinary", "Hospital", "Veterinary"),
]

US_ADDRS = [
    ("100 Montgomery St, Suite 1500", "San Francisco", "CA", "94104"),
    ("350 Fifth Ave, 54th Floor", "New York", "NY", "10118"),
    ("2000 Avenue of the Stars", "Los Angeles", "CA", "90067"),
    ("1200 Smith Street, Suite 2200", "Houston", "TX", "77002"),
    ("500 West Madison Street", "Chicago", "IL", "60661"),
    ("701 Brickell Avenue, Suite 1700", "Miami", "FL", "33131"),
    ("100 Federal Street, 28th Floor", "Boston", "MA", "02110"),
    ("111 Congress Avenue, Suite 400", "Austin", "TX", "78701"),
    ("1301 Second Avenue, Suite 3000", "Seattle", "WA", "98101"),
    ("2500 Peachtree Rd NW", "Atlanta", "GA", "30305"),
]

# Sample base entities for France (Test only open-set)
FRANCE_NAMES = [
    ("Boulangerie Patisserie Paul", "SARL", "Bakery"),
    ("Pharmacie Centrale de Paris", "SELARL", "Pharmacy"),
    ("Cabinet Conseil Dupont", "SAS", "Consulting"),
    ("Transport Express Lyon", "SA", "Logistics"),
    ("Atelier Mecanique Du Nord", "EURL", "Automotive"),
    ("Librairie Des Arts Modernes", "SASU", "Books"),
    ("Societe Civile Immobiliere Riviera", "SCI", "Real Estate"),
    ("Boucherie Traditionnelle Charcuterie", "SARL", "Food"),
    ("Clinique Veterinaire Du Parc", "SCP", "Veterinary"),
    ("Coiffure Style et Beaute", "EIRL", "Salon"),
    ("Menuiserie Generale D'Aquitaine", "SAS", "Carpentry"),
    ("Imprimerie Bordelaise Graphique", "SARL", "Printing"),
    ("Restaurant Le Bistrot De France", "", "Dining"),
    ("Optique Vision Nouvelle", "SAS", "Eyewear"),
    ("Fleuriste Les Jardins De Flore", "EURL", "Florist"),
]

FRANCE_ADDRS = [
    ("15 Rue de la Paix", "Paris", "", "75002"),
    ("42 Avenue des Champs-Elysees", "Paris", "", "75008"),
    ("8 Boulevard Saint-Germain", "Paris", "", "75005"),
    ("25 Rue de la Republique", "Lyon", "", "69002"),
    ("120 Cours Gambetta", "Lyon", "", "69007"),
    ("10 Quai des Belges", "Marseille", "", "13001"),
    ("55 Rue Nationale", "Lille", "", "59800"),
    ("14 Place du Capitole", "Toulouse", "", "31000"),
    ("3 Boulevard Victor Hugo", "Nice", "", "06000"),
    ("88 Rue Sainte-Catherine", "Bordeaux", "", "33000"),
    ("Zone Industrielle Les Paluds, Rue de la Gineste", "Aubagne", "", "13400"),
    ("Allée des Platanes, Batiment B", "Montpellier", "", "34000"),
]

def apply_name_noise(name, country, noise_level=1):
    n = name
    if noise_level == 0:
        return n
    # Abbreviation / suffix transformations
    transformations = [
        ("Pvt Ltd", "Private Limited"),
        ("Private Limited", "Pvt. Ltd."),
        ("Limited", "Ltd."),
        ("Technologies", "Tech"),
        ("Enterprises", "Ent."),
        ("Solutions", "Solns"),
        ("Services", "Serv."),
        ("Corporation", "Corp."),
        ("&", "and"),
        ("and", "&"),
        ("Shree", "Sri"),
        ("Sri", "Shree"),
        ("Kirana", "General Store"),
        ("SARL", "Sté"),
        ("SAS", "Société par actions simplifiée"),
        ("Co.", "Company"),
    ]
    for old, new in transformations:
        if old in n and random.random() < 0.6:
            n = n.replace(old, new)
            break
    
    # Typos or case change
    if random.random() < 0.25:
        n = n.upper() if random.random() < 0.4 else n.lower()
    
    if random.random() < 0.15 and len(n) > 6:
        idx = random.randint(1, len(n) - 2)
        n = n[:idx] + n[idx+1:] # dropped char typo
        
    return n.strip()

def apply_addr_noise(addr_tuple, country, noise_level=1):
    street, city, state, postal = addr_tuple
    if noise_level == 0:
        parts = [street, city, state, postal]
        return ", ".join([p for p in parts if p])
    
    st = street
    # Street abbreviations
    abbr_map = {
        "Road": "Rd", "Street": "St", "Avenue": "Ave", "Boulevard": "Blvd",
        "Phase": "Ph", "Sector": "Sec", "Floor": "Fl", "Suite": "Ste",
        "Opposite": "Opp.", "Near": "Nr", "Behind": "Bhnd", "Rue": "R.",
    }
    for k, v in abbr_map.items():
        if k in st and random.random() < 0.5:
            st = st.replace(k, v)
        elif v in st and random.random() < 0.3:
            st = st.replace(v, k)
            
    # Component dropping
    drop_postal = random.random() < 0.35
    drop_state = random.random() < 0.4
    drop_city = random.random() < 0.1
    
    c_part = "" if drop_city else city
    s_part = "" if drop_state else state
    p_part = "" if drop_postal else postal
    
    # Reorder components occasionally
    parts = [st, c_part, s_part, p_part]
    clean_parts = [p for p in parts if p]
    if random.random() < 0.2 and len(clean_parts) >= 2:
        random.shuffle(clean_parts)
    
    sep = ", " if random.random() < 0.85 else " - "
    return sep.join(clean_parts)

def build_benchmark_dataset():
    print("Generating comprehensive challenge benchmark dataset...")
    
    # 1. Train set (US and India)
    train_s1_records = []
    train_s2_records = []
    train_s3_records = []
    train_ground_truth = []
    
    s1_id_counter = 100000
    s2_id_counter = 200000
    s3_id_counter = 300000
    
    # Generate 1500 Training Source 1 records
    for i in range(1500):
        s1_id = f"S1-{s1_id_counter}"
        s1_id_counter += 1
        
        country = "India" if random.random() < 0.55 else "US"
        name_pool = INDIA_NAMES if country == "India" else US_NAMES
        addr_pool = INDIA_ADDRS if country == "India" else US_ADDRS
        
        base_name_item = random.choice(name_pool)
        biz_code = f"#{s1_id_counter % 2000 + 1}"
        raw_name = f"{base_name_item[0]} {biz_code} {base_name_item[1]}".strip()
        raw_addr_tuple = random.choice(addr_pool)
        base_addr = (f"Unit {biz_code}, {raw_addr_tuple[0]}", raw_addr_tuple[1], raw_addr_tuple[2], raw_addr_tuple[3])
        
        s1_name = apply_name_noise(raw_name, country, noise_level=random.choice([0, 1]))
        s1_addr = apply_addr_noise(base_addr, country, noise_level=random.choice([0, 1]))
        train_s1_records.append((s1_id, s1_name, s1_addr, country))
        
        # Decide match pattern:
        # 12% singleton (no match)
        # 55% matches in both S2 and S3 (multi-match across sources)
        # 20% matches in S2 only
        # 13% matches in S3 only
        r = random.random()
        matched_ids = []
        
        if r < 0.12:
            # Singleton!
            pass
        elif r < 0.67:
            # Matches in both S2 and S3
            s2_id = f"S2-{s2_id_counter}"
            s2_id_counter += 1
            s2_name = apply_name_noise(raw_name, country, noise_level=1)
            s2_addr = apply_addr_noise(base_addr, country, noise_level=1)
            train_s2_records.append((s2_id, s2_name, s2_addr, country))
            matched_ids.append(s2_id)
            
            s3_id = f"S3-{s3_id_counter}"
            s3_id_counter += 1
            s3_name = apply_name_noise(raw_name, country, noise_level=1)
            s3_addr = apply_addr_noise(base_addr, country, noise_level=1)
            train_s3_records.append((s3_id, s3_name, s3_addr, country))
            matched_ids.append(s3_id)
        elif r < 0.87:
            # S2 only
            s2_id = f"S2-{s2_id_counter}"
            s2_id_counter += 1
            s2_name = apply_name_noise(raw_name, country, noise_level=1)
            s2_addr = apply_addr_noise(base_addr, country, noise_level=1)
            train_s2_records.append((s2_id, s2_name, s2_addr, country))
            matched_ids.append(s2_id)
        else:
            # S3 only
            s3_id = f"S3-{s3_id_counter}"
            s3_id_counter += 1
            s3_name = apply_name_noise(raw_name, country, noise_level=1)
            s3_addr = apply_addr_noise(base_addr, country, noise_level=1)
            train_s3_records.append((s3_id, s3_name, s3_addr, country))
            matched_ids.append(s3_id)
            
        train_ground_truth.append((s1_id, ",".join(matched_ids)))

    # Add realistic unlinked distractors into S2 and S3
    for _ in range(300):
        country = "India" if random.random() < 0.55 else "US"
        name_pool = INDIA_NAMES if country == "India" else US_NAMES
        addr_pool = INDIA_ADDRS if country == "India" else US_ADDRS
        b_name = f"Distractor {random.choice(name_pool)[0]} Store"
        b_addr = apply_addr_noise(random.choice(addr_pool), country, noise_level=1)
        
        s2_id = f"S2-{s2_id_counter}"
        s2_id_counter += 1
        train_s2_records.append((s2_id, b_name, b_addr, country))
        
        s3_id = f"S3-{s3_id_counter}"
        s3_id_counter += 1
        train_s3_records.append((s3_id, b_name + " Enterprises", b_addr, country))

    # Write training files
    def write_tsv(filepath, header, rows):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\t".join(header) + "\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")

    entity_header = ["entity_id", "business_name", "business_address", "country"]
    write_tsv(f"{TRAIN_DIR}/train_source1.tsv", entity_header, train_s1_records)
    write_tsv(f"{TRAIN_DIR}/train_source2.tsv", entity_header, train_s2_records)
    write_tsv(f"{TRAIN_DIR}/train_source3.tsv", entity_header, train_s3_records)
    write_tsv(f"{TRAIN_DIR}/train_ground_truth.tsv", ["source1_entity_id", "matched_entity_ids"], train_ground_truth)

    # 2. Test set (India, US, and OPEN-SET France!)
    test_s1_records = []
    test_s2_records = []
    test_s3_records = []
    test_ground_truth_shadow = {} # For internal validation benchmark

    # Generate 1200 Test entities (450 India, 450 US, 300 France)
    countries_to_generate = ["India"] * 450 + ["US"] * 450 + ["France"] * 300
    random.shuffle(countries_to_generate)

    for country in countries_to_generate:
        s1_id = f"S1-{s1_id_counter}"
        s1_id_counter += 1
        
        if country == "India":
            name_pool, addr_pool = INDIA_NAMES, INDIA_ADDRS
        elif country == "US":
            name_pool, addr_pool = US_NAMES, US_ADDRS
        else:
            name_pool, addr_pool = FRANCE_NAMES, FRANCE_ADDRS
            
        base_name_item = random.choice(name_pool)
        biz_code = f"#{s1_id_counter % 2000 + 1}"
        raw_name = f"{base_name_item[0]} {biz_code} {base_name_item[1]}".strip()
        raw_addr_tuple = random.choice(addr_pool)
        base_addr = (f"Unit {biz_code}, {raw_addr_tuple[0]}", raw_addr_tuple[1], raw_addr_tuple[2], raw_addr_tuple[3])
        
        s1_name = apply_name_noise(raw_name, country, noise_level=random.choice([0, 1]))
        s1_addr = apply_addr_noise(base_addr, country, noise_level=random.choice([0, 1]))
        test_s1_records.append((s1_id, s1_name, s1_addr, country))
        
        r = random.random()
        matched_ids = []
        if r < 0.08:
            # Singleton in test
            pass
        elif r < 0.65:
            # Both S2 and S3
            s2_id = f"S2-{s2_id_counter}"
            s2_id_counter += 1
            s2_name = apply_name_noise(raw_name, country, noise_level=1)
            s2_addr = apply_addr_noise(base_addr, country, noise_level=1)
            test_s2_records.append((s2_id, s2_name, s2_addr, country))
            matched_ids.append(s2_id)
            
            s3_id = f"S3-{s3_id_counter}"
            s3_id_counter += 1
            s3_name = apply_name_noise(raw_name, country, noise_level=1)
            s3_addr = apply_addr_noise(base_addr, country, noise_level=1)
            test_s3_records.append((s3_id, s3_name, s3_addr, country))
            matched_ids.append(s3_id)
        elif r < 0.85:
            # S2 only
            s2_id = f"S2-{s2_id_counter}"
            s2_id_counter += 1
            s2_name = apply_name_noise(raw_name, country, noise_level=1)
            s2_addr = apply_addr_noise(base_addr, country, noise_level=1)
            test_s2_records.append((s2_id, s2_name, s2_addr, country))
            matched_ids.append(s2_id)
        else:
            # S3 only
            s3_id = f"S3-{s3_id_counter}"
            s3_id_counter += 1
            s3_name = apply_name_noise(raw_name, country, noise_level=1)
            s3_addr = apply_addr_noise(base_addr, country, noise_level=1)
            test_s3_records.append((s3_id, s3_name, s3_addr, country))
            matched_ids.append(s3_id)
            
        test_ground_truth_shadow[s1_id] = matched_ids

    # Add distractors to test
    for _ in range(250):
        country = random.choice(["India", "US", "France"])
        if country == "India":
            name_pool, addr_pool = INDIA_NAMES, INDIA_ADDRS
        elif country == "US":
            name_pool, addr_pool = US_NAMES, US_ADDRS
        else:
            name_pool, addr_pool = FRANCE_NAMES, FRANCE_ADDRS
        b_name = f"Global {random.choice(name_pool)[0]}"
        b_addr = apply_addr_noise(random.choice(addr_pool), country, noise_level=1)
        
        s2_id = f"S2-{s2_id_counter}"
        s2_id_counter += 1
        test_s2_records.append((s2_id, b_name, b_addr, country))
        
        s3_id = f"S3-{s3_id_counter}"
        s3_id_counter += 1
        test_s3_records.append((s3_id, b_name + " Trading", b_addr, country))

    # Shuffle test targets
    random.shuffle(test_s2_records)
    random.shuffle(test_s3_records)

    write_tsv(f"{TEST_DIR}/test_source1.tsv", entity_header, test_s1_records)
    write_tsv(f"{TEST_DIR}/test_source2.tsv", entity_header, test_s2_records)
    write_tsv(f"{TEST_DIR}/test_source3.tsv", entity_header, test_s3_records)

    print(f"Generated Training Data:")
    print(f"  Source 1: {len(train_s1_records):,} entities")
    print(f"  Source 2: {len(train_s2_records):,} entities")
    print(f"  Source 3: {len(train_s3_records):,} entities")
    print(f"  Ground Truth: {len(train_ground_truth):,} pairs")
    print(f"Generated Test Data (Open-Set including France):")
    print(f"  Source 1: {len(test_s1_records):,} entities")
    print(f"  Source 2: {len(test_s2_records):,} entities")
    print(f"  Source 3: {len(test_s3_records):,} entities")

if __name__ == "__main__":
    build_benchmark_dataset()
