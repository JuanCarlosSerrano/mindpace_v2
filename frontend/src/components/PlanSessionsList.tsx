import { useState } from "react";
import type { PlanSessionDetail, WeeklySummary } from "../api/types";

type Props = {
  summary: WeeklySummary;
};

const summarizeBlocks = (blocks?: Array<Record<string, unknown>>) => {
  if (!blocks || !blocks.length) return [];
  const parts: string[] = [];
  for (const b of blocks) {
    const type = String(b.type ?? "");
    if (type === "warmup") {
      const value = b.value ?? b.minutes ?? "";
      const unit = b.unit ?? "min";
      parts.push(`Calentamiento ${value}${unit}`);
      continue;
    }
    if (type === "cooldown") {
      const value = b.value ?? b.minutes ?? "";
      const unit = b.unit ?? "min";
      parts.push(`Enfriamiento ${value}${unit}`);
      continue;
    }
    if (type === "repeat") {
      const reps = b.reps ?? "-";
      const steps = Array.isArray(b.steps) ? b.steps : [];
      const first = steps[0] || {};
      if (String(first.type ?? "") === "repeat") {
        const innerReps = first.reps ?? "-";
        const innerSteps = Array.isArray(first.steps) ? first.steps : [];
        const inner = innerSteps[0] || {};
        const innerTarget = inner.target ?? "";
        const innerVal = inner.value ?? "";
        const innerUnit = inner.unit ?? "";
        const innerZone = inner.zone ? ` ${inner.zone}` : "";
        const innerRec =
          inner.recovery_sec != null
            ? ` rec ${Math.round(Number(inner.recovery_sec) / 60)}'`
            : "";
        const innerBase = innerTarget ? `${innerVal}${innerUnit}` : `${innerVal}`;
        const rest = steps.find((s) => String(s.type ?? "") === "recovery");
        const restLabel =
          rest && rest.value
            ? ` + ${Math.round(Number(rest.value) / 60)}' entre bloques`
            : "";
        parts.push(
          `Series ${reps}x(${innerReps}x${innerBase}${innerZone}${innerRec})${restLabel}`
        );
        continue;
      }
      const target = first.target ?? "";
      const val = first.value ?? "";
      const unit = first.unit ?? "";
      const zone = first.zone ? ` ${first.zone}` : "";
      const rec =
        first.recovery_sec != null
          ? ` rec ${Math.round(Number(first.recovery_sec) / 60)}'`
          : "";
      const base = target ? `${val}${unit}` : `${val}`;
      parts.push(`Series ${reps}x${base}${zone}${rec}`);
      continue;
    }
    if (type === "main") {
      const target = b.target ?? "";
      const val = b.value ?? "";
      const unit = b.unit ?? "";
      const zone = b.zone ? ` ${b.zone}` : "";
      const base = target ? `${val}${unit}` : `${val}`;
      parts.push(`Bloque ${base}${zone}`);
      continue;
    }
  }
  return parts;
};

const formatDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("es-ES", {
    month: "short",
    day: "2-digit",
  });
};

const renderBlockChips = (detail: PlanSessionDetail) => {
  const blocks = summarizeBlocks(detail.blocks);
  if (!blocks.length) return null;
  return (
    <div className="block-chip-row">
      {blocks.map((label, idx) => (
        <span key={`${detail.id}-block-${idx}`} className="block-chip">
          {label}
        </span>
      ))}
    </div>
  );
};

const renderBlockDetails = (detail: PlanSessionDetail) => {
  const blocks = detail.blocks ?? [];
  if (!blocks.length) return null;
  return (
    <div className="block-detail">
      {blocks.map((block, idx) => (
        <pre key={`${detail.id}-raw-${idx}`} className="block-json">
          {JSON.stringify(block, null, 2)}
        </pre>
      ))}
    </div>
  );
};

export default function PlanSessionsList({ summary }: Props) {
  const details = summary.plan.sessions_detail ?? [];
  const [expandedId, setExpandedId] = useState<number | null>(null);
  if (!details.length) return null;

  return (
    <section className="panel">
      <div className="catalog-header">
        <h2>Sesiones planificadas</h2>
      </div>
      <div className="plan-sessions-grid">
        {details.map((detail) => (
          <article key={detail.id} className="plan-session-card">
            <div className="plan-session-header">
              <strong>{formatDate(detail.date)}</strong>
              <span className="pill info">{detail.tipo_sesion ?? "tipo"}</span>
            </div>
            <div className="plan-session-meta">
              <span>Volumen: {detail.volumen_objetivo ?? "-"}</span>
              <span>Ritmo: {detail.ritmo_objetivo ?? "-"}</span>
              <span>Series: {detail.detalle_series ?? "-"}</span>
            </div>
            {renderBlockChips(detail)}
            {detail.blocks?.length ? (
              <button
                className="ghost block-toggle"
                onClick={() =>
                  setExpandedId((prev) => (prev === detail.id ? null : detail.id))
                }
              >
                {expandedId === detail.id ? "Ocultar bloques" : "Ver bloques"}
              </button>
            ) : null}
            {expandedId === detail.id ? renderBlockDetails(detail) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
