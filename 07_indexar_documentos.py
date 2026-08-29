"""Ingiere PDFs con fallback OCR y construye un índice vectorial persistente."""

from __future__ import annotations

from pathlib import Path

from config import build_client, load_settings
from document_models import PaginaExtraida
from document_pipeline import make_chunks, parse_pdf_text, pdf_page_to_png_bytes
from vector_store import JsonVectorStore

INPUT_DIR = Path("data/entrada")
INDEX_PATH = Path("data/indice/vector_store.json")


def extraer_documento(path: Path) -> list[PaginaExtraida]:
    """Extrae texto y activa OCR multimodal solo si el parsing fue insuficiente.

    El fallback basado en evidencia equilibra calidad, costo y latencia. Registrar el
    método por página permite al futuro agente y al auditor evaluar confiabilidad.
    """
    paginas = parse_pdf_text(path)
    total_chars = sum(len(p.text) for p in paginas)

    # Para esta clase, si el parsing recupera muy poco texto, hacemos OCR multimodal.
    if total_chars >= 40:
        return paginas

    settings = load_settings()
    client = build_client(settings)
    from document_pipeline import image_bytes_to_data_url

    extraidas: list[PaginaExtraida] = []
    for page_number in range(1, len(paginas) + 1):
        image_bytes = pdf_page_to_png_bytes(path, page_number)
        response = client.responses.create(
            model=settings.vision_model,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Transcribe fielmente todo el texto visible. No resumas."},
                    {"type": "input_image", "image_url": image_bytes_to_data_url(image_bytes)},
                ],
            }],
        )
        extraidas.append(PaginaExtraida(
            source=path.name,
            page=page_number,
            text=response.output_text.strip(),
            extraction_method="vision_ocr",
        ))
    return extraidas


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
