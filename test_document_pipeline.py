"""Pruebas de segmentación y procedencia de la canalización documental."""

import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from document_models import PaginaExtraida
from pathlib import Path

from document_pipeline import crear_chunks, extraer_paginas
from document_search import buscar_documentacion


class DocumentPipelineTests(unittest.TestCase):
    """Protege contratos que determinan la calidad del contexto del futuro agente."""

    def test_ocr_pdf_mixto_conserva_paginas_digitales(self):
        pages = [
            PaginaExtraida(source="mixto.pdf", page=1, text="Texto digital " * 10, extraction_method="pdf_text_layer"),
            PaginaExtraida(source="mixto.pdf", page=2, text="", extraction_method="pdf_text_layer"),
        ]
        client = MagicMock()
        client.responses.create.return_value.output_text = "Texto recuperado por OCR"
        with patch("document_pipeline.parse_pdf_text", return_value=pages), \
             patch("document_pipeline.pdf_page_to_png_bytes", return_value=b"image") as render, \
             patch("config.load_settings"), patch("config.build_client", return_value=client):
            result = extraer_paginas("mixto.pdf")
        render.assert_called_once_with("mixto.pdf", 2)
        client.responses.create.assert_called_once()
        self.assertEqual(result[0]["text"], pages[0].text)
        self.assertEqual(result[0]["metadata"]["extraction_method"], "pdf_text_layer")
        self.assertEqual(result[1]["text"], "Texto recuperado por OCR")
        self.assertEqual(result[1]["metadata"]["page"], 2)
        self.assertEqual(result[1]["metadata"]["extraction_method"], "vision_ocr")

    def test_no_ocr_no_llama_servicios(self):
        pages = [PaginaExtraida(source="scan.pdf", page=1, text="", extraction_method="pdf_text_layer")]
        with patch("document_pipeline.parse_pdf_text", return_value=pages), \
             patch("config.build_client") as build:
            result = extraer_paginas("scan.pdf", use_ocr=False)
        build.assert_not_called()
        self.assertEqual(result[0]["text"], "")

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
