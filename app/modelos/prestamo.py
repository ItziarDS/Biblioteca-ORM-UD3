from __future__ import annotations

from datetime import date

from sqlalchemy import Column, Date, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import Base

# Tabla intermedia N:M entre Préstamo y Ejemplar.
# (En la BD tiene además la columna "renovaciones", con valor por defecto 0;
# no hace falta mapearla porque la aplicación no la usa.)
detalle_prestamo = Table(
    "detalle_prestamo",
    Base.metadata,
    Column("id_prestamo", ForeignKey("prestamos.id_prestamo"), primary_key=True),
    Column("id_ejemplar", ForeignKey("ejemplares.id_ejemplar"), primary_key=True),
)


class Prestamo(Base):
    __tablename__ = "prestamos"

    id_prestamo: Mapped[int] = mapped_column(primary_key=True)
    id_socio: Mapped[int] = mapped_column(ForeignKey("socios.id_socio"))
    fecha_prestamo: Mapped[date] = mapped_column(Date)
    fecha_limite: Mapped[date] = mapped_column(Date)
    fecha_devolucion: Mapped[date | None] = mapped_column(Date)
    observaciones: Mapped[str | None] = mapped_column(String(255))

    socio: Mapped["Socio"] = relationship(back_populates="prestamos")
    ejemplares: Mapped[list["Ejemplar"]] = relationship(
        secondary=detalle_prestamo,
        back_populates="prestamos",
    )

    def __repr__(self) -> str:
        return (
            f"Prestamo(id_prestamo={self.id_prestamo!r}, "
            f"id_socio={self.id_socio!r}, fecha_limite={self.fecha_limite!r})"
        )