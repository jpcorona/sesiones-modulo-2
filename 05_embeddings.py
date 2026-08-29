"""Convierte chunks en embeddings y muestra la representación usada para retrieval."""

from pathlib import Path

from config import build_client, load_settings
from document_pipeline import make_chunks, parse_pdf_text

PDF = Path("data/entrada/politica_vacaciones_digital.pdf")

# Separar preparación, extracción, chunking y embedding hace observable cada etapa;
# un agente solo debería consumir el contexto después de verificar esta cadena.
settings = load_settings()
client = build_client(settings)

paginas = parse_pdf_text(PDF)
chunks = make_chunks(paginas, chunk_size=250, overlap=60)
texts = [chunk.text for chunk in chunks]

response = client.embeddings.create(
    model=settings.embedding_model,
    input=texts,
)

print(f"Modelo: {settings.embedding_model}")
print(f"Chunks enviados: {len(texts)}")
print(f"Embeddings recibidos: {len(response.data)}")

first = response.data[0].embedding
print(f"Dimension del vector: {len(first)}")
print(f"Primeros 8 valores: {first[:8]}")
print("\nIDEA: no buscamos palabras exactas; creamos una representacion numerica comparable.")
