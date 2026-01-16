import { apiFetch } from "./client";
import type { FeedbackPayload } from "./types";

export function postFeedback(athleteId: number, payload: FeedbackPayload) {
  return apiFetch(`/api/v1/athletes/${athleteId}/feedback`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
