"""Unit of Work: una Session, una transacción, un commit o un rollback."""
from sqlalchemy.orm import sessionmaker

from app.repositorios import (
    AutorRepositorio,
    EjemplarRepositorio,
    LibroRepositorio,
    PrestamoRepositorio,
    SocioRepositorio,
)


class UnidadTrabajoSQLAlchemy:
    def __init__(self, fabrica_sesiones: sessionmaker) -> None:
        self.fabrica_sesiones = fabrica_sesiones

    def __enter__(self):
        # Una única Session compartida por todos los repositorios.
        self.session = self.fabrica_sesiones()
        self.autores = AutorRepositorio(self.session)
        self.libros = LibroRepositorio(self.session)
        self.socios = SocioRepositorio(self.session)
        self.ejemplares = EjemplarRepositorio(self.session)
        self.prestamos = PrestamoRepositorio(self.session)
        return self

    def __exit__(self, tipo_error, error, traceback) -> None:
        # Si hubo excepción dentro del with, se deshace todo.
        if tipo_error is not None:
            self.session.rollback()
        # Siempre se cierra la sesión.
        self.session.close()

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()