"""Pruebas de segmentación y procedencia de la canalización documental."""

import json
import tempfile
import unittest
from pathlib import Path

from document_pipeline import crear_chunks
from document_search import buscar_documentacion


class DocumentPipelineTests(unittest.TestCase):
    """Protege contratos que determinan la calidad del contexto del futuro agente."""

    def test_chunking_con_overlap_y_metadata(self) -> None:
        """Verifica que el overlap preserve contenido y que cada chunk sea rastreable."""
        pages = [{
            "text": "abcdefghij",
            "metadata": {"source": "demo.pdf", "page": 1, "extraction_method": "parsing"},
        }]
        chunks = crear_chunks(pages, max_chars=6, overlap=2)
        self.assertEqual([item["text"] for item in chunks], ["abcdef", "efghij"])
        self.assertEqual(chunks[1]["metadata"]["chunk_id"], "demo.pdf-p1-c2")

    def test_overlap_invalido(self) -> None:
        """Impide configuraciones que harían que la segmentación no avanzara."""
        with self.assertRaises(ValueError):
            crear_chunks([], max_chars=100, overlap=100)

    def test_busqueda_conserva_procedencia(self) -> None:
        """Garantiza que retrieval no pierda la página necesaria para citar evidencia."""
        chunks = [{
            "text": "El SLA de criticidad alta es de cuatro horas.",
            "metadata": {"source": "sla.pdf", "page": 3, "chunk_id": "sla.pdf-p3-c1"},
        }]
        with tempfile.TemporaryDirectory() as temp_dir:
            index = Path(temp_dir) / "chunks.json"
            index.write_text(json.dumps(chunks), encoding="utf-8")
            result = buscar_documentacion("SLA alta", index_path=index)
        self.assertEqual(result["resultados"][0]["metadata"]["page"], 3)


if __name__ == "__main__":
    unittest.main()
