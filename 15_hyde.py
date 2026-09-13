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
    from retrieval_advanced import hyde_search
    # El texto inventado guía la búsqueda semántica; no se agrega al índice.
    # Compare la hipótesis con los documentos reales para detectar diferencias.
    hypothetical, results = hyde_search(client, settings, args.query, args.top_k)
    print('\n=== DOCUMENTO HIPOTÉTICO: NO ES EVIDENCIA ===\n', hypothetical)
    print('\n=== DOCUMENTOS REALES RECUPERADOS ===')
    for rank, item in enumerate(results, 1):
        print(rank, item['chunk'].source, f"score={item['score']:.4f}")
        print(item['chunk'].text)

if __name__ == "__main__":
    main()
