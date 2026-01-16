export type ActionItem = {
  code?: string;
  message?: string;
};

export type CoachRecommendation = {
  action_type: string;
  summary: string;
  actions: ActionItem[];
  explanation: string;
  date?: string | null;
  scope?: string | null;
  reason?: string | null;
  confidence?: string | null;
  kind?: string | null;
  severity?: string | null;
  priority?: number | null;
};

export type WeeklySummary = {
  meta: {
    plan_id: number;
    generated_at: string;
    data_confidence_ratio?: number | null;
  };
  week: {
    iso: string;
    start_date: string;
    end_date: string;
  };
  plan: {
    sessions_count: number;
    volume_km_total: number;
    by_type: Record<string, number>;
  };
  real: {
    sessions_count: number;
    volume_km_total: number;
    coverage_ratio: number | null;
  };
  compliance: {
    status: string;
    label: string;
    ratio_volume: number | null;
    ratio_sessions: number | null;
  };
  load: {
    load_index: number | null;
    trend: string | null;
    alerts: string[];
  };
  alerts: {
    plan: string[];
    real_risk: string[];
  };
  coach: {
    recommended: CoachRecommendation[];
  };
  actions: {
    applied: Array<{
      id: number;
      action_type: string;
      state: string;
      actions: ActionItem[];
      created_at: string | null;
    }>;
  };
  history: Array<{
    id: number;
    action_type: string;
    state: string;
    actions: ActionItem[];
    created_at: string | null;
  }>;
  feedback: {
    count: number;
    coverage: number;
    avg_rpe: number | null;
    high_fatigue_days: number;
    pain_days: number;
    pain_signal: boolean;
    notes_preview: Array<{ date: string; text: string }>;
  };
};

export type FeedbackPayload = {
  date: string;
  plan_id?: number;
  rpe?: number;
  mood?: number;
  fatigue?: number;
  soreness?: number;
  pain?: boolean;
  notes?: string;
};

export type CoachApplyPayload = {
  week?: string;
  dry_run?: boolean;
};

export type CoachRevertPayload = {
  week?: string;
  ids?: number[];
  last?: number;
  yes?: boolean;
};
