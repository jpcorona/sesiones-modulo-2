"""Demostración de parsing tradicional sobre un PDF escaneado sin capa textual."""

from pathlib import Path

from document_pipeline import parse_pdf_text

PDF = Path("data/entrada/orden_trabajo_escaneada.pdf")

if not PDF.exists():
    raise SystemExit("Falta el PDF demo. Ejecuta primero: python 00_generar_documentos_demo.py")

# Ejecutar solo parsing establece una línea base: un resultado vacío justifica OCR,
# en vez de enviar imágenes y asumir su costo para todos los documentos.
paginas = parse_pdf_text(PDF)

print(f"Archivo: {PDF.name}")
print(f"Paginas: {len(paginas)}")

for pagina in paginas:
    print(f"\n--- PAGINA {pagina.page} · {pagina.extraction_method} ---")
    print(pagina.text)
    print(f"Caracteres extraidos: {len(pagina.text)}")

print("\nPREGUNTA AL CURSO: ¿Aqui usamos OCR?")
print("RESPUESTA: No. Solo leimos la capa de texto existente en el PDF.")
