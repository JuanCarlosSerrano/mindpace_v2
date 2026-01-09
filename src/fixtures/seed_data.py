from datetime import date
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.db.models import (
    Usuario,
    Atleta,
    PlantillaPlan,
    PlantillaSesion,
    PlanAtleta,
    EntrenamientoPlanificado,
    EntrenamientoRealizado,
)


DATABASE_URL = "sqlite:///mindpace_dev.db"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
def reset_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
def crear_usuarios(session):
    entrenador = Usuario(
        email="entrenador@club.com",
        password_hash="hash_fake",
        rol="entrenador"
    )

    atleta_user = Usuario(
        email="atleta@club.com",
        password_hash="hash_fake",
        rol="atleta"
    )

    session.add_all([entrenador, atleta_user])
    session.commit()

    return entrenador, atleta_user
def crear_atleta(session, entrenador, atleta_user):
    atleta = Atleta(
        usuario_id=atleta_user.id,
        entrenador_id=entrenador.id,
        fecha_nacimiento=date(2005, 6, 12),
        sexo="M",
        experiencia_anios=4,
        dias_entreno_semana=6,
        volumen_actual_km=70,
        vam=18.5,
        ritmo_umbral=210,
        categoria="sub20"
    )

    session.add(atleta)
    session.commit()
    return atleta
def crear_plantilla(session):
    plantilla = PlantillaPlan(
        nombre="Cross base 8 semanas",
        descripcion="Plantilla base para preparación de cross",
        distancia_objetivo="cross",
        nivel="intermedio",
        duracion_semanas=8,
        metodo="tradicional"
    )

    session.add(plantilla)
    session.commit()
    return plantilla
def crear_sesiones_plantilla(session, plantilla):
    sesiones = []

    for semana in range(1, 9):  # 8 semanas
        # Rodaje medio
        sesiones.append(
            PlantillaSesion(
                plantilla_id=plantilla.id,
                semana=semana,
                dia_semana=2,
                tipo_sesion="rodaje",
                volumen_base=10 + semana,  # progresivo
                intensidad_pct_vam=0.7
            )
        )

        # Series
        sesiones.append(
            PlantillaSesion(
                plantilla_id=plantilla.id,
                semana=semana,
                dia_semana=4,
                tipo_sesion="series",
                formato_series="6x1000",
                intensidad_pct_vam=0.9,
                recuperacion_seg=120
            )
        )

        # Rodaje largo
        sesiones.append(
            PlantillaSesion(
                plantilla_id=plantilla.id,
                semana=semana,
                dia_semana=6,
                tipo_sesion="rodaje",
                volumen_base=14 + semana * 1.5,
                intensidad_pct_vam=0.65
            )
        )

    session.add_all(sesiones)
    session.commit()

def crear_plan_atleta(session, atleta, plantilla):
    plan = PlanAtleta(
        atleta_id=atleta.id,
        plantilla_id=plantilla.id,
        fecha_inicio=date(2026, 1, 5),
        objetivo_descripcion="Preparación cross regional"
    )

    session.add(plan)
    session.commit()
    return plan
from datetime import timedelta

def crear_entrenamientos_planificados(session, plan):
    entrenos = []
    fecha_base = plan.fecha_inicio

    for semana in range(1, 9):
        inicio_semana = fecha_base + timedelta(weeks=semana - 1)

        entrenos.append(
            EntrenamientoPlanificado(
                plan_id=plan.id,
                fecha=inicio_semana + timedelta(days=1),
                tipo_sesion="rodaje",
                volumen_objetivo=10 + semana,
                ritmo_objetivo=300
            )
        )

        entrenos.append(
            EntrenamientoPlanificado(
                plan_id=plan.id,
                fecha=inicio_semana + timedelta(days=3),
                tipo_sesion="series",
                detalle_series="6x1000",
                ritmo_objetivo=195
            )
        )

        entrenos.append(
            EntrenamientoPlanificado(
                plan_id=plan.id,
                fecha=inicio_semana + timedelta(days=5),
                tipo_sesion="rodaje",
                volumen_objetivo=14 + semana * 1.5,
                ritmo_objetivo=310
            )
        )

    session.add_all(entrenos)
    session.commit()

def crear_entrenamiento_real(session, atleta):
    entreno = EntrenamientoRealizado(
        atleta_id=atleta.id,
        fecha=date(2026, 1, 6),
        origen="manual",
        tipo_sesion="rodaje",
        distancia_km=11.5,
        tiempo_seg=3450,
        ritmo_medio=300,
        sensacion=6,
        comentarios="Rodaje comodo"
    )

    session.add(entreno)
    session.commit()
def main():
    reset_db()
    session = Session()

    entrenador, atleta_user = crear_usuarios(session)
    atleta = crear_atleta(session, entrenador, atleta_user)
    plantilla = crear_plantilla(session)
    crear_sesiones_plantilla(session, plantilla)

    plan = crear_plan_atleta(session, atleta, plantilla)
    crear_entrenamientos_planificados(session, plan)
    crear_entrenamiento_real(session, atleta)

    print("✔ Base de datos de ejemplo creada correctamente")


if __name__ == "__main__":
    main()
