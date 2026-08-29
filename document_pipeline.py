"""Etapas de extracción, render, segmentación y enriquecimiento de documentos."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF
from pypdf import PdfReader

from document_models import ChunkDocumento, PaginaExtraida


def parse_pdf_text(pdf_path: str | Path) -> list[PaginaExtraida]:
    """Extrae la capa de texto de cada página sin realizar OCR.

    Probar primero el método más directo reduce costo y latencia, y registrar el
    método evita que un futuro agente confunda texto digital con texto inferido.
    """
    path = Path(pdf_path)
    reader = PdfReader(str(path))
    paginas: list[PaginaExtraida] = []
    for numero, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        paginas.append(
            PaginaExtraida(
                source=path.name,
                page=numero,
                text=text,
                extraction_method="pdf_text_layer",
            )
        )
    return paginas


def pdf_page_to_png_bytes(pdf_path: str | Path, page_number: int, dpi: int = 180) -> bytes:
    """Renderiza una página como PNG para que un motor OCR pueda verla.

    Esta conversión es el puente necesario cuando el PDF solo contiene píxeles.
    """
    doc = fitz.open(str(pdf_path))
    try:
        page = doc.load_page(page_number - 1)
        zoom = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def image_bytes_to_data_url(image_bytes: bytes, mime: str = "image/png") -> str:
    """Codifica una imagen en una URL de datos aceptada por una entrada multimodal."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def chunk_text(text: str, *, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Divide texto en ventanas solapadas con parámetros defensivamente validados.

    Los chunks caben mejor en el contexto del agente y el overlap reduce la pérdida
    de significado en los límites, aunque aumenta almacenamiento y redundancia.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser > 0")
    if overlap < 0:
        raise ValueError("overlap debe ser >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap debe ser menor que chunk_size")

    clean = " ".join(text.split())
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_size)
        piece = clean[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(clean):
            break
        start += chunk_size - overlap
    return chunks


def infer_section(text: str) -> str | None:
    """Asigna una sección didáctica por palabras clave para mejorar filtros y citas."""
    lowered = text.lower()
    rules = [
        ("vacaciones", "Vacaciones"),
        ("incidente", "Incidentes"),
        ("temperatura", "Temperatura"),
        ("mantenimiento", "Mantenimiento"),
        ("bomba", "Operación de bomba"),
    ]
    for keyword, section in rules:
        if keyword in lowered:
            return section
    return None


def infer_document_type(source: str) -> str:
    """Infiere un tipo documental básico desde el nombre de la fuente.

    Clasificar antes de recuperar permite aplicar políticas distintas por documento.
    """
    lowered = source.lower()
    if "politica" in lowered:
        return "politica"
    if "orden" in lowered or "trabajo" in lowered:
        return "orden_trabajo"
    return "documento"


def make_chunks(
    paginas: Iterable[PaginaExtraida],
    *,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[ChunkDocumento]:
    """Convierte páginas extraídas en chunks tipados, identificables y trazables.

    Esta es una frontera crítica antes del agente: el texto adquiere fuente, página,
    sección e ID estable, datos necesarios para recuperar y auditar evidencia.
    """
    output: list[ChunkDocumento] = []
    for pagina in paginas:
        pieces = chunk_text(pagina.text, chunk_size=chunk_size, overlap=overlap)
        for idx, piece in enumerate(pieces):
            raw_id = f"{pagina.source}:{pagina.page}:{idx}:{piece[:80]}"
            chunk_id = hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:16]
            output.append(
                ChunkDocumento(
                    chunk_id=chunk_id,
                    text=piece,
                    source=pagina.source,
                    page=pagina.page,
                    section=infer_section(piece),
                    document_type=infer_document_type(pagina.source),
                    extraction_method=pagina.extraction_method,
                    chunk_index=idx,
                )
            )
    return output
