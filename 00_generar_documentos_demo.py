"""Genera PDFs controlados para comparar parsing digital y OCR antes del agente."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path("data/entrada")
OUT.mkdir(parents=True, exist_ok=True)


def crear_pdf_digital() -> None:
    """Crea un PDF con capa de texto para demostrar extracción directa y barata."""
    path = OUT / "politica_vacaciones_digital.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 70, "Politica de Vacaciones 2026")
    c.setFont("Helvetica", 11)
    lines = [
        "Objetivo: definir reglas simples para la solicitud y aprobacion de vacaciones.",
        "Los colaboradores con jornada completa disponen de 15 dias habiles de vacaciones al ano.",
        "La solicitud debe realizarse con al menos 10 dias corridos de anticipacion.",
        "La jefatura debe aprobar o rechazar la solicitud antes de que el periodo comience.",
        "Las vacaciones no se consideran aprobadas hasta existir confirmacion explicita en el sistema.",
        "Ante dudas, el colaborador debe contactar a Recursos Humanos.",
    ]
    y = height - 110
    for line in lines:
        c.drawString(60, y, line)
        y -= 24
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, height - 70, "Excepciones y trazabilidad")
    c.setFont("Helvetica", 11)
    for line in [
        "Los feriados legales no descuentan dias habiles de vacaciones.",
        "Cada solicitud debe conservar fecha, responsable, estado y comentario de aprobacion.",
        "Cambios posteriores deben quedar auditados.",
    ]:
        c.drawString(60, y, line)
        y -= 24
    c.save()
    print("CREADO", path)


def crear_pdf_escaneado() -> None:
    """Crea un PDF compuesto por imagen para demostrar cuándo hace falta OCR.

    Contrastar ambos formatos evita diseñar un agente que asuma erróneamente que
    todo PDF contiene texto legible por un parser.
    """
    path = OUT / "orden_trabajo_escaneada.pdf"
    width, height = 1240, 1754
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
        body_font = ImageFont.truetype("DejaVuSans.ttf", 30)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    y = 120
    draw.text((100, y), "ORDEN DE TRABAJO OT-1842", fill="black", font=title_font)
    y += 100
    lines = [
        "Equipo: Bomba de recirculacion B-17",
        "Area: Sala de proceso",
        "Fecha: 28-08-2026",
        "Hallazgo: temperatura de rodamiento sobre rango esperado.",
        "Regla operacional: si la temperatura supera 85 C, detener la prueba",
        "y solicitar validacion de mantenimiento antes de reiniciar.",
        "Ultima medicion registrada: 89 C.",
        "Accion solicitada: inspeccionar lubricacion y alineacion.",
    ]
    for line in lines:
        draw.text((100, y), line, fill="black", font=body_font)
        y += 70

    # Pillow crea un PDF compuesto por imagen: deliberadamente sin capa de texto.
    image.save(path, "PDF", resolution=150.0)
    print("CREADO", path)


if __name__ == "__main__":
    # Este guard permite importar las funciones en pruebas sin regenerar archivos.
    crear_pdf_digital()
    crear_pdf_escaneado()
