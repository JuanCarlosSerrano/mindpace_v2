from src.ai.coach import _filtrar_acciones_no_data, _modular_acciones_por_cumplimiento


def test_no_data_no_incluye_reducir_volumen():
    acciones = [
        "Reducir volumen semanal un 10%",
        "Semana marcada como descarga",
    ]
    filtradas = _filtrar_acciones_no_data(acciones)
    assert all("reducir volumen" not in a.lower() for a in filtradas)


def test_no_data_no_incluye_eliminar_sesion_dura():
    acciones = [
        "Eliminar 1 sesión dura",
        "Semana marcada como descarga",
    ]
    filtradas = _filtrar_acciones_no_data(acciones)
    assert all("eliminar" not in a.lower() for a in filtradas)


def test_no_data_con_alerta_permita_descarga_suave():
    acciones = [
        "Reducir volumen semanal un 10%",
        "Eliminar 1 sesión dura",
        "Semana marcada como descarga",
    ]
    cumplimiento = {"estado": "datos_insuficientes"}
    moduladas = _modular_acciones_por_cumplimiento(acciones, cumplimiento)
    assert "Semana marcada como descarga" in moduladas
    assert all("reducir volumen" not in a.lower() for a in moduladas)
    assert all("eliminar" not in a.lower() for a in moduladas)
