"""Demostración ejecutable de Retrieval Avanzado, sesión 06."""
import argparse
from retrieval_advanced import positive_int

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default='¿Por qué falló lo de ayer?')
    parser.add_argument("--top-k", type=positive_int, default=5)
    parser.add_argument("--history", default='Revisamos SAP F110 del 2026-09-03 y apareció F110-031')
    args = parser.parse_args()
    from config import load_settings, build_client
    settings = load_settings()
    client = build_client(settings)
    from retrieval_advanced import rewrite_query
    # Observe cómo el historial resuelve la referencia ambigua de la consulta.
    # Esta demo solo reescribe: no recupera documentos ni utiliza --top-k.
    print('ORIGINAL:', args.query)
    print('HISTORIAL:', args.history)
    print('REWRITTEN:', rewrite_query(client, settings, args.query, args.history))

if __name__ == "__main__":
    main()
