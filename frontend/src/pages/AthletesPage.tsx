export default function AthletesPage() {
  return (
    <div className="page">
      <header className="hero">
        <div className="section-header">
          <div>
            <h1>Atletas</h1>
            <p>Gestiona perfiles, objetivos y asignaciones.</p>
          </div>
          <button>Crear atleta</button>
        </div>
      </header>

      <section className="panel">
        <p className="muted">
          TODO: conectar listado de atletas con la API cuando esten disponibles
          los endpoints.
        </p>
      </section>
    </div>
  );
}
