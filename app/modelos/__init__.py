"""Importa todas las entidades para que SQLAlchemy conozca todas las
relaciones (las referencias por nombre como "Ejemplar" se resuelven aquí)."""
from app.modelos.base import Base
from app.modelos.autor import Autor
from app.modelos.libro import Libro
from app.modelos.ejemplar import Ejemplar
from app.modelos.socio import Socio
from app.modelos.prestamo import Prestamo, detalle_prestamo

__all__ = [
    "Base",
    "Autor",
    "Libro",
    "Ejemplar",
    "Socio",
    "Prestamo",
    "detalle_prestamo",
]