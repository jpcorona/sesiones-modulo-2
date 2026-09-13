"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=positive_int, default=5)
    args = parser.parse_args()
    from config import load_settings, build_client
    settings = load_settings()
    client = build_client(settings)
    from retrieval_advanced import bm25_search, vector_search
    # Comparamos las dos señales lado a lado; esta demo todavía no las fusiona.
    # Sus scores no son directamente comparables porque usan escalas distintas.
    for name, results in [('BM25', bm25_search(args.query, args.top_k)), ('VECTOR', vector_search(client, settings, args.query, args.top_k))]:
        print('\n===', name, '===')
        for rank, item in enumerate(results, 1):
            print(rank, f"score={item['score']:.4f}", item['chunk'].source)

if __name__ == "__main__":
    main()
