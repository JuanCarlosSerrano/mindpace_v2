from collections import defaultdict

SESIONES_DURAS = {"series", "tempo", "intervalos"}

def analizar_carga_semanal(plan_semanal: dict):
    """
    Añade métricas de carga y alertas a la vista semanal.
    Detecta subida brusca y sostenida de volumen.
    """
    semanas_ordenadas = sorted(
    plan_semanal.items(),
    key=lambda x: (int(x[0].split("-W")[0]), int(x[0].split("-W")[1]))
    )

    resultado = {}

    volumen_prev = None
    subidas_consecutivas = 0

    for semana, data in semanas_ordenadas:
        volumen = data["volumen_total"]
        sesiones_duras = sum(
            n for tipo, n in data["por_tipo"].items()
            if tipo in SESIONES_DURAS
        )

        # 🔥 Índice de carga (volumen pesa más)
        carga = volumen * 1.5 + sesiones_duras * 5

        alertas = []

        # Regla 1: demasiadas sesiones duras
        if sesiones_duras >= 3:
            alertas.append("⚠️ Demasiadas sesiones duras")

        # Regla 2: volumen
        if volumen_prev is not None and volumen_prev > 0:
            incremento = (volumen - volumen_prev) / volumen_prev

            if incremento > 0.10:
                alertas.append("🚨 Aumento de volumen > 25%")
                subidas_consecutivas += 1
            else:
                subidas_consecutivas = 0

            # 🔥 NUEVO: subida sostenida
            if subidas_consecutivas >= 2:
                alertas.append("🚨 Subida sostenida de volumen")

        resultado[semana] = {
            **data,
            "sesiones_duras": sesiones_duras,
            "indice_carga": round(carga, 1),
            "alertas": alertas
        }

        volumen_prev = volumen
        print(
            f"[CARGA] {semana} | vol={volumen:.1f} | "
            f"carga={carga:.1f} | alertas={alertas}"
        )
    return resultado


