from collections import defaultdict

SESIONES_DURAS = {"series", "tempo", "intervalos"}


def analizar_carga_semanal(plan_semanal: dict):
    """
    Añade métricas de carga y alertas a la vista semanal.
    """
    semanas_ordenadas = sorted(plan_semanal.items())
    resultado = {}

    volumen_prev = None

    for semana, data in semanas_ordenadas:
        volumen = data["volumen_total"]
        sesiones_duras = sum(
            n for tipo, n in data["por_tipo"].items()
            if tipo in SESIONES_DURAS
        )

        # Índice simple de carga
        carga = volumen + sesiones_duras * 5

        alertas = []

        # Regla 1: demasiadas sesiones duras
        if sesiones_duras >= 3:
            alertas.append("⚠️ Demasiadas sesiones duras")

        # Regla 2: salto brusco de volumen
        if volumen_prev is not None:
            incremento = (volumen - volumen_prev) / volumen_prev if volumen_prev > 0 else 0
            if incremento > 0.25:
                alertas.append("🚨 Aumento de volumen > 25%")

        resultado[semana] = {
            **data,
            "sesiones_duras": sesiones_duras,
            "indice_carga": round(carga, 1),
            "alertas": alertas
        }

        volumen_prev = volumen

    return resultado
