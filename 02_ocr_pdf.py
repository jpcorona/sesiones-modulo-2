"""Compara OCR local y visión multimodal para recuperar texto desde píxeles."""

from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

from PIL import Image

from config import build_client, load_settings
from document_pipeline import image_bytes_to_data_url, parse_pdf_text, pdf_page_to_png_bytes

PDF = Path("data/entrada/orden_trabajo_escaneada.pdf")



def ocr_tesseract(image_bytes: bytes) -> str:
    """Transcribe una imagen con Tesseract instalado localmente.

    Es importante como alternativa privada y sin costo por llamada, aunque su calidad
    depende del idioma, la instalación y la legibilidad del documento.
    """
    import pytesseract

    if shutil.which("tesseract") is None:
        raise RuntimeError(
            "Tesseract no esta instalado o no esta en PATH. Usa --engine vision o instala Tesseract OCR."
        )
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image, lang="eng").strip()


def ocr_vision(image_bytes: bytes) -> str:
    """Transcribe una imagen mediante un modelo multimodal configurado.

    Este camino puede manejar layouts complejos, pero añade red, costo y riesgo de
    inferencia; por eso el prompt exige transcripción fiel y no un resumen.
    """
    settings = load_settings()
    client = build_client(settings)
    data_url = image_bytes_to_data_url(image_bytes)
    response = client.responses.create(
        model=settings.vision_model,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Transcribe fielmente todo el texto visible de esta pagina. "
                            "No resumas, no expliques y no agregues informacion."
                        ),
                    },
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
    )
    return response.output_text.strip()


def main() -> None:
    """Selecciona el motor, muestra cada etapa y compara el texto recuperado."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["tesseract", "vision"], default="tesseract")
    args = parser.parse_args()

    if not PDF.exists():
        raise SystemExit("Falta el PDF demo. Ejecuta primero: python 00_generar_documentos_demo.py")

    parsed = parse_pdf_text(PDF)
    print("=== 1) PARSING TRADICIONAL ===")
    for pagina in parsed:
        print(f"Pagina {pagina.page}: {len(pagina.text)} caracteres")
        print(repr(pagina.text[:200]))

    print("\n=== 2) RENDER DE LA PAGINA COMO IMAGEN ===")
    image_bytes = pdf_page_to_png_bytes(PDF, 1)
    print(f"PNG generado en memoria: {len(image_bytes)} bytes")

    print(f"\n=== 3) OCR · ENGINE={args.engine} ===")
    if args.engine == "tesseract":
        text = ocr_tesseract(image_bytes)
    else:
        text = ocr_vision(image_bytes)

    print(text)
    print(f"\nCaracteres recuperados por OCR: {len(text)}")
    print("\nIDEA: parsing intento leer texto digital; OCR recupero texto desde pixeles.")


if __name__ == "__main__":
    main()
