import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <main className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="brand">
          <img src="/logo_sin_fondo.png" alt="MindPace" />
          <div className="brand-text">
            <span className="brand-title">MindPace</span>
            <span className="brand-sub">Coach Console</span>
          </div>
        </div>
        <nav className="sidebar-links">
          <NavLink to="/home">Inicio</NavLink>
          <NavLink to="/library/sessions">Biblioteca</NavLink>
          <NavLink to="/planner/week">Planificador</NavLink>
          <NavLink to="/athletes">Atletas</NavLink>
          <NavLink to="/groups">Grupos</NavLink>
          <NavLink to="/coach-ai">CoachAI</NavLink>
          <NavLink to="/templates">Plantillas</NavLink>
        </nav>
      </aside>
      <section className="content">
        <div className="content-header">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((open) => !open)}
          >
            {sidebarOpen ? "Ocultar menú" : "Mostrar menú"}
          </button>
        </div>
        <Outlet />
      </section>
    </main>
  );
}
