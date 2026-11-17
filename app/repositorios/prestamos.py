from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modelos import Ejemplar, Prestamo


class PrestamoRepositorio:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_prestamo: int) -> Prestamo | None:
        return self.session.get(Prestamo, id_prestamo)

    def añadir(self, prestamo: Prestamo) -> None:
        self.session.add(prestamo)

    def listar_abiertos(self) -> list[Prestamo]:
        """Préstamos sin devolver, con socio, ejemplares y libro ya cargados:
        1 consulta (préstamos + socio) + 1 consulta (ejemplares + libro)."""
        consulta = (
            select(Prestamo)
            .where(Prestamo.fecha_devolucion.is_(None))
            .options(
                joinedload(Prestamo.socio),
                selectinload(Prestamo.ejemplares).joinedload(Ejemplar.libro),
            )
            .order_by(Prestamo.id_prestamo)
        )
        return list(self.session.scalars(consulta).all())