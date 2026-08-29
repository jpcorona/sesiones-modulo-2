"""Demuestra cómo tamaño y solapamiento cambian el contexto recuperable."""

from __future__ import annotations

import argparse
from pathlib import Path

from document_pipeline import chunk_text, parse_pdf_text

PDF = Path("data/entrada/politica_vacaciones_digital.pdf")


def main() -> None:
    """Compara chunks sin overlap y con overlap usando parámetros ajustables.

    Esta inspección debe ocurrir antes del agente porque cortes deficientes pueden
    separar una regla de su condición y producir respuestas incompletas.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=250)
    parser.add_argument("--overlap", type=int, default=60)
    args = parser.parse_args()

    paginas = parse_pdf_text(PDF)
    text = "\n".join(page.text for page in paginas)

    print("=== TEXTO TOTAL ===")
    print(f"Caracteres: {len(text)}")

    print("\n=== CHUNKING INGENUO SIN OVERLAP ===")
    naive = chunk_text(text, chunk_size=args.chunk_size, overlap=0)
    for i, chunk in enumerate(naive):
        print(f"\n[NAIVE {i}] len={len(chunk)}")
        print(chunk)

    print("\n=== CHUNKING CON OVERLAP ===")
    chunks = chunk_text(text, chunk_size=args.chunk_size, overlap=args.overlap)
    for i, chunk in enumerate(chunks):
        print(f"\n[CHUNK {i}] len={len(chunk)}")
        print(chunk)

    print("\nPREGUNTA: ¿Que informacion se repite entre chunks vecinos y por que puede ayudar?")


if __name__ == "__main__":
    main()
