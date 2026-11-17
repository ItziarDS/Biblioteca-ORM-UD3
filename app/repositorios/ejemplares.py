from sqlalchemy.orm import Session

from app.modelos import Ejemplar


class EjemplarRepositorio:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_ejemplar: int) -> Ejemplar | None:
        return self.session.get(Ejemplar, id_ejemplar)

    def añadir(self, ejemplar: Ejemplar) -> None:
        self.session.add(ejemplar)