export interface SystemInfo {
  title: string;
  tagline: string;
  competition: string;
  version: string;
  validator_status: string;
  compliance: {
    zero_external_apis: boolean;
    permissive_license: string;
    max_parameters: string;
    open_set_generalized: boolean;
  };
}

export interface DataProfile {
  train: {
    source1_count: number;
    source2_count: number;
    source3_count: number;
    ground_truth_count: number;
    countries: string[];
    country_distribution: Record<string, number>;
  };
  test: {
    source1_count: number;
    source2_count: number;
    source3_count: number;
    predicted_singletons: number;
    predicted_matched_entities: number;
    total_links: number;
    countries: string[];
    country_distribution: Record<string, number>;
  };
  metrics: {
    macro_f05: number;
    precision: number;
    recall: number;
    macro_f1: number;
    candidate_recall: number;
    singleton_accuracy: number;
    optimal_s2_threshold: number;
    optimal_s3_threshold: number;
  };
}

export interface GraphNode {
  id: string;
  label: string;
  source: string;
  type: 'reference' | 'match';
  address: string;
  country: string;
  confidence?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  confidence: number;
  status: string;
}

export interface CanonicalEntity {
  canonical_id: string;
  canonical_name: string;
  canonical_address: string;
  country: string;
  is_singleton: boolean;
  match_count: number;
  overall_confidence: number;
  normalized_identity?: {
    clean_name: string;
    core_brand: string;
    clean_address: string;
    postal_code: string;
    primary_numbers: string[];
  };
  matching_evidence?: Array<{
    target_id: string;
    target_name: string;
    target_addr: string;
    confidence: number;
    status: string;
    badge_color: string;
    name_jw: number;
    addr_jw: number;
    token_sort: number;
    country_match: boolean;
    evidence_list: string[];
    decision_summary: string;
  }>;
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  alternatives?: Array<{
    id: string;
    label: string;
    source: string;
    address: string;
    confidence: number;
    reason: string;
  }>;
}

export interface ExperimentRun {
  run_id: string;
  name: string;
  timestamp: string;
  model: string;
  features_count: number;
  tau_s2: number;
  tau_s3: number;
  macro_f05: number;
  precision: number;
  recall: number;
  candidate_recall: number;
  singleton_acc: number;
  status: string;
}

export interface ErrorCase {
  case_id: string;
  category: string;
  source1_name: string;
  source1_addr: string;
  target_id: string;
  target_name: string;
  target_addr: string;
  country: string;
  actual: string;
  predicted: string;
  confidence: number;
  insight: string;
}

export interface FeatureDef {
  name: string;
  group: string;
  importance: number;
  desc: string;
}
