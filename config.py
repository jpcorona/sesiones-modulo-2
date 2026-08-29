"""Configuración centralizada para que el agente use modelos y límites consistentes."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI


@dataclass(frozen=True)
class Settings:
    """Agrupa la configuración validada que compartirán todos los componentes.

    Centralizarla antes de construir un agente evita que cada módulo elija modelos,
    tiempos de espera o reintentos diferentes y vuelva impredecible el sistema.
    """
    model: str
    embedding_model: str
    vision_model: str
    timeout_seconds: float
    max_retries: int


def load_settings(*, require_api_key: bool = True) -> Settings:
    """Carga variables de entorno y falla temprano si falta una credencial requerida.

    Es importante validar la configuración antes de iniciar el agente: un error claro
    aquí es más seguro y fácil de diagnosticar que un fallo a mitad de una tarea.
    """
    load_dotenv()
    if require_api_key and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Falta OPENAI_API_KEY. Guarda CONFIGURA_AQUI.env como .env y agrega tu clave."
        )
    return Settings(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        vision_model=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-5.4-mini")),
        timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )


def build_client(settings: Settings) -> OpenAI:
    """Construye el cliente OpenAI con límites de resiliencia explícitos.

    El timeout y los reintentos acotados impiden que un agente quede esperando o
    repitiendo indefinidamente una operación externa.
    """
    return OpenAI(timeout=settings.timeout_seconds, max_retries=settings.max_retries)
