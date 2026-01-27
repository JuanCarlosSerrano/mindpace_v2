import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { getSessions } from "../api/sessions";
import {
  createSessionPreset,
  deleteSessionPreset,
  getSessionPresets,
  toPresetPatch,
  updateSessionPreset,
} from "../api/sessionPresets";
import {
  createTemplate,
  generatePlanFromTemplate,
} from "../api/templates";
import type { TemplateSessionPayload } from "../api/templates";
import type { SessionPreset as ApiSessionPreset, SessionSummary } from "../api/types";

type SessionDraft = TemplateSessionPayload & { id: string };
type QuickPreset = {
  label: string;
  patch: Partial<SessionDraft>;
};

const emptySession = (): SessionDraft => ({
  id: crypto.randomUUID(),
  week: 1,
  day_of_week: 2,
  tipo_sesion: "rodaje",
  volumen_base: 8,
  intensidad_pct_vam: 0.7,
  blocks: [],
});

const SESSION_PRESETS: QuickPreset[] = [
  {
    label: "4x1000 (rec 2')",
    patch: {
      tipo_sesion: "series",
      volumen_base: 8,
      intensidad_pct_vam: 0.9,
      formato_series: "4x1000",
      recuperacion_seg: 120,
    },
  },
  {
    label: "6x1000 (rec 2')",
    patch: {
      tipo_sesion: "series",
      volumen_base: 10,
      intensidad_pct_vam: 0.9,
      formato_series: "6x1000",
      recuperacion_seg: 120,
    },
  },
  {
    label: "10x400 (rec 90s)",
    patch: {
      tipo_sesion: "series",
      volumen_base: 7,
      intensidad_pct_vam: 0.95,
      formato_series: "10x400",
      recuperacion_seg: 90,
    },
  },
  {
    label: "Tempo 20'",
    patch: {
      tipo_sesion: "tempo",
      volumen_base: 12,
      intensidad_pct_vam: 0.85,
      formato_series: "20' continuo",
      recuperacion_seg: undefined,
    },
  },
  {
    label: "Rodaje suave 40'",
    patch: {
      tipo_sesion: "rodaje",
      volumen_base: 8,
      intensidad_pct_vam: 0.65,
      formato_series: undefined,
      recuperacion_seg: undefined,
    },
  },
];

export default function TemplateEditorPage() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [goal, setGoal] = useState("base");
  const [level, setLevel] = useState("intermedio");
  const [durationWeeks, setDurationWeeks] = useState(8);
  const [tags, setTags] = useState("rodaje, base");
  const [estimatedLoad, setEstimatedLoad] = useState<number | undefined>(undefined);
  const [sessions, setSessions] = useState<SessionDraft[]>([emptySession()]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdTemplateId, setCreatedTemplateId] = useState<number | null>(null);
  const [librarySessions, setLibrarySessions] = useState<SessionSummary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState<string>("");
  const [trainerId, setTrainerId] = useState(1);
  const [presetLabel, setPresetLabel] = useState("");
  const [customPresets, setCustomPresets] = useState<ApiSessionPreset[]>([]);
  const [editingPresetId, setEditingPresetId] = useState<number | null>(null);

  const [athleteId, setAthleteId] = useState(1);
  const [startDate, setStartDate] = useState("2026-01-05");
  const [goalText, setGoalText] = useState("Plan generado desde plantilla");
  const [generateResult, setGenerateResult] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadSessions = async () => {
      try {
        const res = await getSessions({ limit: 100, sort: "name" });
        if (active) setLibrarySessions(res.items);
      } catch (err) {
        if (active) handleError(err);
      }
    };
    loadSessions();
    return () => {
      active = false;
    };
  }, []);

  const fetchPresets = async (active = true) => {
    try {
      const res = await getSessionPresets({
        entrenador_id: trainerId,
        sort: "updated",
        limit: 100,
      });
      if (active) setCustomPresets(res.items);
    } catch (err) {
      if (active) handleError(err);
    }
  };

  useEffect(() => {
    let active = true;
    fetchPresets(active);
    return () => {
      active = false;
    };
  }, [trainerId]);

  const tagList = useMemo(
    () =>
      tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    [tags]
  );

  const addSession = () => {
    const next = emptySession();
    setSessions((prev) => [...prev, next]);
    setSelectedSessionId(next.id);
  };

  const addFromLibrary = () => {
    const selected = librarySessions.find(
      (s) => String(s.id) === selectedLibraryId
    );
    if (!selected) return;
    const next = {
      id: crypto.randomUUID(),
      week: 1,
      day_of_week: 2,
      tipo_sesion: selected.tipo_sesion ?? "rodaje",
      volumen_base: selected.volumen_base ?? undefined,
      intensidad_pct_vam: selected.intensidad_pct_vam ?? undefined,
      formato_series: selected.formato_series ?? undefined,
      recuperacion_seg: selected.recuperacion_seg ?? undefined,
      blocks: selected.blocks ?? [],
    };
    setSessions((prev) => [...prev, next]);
    setSelectedSessionId(next.id);
  };

  const removeSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    setSelectedSessionId((prev) => (prev === id ? null : prev));
  };

  const updateSession = (id: string, patch: Partial<SessionDraft>) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, ...patch } : s))
    );
  };

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      setError(`${err.message}: ${JSON.stringify(err.details)}`);
      return;
    }
    setError("Error desconocido");
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setGenerateResult(null);
    try {
      const payload = {
        name,
        description,
        goal,
        level,
        duration_weeks: durationWeeks,
        tags: tagList,
        estimated_weekly_load: estimatedLoad,
        sessions: sessions.map(({ id, ...rest }) => rest),
      };
      const res = (await createTemplate(payload)) as { id: number };
      setCreatedTemplateId(res.id);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!createdTemplateId) return;
    setLoading(true);
    setError(null);
    try {
      const res = (await generatePlanFromTemplate(createdTemplateId, {
        athlete_id: athleteId,
        start_date: startDate,
        objetivo_descripcion: goalText,
      })) as { plan_id: number };
      setGenerateResult(`Plan creado: id=${res.plan_id}`);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreset = async () => {
    if (!selectedSessionId) {
      setError("Selecciona una sesión para guardar como preset");
      return;
    }
    if (!presetLabel.trim()) {
      setError("El nombre del preset es obligatorio");
      return;
    }
    const session = sessions.find((s) => s.id === selectedSessionId);
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      if (editingPresetId) {
        await updateSessionPreset(
          editingPresetId,
          {
            label: presetLabel.trim(),
            tipo_sesion: session.tipo_sesion ?? undefined,
            volumen_base: session.volumen_base ?? undefined,
            intensidad_pct_vam: session.intensidad_pct_vam ?? undefined,
            formato_series: session.formato_series ?? undefined,
            recuperacion_seg: session.recuperacion_seg ?? undefined,
            tags: tagList,
          },
          trainerId
        );
      } else {
        await createSessionPreset({
          entrenador_id: trainerId,
          label: presetLabel.trim(),
          tipo_sesion: session.tipo_sesion ?? undefined,
          volumen_base: session.volumen_base ?? undefined,
          intensidad_pct_vam: session.intensidad_pct_vam ?? undefined,
          formato_series: session.formato_series ?? undefined,
          recuperacion_seg: session.recuperacion_seg ?? undefined,
          tags: tagList,
        });
      }
      setPresetLabel("");
      setEditingPresetId(null);
      await fetchPresets();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditPreset = (preset: ApiSessionPreset) => {
    setEditingPresetId(preset.id);
    setPresetLabel(preset.label);
  };

  const handleDeletePreset = async (presetId: number) => {
    setLoading(true);
    setError(null);
    try {
      await deleteSessionPreset(presetId, trainerId);
      if (editingPresetId === presetId) {
        setEditingPresetId(null);
        setPresetLabel("");
      }
      await fetchPresets();
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
            <h1>Crear plantilla</h1>
            <p>Define sesiones base y guarda en el catálogo.</p>
          </div>
          <button disabled={loading} onClick={handleSave}>
            Guardar plantilla
          </button>
        </div>
      </header>

      <section className="panel editor-grid">
        <div className="section-header editor-span">
          <h2>Datos generales</h2>
          <p>Información base para el catálogo.</p>
        </div>
        <div>
          <label>Nombre</label>
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
          <label>Duración (semanas)</label>
          <input
            type="number"
            min={1}
            value={durationWeeks}
            onChange={(e) => setDurationWeeks(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Tags (coma)</label>
          <input value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
        <div>
          <label>Carga semanal estimada</label>
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
        <div>
          <label>Entrenador ID</label>
          <input
            type="number"
            min={1}
            value={trainerId}
            onChange={(e) => setTrainerId(Number(e.target.value))}
          />
        </div>
        <div className="editor-span">
          <label>Descripción</label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
      </section>

      <section className="panel editor-with-sidebar">
        <div className="section-header">
          <div>
            <h2>Sesiones base</h2>
            <p>Define estructura semanal y tipo de sesiones.</p>
          </div>
          <div className="button-row">
            <button className="ghost" onClick={addSession}>
              + Añadir sesión
            </button>
            <select
              value={selectedLibraryId}
              onChange={(e) => setSelectedLibraryId(e.target.value)}
            >
              <option value="">Biblioteca...</option>
              {librarySessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <button className="ghost" onClick={addFromLibrary}>
              Añadir desde biblioteca
            </button>
          </div>
        </div>
        <div className="editor-body">
          <div className="sessions-table">
            <div className="sessions-row sessions-head">
              <span>Semana</span>
              <span>Día</span>
              <span>Tipo</span>
              <span>Volumen</span>
              <span>Intensidad</span>
              <span>Series</span>
              <span>Recup.</span>
              <span></span>
            </div>
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`sessions-row ${s.id === selectedSessionId ? "selected" : ""}`}
                onClick={() => setSelectedSessionId(s.id)}
              >
                <input
                  type="number"
                  min={1}
                  value={s.week}
                  onChange={(e) =>
                    updateSession(s.id, { week: Number(e.target.value) })
                  }
                />
                <input
                  type="number"
                  min={1}
                  max={7}
                  value={s.day_of_week}
                  onChange={(e) =>
                    updateSession(s.id, { day_of_week: Number(e.target.value) })
                  }
                />
                <input
                  value={s.tipo_sesion ?? ""}
                  onChange={(e) =>
                    updateSession(s.id, { tipo_sesion: e.target.value })
                  }
                />
                <input
                  type="number"
                  value={s.volumen_base ?? ""}
                  onChange={(e) =>
                    updateSession(s.id, {
                      volumen_base: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
                <input
                  type="number"
                  step="0.05"
                  value={s.intensidad_pct_vam ?? ""}
                  onChange={(e) =>
                    updateSession(s.id, {
                      intensidad_pct_vam: e.target.value
                        ? Number(e.target.value)
                        : undefined,
                    })
                  }
                />
                <input
                  value={s.formato_series ?? ""}
                  onChange={(e) =>
                    updateSession(s.id, { formato_series: e.target.value })
                  }
                />
                <input
                  type="number"
                  value={s.recuperacion_seg ?? ""}
                  onChange={(e) =>
                    updateSession(s.id, {
                      recuperacion_seg: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
                <button className="ghost" onClick={() => removeSession(s.id)}>
                  ✕
                </button>
              </div>
            ))}
          </div>

          <aside className="session-sidebar">
            <h3>Editar sesión</h3>
            {selectedSessionId ? (
              <>
                {sessions
                  .filter((s) => s.id === selectedSessionId)
                  .map((s) => (
                    <div key={s.id} className="sidebar-fields">
                      <div>
                        <label>Semana</label>
                        <input
                          type="number"
                          min={1}
                          value={s.week}
                          onChange={(e) =>
                            updateSession(s.id, { week: Number(e.target.value) })
                          }
                        />
                      </div>
                      <div>
                        <label>Día semana</label>
                        <input
                          type="number"
                          min={1}
                          max={7}
                          value={s.day_of_week}
                          onChange={(e) =>
                            updateSession(s.id, { day_of_week: Number(e.target.value) })
                          }
                        />
                      </div>
                      <div>
                        <label>Tipo</label>
                        <input
                          value={s.tipo_sesion ?? ""}
                          onChange={(e) =>
                            updateSession(s.id, { tipo_sesion: e.target.value })
                          }
                        />
                      </div>
                      <div>
                        <label>Volumen base</label>
                        <input
                          type="number"
                          value={s.volumen_base ?? ""}
                          onChange={(e) =>
                            updateSession(s.id, {
                              volumen_base: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                        />
                      </div>
                      <div>
                        <label>Intensidad % VAM</label>
                        <input
                          type="number"
                          step="0.05"
                          value={s.intensidad_pct_vam ?? ""}
                          onChange={(e) =>
                            updateSession(s.id, {
                              intensidad_pct_vam: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                        />
                      </div>
                      <div>
                        <label>Formato series</label>
                        <input
                          value={s.formato_series ?? ""}
                          onChange={(e) =>
                            updateSession(s.id, { formato_series: e.target.value })
                          }
                        />
                      </div>
                      <div>
                        <label>Recuperación (seg)</label>
                        <input
                          type="number"
                          value={s.recuperacion_seg ?? ""}
                          onChange={(e) =>
                            updateSession(s.id, {
                              recuperacion_seg: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                        />
                      </div>
                      <div>
                        <label>Presets rápidos</label>
                        <div className="preset-row">
                          {SESSION_PRESETS.map((preset) => (
                            <button
                              key={preset.label}
                              className="ghost preset-btn"
                              onClick={() => updateSession(s.id, preset.patch)}
                            >
                              {preset.label}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label>Presets personalizados</label>
                        <div className="preset-column">
                          {customPresets.map((preset) => (
                            <div key={preset.id} className="preset-item">
                              <button
                                className="ghost preset-btn"
                                onClick={() => updateSession(s.id, toPresetPatch(preset))}
                              >
                                {preset.label}
                              </button>
                              <div className="preset-actions">
                                <button
                                  className="ghost"
                                  onClick={() => handleEditPreset(preset)}
                                >
                                  Editar
                                </button>
                                <button
                                  className="ghost"
                                  onClick={() => handleDeletePreset(preset.id)}
                                >
                                  Borrar
                                </button>
                              </div>
                            </div>
                          ))}
                          {!customPresets.length && (
                            <span className="muted">Sin presets guardados.</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <label>
                          {editingPresetId ? "Editar preset" : "Guardar preset"}
                        </label>
                        <div className="preset-row">
                          <input
                            value={presetLabel}
                            onChange={(e) => setPresetLabel(e.target.value)}
                            placeholder="Nombre del preset"
                          />
                          <button
                            className="secondary"
                            onClick={handleSavePreset}
                            disabled={loading}
                          >
                            {editingPresetId ? "Actualizar" : "Guardar"}
                          </button>
                          {editingPresetId && (
                            <button
                              className="ghost"
                              onClick={() => {
                                setEditingPresetId(null);
                                setPresetLabel("");
                              }}
                              disabled={loading}
                            >
                              Cancelar
                            </button>
                          )}
                        </div>
                      </div>
                      <button className="ghost" onClick={() => removeSession(s.id)}>
                        Eliminar sesión
                      </button>
                    </div>
                  ))}
              </>
            ) : (
              <p className="muted">Selecciona una sesión para editar.</p>
            )}
          </aside>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      {createdTemplateId && (
        <div className="panel">
          <strong>Plantilla guardada</strong>
          <p className="muted">ID generado: {createdTemplateId}</p>
        </div>
      )}

      <section className="panel editor-grid">
        <div className="section-header editor-span">
          <h2>Generar plan desde plantilla</h2>
          <p>Usa la plantilla guardada para crear un plan de atleta.</p>
        </div>
        <div>
          <label>Atleta ID</label>
          <input
            type="number"
            min={1}
            value={athleteId}
            onChange={(e) => setAthleteId(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Fecha inicio</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="editor-span">
          <label>Objetivo descripción</label>
          <input
            value={goalText}
            onChange={(e) => setGoalText(e.target.value)}
          />
        </div>
        <div className="editor-span">
          <button
            className="secondary"
            disabled={!createdTemplateId || loading}
            onClick={handleGenerate}
          >
            Generar plan para atleta
          </button>
          {generateResult && <span className="muted">{generateResult}</span>}
        </div>
      </section>
    </div>
  );
}
