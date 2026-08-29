"""Persistencia y búsqueda léxica local para el contexto documental didáctico."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_INDEX = Path(__file__).parent / "data" / "processed" / "chunks.json"


def guardar_chunks(chunks: list[dict[str, Any]], output_path: str | Path) -> None:
    """Guarda chunks en JSON para separar ingesta de consulta y hacerla repetible."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


def cargar_chunks(index_path: str | Path = DEFAULT_INDEX) -> list[dict[str, Any]]:
    """Carga el índice local o devuelve una colección vacía si aún no existe."""
    path = Path(index_path)
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> set[str]:
    """Normaliza texto a tokens únicos comparables por la búsqueda léxica."""
    return set(re.findall(r"[a-záéíóúñ0-9]+", text.lower()))


def buscar_documentacion(
    consulta: str,
    *,
    index_path: str | Path = DEFAULT_INDEX,
    top_k: int = 3,
) -> dict[str, Any]:
    """Recupera por coincidencia léxica y conserva metadatos de procedencia.

    Esta línea base hace visible qué evidencia recibe el agente antes de introducir
    embeddings; así se puede medir si la búsqueda semántica mejora el contexto.
    """
    query_tokens = _tokens(consulta)
    chunks = cargar_chunks(index_path)
    scored = []
    for chunk in chunks:
        score = len(query_tokens & _tokens(chunk["text"]))
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)

    results = [
        {"score": score, "text": chunk["text"], "metadata": chunk["metadata"]}
        for score, chunk in scored[:top_k]
    ]
    return {
        "estado": "ok",
        "consulta": consulta,
        "resultados": results,
        "total_indexado": len(chunks),
    }
