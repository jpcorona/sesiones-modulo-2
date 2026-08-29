"""Prueba el ciclo del agente con un cliente falso, determinista y sin red."""

import json
import unittest
from types import SimpleNamespace

from main import procesar_ticket


class FakeResponses:
    """Simula una llamada de herramienta seguida por la respuesta final del modelo."""

    def __init__(self) -> None:
        """Crea un registro de solicitudes para poder inspeccionar el contexto enviado."""
        self.requests = []

    def create(self, **kwargs):
        """Devuelve respuestas prefijadas y conserva una copia estable de cada input."""
        snapshot = dict(kwargs)
        snapshot["input"] = list(kwargs["input"])
        self.requests.append(snapshot)
        if len(self.requests) == 1:
            call = SimpleNamespace(
                type="function_call",
                name="obtener_sla",
                arguments='{"criticidad":"alta"}',
                call_id="call_demo_123",
            )
            return SimpleNamespace(output=[call], output_text="", usage=None)

        return SimpleNamespace(
            output=[SimpleNamespace(type="message")],
            output_text="El SLA para criticidad alta es de 4 horas.",
            usage={"total_tokens": 42},
        )


class MainFlowTests(unittest.TestCase):
    """Valida que llamadas, resultados y texto final permanezcan correctamente unidos."""

    def test_ciclo_tool_call_y_respuesta_final(self) -> None:
        """Comprueba que el resultado de la tool vuelve al modelo con el call_id exacto."""
        responses = FakeResponses()
        client = SimpleNamespace(responses=responses)

        texto = procesar_ticket(
            "Consulta el SLA de criticidad alta.",
            client=client,
            model="modelo-de-prueba",
        )

        self.assertEqual(texto, "El SLA para criticidad alta es de 4 horas.")
        self.assertEqual(len(responses.requests), 2)
        segunda_entrada = responses.requests[1]["input"]
        resultado = segunda_entrada[-1]
        self.assertEqual(resultado["type"], "function_call_output")
        self.assertEqual(resultado["call_id"], "call_demo_123")
        self.assertEqual(json.loads(resultado["output"])["sla_horas"], 4)


if __name__ == "__main__":
    unittest.main()
