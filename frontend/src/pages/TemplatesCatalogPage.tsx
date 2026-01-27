import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getTemplates, getTemplatesMeta } from "../api/templates";
import type { TemplateMeta, TemplateSummary, TemplatesResponse } from "../api/types";

const parseNumber = (value: string | null) =>
  value ? Number.parseInt(value, 10) : undefined;

export default function TemplatesCatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<TemplateSummary[]>([]);
  const [meta, setMeta] = useState<TemplateMeta | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryState = useMemo(
    () => ({
      q: searchParams.get("q") ?? "",
      goal: searchParams.get("goal") ?? "",
      level: searchParams.get("level") ?? "",
      min_weeks: parseNumber(searchParams.get("min_weeks")),
      max_weeks: parseNumber(searchParams.get("max_weeks")),
      tags: searchParams.getAll("tag"),
      sort: (searchParams.get("sort") ?? "updated") as
        | "updated"
        | "load"
        | "duration"
        | "name",
    }),
    [searchParams]
  );

  const handleError = (err: unknown) => {
    if (err instanceof ApiError) {
      setError(`${err.message}`);
      return;
    }
    setError("Error desconocido");
  };

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res: TemplatesResponse = await getTemplates({
        q: queryState.q || undefined,
        goal: queryState.goal || undefined,
        level: queryState.level || undefined,
        min_weeks: queryState.min_weeks,
        max_weeks: queryState.max_weeks,
        tag: queryState.tags,
        sort: queryState.sort,
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
    void loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  useEffect(() => {
    const loadMeta = async () => {
      try {
        setMeta(await getTemplatesMeta());
      } catch (err) {
        handleError(err);
      }
    };
    void loadMeta();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next);
  };

  const toggleTag = (tag: string) => {
    const next = new URLSearchParams(searchParams);
    const current = new Set(next.getAll("tag"));
    if (current.has(tag)) {
      current.delete(tag);
    } else {
      current.add(tag);
    }
    next.delete("tag");
    [...current].forEach((t) => next.append("tag", t));
    setSearchParams(next);
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Catálogo de plantillas</h1>
            <p>Explora plantillas listas para asignar a atletas.</p>
          </div>
          <Link className="button-link" to="/templates/new">
            + Crear plantilla
          </Link>
        </div>
      </header>

      <section className="panel controls">
        <div className="section-header">
          <h2>Filtros</h2>
          <p>Busca por objetivo, nivel, duración o tags.</p>
        </div>
        <div className="controls-grid">
          <div>
            <label>Buscar</label>
            <input
              value={queryState.q}
              onChange={(e) => updateParam("q", e.target.value)}
              placeholder="Base, 10K, maratón..."
            />
          </div>
          <div>
            <label>Objetivo</label>
            <select
              value={queryState.goal}
              onChange={(e) => updateParam("goal", e.target.value)}
            >
              <option value="">Todos</option>
              {meta?.goals.map((goal) => (
                <option key={goal} value={goal}>
                  {goal}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Nivel</label>
            <select
              value={queryState.level}
              onChange={(e) => updateParam("level", e.target.value)}
            >
              <option value="">Todos</option>
              {meta?.levels.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Min semanas</label>
            <input
              type="number"
              min={1}
              value={queryState.min_weeks ?? ""}
              onChange={(e) => updateParam("min_weeks", e.target.value)}
            />
          </div>
          <div>
            <label>Max semanas</label>
            <input
              type="number"
              min={1}
              value={queryState.max_weeks ?? ""}
              onChange={(e) => updateParam("max_weeks", e.target.value)}
            />
          </div>
          <div>
            <label>Orden</label>
            <select
              value={queryState.sort}
              onChange={(e) => updateParam("sort", e.target.value)}
            >
              <option value="updated">Recientes</option>
              <option value="load">Carga</option>
              <option value="duration">Duración</option>
              <option value="name">Nombre</option>
            </select>
          </div>
        </div>
        <div className="tag-row">
          {meta?.tags.map((tag) => {
            const active = queryState.tags.includes(tag);
            return (
              <button
                key={tag}
                className={`tag-chip ${active ? "active" : ""}`}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </button>
            );
          })}
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="panel">
        <div className="section-header">
          <div>
            <h2>{total} plantillas</h2>
            <p className="muted">Lista actualizada con filtros aplicados.</p>
          </div>
          {loading && <span className="muted">Cargando…</span>}
        </div>
        <div className="card-grid">
          {items.map((item) => (
            <article key={item.id} className="template-card">
              <div className="template-card__top">
                <h3>{item.name}</h3>
                <span className="pill info">{item.level ?? "nivel"}</span>
              </div>
              <p className="muted">{item.description}</p>
              <div className="template-card__meta">
                <span>{item.duration_weeks ?? "-"} semanas</span>
                <span>
                  {item.estimated_weekly_load ?? "-"} carga/sem
                </span>
                <span>{item.goal ?? "objetivo"}</span>
              </div>
              <div className="tag-row">
                {item.tags.map((tag) => (
                  <span key={`${item.id}-${tag}`} className="tag-pill">
                    {tag}
                  </span>
                ))}
              </div>
              <div className="card-actions">
                <Link className="button-link ghost" to={`/templates/${item.id}`}>
                  Ver detalle
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
