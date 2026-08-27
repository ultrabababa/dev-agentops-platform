export type FormalMetricVector = {
  execution_coverage: number;
  failure_type_exact_match: number;
  report_evidence_hit_rate: number;
  required_fields_completeness: number;
  protocol_validity_rate: number;
};

export type ConditionId = "L1" | "L2" | "L3" | "L4" | "Oracle";

export type CanonicalizationFinding = {
  artifact_id: string;
  authority: "fixed_output_offline_replay";
  l4: {
    protocol_validity_before: number;
    protocol_validity_after: number;
    unknown_evidence_ids_before: number;
    unknown_evidence_ids_after: number;
    failure_type_exact_match_before: number;
    failure_type_exact_match_after: number;
  };
};

export type RuntimeOptimizationFinding = {
  artifact_id: string;
  authority: "formal_trace_metrics_and_replication";
  run_ids: [string, string];
  model_decisions: [number, number];
  executed_tool_calls: [number, number];
  run_wall_seconds: [number, number];
  interpretation: string;
};

export type RetrievalAttributionFinding = {
  artifact_id: string;
  authority: "formal_l3_result_snapshot";
  run_id: string;
  retrieval_acquisition_recall: number;
  acquired_required_evidence_utilization: number;
  report_evidence_hit_rate: number;
  report_evidence_improvement_over_l1_l2: "not_demonstrated";
};

export type FeaturedFindings = {
  canonicalization: CanonicalizationFinding;
  runtime_optimization: RuntimeOptimizationFinding;
  retrieval_attribution: RetrievalAttributionFinding;
};

export type Overview = {
  benchmark: {
    case_count: number;
    repeats_per_case: number;
    samples_per_formal_run: number;
    failure_type_count: number;
  };
  representative_conditions: Record<
    "L1" | "L2" | "L3" | "L4" | "Oracle",
    { run_id: string; runtime_variant: string }
  >;
  experiment_evolution_endpoint: string;
  featured_findings: FeaturedFindings;
};

export type Condition = {
  condition: ConditionId;
  runtime_variant: string;
  representative_run: {
    run_id: string;
    status: string;
    planned_samples: number;
    scored_samples: number;
    failed_samples: number;
  };
  formal_metric_vector: FormalMetricVector | null;
  related_run_ids: string[];
  comparison_group: string;
};

export type EvolutionStage = {
  stage: "baseline" | "canonicalization" | "runtime_optimization" | "retrieval_attribution";
  run_ids: string[];
  artifact_id: string | null;
  key_observation:
    | CanonicalizationFinding
    | RuntimeOptimizationFinding
    | RetrievalAttributionFinding
    | null;
};

export type Evolution = { stages: EvolutionStage[] };

export type HomepageData = {
  overview: Overview;
  conditions: Condition[];
  evolution: Evolution;
};
