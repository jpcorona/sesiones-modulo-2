"""Herramientas permitidas, sus contratos y el despachador seguro del agente."""

import json
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, ValidationError


class ArgumentosSLA(BaseModel):
    """Valida que la herramienta de SLA reciba solo la criticidad esperada."""
    model_config = ConfigDict(extra="forbid")
    criticidad: str


class ArgumentosEstado(BaseModel):
    """Valida que la consulta de estado reciba solo un identificador de sistema."""
    model_config = ConfigDict(extra="forbid")
    sistema: str


def obtener_sla(criticidad: str) -> dict:
    """Consulta una tabla controlada de SLA sin permitir que el modelo la invente."""
    slas = {"baja": 24, "media": 8, "alta": 4, "critica": 1}
    if criticidad not in slas:
        return {"estado": "error", "mensaje": "Criticidad no reconocida"}
    return {"estado": "ok", "criticidad": criticidad, "sla_horas": slas[criticidad]}


def consultar_estado_sistema(sistema: str) -> dict:
    """Simula una fuente externa de estado y explicita los sistemas desconocidos."""
    sistemas = {
        "dashboard_produccion": {"estado": "degradado", "ultima_actualizacion": "08:15"},
        "erp": {"estado": "operacional", "ultima_actualizacion": "10:30"},
        "base_datos_produccion": {"estado": "operacional", "ultima_actualizacion": "10:32"},
    }
    resultado = sistemas.get(sistema)
    if resultado is None:
        return {"estado": "desconocido", "ultima_actualizacion": None, "mensaje": "Sistema no registrado"}
    return {"sistema": sistema, **resultado}


# Los esquemas son el contrato visible para el modelo. Descripciones precisas,
# enums y additionalProperties=False reducen llamadas ambiguas o no autorizadas.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "obtener_sla",
        "description": "Consulta el SLA oficial en horas para una criticidad ya determinada. No usar para inventar o cambiar la criticidad.",
        "parameters": {
            "type": "object",
            "properties": {
                "criticidad": {
                    "type": "string",
                    "enum": ["baja", "media", "alta", "critica"],
                    "description": "Criticidad normalizada del incidente.",
                }
            },
            "required": ["criticidad"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "consultar_estado_sistema",
        "description": "Consulta el estado registrado de un sistema. Usar cuando el ticket pide verificar disponibilidad o degradación.",
        "parameters": {
            "type": "object",
            "properties": {
                "sistema": {
                    "type": "string",
                    "enum": ["dashboard_produccion", "erp", "base_datos_produccion", "facturacion_internacional"],
                    "description": "Identificador normalizado del sistema que se desea consultar.",
                }
            },
            "required": ["sistema"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


# La lista permitida funciona como frontera de seguridad: aunque el modelo solicite
# otro nombre, solo estas funciones pueden ejecutarse.
REGISTRO: dict[str, tuple[type[BaseModel], Callable[..., dict]]] = {
    "obtener_sla": (ArgumentosSLA, obtener_sla),
    "consultar_estado_sistema": (ArgumentosEstado, consultar_estado_sistema),
}


def ejecutar_herramienta(nombre: str, argumentos: str) -> dict:
    """Valida y despacha una llamada del modelo dentro de una lista permitida.

    Esta función es esencial antes de crear un agente porque el texto generado no
    debe convertirse directamente en ejecución: primero se autoriza, parsea, valida
    y transforma cada error en un resultado controlado para el siguiente turno.
    """
    if nombre not in REGISTRO:
        return {"estado": "error", "tipo": "herramienta_no_autorizada", "mensaje": f"Herramienta no permitida: {nombre}"}
    try:
        datos: Any = json.loads(argumentos)
    except json.JSONDecodeError as error:
        return {"estado": "error", "tipo": "json_invalido", "mensaje": str(error)}
    if not isinstance(datos, dict):
        return {"estado": "error", "tipo": "argumentos_invalidos", "mensaje": "Los argumentos deben ser un objeto JSON"}
    modelo, funcion = REGISTRO[nombre]
    try:
        argumentos_validados = modelo.model_validate(datos)
        return funcion(**argumentos_validados.model_dump())
    except ValidationError as error:
        return {"estado": "error", "tipo": "validacion", "mensaje": "Argumentos rechazados", "detalle": error.errors(include_url=False)}
    except Exception as error:
        return {"estado": "error", "tipo": "inesperado", "mensaje": type(error).__name__}
