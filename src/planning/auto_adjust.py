def ajustar_plan_semanal(analisis_tendencia: dict):
    """
    Aplica ajustes automáticos al plan en base a alertas detectadas.
    Devuelve propuestas de ajuste por semana.
    """
    ajustes = {}

    for semana, data in analisis_tendencia.items():
        acciones = []

        volumen = data["volumen_total"]
        sesiones_duras = data["sesiones_duras"]
        alertas = data["alertas"]

        nuevo_volumen = volumen
        nuevas_sesiones_duras = sesiones_duras

        # Regla 1: subida brusca
        if any("subida" in a.lower() for a in alertas):
            nuevo_volumen = round(volumen * 0.85, 1)
            acciones.append(
                f"Reducir volumen de {volumen} km a {nuevo_volumen} km"
            )

            if sesiones_duras > 0:
                nuevas_sesiones_duras -= 1
                acciones.append("Eliminar 1 sesión dura")

        # Regla 2: demasiadas sesiones duras
        if sesiones_duras >= 3:
            nuevas_sesiones_duras -= 1
            acciones.append("Convertir 1 sesión dura en rodaje")

        # Regla 3: descarga fuerte
        if any("descarga" in a.lower() for a in alertas):
            acciones.append("Semana marcada como descarga")

        if acciones:
            ajustes[semana] = {
                "volumen_original": volumen,
                "volumen_propuesto": nuevo_volumen,
                "sesiones_duras_original": sesiones_duras,
                "sesiones_duras_propuestas": nuevas_sesiones_duras,
                "acciones": acciones
            }

    return ajustes
