"""Demo final: herramientas, retrieval avanzado y respuesta con fuentes."""
import argparse
import json
from pathlib import Path

from agente_rag import ejecutar_agente
from config import build_client, load_settings
from retrieval_advanced import positive_int


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--history", default="")
    parser.add_argument("--candidate-k", type=positive_int, default=20)
    parser.add_argument("--top-k", type=positive_int, default=5)
    parser.add_argument("--no-rewrite", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    if args.top_k > args.candidate_k:
        parser.error("--top-k no puede superar --candidate-k")
    settings = load_settings()
    def show(event):
        print(json.dumps(event, ensure_ascii=False, indent=2), flush=True)
    result = ejecutar_agente(
        args.query, client=build_client(settings), settings=settings,
        history=args.history, candidate_k=args.candidate_k, top_k=args.top_k,
        use_rewrite=not args.no_rewrite, on_event=show if args.trace else None,
    )
    print("\n=== RESPUESTA FINAL ===\n" + result["respuesta"])
    print("\n=== FUENTES RECUPERADAS (NO TODAS NECESARIAMENTE CITADAS) ===")
    for source in result["fuentes"]:
        print(f"[{source['citation_id']}] {source['source']} | página {source['page']} | chunk={source['chunk_id']}")
    print(f"\nTiempo total: {result['latencia_s']} s")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
