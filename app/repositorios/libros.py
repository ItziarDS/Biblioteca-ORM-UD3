from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.dto.libros import FiltroLibros
from app.modelos import Libro


class LibroRepositorio:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_libro: int) -> Libro | None:
        return self.session.get(Libro, id_libro)

    def buscar_por_isbn(self, isbn: str) -> Libro | None:
        consulta = select(Libro).where(Libro.isbn == isbn)
        return self.session.scalars(consulta).first()

    def añadir(self, libro: Libro) -> None:
        self.session.add(libro)

    @staticmethod
    def _condiciones(filtro: FiltroLibros) -> list:
        """Solo añade las condiciones que tienen valor."""
        condiciones = []
        if filtro.texto:
            condiciones.append(Libro.titulo.ilike(f"%{filtro.texto}%"))
        if filtro.precio_minimo is not None:
            condiciones.append(Libro.precio >= filtro.precio_minimo)
        if filtro.precio_maximo is not None:
            condiciones.append(Libro.precio <= filtro.precio_maximo)
        if filtro.id_autor is not None:
            condiciones.append(Libro.id_autor == filtro.id_autor)
        if filtro.solo_activos:
            condiciones.append(Libro.publicado.is_(True))
        return condiciones

    def listar(self, filtro: FiltroLibros) -> list[Libro]:
        """Libros filtrados y paginados, con su autor en la MISMA consulta
        (joinedload) para evitar el problema N+1."""
        consulta = (
            select(Libro)
            .options(joinedload(Libro.autor))
            .where(*self._condiciones(filtro))
            .order_by(Libro.id_libro)
            .offset((filtro.pagina - 1) * filtro.tamano)
            .limit(filtro.tamano)
        )
        return list(self.session.scalars(consulta).all())

    def contar(self, filtro: FiltroLibros) -> int:
        """Total de libros que cumplen el filtro (sin paginar)."""
        consulta = (
            select(func.count())
            .select_from(Libro)
            .where(*self._condiciones(filtro))
        )
        return self.session.scalar(consulta) or 0