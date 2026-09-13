"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=positive_int, default=5)
    args = parser.parse_args()
    from retrieval_advanced import bm25_search
    # Primera referencia: buscar términos exactos sin generar una respuesta.
    results = bm25_search(args.query, args.top_k)
    for rank, item in enumerate(results, 1):
        chunk = item['chunk']
        print(f"\n#{rank} bm25={item['score']:.4f} | {chunk.source} | página {chunk.page} | {chunk.section}")
        print(chunk.text)
    if not results:
        print('Sin coincidencias léxicas.')

if __name__ == "__main__":
    main()
