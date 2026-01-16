import { apiFetch } from "./client";
import type { WeeklySummary } from "./types";

export function getWeekSummary(planId: number, isoWeek: string) {
  return apiFetch<WeeklySummary>(`/api/v1/plans/${planId}/weeks/${isoWeek}`);
}
