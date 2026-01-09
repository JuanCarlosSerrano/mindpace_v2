from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Literal
from decimal import Decimal, ROUND_HALF_UP

@dataclass(frozen=True)
class AthleteContext:
    edad: int | None
    volumen_actual_km: float | None
    vam: float | None  # km/h

    @property
    def grupo_edad(self) -> Literal["menor", "adulto"]:
        if self.edad is not None and self.edad < 18:
            return "menor"
        return "adulto"

    @property
    def nivel_volumen(self) -> Literal["bajo", "medio", "alto"]:
        v = float(self.volumen_actual_km or 0)
        if v < 40:
            return "bajo"
        if v < 80:
            return "medio"
        return "alto"


def ajustar_volumen_sesion(volumen_base: float | None, ctx: AthleteContext) -> float | None:
    """Ajuste simple: si el atleta hace poco volumen, recorta un poco; si hace mucho, sube un poco."""
    if volumen_base is None:
        return None
    factor = 1.0
    if ctx.nivel_volumen == "bajo":
        factor = 0.85
    elif ctx.nivel_volumen == "alto":
        factor = 1.10
    return round(float(volumen_base) * factor, 2)


def ritmo_objetivo_por_vam(vam_kmh: float | None, tipo_sesion: str) -> int | None:
    """
    Estima ritmo objetivo (seg/km) en función de VAM.
    Regla v1:
      - rodaje: 70% VAM
      - series: 95% VAM
      - fuerza/descanso: None
    """
    if not vam_kmh or vam_kmh <= 0:
        return None

    tipo = (tipo_sesion or "").lower().strip()
    if tipo in ("fuerza", "descanso"):
        return None

    if tipo == "rodaje":
        pct = 0.70
    elif tipo == "series":
        pct = 0.95
    else:
        pct = 0.80  # por defecto (tempo suave / técnica / etc.)

    velocidad_obj_kmh = vam_kmh * pct
    # seg/km = 3600 / (km/h)
    seg_por_km = int(round(3600 / velocidad_obj_kmh))
    return seg_por_km


def limitar_intensidad_menores(intensidad_pct_vam: float | None, ctx: AthleteContext) -> float | None:
    """
    Seguridad v1: en menores limitamos intensidad máxima al 0.92 (92% VAM).
    """
    if intensidad_pct_vam is None:
        return None
    if ctx.grupo_edad == "menor":
        return float(min(float(intensidad_pct_vam), 0.92))
    return float(intensidad_pct_vam)

def es_semana_descarga(semana: int) -> bool:
    """
    Regla v1: cada 4 semanas hay descarga.
    """
    return semana % 4 == 0

def aplicar_descarga(volumen, semana):
    if volumen is None:
        return None

    if semana % 4 == 0:
        return (
            (volumen * Decimal("0.70"))
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    return volumen


