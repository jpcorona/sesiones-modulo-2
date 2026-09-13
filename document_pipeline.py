"""Etapas de extracción, render, segmentación y enriquecimiento de documentos."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF
from pydantic import BaseModel
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


def extract_pdf_pages(pdf_path: str | Path, *, use_ocr: bool = True) -> list[PaginaExtraida]:
    """Conserva texto digital y aplica OCR solo a páginas con poco texto."""
    paginas = parse_pdf_text(pdf_path)
    # El umbral de 40 caracteres es una heurística: una página corta puede ser
    # digital y una página larga puede contener texto de mala calidad.
    if not use_ocr or all(len(p.text) >= 40 for p in paginas):
        return paginas

    from config import build_client, load_settings

    settings = load_settings()
    client = build_client(settings)
    extraidas = []
    for pagina in paginas:
        if len(pagina.text) >= 40:
            extraidas.append(pagina)
            continue
        image_bytes = pdf_page_to_png_bytes(pdf_path, pagina.page)
        response = client.responses.create(
            model=settings.vision_model,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Transcribe fielmente todo el texto visible. No resumas. Si la página está vacía, devuelve texto vacío."},
                    {"type": "input_image", "image_url": image_bytes_to_data_url(image_bytes)},
                ],
            }],
        )
        extraidas.append(PaginaExtraida(
            source=pagina.source, page=pagina.page,
            text=response.output_text.strip(), extraction_method="vision_ocr",
        ))
    return extraidas


def extraer_paginas(pdf_path: str | Path, *, use_ocr: bool = True) -> list[dict[str, Any]]:
    """Devuelve páginas con metadatos y fallback OCR opcional."""
    return [
        {
            "text": pagina.text,
            "metadata": {
                "source": pagina.source,
                "page": pagina.page,
                "extraction_method": pagina.extraction_method,
            },
        }
        for pagina in extract_pdf_pages(pdf_path, use_ocr=use_ocr)
    ]


def crear_chunks(
    paginas: Iterable[dict[str, Any] | PaginaExtraida],
    *,
    max_chars: int = 500,
    overlap: int = 100,
) -> list[dict[str, Any]]:
    """Versión compatible con los tests: genera chunks con metadata de procedencia."""
    if max_chars <= 0:
        raise ValueError("max_chars debe ser > 0")
    if overlap >= max_chars:
        raise ValueError("overlap debe ser menor que max_chars")

    output: list[dict[str, Any]] = []
    for pagina in paginas:
        if isinstance(pagina, BaseModel):
            text = pagina.text
            source = pagina.source
            page = pagina.page
            extraction_method = pagina.extraction_method
        else:
            text = pagina["text"]
            metadata = pagina.get("metadata", {})
            source = metadata.get("source", "unknown.pdf")
            page = metadata.get("page", 1)
            extraction_method = metadata.get("extraction_method", "unknown")

        pieces = chunk_text(text, chunk_size=max_chars, overlap=overlap)
        for idx, piece in enumerate(pieces, start=1):
            output.append(
                {
                    "text": piece,
                    "metadata": {
                        "source": source,
                        "page": page,
                        "chunk_id": f"{source}-p{page}-c{idx}",
                        "extraction_method": extraction_method,
                    },
                }
            )
    return output


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

    # La ventana se mide en caracteres, no en tokens; puede cortar una oración.
    # Normalizar espacios simplifica la demo, pero pierde estructura de tablas.
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
        # Ejemplo: tamaño 300 y solapamiento 80 avanzan 220 caracteres.
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
            # ID reproducible a partir de fuente, página, posición y prefijo.
            # No es un hash del contenido completo ni una garantía de unicidad.
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
