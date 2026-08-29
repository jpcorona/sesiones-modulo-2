"""Almacén vectorial JSON simple para enseñar recuperación con trazabilidad."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from document_models import ChunkDocumento, VectorRecord


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calcula similitud coseno entre dos embeddings.

    Esta medida permite ordenar evidencia por cercanía semántica antes de dársela
    al agente; el control del vector nulo evita resultados numéricos inválidos.
    """
    va = np.asarray(a, dtype=float)
    vb = np.asarray(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class JsonVectorStore:
    """Índice educativo local; en producción puede reemplazarse por un vector DB.

    Encapsular persistencia y búsqueda desacopla el agente de una tecnología concreta.
    """

    def __init__(self, path: str | Path):
        """Inicializa un índice vacío y conserva la ruta donde se persistirá."""
        self.path = Path(path)
        self.records: list[VectorRecord] = []

    def add(self, chunk: ChunkDocumento, embedding: list[float]) -> None:
        """Agrega contenido y vector como una unidad validada y trazable."""
        self.records.append(VectorRecord(chunk=chunk, embedding=embedding))

    def save(self) -> None:
        """Serializa el índice para reutilizarlo sin recalcular embeddings."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.model_dump() for record in self.records]
        self.path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def load(self) -> None:
        """Carga y revalida el índice para detectar datos incompatibles temprano."""
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.records = [VectorRecord.model_validate(item) for item in payload]

    def search(self, query_embedding: list[float], top_k: int = 3):
        """Devuelve los chunks más similares que formarán el contexto del agente."""
        scored = [
            (cosine_similarity(query_embedding, record.embedding), record.chunk)
            for record in self.records
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]
