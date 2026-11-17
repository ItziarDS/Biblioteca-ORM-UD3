from sqlalchemy.orm import Session

from app.modelos import Socio


class SocioRepositorio:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_socio: int) -> Socio | None:
        return self.session.get(Socio, id_socio)

    def añadir(self, socio: Socio) -> None:
        self.session.add(socio)