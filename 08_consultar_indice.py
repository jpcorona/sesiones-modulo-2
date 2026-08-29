"""Consulta el índice persistente y presenta evidencia candidata para un agente RAG."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import build_client, load_settings
from vector_store import JsonVectorStore

INDEX_PATH = Path("data/indice/vector_store.json")


def main() -> None:
    """Embebe una pregunta y recupera los chunks más cercanos del índice local.

    Mostrar fuente, página y score permite validar qué contexto se entregaría al LLM
    antes de permitirle redactar una respuesta final.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        raise SystemExit("No existe el indice. Ejecuta primero: python 07_indexar_documentos.py")

    settings = load_settings()
    client = build_client(settings)

    query_embedding = client.embeddings.create(
        model=settings.embedding_model,
        input=args.query,
    ).data[0].embedding

    store = JsonVectorStore(INDEX_PATH)
    store.load()
    results = store.search(query_embedding, top_k=args.top_k)

    print(f"QUERY: {args.query}")
    for rank, (score, chunk) in enumerate(results, start=1):
        print(f"\n#{rank} score={score:.4f}")
        print(f"{chunk.source} · pagina {chunk.page} · {chunk.section}")
        print(chunk.text)

    print("\nSIGUIENTE ESCALON: entregar estos Top-K chunks a un LLM para construir la respuesta RAG.")


if __name__ == "__main__":
    main()
