"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=positive_int, default=5)
    parser.add_argument("--candidate-k", type=positive_int, default=20)
    parser.add_argument("--history", default='')
    parser.add_argument("--no-rewrite", action="store_true")
    args = parser.parse_args()
    if args.top_k > args.candidate_k:
        parser.error("--top-k no puede superar --candidate-k")
    from config import load_settings, build_client
    settings = load_settings()
    client = build_client(settings)
    from retrieval_advanced import advanced_retrieval
    # Este recorrido termina en evidencia ordenada; aún no redacta una respuesta.
    # --no-rewrite permite comparar el efecto de reescribir la misma consulta.
    search_query, results = advanced_retrieval(client, settings, args.query, args.history, args.candidate_k, args.top_k, not args.no_rewrite)
    print('QUERY ORIGINAL:', args.query)
    print('QUERY BÚSQUEDA:', search_query)
    for rank, item in enumerate(results, 1):
        chunk = item['chunk']
        print(f"\n#{rank} rerank={item['rerank_score']:.4f} rrf={item['rrf_score']:.6f} ranks={item['ranks']}")
        print(f'{chunk.source} | página {chunk.page} | {chunk.section}')
        print(chunk.text)

if __name__ == "__main__":
    main()
