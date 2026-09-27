import { SystemInfo, DataProfile, ExperimentRun, ErrorCase, FeatureDef, CanonicalEntity } from './types';

export const initialSystemInfo: SystemInfo = {
  title: "Bharat EntityGraph",
  tagline: "Reconstructing Business Identity from Fragmented Data",
  competition: "Amazon ML Challenge 2026",
  version: "2.0.0",
  validator_status: "PASS",
  compliance: {
    zero_external_apis: true,
    permissive_license: "MIT License",
    max_parameters: "<100K (Under 8B Ceiling)",
    open_set_generalized: true
  }
};

export const initialDataProfile: DataProfile = {
  train: {
    source1_count: 1500,
    source2_count: 1399,
    source3_count: 1289,
    ground_truth_count: 1500,
    countries: ["India", "US"],
    country_distribution: {
      "India": 825,
      "US": 675
    }
  },
  test: {
    source1_count: 1200,
    source2_count: 1184,
    source3_count: 1123,
    predicted_singletons: 86,
    predicted_matched_entities: 1114,
    total_links: 1785,
    countries: ["India", "France", "US"],
    country_distribution: {
      "India": 450,
      "France": 300,
      "US": 450
    }
  },
  metrics: {
    macro_f05: 0.9869,
    precision: 0.9976,
    recall: 0.9744,
    macro_f1: 0.9798,
    candidate_recall: 0.9791,
    singleton_accuracy: 1.0000,
    optimal_s2_threshold: 0.05,
    optimal_s3_threshold: 0.05
  }
};

export const initialFeatures: FeatureDef[] = [
  { name: "name_jw_sim", group: "Name", importance: 0.18, desc: "RapidFuzz Jaro-Winkler similarity on legal-suffix-stripped core brand stems" },
  { name: "name_exact_core", group: "Name", importance: 0.16, desc: "Binary flag for exact core brand stem equality after token normalization" },
  { name: "name_exact_clean", group: "Name", importance: 0.14, desc: "Binary flag for exact lowercase cleaned name equality" },
  { name: "postal_exact_match", group: "Structural", importance: 0.13, desc: "Exact 6-digit Indian PIN or 5-digit US/French postal code match" },
  { name: "name_token_sort", group: "Name", importance: 0.11, desc: "Token sort ratio handling word order transpositions and variations" },
  { name: "name_token_jaccard", group: "Name", importance: 0.09, desc: "Jaccard similarity index across significant brand tokens" },
  { name: "primary_number_match", group: "Structural", importance: 0.08, desc: "Primary street, unit, or municipal building number exact equality" },
  { name: "addr_jw_sim", group: "Address", importance: 0.07, desc: "Jaro-Winkler similarity across cleaned street and locality tokens" },
  { name: "cross_prod", group: "Interaction", importance: 0.04, desc: "Non-linear interaction term (name_jw * addr_jw)" }
];

export const initialRuns: ExperimentRun[] = [
  {
    run_id: "EXP-01",
    name: "SuperBlocking Baseline + LightGBM (Default Tau)",
    timestamp: "2026-09-26 14:20:10",
    model: "LightGBM GBDT",
    features_count: 28,
    tau_s2: 0.50,
    tau_s3: 0.50,
    macro_f05: 0.9687,
    precision: 0.9815,
    recall: 0.9521,
    candidate_recall: 0.9648,
    singleton_acc: 0.9650,
    status: "COMPLETED"
  },
  {
    run_id: "EXP-02",
    name: "LightGBM + Source-Aware Dual Calibration",
    timestamp: "2026-09-26 18:45:22",
    model: "LightGBM GBDT",
    features_count: 28,
    tau_s2: 0.75,
    tau_s3: 0.80,
    macro_f05: 0.9745,
    precision: 0.9920,
    recall: 0.9425,
    candidate_recall: 0.9648,
    singleton_acc: 0.9780,
    status: "COMPLETED"
  },
  {
    run_id: "EXP-03",
    name: "Ablation: Brand Name Features Only",
    timestamp: "2026-09-26 20:12:05",
    model: "LightGBM GBDT",
    features_count: 11,
    tau_s2: 0.65,
    tau_s3: 0.65,
    macro_f05: 0.8897,
    precision: 0.8859,
    recall: 0.8734,
    candidate_recall: 0.9648,
    singleton_acc: 0.8920,
    status: "COMPLETED"
  },
  {
    run_id: "EXP-04",
    name: "Ablation: Address Locality Features Only",
    timestamp: "2026-09-26 21:05:40",
    model: "LightGBM GBDT",
    features_count: 10,
    tau_s2: 0.60,
    tau_s3: 0.60,
    macro_f05: 0.9191,
    precision: 0.9690,
    recall: 0.8494,
    candidate_recall: 0.9648,
    singleton_acc: 0.9310,
    status: "COMPLETED"
  },
  {
    run_id: "EXP-05",
    name: "Bharat EntityGraph Production Engine (Enhanced 33 Feats + Bipartite Exclusivity)",
    timestamp: "2026-09-27 11:01:00",
    model: "LightGBM GBDT (<100K Params)",
    features_count: 33,
    tau_s2: 0.05,
    tau_s3: 0.05,
    macro_f05: 0.9869,
    precision: 0.9976,
    recall: 0.9744,
    candidate_recall: 0.9791,
    singleton_acc: 1.0000,
    status: "PRODUCTION_ACTIVE"
  }
];

export const initialErrors: ErrorCase[] = [
  {
    case_id: "ERR-001",
    category: "Transliteration Variance (Indian Script)",
    source1_name: "Shree Ganesh Kirana Store #1001",
    source1_addr: "Unit #1001, Near SBI ATM, Gali No 4, Karol Bagh, New Delhi, Delhi, 110005",
    target_id: "S2-200042",
    target_name: "Sri Ganesha General Stores #1001",
    target_addr: "Unit #1001, Gali 4, Karol Bagh, 110005",
    country: "India",
    actual: "MATCH",
    predicted: "MATCH",
    confidence: 0.92,
    insight: "Phonetic unidecoding unifies Shree/Sri and transliteration suffixes; PIN match confirms resolution."
  },
  {
    case_id: "ERR-002",
    category: "Corporate Legal Suffix Transformation",
    source1_name: "Tata Consultancy Services #1002 Limited",
    source1_addr: "Unit #1002, Plot 42, Electronic City Phase 1, Bengaluru, Karnataka, 560100",
    target_id: "S3-300109",
    target_name: "TCS #1002 Tech Pvt Ltd",
    target_addr: "Unit #1002, Electronic City Ph 1, 560100",
    country: "India",
    actual: "MATCH",
    predicted: "MATCH",
    confidence: 0.89,
    insight: "Core brand stem 'tata consultancy services' handles acronym 'TCS' with shared postal PIN code."
  },
  {
    case_id: "ERR-003",
    category: "Address Component Reordering & Abbreviation",
    source1_name: "Acme Industrial Solutions #1003 LLC",
    source1_addr: "Unit #1003, 500 West Madison Street, Chicago, IL, 60661",
    target_id: "S2-200318",
    target_name: "Acme Industrial Solns #1003",
    target_addr: "Unit #1003, Chicago, 60661, 500 W Madison St, Suite 400",
    country: "US",
    actual: "MATCH",
    predicted: "MATCH",
    confidence: 0.95,
    insight: "Token sort and primary unit number #1003 alignment robustly overcomes street token transpositions."
  },
  {
    case_id: "ERR-004",
    category: "Open-Set French Commercial Registration",
    source1_name: "Pharmacie Centrale de Paris #1004 SELARL",
    source1_addr: "Unit #1004, 15 Rue de la Paix, Paris, 75002",
    target_id: "S3-300481",
    target_name: "Pharmacie Centrale de Paris #1004 Sté",
    target_addr: "Unit #1004, 15 R. de la Paix, 75002",
    country: "France",
    actual: "MATCH",
    predicted: "MATCH",
    confidence: 0.96,
    insight: "Unseen country handled seamlessly by French suffix stripping ('selarl', 'ste') and 5-digit postal code matching."
  },
  {
    case_id: "ERR-005",
    category: "Singleton True Negative Protection",
    source1_name: "Radha Raman Handlooms Emporium #100003",
    source1_addr: "Unit #100003, 45-B, Anna Salai, Mount Road, Chennai, Tamil Nadu, 600002",
    target_id: "S2-200599 (Distractor)",
    target_name: "Distractor Radha Raman Handlooms Store",
    target_addr: "100 Montgomery St, Suite 1500, San Francisco, CA, 94104",
    country: "India",
    actual: "SINGLETON (NO MATCH)",
    predicted: "SINGLETON (NO MATCH)",
    confidence: 0.02,
    insight: "Thresholding and country/postal conflict correctly rejects look-alike brand distractor, earning perfect 1.0 entity score."
  }
];

export const sampleCanonicalEntities: CanonicalEntity[] = [
  {
    canonical_id: "CANONICAL-101500",
    canonical_name: "ICICI Securities #1501 Private Limited",
    canonical_address: "Unit #1501, Shop 15, Sector 18 Market, Noida, Uttar Pradesh, 201301",
    country: "India",
    is_singleton: false,
    match_count: 2,
    overall_confidence: 0.94,
    normalized_identity: {
      clean_name: "icici securities 1501 private limited",
      core_brand: "icici securities 1501",
      clean_address: "unit 1501 shop 15 sector 18 market noida uttar pradesh 201301",
      postal_code: "201301",
      primary_numbers: ["1501", "15", "18", "201301"]
    },
    matching_evidence: [
      {
        target_id: "S2-200114",
        target_name: "ICICI Securities #1501 Pvt Ltd",
        target_addr: "Unit #1501, Sec 18 Market, Noida, 201301",
        confidence: 0.95,
        status: "AUTO_ACCEPTED",
        badge_color: "emerald",
        name_jw: 0.98,
        addr_jw: 0.92,
        token_sort: 0.96,
        country_match: true,
        evidence_list: [
          "Strong Core Name Match (0.98)",
          "Exact PIN Code Match (201301)",
          "Primary Unit #1501 Alignment",
          "Country Agreement: India"
        ],
        decision_summary: "AUTO_ACCEPTED (Score: 0.95, Threshold: 0.05)"
      },
      {
        target_id: "S3-300182",
        target_name: "ICICI Securities #1501 Financial Services",
        target_addr: "Unit #1501, Shop 15, Sector 18, Noida",
        confidence: 0.93,
        status: "AUTO_ACCEPTED",
        badge_color: "emerald",
        name_jw: 0.94,
        addr_jw: 0.90,
        token_sort: 0.92,
        country_match: true,
        evidence_list: [
          "Strong Brand Identity Match (0.94)",
          "Unit #1501 and Shop 15 Alignment",
          "Country Agreement: India"
        ],
        decision_summary: "AUTO_ACCEPTED (Score: 0.93, Threshold: 0.05)"
      }
    ],
    graph_nodes: [
      {
        id: "S1-101500",
        label: "ICICI Securities #1501 Private Limited",
        source: "Source 1 (Reference)",
        type: "reference",
        address: "Unit #1501, Shop 15, Sector 18 Market, Noida, Uttar Pradesh, 201301",
        country: "India"
      },
      {
        id: "S2-200114",
        label: "ICICI Securities #1501 Pvt Ltd",
        source: "Source 2",
        type: "match",
        address: "Unit #1501, Sec 18 Market, Noida, 201301",
        country: "India",
        confidence: 0.95
      },
      {
        id: "S3-300182",
        label: "ICICI Securities #1501 Financial Services",
        source: "Source 3",
        type: "match",
        address: "Unit #1501, Shop 15, Sector 18, Noida",
        country: "India",
        confidence: 0.93
      }
    ],
    graph_edges: [
      { source: "S1-101500", target: "S2-200114", confidence: 0.95, status: "ACCEPTED" },
      { source: "S1-101500", target: "S3-300182", confidence: 0.93, status: "ACCEPTED" }
    ],
    alternatives: [
      {
        id: "S2-200991",
        label: "Global ICICI Banking Branch",
        source: "Source 2",
        address: "Express Towers, Mumbai",
        confidence: 0.03,
        reason: "Below decision threshold (Postal and Unit Mismatch)"
      }
    ]
  },
  {
    canonical_id: "CANONICAL-101501",
    canonical_name: "Pharmacie Centrale de Paris #1502 SELARL",
    canonical_address: "Unit #1502, 15 Rue de la Paix, Paris, 75002",
    country: "France",
    is_singleton: false,
    match_count: 2,
    overall_confidence: 0.96,
    normalized_identity: {
      clean_name: "pharmacie centrale de paris 1502 selarl",
      core_brand: "pharmacie centrale de paris 1502",
      clean_address: "unit 1502 15 rue de la paix paris 75002",
      postal_code: "75002",
      primary_numbers: ["1502", "15", "75002"]
    },
    matching_evidence: [
      {
        target_id: "S2-200219",
        target_name: "Pharmacie Centrale de Paris #1502 Sté",
        target_addr: "Unit #1502, 15 R. de la Paix, 75002 Paris",
        confidence: 0.97,
        status: "AUTO_ACCEPTED",
        badge_color: "emerald",
        name_jw: 0.99,
        addr_jw: 0.96,
        token_sort: 0.98,
        country_match: true,
        evidence_list: [
          "Open-Set France Generalization Active",
          "French Legal Suffix Stripped ('selarl', 'ste')",
          "Exact Postal Code Match (75002)",
          "Unit #1502 & Street #15 Alignment"
        ],
        decision_summary: "AUTO_ACCEPTED (Score: 0.97, Threshold: 0.05)"
      }
    ],
    graph_nodes: [
      {
        id: "S1-101501",
        label: "Pharmacie Centrale de Paris #1502 SELARL",
        source: "Source 1 (Reference)",
        type: "reference",
        address: "Unit #1502, 15 Rue de la Paix, Paris, 75002",
        country: "France"
      },
      {
        id: "S2-200219",
        label: "Pharmacie Centrale de Paris #1502 Sté",
        source: "Source 2",
        type: "match",
        address: "Unit #1502, 15 R. de la Paix, 75002 Paris",
        country: "France",
        confidence: 0.97
      }
    ],
    graph_edges: [
      { source: "S1-101501", target: "S2-200219", confidence: 0.97, status: "ACCEPTED" }
    ]
  },
  {
    canonical_id: "CANONICAL-101502",
    canonical_name: "Acme Industrial Solutions #1503 LLC",
    canonical_address: "Unit #1503, 500 West Madison Street, Chicago, IL, 60661",
    country: "US",
    is_singleton: false,
    match_count: 2,
    overall_confidence: 0.95,
    graph_nodes: [
      {
        id: "S1-101502",
        label: "Acme Industrial Solutions #1503 LLC",
        source: "Source 1 (Reference)",
        type: "reference",
        address: "Unit #1503, 500 West Madison Street, Chicago, IL, 60661",
        country: "US"
      },
      {
        id: "S2-200388",
        label: "Acme Industrial Solns #1503",
        source: "Source 2",
        type: "match",
        address: "Unit #1503, 500 W Madison St, Chicago, 60661",
        country: "US",
        confidence: 0.96
      }
    ],
    graph_edges: [
      { source: "S1-101502", target: "S2-200388", confidence: 0.96, status: "ACCEPTED" }
    ]
  },
  {
    canonical_id: "CANONICAL-101503",
    canonical_name: "Radha Raman Handlooms Emporium #1504",
    canonical_address: "Unit #1504, 45-B, Anna Salai, Mount Road, Chennai, Tamil Nadu, 600002",
    country: "India",
    is_singleton: true,
    match_count: 0,
    overall_confidence: 1.0,
    graph_nodes: [
      {
        id: "S1-101503",
        label: "Radha Raman Handlooms Emporium #1504",
        source: "Source 1 (Reference)",
        type: "reference",
        address: "Unit #1504, 45-B, Anna Salai, Mount Road, Chennai, Tamil Nadu, 600002",
        country: "India"
      }
    ],
    graph_edges: [],
    alternatives: [
      {
        id: "S2-200812",
        label: "Global Handloom Store",
        source: "Source 2",
        address: "Delhi",
        confidence: 0.04,
        reason: "True Singleton Protected: Zero candidate exceeded threshold"
      }
    ]
  }
];
