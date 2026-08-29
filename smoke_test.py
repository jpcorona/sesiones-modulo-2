"""Verificaciones rápidas de seguridad y contratos sin llamadas a servicios externos."""

from tools import (
    consultar_estado_sistema,
    ejecutar_herramienta,
    obtener_sla,
)


def ejecutar_pruebas() -> None:
    """Comprueba rutas normales y errores que el agente debe manejar sin ejecutar."""
    assert obtener_sla("alta")["sla_horas"] == 4
    assert obtener_sla("urgente")["estado"] == "error"
    assert consultar_estado_sistema("dashboard_produccion")["estado"] == "degradado"
    assert consultar_estado_sistema("facturacion_internacional")["estado"] == "desconocido"
    assert ejecutar_herramienta("borrar_base", "{}")["tipo"] == "herramienta_no_autorizada"
    assert ejecutar_herramienta("obtener_sla", "{")["tipo"] == "json_invalido"
    resultado = ejecutar_herramienta(
        "obtener_sla",
        '{"criticidad":"alta","extra":1}',
    )
    assert resultado["tipo"] == "validacion"
    print("7 verificaciones locales: OK")


if __name__ == "__main__":
    ejecutar_pruebas()
