"""Esquema de salida estructurada esperado al procesar un ticket de soporte."""

from typing import Literal

from pydantic import BaseModel, Field


class ResultadoTicket(BaseModel):
    """Define los campos y restricciones de una respuesta operativa del agente.

    Un esquema explícito reduce ambigüedad, facilita validación automática y separa
    recomendaciones de acciones realmente ejecutadas o sujetas a revisión humana.
    """
    resumen: str = Field(min_length=1)
    sistema_afectado: str | None = None
    criticidad: Literal["baja", "media", "alta", "critica"]
    sla_horas: int | None = None
    estado_sistema: str | None = None
    causa_confirmada: bool = False
    accion_recomendada: str
    requiere_escalamiento: bool
    accion_ejecutada: bool = False
    requiere_revision_humana: bool
