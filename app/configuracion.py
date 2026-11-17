"""Configuración de la base de datos a partir de variables de entorno.

Nunca se escriben usuario ni contraseña en el código: se leen del entorno.
"""
import os
from urllib.parse import quote_plus


def obtener_url_bd() -> str:
    host = os.getenv("DB_HOST", "localhost")
    puerto = os.getenv("DB_PORT", "5432")
    nombre = os.getenv("DB_NAME", "biblioteca_test")
    usuario = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not usuario or not password:
        raise ValueError("Faltan DB_USER o DB_PASSWORD.")

    return (
        f"postgresql+psycopg://{quote_plus(usuario)}:{quote_plus(password)}"
        f"@{host}:{puerto}/{nombre}"
    )