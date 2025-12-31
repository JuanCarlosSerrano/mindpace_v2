def analizar_tendencia_semanal(analisis_semanal: dict):
    """
    Añade información de tendencia comparando semanas consecutivas.
    """
    semanas = list(analisis_semanal.keys())
    resultado = {}

    carga_prev = None

    for semana in semanas:
        data = analisis_semanal[semana]
        carga = data["indice_carga"]

        tendencia = "—"
        variacion_pct = None
        alertas = list(data["alertas"])  # copiamos las existentes

        if carga_prev is not None and carga_prev > 0:
            variacion_pct = (carga - carga_prev) / carga_prev

            if variacion_pct > 0.25:
                tendencia = "📈 subida brusca"
                alertas.append("🚨 Progresión demasiado rápida")
            elif variacion_pct > 0.05:
                tendencia = "⬆️ subida controlada"
            elif variacion_pct < -0.20:
                tendencia = "📉 bajada fuerte"
                alertas.append("⚠️ Descarga muy pronunciada")
            elif abs(variacion_pct) <= 0.05:
                tendencia = "➖ estable"
            else:
                tendencia = "⬇️ bajada suave"

        resultado[semana] = {
            **data,
            "tendencia": tendencia,
            "variacion_pct": round(variacion_pct * 100, 1) if variacion_pct is not None else None,
            "alertas": alertas
        }

        carga_prev = carga

    return resultado
