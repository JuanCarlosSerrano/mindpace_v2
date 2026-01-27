import { Link } from "react-router-dom";

const MOCK_KPIS = [
  { label: "Alertas activas", value: 3 },
  { label: "Feedback pendiente", value: 7 },
  { label: "Entrenos 48h", value: 5 },
  { label: "Atletas sin plan", value: 2 },
];

const MOCK_ALERTS = [
  { id: 1, text: "Sobrecarga detectada en Grupo Alpha", link: "/coach-ai" },
  { id: 2, text: "Semana con baja cobertura de datos", link: "/dashboard/week" },
];

const MOCK_FEEDBACK = [
  { id: 1, text: "Atleta 4 · RPE alto sin nota", link: "/dashboard/week" },
  { id: 2, text: "Atleta 2 · Feedback pendiente 3 sesiones", link: "/dashboard/week" },
];

const MOCK_UPCOMING = [
  { id: 1, text: "Series 4x1000 · Atleta 1 · Vie", link: "/dashboard/week" },
  { id: 2, text: "Rodaje suave · Atleta 3 · Sáb", link: "/dashboard/week" },
];

const MOCK_MISSING = [
  { id: 1, text: "Atleta 5 sin plan asignado", link: "/planner/week" },
  { id: 2, text: "Atleta 8 sin semana creada", link: "/planner/week" },
];

export default function HomeCoachPage() {
  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Inicio · Urgencias</h1>
            <p>Resumen operativo para actuar rápido.</p>
          </div>
          <Link className="button-link ghost" to="/coach-ai">
            Ir a CoachAI
          </Link>
        </div>
      </header>

      <section className="grid-two">
        {MOCK_KPIS.map((item) => (
          <div key={item.label} className="stat-card">
            <span className="stat-label">{item.label}</span>
            <span className="stat-value">{item.value}</span>
          </div>
        ))}
      </section>

      <section className="layout-grid">
        <div className="panel">
          <div className="section-header">
            <h2>Alertas</h2>
            <p>Prioridad alta para revisar hoy.</p>
          </div>
          <ul className="card-list">
            {MOCK_ALERTS.map((alert) => (
              <li key={alert.id}>
                <span>{alert.text}</span>
                <Link className="link" to={alert.link}>
                  Ver detalle
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <aside className="panel sidebar-panel">
          <div className="section-header">
            <h2>Feedback pendiente</h2>
            <p>Requiere seguimiento del entrenador.</p>
          </div>
          <ul className="card-list">
            {MOCK_FEEDBACK.map((item) => (
              <li key={item.id}>
                <span>{item.text}</span>
                <Link className="link" to={item.link}>
                  Abrir semana
                </Link>
              </li>
            ))}
          </ul>
        </aside>
      </section>

      <section className="layout-grid">
        <div className="panel">
          <div className="section-header">
            <h2>Próximos entrenamientos</h2>
            <p>Sesiones dentro de las próximas 48h.</p>
          </div>
          <ul className="card-list">
            {MOCK_UPCOMING.map((item) => (
              <li key={item.id}>
                <span>{item.text}</span>
                <Link className="link" to={item.link}>
                  Ver semana
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <aside className="panel sidebar-panel">
          <div className="section-header">
            <h2>Atletas sin plan</h2>
            <p>Asignar plan lo antes posible.</p>
          </div>
          <ul className="card-list">
            {MOCK_MISSING.map((item) => (
              <li key={item.id}>
                <span>{item.text}</span>
                <Link className="link" to={item.link}>
                  Planificar
                </Link>
              </li>
            ))}
          </ul>
        </aside>
      </section>
    </div>
  );
}
