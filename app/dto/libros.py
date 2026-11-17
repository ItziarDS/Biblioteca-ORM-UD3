"""DTO (Data Transfer Objects) del catálogo: datos simples, sin base de datos."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DatosLibro:
    """Entrada: lo que se necesita para crear un libro."""
    isbn: str
    titulo: str
    precio: Decimal
    id_autor: int


@dataclass(frozen=True)
class LibroResumen:
    """Salida: lo que se muestra de un libro (ya no depende de la Session)."""
    id_libro: int
    titulo: str
    autor: str
    precio: Decimal


@dataclass(frozen=True)
class FiltroLibros:
    """Filtro dinámico: solo se aplican las condiciones que tengan valor."""
    texto: str | None = None
    precio_minimo: Decimal | None = None
    precio_maximo: Decimal | None = None
    id_autor: int | None = None
    solo_activos: bool = True
    pagina: int = 1
    tamano: int = 10