def analizar_tendencia_semanal(analisis_semanal: dict):
    """
    Añade información de tendencia comparando semanas consecutivas.
    Detecta subida brusca y subida sostenida.
    """
    semanas = list(analisis_semanal.keys())
    resultado = {}

    carga_prev = None
    subidas_consecutivas = 0  # 🔑 memoria de semanas previas

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
                subidas_consecutivas += 1
            else:
                subidas_consecutivas = 0

            if variacion_pct > 0.05 and variacion_pct <= 0.25:
                tendencia = "⬆️ subida controlada"
            elif variacion_pct < -0.20:
                tendencia = "📉 bajada fuerte"
                alertas.append("⚠️ Descarga muy pronunciada")
            elif variacion_pct is not None and abs(variacion_pct) <= 0.05:
                tendencia = "➖ estable"
            elif variacion_pct is not None and variacion_pct < 0:
                tendencia = "⬇️ bajada suave"

            # 🔥 NUEVO: subida sostenida
            if subidas_consecutivas >= 2:
                alertas.append("🚨 Subida sostenida sin descarga")

        resultado[semana] = {
            **data,
            "tendencia": tendencia,
            "variacion_pct": round(variacion_pct * 100, 1) if variacion_pct is not None else None,
            "alertas": alertas
        }

        carga_prev = carga

    return resultado
