import { useState } from "react";
import type { FeedbackPayload } from "../api/types";

type Props = {
  athleteId: number;
  planId: number;
  isoWeek: string;
  onSubmit: (payload: FeedbackPayload) => Promise<void>;
  disabled?: boolean;
};

export default function FeedbackForm({
  athleteId,
  planId,
  isoWeek,
  onSubmit,
  disabled,
}: Props) {
  const [date, setDate] = useState("2026-01-15");
  const [rpe, setRpe] = useState<number | undefined>(undefined);
  const [fatigue, setFatigue] = useState<number | undefined>(undefined);
  const [soreness, setSoreness] = useState<number | undefined>(undefined);
  const [pain, setPain] = useState(false);
  const [notes, setNotes] = useState("");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await onSubmit({
      date,
      plan_id: planId,
      rpe,
      fatigue,
      soreness,
      pain,
      notes,
    });
  };

  return (
    <div className="panel">
      <h2>Feedback del atleta</h2>
      <p className="muted">
        Plan {planId} · Athlete {athleteId} · Semana {isoWeek}
      </p>
      <form className="controls" onSubmit={handleSubmit}>
        <div className="controls-grid">
          <div>
            <label>Fecha</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <div>
            <label>RPE</label>
            <input
              type="number"
              min={1}
              max={10}
              value={rpe ?? ""}
              onChange={(e) => setRpe(e.target.value ? Number(e.target.value) : undefined)}
            />
          </div>
          <div>
            <label>Fatiga</label>
            <input
              type="number"
              min={1}
              max={10}
              value={fatigue ?? ""}
              onChange={(e) =>
                setFatigue(e.target.value ? Number(e.target.value) : undefined)
              }
            />
          </div>
          <div>
            <label>Molestias</label>
            <input
              type="number"
              min={1}
              max={10}
              value={soreness ?? ""}
              onChange={(e) =>
                setSoreness(e.target.value ? Number(e.target.value) : undefined)
              }
            />
          </div>
        </div>
        <div>
          <label>Notas</label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <label>
          <input
            type="checkbox"
            checked={pain}
            onChange={(e) => setPain(e.target.checked)}
          />{" "}
          Dolor reportado
        </label>
        <button disabled={disabled} type="submit">
          Guardar feedback
        </button>
      </form>
    </div>
  );
}
