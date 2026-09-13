"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default='¿Cómo revisar un fallo del proceso automático de pagos SAP F110?')
    parser.add_argument("--top-k", type=positive_int, default=5)
    parser.add_argument("--n", type=positive_int, default=3)
    args = parser.parse_args()
    from config import load_settings, build_client
    settings = load_settings()
    client = build_client(settings)
    from retrieval_advanced import generate_queries, bm25_search, reciprocal_rank_fusion
    queries = generate_queries(client, settings, args.query, args.n)
    # Incluimos la consulta original para no depender solo de variantes generadas.
    # Aquí cada búsqueda es BM25; las variantes pueden ampliar la cobertura.
    rankings = {'original': bm25_search(args.query, args.top_k)}
    for i, query in enumerate(queries, 1):
        print(f'\nQUERY {i}: {query}')
        rankings[f'query_{i}'] = bm25_search(query, args.top_k)
        for rank, item in enumerate(rankings[f'query_{i}'], 1):
            print(rank, item['chunk'].source)
    print('\n=== RESULTADOS DEDUPLICADOS Y FUSIONADOS ===')
    for rank, item in enumerate(reciprocal_rank_fusion(rankings)[:args.top_k], 1):
        print(rank, item['chunk'].source, item['ranks'], f"rrf={item['rrf_score']:.6f}")

if __name__ == "__main__":
    main()
