from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modelos import Autor


class AutorRepositorio:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_autor: int) -> Autor | None:
        return self.session.get(Autor, id_autor)

    def añadir(self, autor: Autor) -> None:
        self.session.add(autor)

    def listar_todos(self) -> list[Autor]:
        """Sin carga previa: acceder a autor.libros provoca N+1."""
        return list(self.session.scalars(select(Autor).order_by(Autor.id_autor)).all())

    def listar_con_libros(self) -> list[Autor]:
        """selectinload: 1 consulta de autores + 1 consulta agrupada de libros."""
        consulta = (
            select(Autor)
            .options(selectinload(Autor.libros))
            .order_by(Autor.id_autor)
        )
        return list(self.session.scalars(consulta).all())