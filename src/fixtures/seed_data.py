from datetime import date
from datetime import timedelta
import re
import os
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
    TemplateCatalog,
    SessionCatalog,
)


DB_PATH = os.getenv("DB_PATH", "mindpace_dev.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

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


def crear_templates_catalog(session):
    templates = [
        {
            "name": "Base 8 semanas",
            "description": "Construcción aeróbica general con énfasis en rodajes.",
            "goal": "base",
            "level": "intermedio",
            "duration_weeks": 8,
            "tags_json": ["rodaje", "base", "aerobico"],
            "estimated_weekly_load": 42.0,
            "source_key": "base_8w_v1",
        },
        {
            "name": "10K rápido 12 semanas",
            "description": "Enfoque en series y umbral para mejorar 10K.",
            "goal": "10k",
            "level": "avanzado",
            "duration_weeks": 12,
            "tags_json": ["series", "umbral", "velocidad"],
            "estimated_weekly_load": 58.0,
            "source_key": "10k_12w_v1",
        },
        {
            "name": "Media maratón 12 semanas",
            "description": "Volumen progresivo y control de ritmo.",
            "goal": "media_maraton",
            "level": "intermedio",
            "duration_weeks": 12,
            "tags_json": ["tempo", "rodaje_largo", "resistencia"],
            "estimated_weekly_load": 60.0,
            "source_key": "hm_12w_v1",
        },
        {
            "name": "Maratón base 16 semanas",
            "description": "Base aeróbica con carga gradual.",
            "goal": "maraton",
            "level": "intermedio",
            "duration_weeks": 16,
            "tags_json": ["rodaje_largo", "base", "resistencia"],
            "estimated_weekly_load": 70.0,
            "source_key": "marathon_base_16w",
        },
        {
            "name": "5K progresivo 8 semanas",
            "description": "Trabajo de velocidad y técnica.",
            "goal": "5k",
            "level": "intermedio",
            "duration_weeks": 8,
            "tags_json": ["series", "velocidad", "tecnica"],
            "estimated_weekly_load": 38.0,
            "source_key": "5k_8w_v1",
        },
        {
            "name": "Trail base 10 semanas",
            "description": "Adaptación a desnivel y fuerza específica.",
            "goal": "trail",
            "level": "intermedio",
            "duration_weeks": 10,
            "tags_json": ["desnivel", "fuerza", "rodaje"],
            "estimated_weekly_load": 50.0,
            "source_key": "trail_10w_v1",
        },
        {
            "name": "Recuperación activa 4 semanas",
            "description": "Baja carga y mantenimiento.",
            "goal": "recuperacion",
            "level": "base",
            "duration_weeks": 4,
            "tags_json": ["recuperacion", "suave", "movilidad"],
            "estimated_weekly_load": 25.0,
            "source_key": "recovery_4w_v1",
        },
        {
            "name": "Cross base 8 semanas",
            "description": "Resistencia + cambios de ritmo controlados.",
            "goal": "cross",
            "level": "intermedio",
            "duration_weeks": 8,
            "tags_json": ["cross", "series", "rodaje"],
            "estimated_weekly_load": 45.0,
            "source_key": "cross_8w_v1",
        },
        {
            "name": "Umbral 6 semanas",
            "description": "Bloque corto de trabajo al umbral.",
            "goal": "umbral",
            "level": "avanzado",
            "duration_weeks": 6,
            "tags_json": ["umbral", "tempo"],
            "estimated_weekly_load": 52.0,
            "source_key": "threshold_6w_v1",
        },
        {
            "name": "Base principiantes 6 semanas",
            "description": "Introducción progresiva al running.",
            "goal": "base",
            "level": "base",
            "duration_weeks": 6,
            "tags_json": ["rodaje", "adaptacion"],
            "estimated_weekly_load": 28.0,
            "source_key": "beginner_6w_v1",
        },
        {
            "name": "Tempo 8 semanas",
            "description": "Bloque de tempo para consolidar ritmo.",
            "goal": "tempo",
            "level": "intermedio",
            "duration_weeks": 8,
            "tags_json": ["tempo", "umbral", "resistencia"],
            "estimated_weekly_load": 48.0,
            "source_key": "tempo_8w_v1",
        },
        {
            "name": "10K base 6 semanas",
            "description": "Base rápida para 10K.",
            "goal": "10k",
            "level": "base",
            "duration_weeks": 6,
            "tags_json": ["rodaje", "progresion"],
            "estimated_weekly_load": 34.0,
            "source_key": "10k_6w_v1",
        },
    ]

    for t in templates:
        session.add(TemplateCatalog(**t))
    session.commit()


def crear_sessions_catalog(session):
    def _infer_tipo(tags, goal):
        tags_lower = {t.lower() for t in tags}
        if "fuerza" in tags_lower or goal == "strength":
            return "fuerza"
        if "rodaje" in tags_lower:
            return "rodaje"
        if "fartlek" in tags_lower:
            return "fartlek"
        if "cambios" in tags_lower:
            return "cambios"
        if "cuestas" in tags_lower:
            return "cuestas"
        if "tempo" in tags_lower or "umbral" in tags_lower:
            return "tempo"
        if "series" in tags_lower:
            return "series"
        if goal == "hills":
            return "cuestas"
        if goal in {"vo2", "speed", "race"}:
            return "series"
        return "rodaje"

    def _infer_zone(tags):
        for z in ("Z5", "Z4", "Z3", "Z2", "Z1"):
            if z.lower() in {t.lower() for t in tags}:
                return z
        return None

    def _extract_zone(text):
        m = re.search(r"\bZ[1-5]\b", text, re.IGNORECASE)
        return m.group(0).upper() if m else None

    def _parse_reps_distance(text):
        m = re.search(r"(\d+)x\((\d+)x(\d+)\s?m", text)
        if m:
            outer_reps = int(m.group(1))
            inner_reps = int(m.group(2))
            distance = int(m.group(3))
            outer_rest = None
            outer_match = re.search(r"con\s+(\d+)'", text)
            if outer_match:
                outer_rest = int(outer_match.group(1)) * 60
            return {
                "reps": outer_reps,
                "target": "distance",
                "value": distance,
                "unit": "m",
                "notes": f"{inner_reps}x{distance}m",
                "inner_reps": inner_reps,
                "outer_recovery_sec": outer_rest,
            }
        if re.search(r"\b200/400/600/800/600/400/200\b", text):
            return {
                "reps": 1,
                "target": "distance",
                "value": None,
                "unit": "m",
                "notes": "200/400/600/800/600/400/200",
            }
        m = re.search(r"(\d+)x\((\d+)'[^/]+/\s*(\d+)'[^)]+\)", text)
        if m:
            return {
                "reps": int(m.group(1)),
                "target": "time",
                "value": int(m.group(2)),
                "unit": "min",
                "recovery_sec": int(m.group(3)) * 60,
                "notes": "bloque trabajo/recuperación",
            }
        m = re.search(r"(\d+)x\((\d+)\"[^/]+/\s*(\d+)\"[^)]+\)", text)
        if m:
            return {
                "reps": int(m.group(1)),
                "target": "time",
                "value": int(m.group(2)),
                "unit": "sec",
                "recovery_sec": int(m.group(3)),
                "notes": "bloque trabajo/recuperación",
            }
        m = re.search(r"(\d+)x(\d+)\s?m", text)
        if m:
            return {
                "reps": int(m.group(1)),
                "target": "distance",
                "value": int(m.group(2)),
                "unit": "m",
            }
        m = re.search(r"(\d+)x(\d+)\s?k", text)
        if m:
            return {
                "reps": int(m.group(1)),
                "target": "distance",
                "value": int(m.group(2)) * 1000,
                "unit": "m",
            }
        m = re.search(r"(\d+)x(\d+)\'", text)
        if m:
            return {
                "reps": int(m.group(1)),
                "target": "time",
                "value": int(m.group(2)),
                "unit": "min",
            }
        return None

    def _parse_recovery_seconds(text):
        m = re.search(r"rec\s*(\d+):(\d+)", text)
        if m:
            return int(m.group(1)) * 60 + int(m.group(2))
        m = re.search(r"rec\s*(\d+)\'", text)
        if m:
            return int(m.group(1)) * 60
        m = re.search(r"rec\s*(\d+)\"", text)
        if m:
            return int(m.group(1))
        return None

    def _volumen_from_duration(duration_min):
        if duration_min is None:
            return None
        return round(duration_min * 0.2, 1)

    def _blocks_for_workout(spec):
        tipo = _infer_tipo(spec["tags_json"], spec["goal"])
        zone = _infer_zone(spec["tags_json"])
        duration_min = spec.get("duration_min")
        workout_text = spec.get("workout_text", "")
        name = spec.get("name", "")
        parse_source = f"{name} {workout_text}"
        if tipo == "series":
            parsed = _parse_reps_distance(parse_source)
            zone = _extract_zone(parse_source) or zone
            recovery = _parse_recovery_seconds(parse_source)
            interval = {
                "type": "interval",
                "target": "text",
                "value": None,
                "unit": "",
                "zone": zone,
                "recovery_sec": recovery,
            }
            reps = 1
            if parsed:
                reps = parsed.get("reps", 1)
                inner_reps = parsed.get("inner_reps")
                if inner_reps:
                    nested = {
                        "type": "repeat",
                        "reps": inner_reps,
                        "steps": [
                            {
                                "type": "interval",
                                "target": "distance",
                                "value": parsed.get("value"),
                                "unit": parsed.get("unit"),
                                "zone": zone,
                                "recovery_sec": parsed.get("recovery_sec", recovery),
                            }
                        ],
                    }
                    outer_steps = [nested]
                    if parsed.get("outer_recovery_sec"):
                        outer_steps.append(
                            {
                                "type": "recovery",
                                "target": "time",
                                "value": parsed["outer_recovery_sec"],
                                "unit": "sec",
                                "notes": "descanso entre bloques",
                            }
                        )
                    interval = {
                        "type": "repeat",
                        "reps": reps,
                        "steps": outer_steps,
                        "notes": parsed.get("notes"),
                    }
                else:
                    interval.update(
                        {
                            "target": parsed.get("target"),
                            "value": parsed.get("value"),
                            "unit": parsed.get("unit"),
                            "recovery_sec": parsed.get("recovery_sec", recovery),
                        }
                    )
                    if parsed.get("notes"):
                        interval["notes"] = parsed["notes"]
            else:
                interval["notes"] = workout_text
            return [
                {"type": "warmup", "target": "time", "value": 15, "unit": "min"},
                {"type": "repeat", "reps": reps, "steps": [interval]},
                {"type": "cooldown", "target": "time", "value": 10, "unit": "min"},
            ]
        if tipo == "fuerza":
            return [
                {
                    "type": "repeat",
                    "reps": 1,
                    "steps": [
                        {
                            "type": "strength",
                            "target": "time",
                            "value": duration_min,
                            "unit": "min",
                            "notes": workout_text,
                        }
                    ],
                }
            ]
        return [
            {
                "type": "main",
                "target": "time",
                "value": duration_min,
                "unit": "min",
                "zone": zone,
                "notes": workout_text,
            }
        ]

    sesiones = [
        {
            "name": "Rodaje suave 40'",
            "description": "Rodaje cómodo de base aeróbica.",
            "tipo_sesion": "rodaje",
            "volumen_base": 8.0,
            "intensidad_pct_vam": 0.65,
            "tags_json": ["rodaje", "suave"],
            "blocks_json": [
                {"type": "warmup", "target": "time", "value": 10, "unit": "min"},
                {"type": "main", "target": "distance", "value": 6, "unit": "km", "zone": "Z2"},
                {"type": "cooldown", "target": "time", "value": 5, "unit": "min"},
            ],
        },
        {
            "name": "Rodaje largo 90'",
            "description": "Rodaje largo progresivo.",
            "tipo_sesion": "rodaje",
            "volumen_base": 18.0,
            "intensidad_pct_vam": 0.7,
            "tags_json": ["rodaje", "largo", "resistencia"],
        },
        {
            "name": "Tempo 20'",
            "description": "Bloque continuo al umbral.",
            "tipo_sesion": "tempo",
            "volumen_base": 12.0,
            "intensidad_pct_vam": 0.85,
            "tags_json": ["tempo", "umbral"],
            "blocks_json": [
                {"type": "warmup", "target": "time", "value": 10, "unit": "min"},
                {"type": "main", "target": "time", "value": 20, "unit": "min", "zone": "Z3"},
                {"type": "cooldown", "target": "time", "value": 5, "unit": "min"},
            ],
        },
        {
            "name": "Series 4x1000",
            "description": "4 repeticiones de 1000m con recuperación.",
            "tipo_sesion": "series",
            "volumen_base": 8.0,
            "intensidad_pct_vam": 0.9,
            "formato_series": "4x1000",
            "recuperacion_seg": 120,
            "tags_json": ["series", "velocidad"],
            "blocks_json": [
                {"type": "warmup", "target": "distance", "value": 2, "unit": "km"},
                {
                    "type": "repeat",
                    "reps": 4,
                    "steps": [
                        {
                            "type": "interval",
                            "target": "distance",
                            "value": 1000,
                            "unit": "m",
                            "zone": "Z4",
                            "recovery_sec": 120,
                        }
                    ],
                },
                {"type": "cooldown", "target": "distance", "value": 2, "unit": "km"},
            ],
        },
        {
            "name": "Series 6x1000",
            "description": "6 repeticiones de 1000m con recuperación.",
            "tipo_sesion": "series",
            "volumen_base": 10.0,
            "intensidad_pct_vam": 0.9,
            "formato_series": "6x1000",
            "recuperacion_seg": 120,
            "tags_json": ["series", "umbral"],
            "blocks_json": [
                {"type": "warmup", "target": "distance", "value": 2, "unit": "km"},
                {
                    "type": "repeat",
                    "reps": 6,
                    "steps": [
                        {
                            "type": "interval",
                            "target": "distance",
                            "value": 1000,
                            "unit": "m",
                            "zone": "Z4",
                            "recovery_sec": 120,
                        }
                    ],
                },
                {"type": "cooldown", "target": "distance", "value": 2, "unit": "km"},
            ],
        },
        {
            "name": "Series 10x400",
            "description": "10 repeticiones de 400m con recuperación corta.",
            "tipo_sesion": "series",
            "volumen_base": 7.0,
            "intensidad_pct_vam": 0.95,
            "formato_series": "10x400",
            "recuperacion_seg": 90,
            "tags_json": ["series", "velocidad"],
            "blocks_json": [
                {"type": "warmup", "target": "distance", "value": 2, "unit": "km"},
                {
                    "type": "repeat",
                    "reps": 10,
                    "steps": [
                        {
                            "type": "interval",
                            "target": "distance",
                            "value": 400,
                            "unit": "m",
                            "zone": "Z5",
                            "recovery_sec": 90,
                        }
                    ],
                },
                {"type": "cooldown", "target": "distance", "value": 1.5, "unit": "km"},
            ],
        },
        {
            "name": "Series 8x500",
            "description": "8 repeticiones de 500m con recuperación moderada.",
            "tipo_sesion": "series",
            "volumen_base": 8.0,
            "intensidad_pct_vam": 0.9,
            "formato_series": "8x500",
            "recuperacion_seg": 90,
            "tags_json": ["series", "ritmo"],
            "blocks_json": [
                {"type": "warmup", "target": "distance", "value": 2, "unit": "km"},
                {
                    "type": "repeat",
                    "reps": 8,
                    "steps": [
                        {
                            "type": "interval",
                            "target": "distance",
                            "value": 500,
                            "unit": "m",
                            "zone": "Z4",
                            "recovery_sec": 90,
                        }
                    ],
                },
                {"type": "cooldown", "target": "distance", "value": 1.5, "unit": "km"},
            ],
        },
        {
            "name": "Fartlek 6x2'",
            "description": "Cambios de ritmo suaves.",
            "tipo_sesion": "tempo",
            "volumen_base": 9.0,
            "intensidad_pct_vam": 0.8,
            "formato_series": "6x2'",
            "recuperacion_seg": 60,
            "tags_json": ["fartlek", "ritmo"],
        },
        {
            "name": "Fuerza general",
            "description": "Sesión de fuerza básica y core.",
            "tipo_sesion": "fuerza",
            "volumen_base": None,
            "intensidad_pct_vam": None,
            "tags_json": ["fuerza", "core"],
            "blocks_json": [
                {
                    "type": "repeat",
                    "reps": 1,
                    "steps": [
                        {"type": "strength", "target": "time", "value": 15, "unit": "min", "notes": "core"},
                        {"type": "strength", "target": "time", "value": 15, "unit": "min", "notes": "tren superior"},
                        {"type": "strength", "target": "time", "value": 15, "unit": "min", "notes": "pierna"},
                    ],
                }
            ],
        },
        {
            "name": "Técnica de carrera",
            "description": "Ejercicios técnicos y coordinativos.",
            "tipo_sesion": "tecnica",
            "volumen_base": None,
            "intensidad_pct_vam": None,
            "tags_json": ["tecnica", "movilidad"],
            "blocks_json": [
                {"type": "main", "target": "time", "value": 30, "unit": "min", "notes": "skipping, multisaltos"},
            ],
        },
        {
            "name": "Rodaje regenerativo",
            "description": "Rodaje muy suave para recuperar.",
            "tipo_sesion": "rodaje",
            "volumen_base": 6.0,
            "intensidad_pct_vam": 0.6,
            "tags_json": ["rodaje", "recuperacion"],
            "blocks_json": [
                {"type": "main", "target": "distance", "value": 6, "unit": "km", "zone": "Z1"},
            ],
        },
    ]

    library_specs = [
        {"code":"BASE_01","name":"Rodaje suave 30'","goal":"base","level":"novice","duration_min":30,"load_est":3,"tags_json":["rodaje","Z2","suave"],"workout_text":"Rodaje 30' en Z2. + 4x20\" progresivos (rec 40\")."},
        {"code":"BASE_02","name":"Rodaje suave 40'","goal":"base","level":"novice","duration_min":40,"load_est":4,"tags_json":["rodaje","Z2"],"workout_text":"Rodaje 40' en Z2. Técnica 8' (skipping, talones, multisaltos suave)."},
        {"code":"BASE_03","name":"Rodaje continuo 50'","goal":"base","level":"intermediate","duration_min":50,"load_est":5,"tags_json":["rodaje","Z2"],"workout_text":"Rodaje 50' en Z2 estable. Últimos 5' un punto más (Z2 alta)."},
        {"code":"BASE_04","name":"Rodaje + rectas","goal":"base","level":"intermediate","duration_min":45,"load_est":5,"tags_json":["rodaje","rectas","técnica"],"workout_text":"Rodaje 35' Z2 + 8x100m recta alegre (rec caminar 60\"). + 10' enfriar suave."},
        {"code":"BASE_05","name":"Progresivo 45'","goal":"base","level":"intermediate","duration_min":45,"load_est":6,"tags_json":["progresivo","Z2","Z3"],"workout_text":"45' progresivo: 20' Z2 + 15' Z2 alta + 10' Z3 suave. Enfriar 10' opcional."},
        {"code":"BASE_06","name":"Rodaje largo 75'","goal":"base","level":"intermediate","duration_min":75,"load_est":7,"tags_json":["largo","Z2"],"workout_text":"Rodaje 75' en Z2. Si vas cargado: 60' y listo (la vida es sabia)."},
        {"code":"BASE_07","name":"Rodaje largo 90'","goal":"base","level":"advanced","duration_min":90,"load_est":8,"tags_json":["largo","Z2"],"workout_text":"Rodaje 90' Z2. Últimos 10' Z2 alta si te ves fino."},
        {"code":"BASE_08","name":"Fartlek suave 10x1'","goal":"base","level":"novice","duration_min":45,"load_est":5,"tags_json":["fartlek","cambios","Z2","Z3"],"workout_text":"Cal 15' + 10x(1' Z3 / 1' Z2) + Enf 10'."},
        {"code":"BASE_09","name":"Fartlek 12x1'","goal":"base","level":"intermediate","duration_min":50,"load_est":6,"tags_json":["fartlek","Z3"],"workout_text":"Cal 15' + 12x(1' Z3 / 1' suave) + Enf 10'."},
        {"code":"BASE_10","name":"Cambios 6x3'","goal":"base","level":"advanced","duration_min":60,"load_est":7,"tags_json":["cambios","Z3"],"workout_text":"Cal 15' + 6x(3' Z3 / 2' suave) + Enf 10'."},
        {"code":"REC_01","name":"Recuperación 25'","goal":"recovery","level":"novice","duration_min":25,"load_est":2,"tags_json":["recuperación","Z1","Z2"],"workout_text":"Rodaje 25' muy suave Z1-Z2 + movilidad 10'."},
        {"code":"REC_02","name":"Recuperación 35'","goal":"recovery","level":"intermediate","duration_min":35,"load_est":3,"tags_json":["recuperación","Z2"],"workout_text":"Rodaje 35' Z2 baja + 6x10\" técnica (sin apretar)."},
        {"code":"REC_03","name":"Rodaje regenerativo + strides","goal":"recovery","level":"advanced","duration_min":40,"load_est":4,"tags_json":["regenerativo","rectas"],"workout_text":"30' Z1-Z2 + 6x15\" strides (rec 45\") + enfriar 10'."},
        {"code":"REC_04","name":"Rodaje + movilidad + core","goal":"recovery","level":"intermediate","duration_min":45,"load_est":4,"tags_json":["movilidad","core"],"workout_text":"Rodaje 30' suave + movilidad 10' + core 10'."},
        {"code":"REC_05","name":"Descarga 50' Z2 baja","goal":"recovery","level":"advanced","duration_min":50,"load_est":4,"tags_json":["descarga","Z2"],"workout_text":"Rodaje 50' Z2 baja. Sin héroes, sin dramas."},
        {"code":"THR_01","name":"Tempo 2x10'","goal":"threshold","level":"novice","duration_min":50,"load_est":6,"tags_json":["umbral","tempo","Z3"],"workout_text":"Cal 15' + 2x10' Z3 (rec 3') + Enf 10'."},
        {"code":"THR_02","name":"Tempo 3x8'","goal":"threshold","level":"intermediate","duration_min":55,"load_est":7,"tags_json":["umbral","Z3"],"workout_text":"Cal 15' + 3x8' Z3 (rec 2') + Enf 10'."},
        {"code":"THR_03","name":"Tempo 20' continuo","goal":"threshold","level":"intermediate","duration_min":55,"load_est":7,"tags_json":["umbral","continuo"],"workout_text":"Cal 15' + 20' Z3 continuo + Enf 15'."},
        {"code":"THR_04","name":"Tempo 2x15'","goal":"threshold","level":"advanced","duration_min":65,"load_est":8,"tags_json":["umbral","Z3"],"workout_text":"Cal 15' + 2x15' Z3 (rec 4') + Enf 10'."},
        {"code":"THR_05","name":"Cruise intervals 5x6'","goal":"threshold","level":"advanced","duration_min":70,"load_est":8,"tags_json":["cruise","Z3"],"workout_text":"Cal 15' + 5x6' Z3 (rec 90\") + Enf 10'."},
        {"code":"THR_06","name":"Progressive tempo 30'","goal":"threshold","level":"advanced","duration_min":70,"load_est":8,"tags_json":["progresivo","umbral"],"workout_text":"Cal 15' + 30' progresivo (Z2 alta→Z3) + Enf 10'."},
        {"code":"THR_07","name":"Tempo en bloques 3-2-1","goal":"threshold","level":"intermediate","duration_min":55,"load_est":7,"tags_json":["umbral","bloques"],"workout_text":"Cal 15' + 3x(3' Z3 / 2' suave) + 3x(2' Z3 / 1' suave) + Enf 10'."},
        {"code":"THR_08","name":"Tempo 4x7'","goal":"threshold","level":"intermediate","duration_min":60,"load_est":7,"tags_json":["umbral","Z3"],"workout_text":"Cal 15' + 4x7' Z3 (rec 2') + Enf 10'."},
        {"code":"THR_09","name":"Tempo 3x12'","goal":"threshold","level":"advanced","duration_min":75,"load_est":9,"tags_json":["umbral","Z3"],"workout_text":"Cal 15' + 3x12' Z3 (rec 3') + Enf 10'."},
        {"code":"THR_10","name":"Tempo 25' continuo","goal":"threshold","level":"novice","duration_min":55,"load_est":6,"tags_json":["umbral","continuo"],"workout_text":"Cal 15' + 25' Z3 suave + Enf 10'."},
        {"code":"VO2_01","name":"VO2 8x400","goal":"vo2","level":"novice","duration_min":55,"load_est":7,"tags_json":["series","400","Z4"],"workout_text":"Cal 15' + 8x400m Z4 (rec 1') + Enf 10'."},
        {"code":"VO2_02","name":"VO2 10x400","goal":"vo2","level":"intermediate","duration_min":60,"load_est":8,"tags_json":["series","400","Z4"],"workout_text":"Cal 15' + 10x400m Z4 (rec 75\") + Enf 10'."},
        {"code":"VO2_03","name":"VO2 6x800","goal":"vo2","level":"intermediate","duration_min":65,"load_est":8,"tags_json":["series","800","Z4"],"workout_text":"Cal 15' + 6x800m Z4 (rec 2') + Enf 10'."},
        {"code":"VO2_04","name":"VO2 5x1000","goal":"vo2","level":"advanced","duration_min":70,"load_est":9,"tags_json":["series","1000","Z4"],"workout_text":"Cal 15' + 5x1000m Z4 (rec 2') + Enf 10'."},
        {"code":"VO2_05","name":"VO2 12x300","goal":"vo2","level":"intermediate","duration_min":55,"load_est":7,"tags_json":["series","300","Z4"],"workout_text":"Cal 15' + 12x300m Z4 (rec 60\") + Enf 10'."},
        {"code":"VO2_06","name":"VO2 16x200","goal":"vo2","level":"novice","duration_min":50,"load_est":6,"tags_json":["series","200","Z4"],"workout_text":"Cal 15' + 16x200m Z4 (rec 45\") + Enf 10'."},
        {"code":"VO2_07","name":"VO2 pirámide 200-400-600-800-600-400-200","goal":"vo2","level":"advanced","duration_min":75,"load_est":9,"tags_json":["pirámide","Z4"],"workout_text":"Cal 15' + 200/400/600/800/600/400/200 en Z4 (rec 90\") + Enf 10'."},
        {"code":"VO2_08","name":"VO2 3x(4x400)","goal":"vo2","level":"advanced","duration_min":75,"load_est":9,"tags_json":["series","bloques","400"],"workout_text":"Cal 15' + 3x(4x400m Z4 rec 60\") con 3' entre bloques + Enf 10'."},
        {"code":"VO2_09","name":"VO2 5x3'","goal":"vo2","level":"intermediate","duration_min":60,"load_est":8,"tags_json":["tiempo","Z4"],"workout_text":"Cal 15' + 5x3' Z4 (rec 2') + Enf 10'."},
        {"code":"VO2_10","name":"VO2 6x2'","goal":"vo2","level":"novice","duration_min":50,"load_est":7,"tags_json":["tiempo","Z4"],"workout_text":"Cal 15' + 6x2' Z4 (rec 2') + Enf 10'."},
        {"code":"SPD_01","name":"Velocidad 10x200","goal":"speed","level":"intermediate","duration_min":50,"load_est":7,"tags_json":["velocidad","200","Z5"],"workout_text":"Cal 15' + 10x200m Z5 (rec 200m suave) + Enf 10'."},
        {"code":"SPD_02","name":"Velocidad 12x150","goal":"speed","level":"novice","duration_min":45,"load_est":6,"tags_json":["velocidad","150","Z5"],"workout_text":"Cal 15' + 12x150m alegre Z5 controlado (rec 60-90\") + Enf 10'."},
        {"code":"SPD_03","name":"Velocidad 8x300","goal":"speed","level":"advanced","duration_min":55,"load_est":8,"tags_json":["velocidad","300","Z5"],"workout_text":"Cal 15' + 8x300m Z5 (rec 2') + Enf 10'."},
        {"code":"SPD_04","name":"Strides 12x100","goal":"speed","level":"novice","duration_min":35,"load_est":4,"tags_json":["strides","técnica"],"workout_text":"Cal 15' suave + 12x100m strides (rec 60\") + Enf 10'."},
        {"code":"SPD_05","name":"Mixto 6x400 + 6x200","goal":"speed","level":"advanced","duration_min":70,"load_est":9,"tags_json":["mixto","400","200"],"workout_text":"Cal 15' + 6x400m Z4 (rec 90\") + 6x200m Z5 (rec 60\") + Enf 10'."},
        {"code":"HILL_01","name":"Cuestas cortas 10x20\"","goal":"hills","level":"novice","duration_min":45,"load_est":6,"tags_json":["cuestas","fuerza","corta"],"workout_text":"Cal 15' + 10x20\" cuesta fuerte (rec bajada) + Enf 10'."},
        {"code":"HILL_02","name":"Cuestas cortas 12x30\"","goal":"hills","level":"intermediate","duration_min":55,"load_est":7,"tags_json":["cuestas","30s"],"workout_text":"Cal 15' + 12x30\" cuesta (rec bajada) + Enf 10'."},
        {"code":"HILL_03","name":"Cuestas largas 6x2'","goal":"hills","level":"advanced","duration_min":65,"load_est":8,"tags_json":["cuestas","larga","Z4"],"workout_text":"Cal 15' + 6x2' cuesta Z4 (rec bajada suave 2') + Enf 10'."},
        {"code":"HILL_04","name":"Cuestas medias 8x1'","goal":"hills","level":"intermediate","duration_min":60,"load_est":8,"tags_json":["cuestas","media"],"workout_text":"Cal 15' + 8x1' cuesta fuerte (rec bajada 1') + Enf 10'."},
        {"code":"HILL_05","name":"Trail fartlek 10x1'","goal":"hills","level":"advanced","duration_min":60,"load_est":8,"tags_json":["trail","fartlek","cuestas"],"workout_text":"Cal 15' + 10x(1' fuerte en terreno ondulado / 1' suave) + Enf 10'."},
        {"code":"RACE_01","name":"Ritmo carrera 3x2k","goal":"race","level":"advanced","duration_min":75,"load_est":9,"tags_json":["ritmo carrera","2000"],"workout_text":"Cal 15' + 3x2000m a ritmo objetivo (rec 3') + Enf 10'."},
        {"code":"RACE_02","name":"Ritmo carrera 4x1k","goal":"race","level":"intermediate","duration_min":60,"load_est":8,"tags_json":["ritmo carrera","1000"],"workout_text":"Cal 15' + 4x1000m a ritmo objetivo (rec 2') + Enf 10'."},
        {"code":"RACE_03","name":"Ritmo carrera 6x800","goal":"race","level":"intermediate","duration_min":65,"load_est":8,"tags_json":["ritmo carrera","800"],"workout_text":"Cal 15' + 6x800m ritmo objetivo (rec 2') + Enf 10'."},
        {"code":"RACE_04","name":"Ritmo 5k 5x1k","goal":"race","level":"advanced","duration_min":70,"load_est":9,"tags_json":["5k","1000"],"workout_text":"Cal 15' + 5x1000m ritmo 5k (rec 2') + Enf 10'."},
        {"code":"RACE_05","name":"Ritmo 10k 3x3k","goal":"race","level":"advanced","duration_min":85,"load_est":9,"tags_json":["10k","3000"],"workout_text":"Cal 15' + 3x3000m ritmo 10k (rec 3') + Enf 10'."},
        {"code":"STR_01","name":"Fuerza general 30'","goal":"strength","level":"novice","duration_min":30,"load_est":4,"tags_json":["fuerza","core"],"workout_text":"Circuito 3 rondas: sentadilla, zancadas, puente glúteo, plancha, gemelos (30-40\" cada)."},
        {"code":"STR_02","name":"Fuerza + técnica 40'","goal":"strength","level":"intermediate","duration_min":40,"load_est":5,"tags_json":["fuerza","técnica"],"workout_text":"10' técnica carrera + 25' fuerza (pierna/core) + 5' movilidad."},
        {"code":"STR_03","name":"Gimnasio pierna 45'","goal":"strength","level":"advanced","duration_min":45,"load_est":6,"tags_json":["gimnasio","pierna"],"workout_text":"Sentadilla / peso muerto rumano / step-up / gemelo + core. 3-4 series, sin morir (hoy)."},
        {"code":"STR_04","name":"Movilidad 20'","goal":"strength","level":"novice","duration_min":20,"load_est":2,"tags_json":["movilidad","recuperación"],"workout_text":"Movilidad cadera/tobillo + estiramientos suaves + respiración 20'."},
        {"code":"STR_05","name":"Pliometría suave 25'","goal":"strength","level":"intermediate","duration_min":25,"load_est":4,"tags_json":["pliometría","técnica"],"workout_text":"Pliometría suave: multisaltos cortos, skipping, saltos a cajón bajo. 20-25'."},
        {"code":"MIX_01","name":"Mixto umbral + rectas","goal":"threshold","level":"intermediate","duration_min":60,"load_est":7,"tags_json":["umbral","rectas"],"workout_text":"Cal 15' + 15' Z3 + 6x100m recta (rec 60\") + Enf 10'."},
        {"code":"MIX_02","name":"Mixto Z3 + 6x200","goal":"speed","level":"advanced","duration_min":70,"load_est":8,"tags_json":["mixto","umbral","200"],"workout_text":"Cal 15' + 20' Z3 + 6x200m Z5 (rec 90\") + Enf 10'."},
        {"code":"MIX_03","name":"Series suaves 6x600","goal":"vo2","level":"novice","duration_min":55,"load_est":7,"tags_json":["600","Z4"],"workout_text":"Cal 15' + 6x600m Z4 (rec 90\") + Enf 10'."},
        {"code":"MIX_04","name":"Cambios 5-4-3-2-1","goal":"base","level":"advanced","duration_min":65,"load_est":7,"tags_json":["cambios","progresivo"],"workout_text":"Cal 15' + 5'/4'/3'/2'/1' Z3 con 2' suave entre + Enf 10'."},
        {"code":"MIX_05","name":"Fartlek 3x(4' fuerte/2' suave)","goal":"threshold","level":"novice","duration_min":50,"load_est":6,"tags_json":["fartlek","Z3"],"workout_text":"Cal 15' + 3x(4' Z3 / 2' suave) + Enf 10'."},
        {"code":"XC_01","name":"Cross: 12x1' ondulado","goal":"race","level":"intermediate","duration_min":60,"load_est":8,"tags_json":["cross","ondulado"],"workout_text":"Cal 15' + 12x(1' fuerte ondulado / 1' suave) + Enf 10'."},
        {"code":"XC_02","name":"Cross: 6x3' terreno","goal":"race","level":"advanced","duration_min":70,"load_est":9,"tags_json":["cross","terreno"],"workout_text":"Cal 15' + 6x3' fuerte en terreno (rec 2') + Enf 10'."},
        {"code":"XC_03","name":"Cross: tempo 25' + 6x20\"","goal":"race","level":"advanced","duration_min":70,"load_est":9,"tags_json":["cross","tempo","strides"],"workout_text":"Cal 15' + 25' Z3 en circuito + 6x20\" fuerte (rec 40\") + Enf 10'."},
        {"code":"XC_04","name":"Cross: cuestas 10x45\"","goal":"hills","level":"advanced","duration_min":70,"load_est":9,"tags_json":["cross","cuestas"],"workout_text":"Cal 15' + 10x45\" cuesta fuerte (rec bajada) + Enf 10'."},
        {"code":"XC_05","name":"Cross: 3x2k circuito","goal":"race","level":"advanced","duration_min":80,"load_est":9,"tags_json":["cross","2000"],"workout_text":"Cal 15' + 3x2000m en circuito (ritmo objetivo) rec 3' + Enf 10'."},
        {"code":"EASY_01","name":"Rodaje 45' + 6 rectas","goal":"base","level":"novice","duration_min":45,"load_est":5,"tags_json":["rodaje","rectas"],"workout_text":"Rodaje 45' Z2 + 6x80-100m recta (rec 60\")."},
        {"code":"EASY_02","name":"Rodaje 60' estable","goal":"base","level":"intermediate","duration_min":60,"load_est":6,"tags_json":["rodaje","Z2"],"workout_text":"Rodaje 60' Z2 estable. Hidratación y a casa."},
        {"code":"EASY_03","name":"Rodaje 30' + técnica 10'","goal":"recovery","level":"novice","duration_min":40,"load_est":3,"tags_json":["técnica","suave"],"workout_text":"Rodaje 30' suave + técnica 10'."},
        {"code":"EASY_04","name":"Rodaje 50' + 8x20\"","goal":"base","level":"advanced","duration_min":55,"load_est":6,"tags_json":["rodaje","aceleraciones"],"workout_text":"Rodaje 50' Z2 + 8x20\" alegres (rec 40\")."},
        {"code":"EASY_05","name":"Rodaje 70' progresivo suave","goal":"base","level":"advanced","duration_min":70,"load_est":7,"tags_json":["progresivo","Z2","Z3"],"workout_text":"70' progresivo: 40' Z2 + 20' Z2 alta + 10' Z3 suave."},
    ]

    for spec in library_specs:
        tags = list(spec["tags_json"])
        tags.append(spec["goal"])
        tags.append(spec["level"])
        tipo_sesion = _infer_tipo(tags, spec["goal"])
        zone = _infer_zone(tags)
        volumen_base = _volumen_from_duration(spec.get("duration_min"))
        blocks_json = _blocks_for_workout(spec)
        sesiones.append(
            {
                "name": spec["name"],
                "description": spec["workout_text"],
                "tipo_sesion": tipo_sesion,
                "volumen_base": volumen_base,
                "intensidad_pct_vam": None if zone is None else {
                    "Z1": 0.6,
                    "Z2": 0.7,
                    "Z3": 0.8,
                    "Z4": 0.9,
                    "Z5": 0.95,
                }[zone],
                "formato_series": None,
                "recuperacion_seg": _parse_recovery_seconds(spec.get("workout_text", "")),
                "tags_json": tags,
                "blocks_json": blocks_json,
            }
        )

    for s in sesiones:
        session.add(SessionCatalog(**s))
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
    crear_templates_catalog(session)
    crear_sessions_catalog(session)

    print("✔ Base de datos de ejemplo creada correctamente")


if __name__ == "__main__":
    main()
