"""Contratos de datos que preservan procedencia y validan el contexto documental."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaginaExtraida(BaseModel):
    """Representa una página y registra cómo se obtuvo su texto.

    La procedencia permite que un agente cite evidencia y distinga parsing de OCR.
    """
    model_config = ConfigDict(extra="forbid")
    source: str
    page: int = Field(ge=1)
    text: str
    extraction_method: str


class ChunkDocumento(BaseModel):
    """Representa un fragmento recuperable con identidad y metadatos verificables.

    Este contrato es clave para no entregar al agente texto huérfano sin fuente,
    página ni método de extracción.
    """
    model_config = ConfigDict(extra="forbid")
    chunk_id: str
    text: str = Field(min_length=1)
    source: str
    page: int = Field(ge=1)
    section: str | None = None
    document_type: str | None = None
    extraction_method: str
    chunk_index: int = Field(ge=0)


class VectorRecord(BaseModel):
    """Asocia un chunk validado con su embedding para búsqueda semántica.

    Mantener unidos contenido y vector evita perder trazabilidad durante retrieval.
    """
    model_config = ConfigDict(extra="forbid")
    chunk: ChunkDocumento
    embedding: list[float]
