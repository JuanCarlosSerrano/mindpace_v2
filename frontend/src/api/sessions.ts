import { client } from "./client";
import type { SessionsResponse, SessionSummary } from "./types";

export type SessionsQuery = {
  q?: string;
  tipo?: string;
  tag?: string[];
  sort?: "updated" | "name" | "load";
  limit?: number;
  offset?: number;
};

const buildQuery = (params: SessionsQuery) => {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.tipo) search.set("tipo", params.tipo);
  if (params.sort) search.set("sort", params.sort);
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  if (params.tag) {
    params.tag.forEach((t) => search.append("tag", t));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
};

export const getSessions = async (
  params: SessionsQuery = {}
): Promise<SessionsResponse> => {
  return client(`/api/v1/sessions${buildQuery(params)}`);
};

export const getSessionDetail = async (id: number): Promise<SessionSummary> => {
  return client(`/api/v1/sessions/${id}`);
};

export type SessionCreatePayload = {
  name: string;
  description?: string;
  tipo_sesion?: string;
  volumen_base?: number;
  intensidad_pct_vam?: number;
  formato_series?: string;
  recuperacion_seg?: number;
  tags?: string[];
  blocks?: Array<Record<string, unknown>>;
};

export const createSession = async (payload: SessionCreatePayload) => {
  return client("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export type SessionUpdatePayload = {
  name?: string;
  description?: string;
  tipo_sesion?: string;
  volumen_base?: number;
  intensidad_pct_vam?: number;
  formato_series?: string;
  recuperacion_seg?: number;
  tags?: string[];
  blocks?: Array<Record<string, unknown>>;
};

export const updateSession = async (id: number, payload: SessionUpdatePayload) => {
  return client(`/api/v1/sessions/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
};

export const deleteSession = async (id: number) => {
  return client(`/api/v1/sessions/${id}`, {
    method: "DELETE",
  });
};
