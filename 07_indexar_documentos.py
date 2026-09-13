"""Ingiere PDFs con fallback OCR y construye un índice vectorial persistente."""

from __future__ import annotations

from pathlib import Path

from config import build_client, load_settings
from document_models import PaginaExtraida
from document_pipeline import extract_pdf_pages, make_chunks
from vector_store import JsonVectorStore

INPUT_DIR = Path("data/entrada")
INDEX_PATH = Path("data/indice/vector_store.json")


def extraer_documento(path: Path) -> list[PaginaExtraida]:
    """Extrae texto con fallback OCR por página, incluso en PDFs mixtos."""
    return extract_pdf_pages(path)


def main() -> None:
    """Procesa todos los PDFs, crea embeddings y guarda un índice reutilizable.

    Desacoplar ingesta de consulta evita pagar y reprocesar documentos en cada turno
    del agente, y hace que el corpus disponible sea explícito y auditable.
    """
    settings = load_settings()
    client = build_client(settings)
    store = JsonVectorStore(INDEX_PATH)

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit("No hay PDFs. Ejecuta primero: python 00_generar_documentos_demo.py")

    all_chunks = []
    for pdf in pdfs:
        paginas = extraer_documento(pdf)
        chunks = make_chunks(paginas, chunk_size=300, overlap=80)
        all_chunks.extend(chunks)
        print(f"{pdf.name}: paginas={len(paginas)} chunks={len(chunks)} metodo={paginas[0].extraction_method}")

    response = client.embeddings.create(
        model=settings.embedding_model,
        input=[chunk.text for chunk in all_chunks],
    )

    for chunk, item in zip(all_chunks, response.data):
        store.add(chunk, item.embedding)

    store.save()
    print(f"\nIndice guardado: {INDEX_PATH}")
    print(f"Vectores: {len(store.records)}")


if __name__ == "__main__":
    main()
