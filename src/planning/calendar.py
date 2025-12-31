from datetime import date, timedelta

def fecha_lunes_semana(fecha_inicio: date) -> date:
    """
    Devuelve el lunes de la semana en la que cae fecha_inicio.
    Si fecha_inicio ya es lunes, la devuelve igual.
    """
    return fecha_inicio - timedelta(days=fecha_inicio.weekday())


def fecha_por_semana_y_dia(
    lunes_semana_1: date,
    semana: int,
    dia_semana: int
) -> date:
    """
    Calcula la fecha real de una sesión.
    semana: 1..N
    dia_semana: 1=lunes .. 7=domingo
    """
    return lunes_semana_1 + timedelta(
        days=(semana - 1) * 7 + (dia_semana - 1)
    )
