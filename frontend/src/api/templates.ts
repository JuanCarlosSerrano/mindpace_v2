import { client } from "./client";
import type { TemplateMeta, TemplatePreview, TemplatesResponse } from "./types";

export type TemplatesQuery = {
  q?: string;
  goal?: string;
  level?: string;
  min_weeks?: number;
  max_weeks?: number;
  tag?: string[];
  sort?: "updated" | "load" | "duration" | "name";
  limit?: number;
  offset?: number;
};

const buildQuery = (params: TemplatesQuery) => {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.goal) search.set("goal", params.goal);
  if (params.level) search.set("level", params.level);
  if (params.min_weeks) search.set("min_weeks", String(params.min_weeks));
  if (params.max_weeks) search.set("max_weeks", String(params.max_weeks));
  if (params.sort) search.set("sort", params.sort);
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  if (params.tag) {
    params.tag.forEach((t) => search.append("tag", t));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
};

export const getTemplates = async (
  params: TemplatesQuery = {}
): Promise<TemplatesResponse> => {
  return client(`/api/v1/templates${buildQuery(params)}`);
};

export const getTemplateDetail = async (
  templateId: number
): Promise<TemplatePreview> => {
  return client(`/api/v1/templates/${templateId}`);
};

export const getTemplatesMeta = async (): Promise<TemplateMeta> => {
  return client("/api/v1/templates/meta");
};

export type TemplateSessionPayload = {
  week: number;
  day_of_week: number;
  tipo_sesion?: string;
  volumen_base?: number;
  intensidad_pct_vam?: number;
  formato_series?: string;
  recuperacion_seg?: number;
  blocks?: Array<Record<string, unknown>>;
};

export type TemplateCreatePayload = {
  name: string;
  description?: string;
  goal?: string;
  level?: string;
  duration_weeks?: number;
  tags?: string[];
  estimated_weekly_load?: number;
  sessions: TemplateSessionPayload[];
};

export const createTemplate = async (payload: TemplateCreatePayload) => {
  return client("/api/v1/templates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export type TemplateGeneratePayload = {
  athlete_id: number;
  start_date: string;
  objetivo_descripcion?: string;
};

export const generatePlanFromTemplate = async (
  templateId: number,
  payload: TemplateGeneratePayload
) => {
  return client(`/api/v1/templates/${templateId}/generate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
