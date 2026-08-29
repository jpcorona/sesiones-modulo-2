"""CLI de ingesta del recorrido didáctico de parsing, OCR y chunking."""

from __future__ import annotations

import argparse

from document_pipeline import crear_chunks, extraer_paginas
from document_search import DEFAULT_INDEX, guardar_chunks


def main() -> None:
    """Procesa un PDF, persiste sus chunks e informa métodos de extracción usados.

    La salida resume la procedencia del índice, condición necesaria para saber qué
    conocimiento estará realmente disponible para el agente.
    """
    parser = argparse.ArgumentParser(description="Procesa un PDF para la sesión 3.")
    parser.add_argument("pdf", help="Ruta del PDF digital o escaneado")
    parser.add_argument("--no-ocr", action="store_true", help="Desactiva fallback OCR")
    parser.add_argument("--max-chars", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--output", default=str(DEFAULT_INDEX))
    args = parser.parse_args()

    pages = extraer_paginas(args.pdf, use_ocr=not args.no_ocr)
    chunks = crear_chunks(pages, max_chars=args.max_chars, overlap=args.overlap)
    guardar_chunks(chunks, args.output)

    methods = {page["metadata"]["extraction_method"] for page in pages}
    print(f"Páginas procesadas: {len(pages)}")
    print(f"Chunks generados: {len(chunks)}")
    print(f"Métodos utilizados: {', '.join(sorted(methods))}")
    print(f"Índice escrito en: {args.output}")


if __name__ == "__main__":
    main()
