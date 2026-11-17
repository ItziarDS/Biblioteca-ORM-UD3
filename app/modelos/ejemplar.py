from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import Base

# Estados posibles de un ejemplar (se guardan como texto en la BD).
DISPONIBLE = "DISPONIBLE"
PRESTADO = "PRESTADO"


class Ejemplar(Base):
    __tablename__ = "ejemplares"

    id_ejemplar: Mapped[int] = mapped_column(primary_key=True)
    id_libro: Mapped[int] = mapped_column(ForeignKey("libros.id_libro"))
    codigo_inventario: Mapped[str] = mapped_column(String(50))
    ubicacion: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(20), default=DISPONIBLE)
    fecha_alta: Mapped[date] = mapped_column(Date)

    libro: Mapped["Libro"] = relationship(back_populates="ejemplares")
    # "detalle_prestamo" se escribe como texto para no importar prestamo.py
    # (evita una importación circular entre ejemplar.py y prestamo.py).
    prestamos: Mapped[list["Prestamo"]] = relationship(
        secondary="detalle_prestamo",
        back_populates="ejemplares",
    )

    def __repr__(self) -> str:
        return (
            f"Ejemplar(id_ejemplar={self.id_ejemplar!r}, "
            f"codigo={self.codigo_inventario!r}, estado={self.estado!r})"
        )