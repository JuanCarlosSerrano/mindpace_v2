from src.ai.coach import (
    _evitar_descarga_consecutiva,
    _modular_acciones_por_cumplimiento,
)


def test_evitar_descarga_consecutiva():
    acciones = ["Reducir volumen semanal un 10%", "Semana marcada como descarga"]
    semanas_descarga = {"2026-W02"}
    filtradas = _evitar_descarga_consecutiva(acciones, "2026-W03", semanas_descarga)
    assert all("descarga" not in a.lower() for a in filtradas)


def test_modular_acciones_por_tipo_sesion():
    acciones = ["Reducir volumen semanal un 10%", "Eliminar 1 sesión dura"]
    cumplimiento = {
        "estado": "cumplida",
        "sesiones_planificadas_peso": 4.0,
        "sesiones_realizadas_peso": 2.0,
    }
    moduladas = _modular_acciones_por_cumplimiento(acciones, cumplimiento)
    assert all("reducir volumen" not in a.lower() for a in moduladas)
    assert all("eliminar" not in a.lower() for a in moduladas)
