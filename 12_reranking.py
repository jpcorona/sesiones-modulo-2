"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=positive_int, default=5)
    parser.add_argument("--candidate-k", type=positive_int, default=20)
    args = parser.parse_args()
    if args.top_k > args.candidate_k:
        parser.error("--top-k no puede superar --candidate-k")
    from config import load_settings, build_client
    settings = load_settings()
    client = build_client(settings)
    from retrieval_advanced import bm25_search, vector_search, reciprocal_rank_fusion, rerank
    fused = reciprocal_rank_fusion({'bm25': bm25_search(args.query, args.candidate_k), 'vector': vector_search(client, settings, args.query, args.candidate_k)})
    # RRF preselecciona; el cross-encoder evalúa juntos consulta y texto.
    # Aumentar candidate_k puede mejorar cobertura a cambio de más trabajo local.
    candidates = fused[:args.candidate_k]
    results = rerank(args.query, candidates, args.top_k)
    print(f'Candidatos reales: {len(candidates)}; resultados finales: {len(results)}')
    for rank, item in enumerate(results, 1):
        print(rank, f"rerank={item['rerank_score']:.4f} rrf={item['rrf_score']:.6f}", item['chunk'].source) # type: ignore
        print(item['chunk'].text) # type: ignore

if __name__ == "__main__":
    main()
