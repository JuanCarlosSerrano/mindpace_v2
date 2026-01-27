import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import {
  createSession,
  deleteSession,
  getSessions,
  updateSession,
  type SessionCreatePayload,
} from "../api/sessions";
import type { SessionSummary } from "../api/types";

type BlockKind = "warmup" | "main" | "cooldown" | "strength" | "technique";
type MainType = "rodaje" | "series" | "cambios" | "cuestas" | "fartlek";

type Block = {
  id: string;
  kind: BlockKind;
  minutes?: number;
  notes?: string;
  mainType?: MainType;
  distanceKm?: number;
  reps?: number;
  distanceM?: number;
  intensityZone?: "Z2" | "Z3" | "Z4" | "Z5";
  recoveryText?: string;
};

const ZONE_TO_VAM: Record<string, number> = {
  Z2: 0.7,
  Z3: 0.8,
  Z4: 0.9,
  Z5: 0.95,
};

const ZONE_OPTIONS = ["Z1", "Z2", "Z3", "Z4", "Z5"] as const;

const SERIES_CHIPS = [
  { label: "4×400 rec 1'", reps: 4, distanceM: 400, recoveryText: "1:00" },
  { label: "6×1000 rec 1'30", reps: 6, distanceM: 1000, recoveryText: "1:30" },
  { label: "3×2000 rec 2'", reps: 3, distanceM: 2000, recoveryText: "2:00" },
];

const parseRecoverySeconds = (text?: string) => {
  if (!text) return undefined;
  const parts = text.split(":").map((p) => p.trim());
  if (parts.length === 1) {
    const sec = Number(parts[0]);
    return Number.isFinite(sec) ? sec : undefined;
  }
  if (parts.length === 2) {
    const min = Number(parts[0]);
    const sec = Number(parts[1]);
    if (!Number.isFinite(min) || !Number.isFinite(sec)) return undefined;
    return min * 60 + sec;
  }
  return undefined;
};

const inferZoneFromVam = (vam?: number | null) => {
  if (vam == null) return "Z2";
  const entries = Object.entries(ZONE_TO_VAM);
  let best = "Z2";
  let bestDiff = Number.POSITIVE_INFINITY;
  for (const [zone, value] of entries) {
    const diff = Math.abs(vam - value);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = zone;
    }
  }
  return best;
};

const buildBlocksJson = (blocks: Block[]) => {
  const main = blocks.find((b) => b.kind === "main");
  const warmup = blocks.find((b) => b.kind === "warmup");
  const cooldown = blocks.find((b) => b.kind === "cooldown");
  const strengthBlocks = blocks.filter((b) => b.kind === "strength");

  if (main?.mainType === "series") {
    const reps = main.reps ?? 4;
    const dist = main.distanceM ?? 1000;
    const zone = main.intensityZone ?? "Z3";
    const rec = parseRecoverySeconds(main.recoveryText) ?? 60;
    return [
      {
        type: "warmup",
        target: "time",
        value: warmup?.minutes ?? 10,
        unit: "min",
      },
      {
        type: "repeat",
        reps,
        steps: [
          {
            type: "interval",
            target: "distance",
            value: dist,
            unit: "m",
            zone,
            recovery_sec: rec,
          },
        ],
      },
      {
        type: "cooldown",
        target: "time",
        value: cooldown?.minutes ?? 5,
        unit: "min",
      },
    ];
  }

  if (strengthBlocks.length) {
    return [
      {
        type: "repeat",
        reps: 1,
        steps: strengthBlocks.map((b) => ({
          type: "strength",
          target: "time",
          value: b.minutes ?? 5,
          unit: "min",
          notes: b.notes,
        })),
      },
    ];
  }

  if (main) {
    return [
      {
        type: "main",
        target: "distance",
        value: main.distanceKm,
        unit: "km",
        zone: main.intensityZone,
        notes: main.notes,
      },
    ];
  }

  return [];
};

export default function SessionsCatalogPage() {
  const [items, setItems] = useState<SessionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState("");
  const [tipo, setTipo] = useState("");
  const [tags, setTags] = useState("");

  const [form, setForm] = useState<SessionCreatePayload>({
    name: "",
    description: "",
    tipo_sesion: "",
    volumen_base: undefined,
    intensidad_pct_vam: undefined,
    formato_series: "",
    recuperacion_seg: undefined,
    tags: [],
    blocks: [],
  });
  const [builderName, setBuilderName] = useState("");
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);
  const [dropPosition, setDropPosition] = useState<"before" | "after" | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [intensityZone, setIntensityZone] = useState<string>("Z2");

  const tagList = useMemo(
    () =>
      tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    [tags]
  );

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      setError(err.message);
      return;
    }
    setError("Error desconocido");
  };

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getSessions({
        q: q || undefined,
        tipo: tipo || undefined,
        tag: tagList,
        sort: "name",
        limit: 50,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilter = () => {
    void loadSessions();
  };

  const handleCreate = async () => {
    if (!form.name.trim()) {
      setError("El nombre es obligatorio");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const intensidad_pct_vam =
        intensityZone && intensityZone in ZONE_TO_VAM
          ? ZONE_TO_VAM[intensityZone]
          : form.intensidad_pct_vam;
      if (editingId) {
        await updateSession(editingId, {
          ...form,
          intensidad_pct_vam,
          tags: form.tags?.length ? form.tags : undefined,
        });
        setEditingId(null);
      } else {
        await createSession({
          ...form,
          intensidad_pct_vam,
          tags: form.tags?.length ? form.tags : undefined,
        });
      }
      setForm({
        name: "",
        description: "",
        tipo_sesion: "",
        volumen_base: undefined,
        intensidad_pct_vam: undefined,
        formato_series: "",
        recuperacion_seg: undefined,
        tags: [],
        blocks: [],
      });
      await loadSessions();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (item: SessionSummary) => {
    setEditingId(item.id);
    setIntensityZone(inferZoneFromVam(item.intensidad_pct_vam ?? undefined));
    setForm({
      name: item.name,
      description: item.description ?? "",
      tipo_sesion: item.tipo_sesion ?? "",
      volumen_base: item.volumen_base ?? undefined,
      intensidad_pct_vam: item.intensidad_pct_vam ?? undefined,
      formato_series: item.formato_series ?? "",
      recuperacion_seg: item.recuperacion_seg ?? undefined,
      tags: item.tags ?? [],
      blocks: item.blocks ?? [],
    });
  };

  const handleDelete = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      await deleteSession(id);
      if (editingId === id) {
        setEditingId(null);
      }
      await loadSessions();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const addBlock = (kind: BlockKind) => {
    const base: Block = {
      id: crypto.randomUUID(),
      kind,
      minutes: kind === "warmup" ? 10 : kind === "cooldown" ? 10 : undefined,
      mainType: kind === "main" ? "rodaje" : undefined,
      reps: kind === "main" ? 4 : undefined,
      distanceM: kind === "main" ? 1000 : undefined,
      intensityZone: kind === "main" ? "Z3" : undefined,
      recoveryText: kind === "main" ? "1:00" : undefined,
    };
    setBlocks((prev) => [...prev, base]);
  };

  const updateBlock = (id: string, patch: Partial<Block>) => {
    setBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, ...patch } : b))
    );
  };

  const duplicateBlock = (id: string) => {
    const original = blocks.find((b) => b.id === id);
    if (!original) return;
    setBlocks((prev) => [...prev, { ...original, id: crypto.randomUUID() }]);
  };

  const removeBlock = (id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
  };

  const moveBlock = (fromId: string, toId: string, position: "before" | "after") => {
    if (fromId === toId) return;
    setBlocks((prev) => {
      const fromIndex = prev.findIndex((b) => b.id === fromId);
      const toIndex = prev.findIndex((b) => b.id === toId);
      if (fromIndex < 0 || toIndex < 0) return prev;
      const next = [...prev];
      const [moved] = next.splice(fromIndex, 1);
      const targetIndex = next.findIndex((b) => b.id === toId);
      if (targetIndex < 0) return prev;
      const insertIndex = position === "after" ? targetIndex + 1 : targetIndex;
      next.splice(insertIndex, 0, moved);
      return next;
    });
  };

  const buildDescription = (block: Block) => {
    const notes = block.notes ? ` (${block.notes})` : "";
    if (block.kind === "warmup") {
      return `Calentamiento ${block.minutes ?? "-"}'${notes}`;
    }
    if (block.kind === "cooldown") {
      return `Enfriamiento ${block.minutes ?? "-"}'${notes}`;
    }
    if (block.kind === "strength") {
      return `Fuerza ${block.minutes ?? "-"}'${notes}`;
    }
    if (block.kind === "technique") {
      return `Técnica ${block.minutes ?? "-"}'${notes}`;
    }
    if (block.kind === "main") {
      if (block.mainType === "series") {
        const reps = block.reps ?? "-";
        const dist = block.distanceM ?? "-";
        const rec = block.recoveryText ? ` rec ${block.recoveryText}` : "";
        const zone = block.intensityZone ? ` ${block.intensityZone}` : "";
        return `Series ${reps}x${dist}${rec}${zone}${notes}`;
      }
      const dist = block.distanceKm ? `${block.distanceKm} km` : "";
      const zone = block.intensityZone ? ` ${block.intensityZone}` : "";
      const type = block.mainType ?? "rodaje";
      return `${type} ${dist}${zone}${notes}`.trim();
    }
    return "";
  };

  const formatDuration = (value?: number | null, unit?: string | null) => {
    if (value == null) return "-";
    if (unit === "sec") {
      const mins = Math.floor(value / 60);
      const secs = Math.round(value % 60);
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    }
    return `${value}${unit ?? ""}`;
  };

  const formatStep = (step: Record<string, unknown>) => {
    const type = String(step.type ?? "");
    const target = step.target ?? "";
    const val = step.value as number | undefined;
    const unit = step.unit as string | undefined;
    const zone = step.zone ? ` Zona ${step.zone}` : "";
    const rec =
      step.recovery_sec != null
        ? ` Rec: ${formatDuration(Number(step.recovery_sec), "sec")}`
        : "";

    if (type === "interval") {
      const base = target ? `${val}${unit ?? ""}` : `${val ?? "-"}`;
      return `Serie ${base}${zone}${rec}`;
    }
    if (type === "strength") {
      return step.notes ? `Fuerza: ${step.notes}` : "Fuerza";
    }
    if (type === "recovery") {
      return `Recuperación ${formatDuration(val, unit)}`;
    }
    return step.notes ? String(step.notes) : "Bloque";
  };

  const renderBlockSection = (block: Record<string, unknown>, idx: number) => {
    const type = String(block.type ?? "");
    const label =
      type === "warmup"
        ? "Calentamiento"
        : type === "cooldown"
        ? "Enfriamiento"
        : type === "repeat"
        ? "Bloque repetido"
        : type === "main"
        ? "Bloque principal"
        : "Bloque";
    const tag = `Bloque ${idx + 1}`;
    const reps = block.reps ? `${block.reps} repeticiones` : null;
    const steps = Array.isArray(block.steps) ? block.steps : [];
    const target = block.target ?? "";
    const val = block.value as number | undefined;
    const unit = block.unit as string | undefined;
    const zone = block.zone ? `Zona ${block.zone}` : "";
    const summary =
      type === "repeat"
        ? null
        : `${formatDuration(val, unit)}${zone ? ` · ${zone}` : ""}`;
    return (
      <div key={`block-${idx}`} className={`block-panel ${type}`}>
        <div className="block-panel-header">
          <strong>{label}</strong>
          <div className="block-panel-meta">
            {reps && <span className="chip-muted">{reps}</span>}
            <span className="chip-muted">{tag}</span>
          </div>
        </div>
        {summary && <div className="block-panel-summary">{summary}</div>}
        {type === "repeat" && steps.length > 0 && (
          <ul className="block-steps">
            {steps.map((step, stepIdx) => {
              if (String(step.type ?? "") === "repeat") {
                const nestedReps = step.reps ?? "-";
                const nestedSteps = Array.isArray(step.steps) ? step.steps : [];
                return (
                  <li key={`step-${stepIdx}`} className="block-step">
                    {`Bloque repetido x${nestedReps}`}
                    <ul>
                      {nestedSteps.map((nested, nIdx) => (
                        <li key={`nested-${nIdx}`}>{formatStep(nested)}</li>
                      ))}
                    </ul>
                  </li>
                );
              }
              return (
                <li key={`step-${stepIdx}`} className="block-step">
                  {formatStep(step)}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    );
  };

  const handleApplyBuilder = () => {
    if (!blocks.length) {
      setError("Añade al menos un bloque");
      return;
    }
    const main = blocks.find((b) => b.kind === "main");
    const tipoSesion =
      main?.mainType ??
      (blocks.find((b) => b.kind === "strength") ? "fuerza" : "tecnica");
    const description = blocks.map(buildDescription).filter(Boolean).join(" + ");
    const intensity =
      main?.intensityZone && ZONE_TO_VAM[main.intensityZone]
        ? ZONE_TO_VAM[main.intensityZone]
        : undefined;
    const volumen =
      main?.mainType === "series" && main.reps && main.distanceM
        ? Number(((main.reps * main.distanceM) / 1000).toFixed(1))
        : main?.distanceKm;
    const formato =
      main?.mainType === "series" && main.reps && main.distanceM
        ? `${main.reps}x${main.distanceM}`
        : undefined;
    const rec = parseRecoverySeconds(main?.recoveryText);
    const tags = [
      tipoSesion,
      ...blocks
        .map((b) => b.kind)
        .filter((k) => k !== "main")
        .map((k) => (k === "warmup" ? "calentamiento" : k)),
    ].filter(Boolean);

    const blocksJson = buildBlocksJson(blocks);
    setForm({
      name: builderName || `Sesión ${tipoSesion ?? "base"}`,
      description,
      tipo_sesion: tipoSesion ?? "",
      volumen_base: volumen ?? undefined,
      intensidad_pct_vam: intensity ?? undefined,
      formato_series: formato ?? "",
      recuperacion_seg: rec ?? undefined,
      tags,
      blocks: blocksJson,
    });
    if (main?.intensityZone) {
      setIntensityZone(main.intensityZone);
    }
    setError(null);
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Biblioteca de sesiones</h1>
            <p>Reutiliza sesiones base para construir plantillas.</p>
          </div>
          <button
            className="ghost"
            onClick={() => setSidebarOpen((prev) => !prev)}
          >
            {sidebarOpen ? "Ocultar editor" : "Mostrar editor"}
          </button>
        </div>
      </header>

      <section className="panel controls">
        <div className="section-header">
          <h2>Filtros</h2>
          <p>Encuentra sesiones por tipo, tags o nombre.</p>
        </div>
        <div className="controls-grid">
          <div>
            <label>Buscar</label>
            <input value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div>
            <label>Tipo</label>
            <input
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              placeholder="rodaje, series, fuerza..."
            />
          </div>
          <div>
            <label>Tags (coma)</label>
            <input value={tags} onChange={(e) => setTags(e.target.value)} />
          </div>
        </div>
        <div className="button-row">
          <button onClick={handleFilter} disabled={loading}>
            Filtrar
          </button>
          {loading && <span className="muted">Cargando…</span>}
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="layout-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <h2>{total} sesiones</h2>
              <p className="muted">Resultados según filtros actuales.</p>
            </div>
            {loading && <span className="muted">Cargando…</span>}
          </div>
          <div className="card-grid">
              {items.map((item) => (
                <article key={item.id} className="template-card">
                  <div className="template-card__top">
                    <h3>{item.name}</h3>
                    <span className="pill info">{item.tipo_sesion ?? "tipo"}</span>
                  </div>
                  <p className="muted">{item.description}</p>
                  <div className="template-card__meta">
                    <span>{item.volumen_base ?? "-"} km</span>
                    <span>
                      {item.intensidad_pct_vam != null
                        ? `${item.intensidad_pct_vam} VAM`
                        : "-"}
                    </span>
                    <span>{item.formato_series ?? "-"}</span>
                  </div>
                  <div className="tag-row">
                    {item.tags.map((tag) => (
                      <span key={`${item.id}-${tag}`} className="tag-pill">
                        {tag}
                      </span>
                    ))}
                  </div>
                  {item.blocks?.length ? (
                    <div className="block-panel-list">
                      {item.blocks.map((block, idx) =>
                        renderBlockSection(block, idx)
                      )}
                    </div>
                  ) : null}
                  <div className="button-row">
                    <button className="ghost" onClick={() => startEdit(item)}>
                      Editar
                    </button>
                    <button className="ghost" onClick={() => handleDelete(item.id)}>
                      Borrar
                    </button>
                  </div>
                </article>
              ))}
            </div>
        </div>

        {sidebarOpen && (
          <aside className="panel sidebar-panel">
            <div className="section-header">
              <div>
                <h2>{editingId ? `Editar sesión #${editingId}` : "Crear sesión"}</h2>
                <p>Completa bloques y guarda en la biblioteca.</p>
              </div>
              <button className="ghost" onClick={() => setSidebarOpen(false)}>
                Ocultar
              </button>
            </div>
            <div className="builder-panel">
              <div className="section-header">
                <h3>Constructor por bloques</h3>
                <button className="ghost" onClick={() => addBlock("main")}>
                  Añadir bloque principal
                </button>
              </div>
              <div className="builder-actions">
                <button className="ghost" onClick={() => addBlock("warmup")}>
                  Calentamiento
                </button>
                <button className="ghost" onClick={() => addBlock("cooldown")}>
                  Enfriamiento
                </button>
                <button className="ghost" onClick={() => addBlock("strength")}>
                  Fuerza
                </button>
                <button className="ghost" onClick={() => addBlock("technique")}>
                  Técnica
                </button>
              </div>
              <div className="builder-grid">
                {blocks.map((block) => (
                  <div
                    key={block.id}
                    className={`block-card ${
                      draggingId === block.id ? "dragging" : ""
                    } ${
                      dropTargetId === block.id
                        ? `drop-target ${dropPosition ?? ""}`
                        : ""
                    }`}
                    draggable
                    onDragStart={() => {
                      setDraggingId(block.id);
                    }}
                    onDragEnd={() => {
                      setDraggingId(null);
                      setDropTargetId(null);
                      setDropPosition(null);
                    }}
                    onDragOver={(e) => {
                      e.preventDefault();
                      const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                      const pos =
                        e.clientY < rect.top + rect.height / 2 ? "before" : "after";
                      setDropTargetId(block.id);
                      setDropPosition(pos);
                    }}
                    onDragEnter={() => setDropTargetId(block.id)}
                    onDragLeave={() => {
                      if (dropTargetId === block.id) {
                        setDropTargetId(null);
                        setDropPosition(null);
                      }
                    }}
                    onDrop={() => {
                      if (draggingId && dropPosition) {
                        moveBlock(draggingId, block.id, dropPosition);
                      }
                      setDraggingId(null);
                      setDropTargetId(null);
                      setDropPosition(null);
                    }}
                  >
                    <div className="block-header">
                      <strong>{block.kind.toUpperCase()}</strong>
                      <div className="block-actions">
                        <button
                          className="ghost"
                          onClick={() => duplicateBlock(block.id)}
                        >
                          Duplicar
                        </button>
                        <button
                          className="ghost"
                          onClick={() => removeBlock(block.id)}
                        >
                          Borrar
                        </button>
                      </div>
                    </div>
                    {block.kind === "main" && (
                      <>
                        <label>Tipo principal</label>
                        <select
                          value={block.mainType}
                          onChange={(e) =>
                            updateBlock(block.id, {
                              mainType: e.target.value as MainType,
                            })
                          }
                        >
                          <option value="rodaje">Rodaje</option>
                          <option value="series">Series</option>
                          <option value="cambios">Cambios</option>
                          <option value="cuestas">Cuestas</option>
                          <option value="fartlek">Fartlek</option>
                        </select>
                        {block.mainType === "series" ? (
                          <>
                            <label>Repeticiones</label>
                            <input
                              type="number"
                              value={block.reps ?? ""}
                              onChange={(e) =>
                                updateBlock(block.id, {
                                  reps: Number(e.target.value),
                                })
                              }
                            />
                            <label>Distancia (m)</label>
                            <input
                              type="number"
                              value={block.distanceM ?? ""}
                              onChange={(e) =>
                                updateBlock(block.id, {
                                  distanceM: Number(e.target.value),
                                })
                              }
                            />
                            <label>Intensidad</label>
                            <select
                              value={block.intensityZone ?? "Z3"}
                              onChange={(e) =>
                                updateBlock(block.id, {
                                  intensityZone:
                                    e.target.value as Block["intensityZone"],
                                })
                              }
                            >
                              <option value="Z2">Z2</option>
                              <option value="Z3">Z3</option>
                              <option value="Z4">Z4</option>
                              <option value="Z5">Z5</option>
                            </select>
                            <label>Recuperación (mm:ss)</label>
                            <input
                              value={block.recoveryText ?? ""}
                              onChange={(e) =>
                                updateBlock(block.id, { recoveryText: e.target.value })
                              }
                              placeholder="1:00"
                            />
                            <div className="chip-row">
                              {SERIES_CHIPS.map((chip) => (
                                <button
                                  key={chip.label}
                                  className="ghost"
                                  onClick={() =>
                                    updateBlock(block.id, {
                                      reps: chip.reps,
                                      distanceM: chip.distanceM,
                                      recoveryText: chip.recoveryText,
                                    })
                                  }
                                >
                                  {chip.label}
                                </button>
                              ))}
                            </div>
                          </>
                        ) : (
                          <>
                            <label>Distancia (km)</label>
                            <input
                              type="number"
                              value={block.distanceKm ?? ""}
                              onChange={(e) =>
                                updateBlock(block.id, {
                                  distanceKm: e.target.value
                                    ? Number(e.target.value)
                                    : undefined,
                                })
                              }
                            />
                            <label>Intensidad</label>
                            <select
                              value={block.intensityZone ?? "Z2"}
                              onChange={(e) =>
                                updateBlock(block.id, {
                                  intensityZone:
                                    e.target.value as Block["intensityZone"],
                                })
                              }
                            >
                              <option value="Z2">Z2</option>
                              <option value="Z3">Z3</option>
                              <option value="Z4">Z4</option>
                              <option value="Z5">Z5</option>
                            </select>
                          </>
                        )}
                      </>
                    )}
                    {block.kind !== "main" && (
                      <>
                        <label>Duración (min)</label>
                        <input
                          type="number"
                          value={block.minutes ?? ""}
                          onChange={(e) =>
                            updateBlock(block.id, {
                              minutes: e.target.value
                                ? Number(e.target.value)
                                : undefined,
                            })
                          }
                        />
                      </>
                    )}
                    <label>Notas (opcional)</label>
                    <input
                      value={block.notes ?? ""}
                      onChange={(e) =>
                        updateBlock(block.id, { notes: e.target.value })
                      }
                      placeholder="ej: ritmo controlado"
                    />
                  </div>
                ))}
              </div>
              <div className="builder-footer">
                <div>
                  <label>Nombre sesión</label>
                  <input
                    value={builderName}
                    onChange={(e) => setBuilderName(e.target.value)}
                    placeholder="ej: Series 4x1000"
                  />
                </div>
                <button className="secondary" onClick={handleApplyBuilder}>
                  Usar constructor
                </button>
              </div>
            </div>
        <div className="controls-grid">
          <div>
            <label>Nombre</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <label>Tipo</label>
            <input
              value={form.tipo_sesion ?? ""}
              onChange={(e) =>
                setForm({ ...form, tipo_sesion: e.target.value })
              }
            />
          </div>
          <div>
            <label>Volumen base (km)</label>
            <input
              type="number"
              value={form.volumen_base ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  volumen_base: e.target.value ? Number(e.target.value) : undefined,
                })
              }
            />
          </div>
          <div>
            <label>Intensidad (zona)</label>
            <select
              value={intensityZone}
              onChange={(e) => setIntensityZone(e.target.value)}
            >
              {ZONE_OPTIONS.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Formato series</label>
            <input
              value={form.formato_series ?? ""}
              onChange={(e) =>
                setForm({ ...form, formato_series: e.target.value })
              }
            />
          </div>
          <div>
            <label>Recuperación (seg)</label>
            <input
              type="number"
              value={form.recuperacion_seg ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  recuperacion_seg: e.target.value
                    ? Number(e.target.value)
                    : undefined,
                })
              }
            />
          </div>
          <div className="editor-span">
            <label>Descripción</label>
            <textarea
              rows={2}
              value={form.description ?? ""}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
          </div>
          <div className="editor-span">
            <label>Tags (coma)</label>
            <input
              value={(form.tags ?? []).join(", ")}
              onChange={(e) =>
                setForm({
                  ...form,
                  tags: e.target.value
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean),
                })
              }
            />
          </div>
        </div>
        <div className="button-row">
          <button disabled={loading} onClick={handleCreate}>
            {editingId ? "Actualizar sesión" : "Guardar sesión"}
          </button>
          {editingId && (
            <button
              className="ghost"
              disabled={loading}
              onClick={() => {
                setEditingId(null);
                setIntensityZone("Z2");
                setForm({
                  name: "",
                  description: "",
                  tipo_sesion: "",
                  volumen_base: undefined,
                  intensidad_pct_vam: undefined,
                  formato_series: "",
                  recuperacion_seg: undefined,
                  tags: [],
                  blocks: [],
                });
              }}
            >
              Cancelar
            </button>
          )}
        </div>
          </aside>
        )}
      </section>
    </div>
  );
}
