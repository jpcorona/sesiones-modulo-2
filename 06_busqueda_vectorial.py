"""Ejecuta búsqueda semántica directa para inspeccionar evidencia antes del RAG."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import build_client, load_settings
from document_pipeline import make_chunks, parse_pdf_text
from vector_store import cosine_similarity

PDF = Path("data/entrada/politica_vacaciones_digital.pdf")


def main() -> None:
    """Embebe consulta y chunks, los ordena por similitud y muestra el Top-K.

    Revisar resultados antes de pedir una respuesta al agente permite atribuir fallos
    al retrieval o a la generación, en vez de tratar todo como una caja negra.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="¿cuantos dias de vacaciones corresponden?")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    settings = load_settings()
    client = build_client(settings)

    chunks = make_chunks(parse_pdf_text(PDF), chunk_size=250, overlap=60)
    texts = [chunk.text for chunk in chunks]

    chunk_response = client.embeddings.create(model=settings.embedding_model, input=texts)
    query_response = client.embeddings.create(model=settings.embedding_model, input=args.query)

    query_vector = query_response.data[0].embedding
    scored = []
    for chunk, item in zip(chunks, chunk_response.data):
        score = cosine_similarity(query_vector, item.embedding)
        scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    print(f"QUERY: {args.query}")
    print(f"TOP-K: {args.top_k}")
    for rank, (score, chunk) in enumerate(scored[: args.top_k], start=1):
        print(f"\n#{rank} score={score:.4f}")
        print(f"source={chunk.source} page={chunk.page} section={chunk.section}")
        print(chunk.text)

    print("\nIDEA: retrieval devuelve evidencia candidata; aun no hemos llamado a un LLM para redactar RAG.")


if __name__ == "__main__":
    main()
