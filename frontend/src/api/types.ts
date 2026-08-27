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

export type ExplorerStage = "baseline" | "canonicalization" | "runtime_optimization" | "retrieval_attribution";

export type PublicRunManifest = {
  schema_version: string | null;
  run_kind: string | null;
  model_configuration: { provider?: string; model?: string };
  output_contract: { id?: string; version?: string; schema_version?: string; evidence_reference_resolution?: string };
  code_revision: string | null;
  git_dirty: boolean | null;
  suite_fingerprint: string | null;
  treatment_fingerprint: string | null;
  condition_fingerprint: string | null;
  execution_policy_fingerprint: string | null;
  run_configuration_fingerprint: string | null;
  evaluation_method: string | null;
  structured_report_schema_version: string | null;
};

export type Aggregate = {
  run_id: string;
  failure_type?: string;
  case_count?: number;
  requested_sample_count: number;
  scored_sample_count: number;
  execution_failed_sample_count: number;
  execution_coverage: number;
  protocol_validity_rate: number;
  quality_status: string;
  formal_metric_vector: FormalMetricVector;
};

export type Run = {
  run_id: string;
  status: string;
  condition_id: string;
  runtime_variant: string;
  suite_id: string;
  suite_version: string;
  started_at: string;
  completed_at: string | null;
  planned_samples: number;
  scored_samples: number;
  failed_samples: number;
  catalog: {
    stage: ExplorerStage;
    role: string;
    condition_family: ConditionId;
    representative: boolean;
    comparison_group: string;
  };
  manifest: PublicRunManifest;
  manifest_sha256: string;
  suite_aggregate: Aggregate | null;
  failure_type_aggregates: FailureTypeAggregate[];
};

export type FailureTypeAggregate = Aggregate & {
  failure_type: string;
};

export type RunCaseAggregate = Aggregate & {
  case_id: string;
  case_sequence: number;
  case_fingerprint: string;
  failure_type: string;
  suite_weight: number;
  scored_repeat_indices_json: string;
  failed_repeat_indices_json: string;
};

export type CaseMetadata = {
  case_id: string;
  failure_type: string;
  weight: number;
  case_schema_version: string;
  case_fingerprint: string;
  provenance: {
    source_type: string | null;
    source_url_or_construction_note: string | null;
    license_or_permission: string | null;
  };
  sanitization: { status: string | null };
};

export type StructuredReport = {
  schema_version?: string;
  case_id?: string;
  classification_status?: string;
  failure_type?: string | null;
  summary?: string;
  root_cause?: string;
  recommended_action?: string;
  confidence?: number;
  evidence_references?: Array<{ evidence_id: string }>;
};

export type ReportValidation = {
  valid: boolean;
  errors?: Array<{ code?: string; field?: string; message?: string }>;
};

export type Sample = {
  identity: { run_id: string; case_id: string; repeat_index: number };
  outcome: {
    sample_sequence: number;
    suite_weight: number;
    evaluation_failure_type: string;
    status: string;
    failure_code: string | null;
    failure_stage: string | null;
    failure_message: string | null;
  };
  report: StructuredReport | null;
  validation: ReportValidation | null;
  score: {
    failure_type_exact_match?: number;
    report_evidence_hit_rate?: number;
    required_fields_completeness?: number;
  } | null;
  diagnostics: Record<string, unknown> | null;
  trajectory_available: boolean;
  trace_available: boolean;
};

export type TokenUsage = { input_tokens: number | null; output_tokens: number | null; total_tokens: number | null };
export type ToolCall = { tool_call_id: string; tool_name: string; arguments: Record<string, unknown> | null };
export type TrajectoryMessage = {
  message_index: number;
  role: "user" | "assistant" | "tool_result";
  visible_content: string | null;
  tool_calls: ToolCall[];
  tool_name: string | null;
  tool_call_id: string | null;
  is_error: boolean | null;
  stop_reason: string | null;
  raw_stop_reason: string | null;
  response_model: string | null;
  usage: TokenUsage | null;
};
export type TrajectoryResponse = { run_id: string; case_id: string; repeat_index: number; messages: TrajectoryMessage[] };
export type TraceEvent = { sequence: number; event_type: string; occurred_at: string; payload: Record<string, unknown> };
export type TraceResponse = { run_id: string; case_id: string; repeat_index: number; events: TraceEvent[] };
