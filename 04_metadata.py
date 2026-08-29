"""Inspecciona cómo los metadatos convierten texto en evidencia trazable."""

import json
from pathlib import Path

from document_pipeline import make_chunks, parse_pdf_text

PDF = Path("data/entrada/politica_vacaciones_digital.pdf")

# El flujo deliberadamente visible permite verificar procedencia antes de indexar.
paginas = parse_pdf_text(PDF)
chunks = make_chunks(paginas, chunk_size=250, overlap=60)

print(f"Chunks creados: {len(chunks)}")

for chunk in chunks:
    print("\n--- CHUNK TIPADO ---")
    print(json.dumps(chunk.model_dump(), ensure_ascii=False, indent=2))

print("\nIDEA: el texto ahora tiene identidad, pagina, fuente, tipo y metodo de extraccion.")
