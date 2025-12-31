def ajustar_entrenamientos_diarios(entrenamientos, alertas_semana):
    """
    Ajusta entrenamientos individuales según alertas semanales.
    """
    ajustes = []

    for e in entrenamientos:
        if e.tipo_sesion in ("series", "tempo") and alertas_semana:
            ajuste = {
                "fecha": e.fecha,
                "tipo_original": e.tipo_sesion,
                "acciones": []
            }

            # Reducir volumen
            if e.volumen_objetivo:
                nuevo_vol = round(e.volumen_objetivo * 0.85, 1)
                ajuste["acciones"].append(
                    f"Reducir volumen de {e.volumen_objetivo} km a {nuevo_vol} km"
                )

            # Bajar intensidad
            if e.ritmo_objetivo:
                ajuste["acciones"].append(
                    "Reducir intensidad (ritmo más conservador)"
                )

            ajustes.append(ajuste)

    return ajustes
