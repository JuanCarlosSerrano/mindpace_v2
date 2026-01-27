import { client } from "./client";
import type { SessionPresetsResponse, SessionPreset } from "./types";

export type PresetsQuery = {
  entrenador_id: number;
  sort?: "updated" | "label";
  limit?: number;
  offset?: number;
};

const buildQuery = (params: PresetsQuery) => {
  const search = new URLSearchParams();
  search.set("entrenador_id", String(params.entrenador_id));
  if (params.sort) search.set("sort", params.sort);
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
};

export const getSessionPresets = async (
  params: PresetsQuery
): Promise<SessionPresetsResponse> => {
  return client(`/api/v1/session-presets${buildQuery(params)}`);
};

export type SessionPresetCreatePayload = {
  entrenador_id: number;
  label: string;
  tipo_sesion?: string;
  volumen_base?: number;
  intensidad_pct_vam?: number;
  formato_series?: string;
  recuperacion_seg?: number;
  tags?: string[];
};

export const createSessionPreset = async (
  payload: SessionPresetCreatePayload
): Promise<{ id: number }> => {
  return client("/api/v1/session-presets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export type SessionPresetUpdatePayload = {
  label?: string;
  tipo_sesion?: string;
  volumen_base?: number;
  intensidad_pct_vam?: number;
  formato_series?: string;
  recuperacion_seg?: number;
  tags?: string[];
};

export const updateSessionPreset = async (
  id: number,
  payload: SessionPresetUpdatePayload,
  entrenadorId?: number
): Promise<{ id: number }> => {
  const qs = entrenadorId ? `?entrenador_id=${entrenadorId}` : "";
  return client(`/api/v1/session-presets/${id}${qs}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
};

export const deleteSessionPreset = async (
  id: number,
  entrenadorId?: number
): Promise<{ deleted: boolean }> => {
  const qs = entrenadorId ? `?entrenador_id=${entrenadorId}` : "";
  return client(`/api/v1/session-presets/${id}${qs}`, {
    method: "DELETE",
  });
};

export const toPresetPatch = (preset: SessionPreset) => ({
  tipo_sesion: preset.tipo_sesion ?? undefined,
  volumen_base: preset.volumen_base ?? undefined,
  intensidad_pct_vam: preset.intensidad_pct_vam ?? undefined,
  formato_series: preset.formato_series ?? undefined,
  recuperacion_seg: preset.recuperacion_seg ?? undefined,
});
