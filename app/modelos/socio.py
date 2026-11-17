from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modelos.base import Base


class Socio(Base):
    __tablename__ = "socios"

    id_socio: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(30))
    fecha_alta: Mapped[date] = mapped_column(Date)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    prestamos: Mapped[list["Prestamo"]] = relationship(back_populates="socio")

    def __repr__(self) -> str:
        return (
            f"Socio(id_socio={self.id_socio!r}, "
            f"nombre={self.nombre!r}, activo={self.activo!r})"
        )