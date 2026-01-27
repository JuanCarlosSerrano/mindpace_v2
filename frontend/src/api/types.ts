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
    sessions_detail?: PlanSessionDetail[];
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

export type PlanSessionDetail = {
  id: number;
  date: string;
  tipo_sesion?: string | null;
  volumen_objetivo?: number | null;
  ritmo_objetivo?: number | null;
  detalle_series?: string | null;
  blocks?: Array<Record<string, unknown>>;
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

export type TemplateSummary = {
  id: number;
  name: string;
  description?: string | null;
  goal?: string | null;
  level?: string | null;
  duration_weeks?: number | null;
  tags: string[];
  estimated_weekly_load?: number | null;
  source_key?: string | null;
  updated_at?: string | null;
};

export type TemplatePreview = TemplateSummary & {
  weekly_preview: Array<{
    week: number;
    load: number;
    focus_tags: string[];
  }>;
};

export type TemplatesResponse = {
  items: TemplateSummary[];
  total: number;
};

export type TemplateMeta = {
  goals: string[];
  levels: string[];
  tags: string[];
};

export type SessionSummary = {
  id: number;
  name: string;
  description?: string | null;
  tipo_sesion?: string | null;
  volumen_base?: number | null;
  intensidad_pct_vam?: number | null;
  formato_series?: string | null;
  recuperacion_seg?: number | null;
  tags: string[];
  blocks?: Array<Record<string, unknown>>;
  updated_at?: string | null;
};

export type SessionsResponse = {
  items: SessionSummary[];
  total: number;
};

export type SessionPreset = {
  id: number;
  entrenador_id: number;
  label: string;
  tipo_sesion?: string | null;
  volumen_base?: number | null;
  intensidad_pct_vam?: number | null;
  formato_series?: string | null;
  recuperacion_seg?: number | null;
  tags: string[];
  updated_at?: string | null;
};

export type SessionPresetsResponse = {
  items: SessionPreset[];
  total: number;
};
