"""Orquesta un agente acotado de soporte con function calling y trazabilidad."""

from __future__ import annotations

import argparse
import json
import logging
import time
from typing import Any

from openai import OpenAI

from config import build_client, load_settings
from prompts import INSTRUCCIONES
from tools import TOOL_SCHEMAS, ejecutar_herramienta

MAX_TOOL_ROUNDS = 3
LOGGER = logging.getLogger("sesion_02")


def procesar_ticket(
    ticket: str,
    *,
    client: OpenAI,
    model: str,
    debug: bool = False,
) -> str:
    """Ejecuta el ciclo acotado modelo → herramientas → modelo.

    Es el núcleo del agente: conserva el contexto, ejecuta solo herramientas
    validadas y devuelve sus resultados al modelo. El máximo de rondas evita bucles
    indefinidos y los logs permiten auditar decisiones, latencia y uso.
    """
    entrada: list[Any] = [{"role": "user", "content": ticket}]
    inicio = time.perf_counter()

    for ronda in range(1, MAX_TOOL_ROUNDS + 1):
        respuesta = client.responses.create(
            model=model,
            instructions=INSTRUCCIONES,
            input=entrada,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            parallel_tool_calls=True,
        )

        if debug:
            print(f"\n--- RESPONSE OUTPUT · RONDA {ronda} ---")
            for item in respuesta.output:
                print(item)

        # Conservar todos los items mantiene intacto el razonamiento conversacional
        # y permite que el modelo relacione cada resultado con su llamada original.
        entrada.extend(respuesta.output)
        llamadas = [
            item for item in respuesta.output if item.type == "function_call"
        ]

        if not llamadas:
            LOGGER.info(
                "flujo_completo ronda=%s latencia_s=%.2f usage=%s",
                ronda,
                time.perf_counter() - inicio,
                getattr(respuesta, "usage", None),
            )
            if not respuesta.output_text:
                raise RuntimeError("El modelo terminó sin texto de respuesta.")
            return respuesta.output_text

        for llamada in llamadas:
            resultado = ejecutar_herramienta(llamada.name, llamada.arguments)
            LOGGER.info(
                "tool=%s call_id=%s estado=%s",
                llamada.name,
                llamada.call_id,
                resultado.get("estado"),
            )
            entrada.append(
                {
                    "type": "function_call_output",
                    "call_id": llamada.call_id,
                    "output": json.dumps(resultado, ensure_ascii=False),
                }
            )

    raise RuntimeError(
        f"Se alcanzó el límite seguro de {MAX_TOOL_ROUNDS} rondas de herramientas."
    )


def parse_args() -> argparse.Namespace:
    """Define una interfaz reproducible para aportar el ticket y activar diagnóstico."""
    parser = argparse.ArgumentParser(
        description="Demo de Context Engineering y Function Calling."
    )
    parser.add_argument("--ticket", help="Ticket a procesar; si se omite se solicita.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra response.output para explicar cada tool call.",
    )
    return parser.parse_args()


def main() -> None:
    """Prepara dependencias, valida la entrada y presenta la respuesta del agente.

    Mantener la preparación fuera del núcleo facilita probar `procesar_ticket` con
    clientes falsos, sin red ni credenciales reales.
    """
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = load_settings()
    client = build_client(settings)

    ticket = (args.ticket or input("Pega el ticket y presiona Enter: ")).strip()
    if not ticket:
        raise SystemExit("El ticket no puede estar vacío.")

    respuesta = procesar_ticket(
        ticket,
        client=client,
        model=settings.model,
        debug=args.debug,
    )
    print("\nRespuesta final:\n")
    print(respuesta)


if __name__ == "__main__":
    main()
