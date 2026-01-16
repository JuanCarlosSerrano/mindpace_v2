import { apiFetch } from "./client";
import type { CoachApplyPayload, CoachRevertPayload } from "./types";

export function applyCoach(planId: number, payload: CoachApplyPayload) {
  return apiFetch(`/api/v1/plans/${planId}/coach/apply`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function revertCoach(planId: number, payload: CoachRevertPayload) {
  return apiFetch(`/api/v1/plans/${planId}/coach/revert`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
