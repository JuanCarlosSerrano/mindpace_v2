from decimal import Decimal, ROUND_HALF_UP


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
                nuevo_vol = (e.volumen_objetivo * Decimal("0.85")).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
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
