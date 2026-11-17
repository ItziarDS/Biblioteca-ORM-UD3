from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PrestamoResumen:
    """Salida: un préstamo con el socio y los ejemplares ya convertidos a texto."""
    id_prestamo: int
    socio: str
    ejemplares: tuple[str, ...]
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: date | None = None