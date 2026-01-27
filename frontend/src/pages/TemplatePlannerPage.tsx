import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { getSessions } from "../api/sessions";
import { createTemplate } from "../api/templates";
import type { TemplateSessionPayload } from "../api/templates";
import type { SessionSummary } from "../api/types";

type SessionDraft = TemplateSessionPayload & { id: string; name?: string };

const DAYS = [
  { key: 1, label: "Lun" },
  { key: 2, label: "Mar" },
  { key: 3, label: "Mié" },
  { key: 4, label: "Jue" },
  { key: 5, label: "Vie" },
  { key: 6, label: "Sáb" },
  { key: 7, label: "Dom" },
];

const emptySessionDraft = (
  session: SessionSummary,
  week: number,
  day: number
): SessionDraft => ({
  id: crypto.randomUUID(),
  name: session.name,
  week,
  day_of_week: day,
  tipo_sesion: session.tipo_sesion ?? "rodaje",
  volumen_base: session.volumen_base ?? undefined,
  intensidad_pct_vam: session.intensidad_pct_vam ?? undefined,
  formato_series: session.formato_series ?? undefined,
  recuperacion_seg: session.recuperacion_seg ?? undefined,
  blocks: session.blocks ?? [],
});

export default function TemplatePlannerPage() {
  const [weeksCount, setWeeksCount] = useState(4);
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("base");
  const [level, setLevel] = useState("intermedio");
  const [tags, setTags] = useState("rodaje, base");
  const [description, setDescription] = useState("");
  const [estimatedLoad, setEstimatedLoad] = useState<number | undefined>(
    undefined
  );

  const [library, setLibrary] = useState<SessionSummary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState<string>("");
  const [schedule, setSchedule] = useState<Record<string, SessionDraft[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [copiedDay, setCopiedDay] = useState<SessionDraft[] | null>(null);

  const tagList = useMemo(
    () =>
      tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    [tags]
  );

  useEffect(() => {
    let active = true;
    const loadLibrary = async () => {
      try {
        const res = await getSessions({ limit: 200, sort: "name" });
        if (active) setLibrary(res.items);
      } catch (err) {
        if (active) handleError(err);
      }
    };
    loadLibrary();
    return () => {
      active = false;
    };
  }, []);

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      setError(`${err.message}`);
      return;
    }
    setError("Error desconocido");
  };

  const addToDay = (week: number, day: number) => {
    const selected = library.find(
      (s) => String(s.id) === selectedLibraryId
    );
    if (!selected) {
      setError("Selecciona una sesión de la biblioteca");
      return;
    }
    setError(null);
    const key = `${week}-${day}`;
    const draft = emptySessionDraft(selected, week, day);
    setSchedule((prev) => ({
      ...prev,
      [key]: [...(prev[key] || []), draft],
    }));
  };

  const removeFromDay = (week: number, day: number, id: string) => {
    const key = `${week}-${day}`;
    setSchedule((prev) => ({
      ...prev,
      [key]: (prev[key] || []).filter((s) => s.id !== id),
    }));
  };

  const copyDay = (week: number, day: number) => {
    const key = `${week}-${day}`;
    const sessions = schedule[key] || [];
    setCopiedDay(
      sessions.map((s) => ({
        ...s,
        id: crypto.randomUUID(),
      }))
    );
  };

  const pasteDay = (week: number, day: number) => {
    if (!copiedDay) return;
    const key = `${week}-${day}`;
    const cloned = copiedDay.map((s) => ({
      ...s,
      id: crypto.randomUUID(),
      week,
      day_of_week: day,
    }));
    setSchedule((prev) => ({
      ...prev,
      [key]: [...(prev[key] || []), ...cloned],
    }));
  };

  const duplicateWeek = (week: number) => {
    const nextWeek = week + 1;
    if (nextWeek > weeksCount) {
      setError("No hay semana siguiente para duplicar");
      return;
    }
    const updates: Record<string, SessionDraft[]> = {};
    for (const day of DAYS) {
      const sourceKey = `${week}-${day.key}`;
      const targetKey = `${nextWeek}-${day.key}`;
      const source = schedule[sourceKey] || [];
      updates[targetKey] = source.map((s) => ({
        ...s,
        id: crypto.randomUUID(),
        week: nextWeek,
        day_of_week: day.key,
      }));
    }
    setSchedule((prev) => ({
      ...prev,
      ...updates,
    }));
  };

  const handleSaveTemplate = async () => {
    setLoading(true);
    setError(null);
    setCreatedId(null);
    try {
      const sessions: TemplateSessionPayload[] = Object.values(schedule)
        .flat()
        .map(({ id, name: _name, ...rest }) => rest);

      if (!sessions.length) {
        setError("Añade al menos una sesión en la planificación");
        return;
      }

      const res = (await createTemplate({
        name,
        description,
        goal,
        level,
        duration_weeks: weeksCount,
        tags: tagList,
        estimated_weekly_load: estimatedLoad,
        sessions,
      })) as { id: number };
      setCreatedId(res.id);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Planificador semanal</h1>
            <p>Organiza sesiones por semana y día con tu biblioteca.</p>
          </div>
          <button disabled={loading} onClick={handleSaveTemplate}>
            Guardar plantilla
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="layout-grid">
        <div className="panel planner-grid">
          {Array.from({ length: weeksCount }, (_, idx) => {
            const week = idx + 1;
            return (
              <div key={week} className="planner-week">
                <div className="planner-week-header">
                  <h3>Semana {week}</h3>
                  <button className="ghost" onClick={() => duplicateWeek(week)}>
                    Duplicar semana
                  </button>
                </div>
                <div className="planner-week-grid">
                  {DAYS.map((day) => {
                    const key = `${week}-${day.key}`;
                    const daySessions = schedule[key] || [];
                    return (
                      <div key={key} className="planner-day">
                        <div className="planner-day-header">
                          <span>{day.label}</span>
                          <div className="planner-day-actions">
                            <button
                              className="ghost"
                              onClick={() => addToDay(week, day.key)}
                            >
                              Añadir
                            </button>
                            <button
                              className="ghost"
                              onClick={() => copyDay(week, day.key)}
                            >
                              Copiar
                            </button>
                            <button
                              className="ghost"
                              onClick={() => pasteDay(week, day.key)}
                              disabled={!copiedDay}
                            >
                              Pegar
                            </button>
                          </div>
                        </div>
                        <div className="planner-day-list">
                          {daySessions.map((session) => (
                            <div key={session.id} className="planner-session">
                              <span>{session.name ?? session.tipo_sesion}</span>
                              <button
                                className="ghost"
                                onClick={() =>
                                  removeFromDay(week, day.key, session.id)
                                }
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                          {!daySessions.length && (
                            <span className="muted">Sin sesiones</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        <aside className="panel sidebar-panel">
          <div className="section-header">
            <h2>Detalles de plantilla</h2>
            <p>Define la base antes de guardar.</p>
          </div>
          <div className="controls-grid">
            <div>
              <label>Nombre plantilla</label>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label>Objetivo</label>
              <input value={goal} onChange={(e) => setGoal(e.target.value)} />
            </div>
            <div>
              <label>Nivel</label>
              <input value={level} onChange={(e) => setLevel(e.target.value)} />
            </div>
            <div>
              <label>Semanas</label>
              <input
                type="number"
                min={1}
                value={weeksCount}
                onChange={(e) => setWeeksCount(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Tags</label>
              <input value={tags} onChange={(e) => setTags(e.target.value)} />
            </div>
            <div>
              <label>Carga semanal</label>
              <input
                type="number"
                value={estimatedLoad ?? ""}
                onChange={(e) =>
                  setEstimatedLoad(
                    e.target.value ? Number(e.target.value) : undefined
                  )
                }
              />
            </div>
            <div className="editor-span">
              <label>Descripción</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="editor-span">
              <label>Sesión seleccionada</label>
              <select
                value={selectedLibraryId}
                onChange={(e) => setSelectedLibraryId(e.target.value)}
              >
                <option value="">Elige una sesión...</option>
                {library.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {createdId && (
            <p className="muted">Plantilla creada con id={createdId}</p>
          )}
        </aside>
      </section>
    </div>
  );
}
