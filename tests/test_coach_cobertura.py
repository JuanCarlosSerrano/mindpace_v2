from decimal import Decimal

from src.ai.coach import _cobertura_suficiente


def test_cobertura_requiere_sesiones_minimas():
    cumplimiento = {
        "estado": "parcial",
        "sesiones_planificadas": 4,
        "sesiones_realizadas": 1,
        "ratio_sesiones": Decimal("0.25"),
    }
    assert _cobertura_suficiente(cumplimiento) is False


def test_cobertura_requiere_ratio_minimo():
    cumplimiento = {
        "estado": "parcial",
        "sesiones_planificadas": 4,
        "sesiones_realizadas": 2,
        "ratio_sesiones": Decimal("0.40"),
    }
    assert _cobertura_suficiente(cumplimiento) is False


def test_cobertura_ok_con_minimo_cumplido():
    cumplimiento = {
        "estado": "parcial",
        "sesiones_planificadas": 2,
        "sesiones_realizadas": 2,
        "ratio_sesiones": Decimal("1.00"),
    }
    assert _cobertura_suficiente(cumplimiento) is True


def test_cobertura_usa_ratio_ponderado_por_tipo():
    cumplimiento = {
        "estado": "parcial",
        "sesiones_planificadas": 4,
        "sesiones_realizadas": 3,
        "ratio_sesiones": Decimal("0.75"),
        "sesiones_planificadas_peso": 4.0,
        "sesiones_realizadas_peso": 1.0,
    }
    assert _cobertura_suficiente(cumplimiento) is False
