"""Contratos del agente final sin red ni descarga de modelos."""
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch
from agente_rag import ejecutar_agente


def response(*calls, text=""):
    return NS(output=list(calls), output_text=text)


def call(name, args, ident="c1"):
    return NS(type="function_call", name=name, arguments=json.dumps(args), call_id=ident)


class AgentTests(unittest.TestCase):
    def run_agent(self, responses, **kwargs):
        client = NS(responses=MagicMock())
        client.responses.create.side_effect = responses
        result = ejecutar_agente("Pregunta", client=client, settings=NS(model="fake"), **kwargs)
        return result, client

    def test_documentos_llegan_al_generador_con_citas(self):
        chunk = NS(chunk_id="abc", source="demo.pdf", page=2, text="Regla documentada")
        with patch("agente_rag.advanced_retrieval", return_value=("consulta", [{"chunk":chunk,"rerank_score":4.2}])):
            result, client = self.run_agent([
                response(call("buscar_documentacion", {"consulta":"regla"})),
                response(text="Regla documentada [DOC1]"),
            ])
        payload = json.loads(client.responses.create.call_args.kwargs["input"][-1]["output"])
        self.assertEqual(payload["evidencia"][0]["citation_id"], "DOC1")
        self.assertEqual(result["fuentes"][0]["page"], 2)
        self.assertEqual(result["fuentes"][0]["text"], "Regla documentada")

    def test_ultima_ronda_reserva_respuesta(self):
        result, client = self.run_agent([
            response(call("obtener_sla", {"criticidad":"alta"})), response(text="4 horas")
        ], max_rounds=1)
        self.assertEqual(client.responses.create.call_args.kwargs["tool_choice"], "none")
        self.assertEqual(result["respuesta"], "4 horas")

    def test_herramienta_inventada_se_rechaza(self):
        result, _ = self.run_agent([response(call("reiniciar", {})), response(text="No ejecutado")])
        self.assertEqual(result["eventos"][1]["resultado"]["tipo"], "herramienta_no_autorizada")

    def test_error_de_red_no_se_disfraza_de_sin_evidencia(self):
        with patch("agente_rag.advanced_retrieval", side_effect=ConnectionError("sin conexión")):
            with self.assertRaises(ConnectionError):
                self.run_agent([response(call("buscar_documentacion", {"consulta":"SAP"}))])

    def test_cita_inventada_se_corrige_sin_herramientas(self):
        result, client = self.run_agent([
            response(text="SLA simulado de 4 horas [DOC?]"),
            response(text="SLA simulado de 4 horas"),
        ])
        self.assertNotIn("[DOC?]", result["respuesta"])
        self.assertEqual(client.responses.create.call_args.kwargs["tool_choice"], "none")

    def test_cita_persistente_invalida_se_rechaza(self):
        with self.assertRaises(RuntimeError):
            self.run_agent([response(text="Dato [DOC99]"), response(text="Dato [DOC99]")])

    def test_consulta_invalida_no_busca(self):
        with patch("agente_rag.advanced_retrieval") as retrieve:
            result, _ = self.run_agent([response(call("buscar_documentacion", {"consulta":""})), response(text="Faltan datos")])
        retrieve.assert_not_called()
        self.assertEqual(result["eventos"][1]["resultado"]["estado"], "error")


if __name__ == "__main__":
    unittest.main()
