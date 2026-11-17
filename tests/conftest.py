"""Fixtures compartidas.

PARTE 1: objetos falsos para las pruebas UNITARIAS (sin base de datos).
PARTE 2: conexión a biblioteca_test para las pruebas de INTEGRACIÓN.
"""
import os
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.configuracion import obtener_url_bd
from app.modelos import Autor, Ejemplar, Libro, Prestamo, Socio


# =====================================================================
# PARTE 1: repositorios falsos y Unit of Work falsa
# =====================================================================
class RepositorioFalso:
    """Guarda las entidades en un diccionario en lugar de PostgreSQL."""

    def __init__(self, nombre_id: str, entidades=()) -> None:
        self.nombre_id = nombre_id
        self.items = {getattr(e, nombre_id): e for e in entidades}
        self.pendientes = []

    def buscar(self, identificador):
        return self.items.get(identificador)

    def añadir(self, entidad) -> None:
        self.pendientes.append(entidad)

    def volcar(self) -> None:
        """Simula flush(): asigna el id que asignaría la base de datos."""
        for entidad in self.pendientes:
            if getattr(entidad, self.nombre_id) is None:
                siguiente = max(self.items, default=0) + 1
                setattr(entidad, self.nombre_id, siguiente)
            self.items[getattr(entidad, self.nombre_id)] = entidad
        self.pendientes.clear()


class LibroRepositorioFalso(RepositorioFalso):
    def buscar_por_isbn(self, isbn):
        for libro in self.items.values():
            if libro.isbn == isbn:
                return libro
        return None


class UnidadTrabajoFalsa:
    """Imita a UnidadTrabajoSQLAlchemy y cuenta commits y rollbacks."""

    def __init__(self, autores=(), libros=(), socios=(), ejemplares=(), prestamos=()):
        self.autores = RepositorioFalso("id_autor", autores)
        self.libros = LibroRepositorioFalso("id_libro", libros)
        self.socios = RepositorioFalso("id_socio", socios)
        self.ejemplares = RepositorioFalso("id_ejemplar", ejemplares)
        self.prestamos = RepositorioFalso("id_prestamo", prestamos)
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def __enter__(self):
        self.cerrada = False
        return self

    def __exit__(self, tipo_error, error, traceback) -> None:
        if tipo_error is not None:
            self.rollback()
        self.cerrada = True

    def flush(self) -> None:
        for repositorio in (self.libros, self.prestamos):
            repositorio.volcar()

    def commit(self) -> None:
        self.flush()
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


# ---------- Entidades de ejemplo ----------
@pytest.fixture
def autor():
    return Autor(id_autor=1, nombre="Miguel", apellidos="de Cervantes")


@pytest.fixture
def libro(autor):
    return Libro(
        id_libro=1,
        isbn="9780000000001",
        titulo="Libro de prueba",
        precio=Decimal("19.90"),
        id_autor=1,
        autor=autor,
        publicado=True,
    )


@pytest.fixture
def socio():
    return Socio(
        id_socio=1, dni="10000001A", nombre="Ana", apellidos="Martín López",
        email="ana@example.test", telefono=None,
        fecha_alta=date(2025, 9, 1), activo=True,
    )


@pytest.fixture
def socio_inactivo():
    return Socio(
        id_socio=2, dni="10000002B", nombre="Pablo", apellidos="Ortega León",
        email="pablo@example.test", telefono=None,
        fecha_alta=date(2025, 9, 1), activo=False,
    )


@pytest.fixture
def ejemplar():
    return Ejemplar(
        id_ejemplar=1, id_libro=1, codigo_inventario="EJ-0001",
        ubicacion="A1-01", estado="DISPONIBLE", fecha_alta=date(2025, 9, 1),
    )


@pytest.fixture
def uow_falsa(autor, libro, socio, socio_inactivo, ejemplar):
    return UnidadTrabajoFalsa(
        autores=[autor],
        libros=[libro],
        socios=[socio, socio_inactivo],
        ejemplares=[ejemplar],
    )


@pytest.fixture
def uow_con_prestamo(autor, libro, socio, ejemplar):
    """Unit of Work con un préstamo abierto del ejemplar 1."""
    ejemplar.estado = "PRESTADO"
    prestamo = Prestamo(
        id_prestamo=1,
        socio=socio,
        fecha_prestamo=date(2026, 11, 1),
        fecha_limite=date(2026, 11, 16),
        ejemplares=[ejemplar],
    )
    return UnidadTrabajoFalsa(
        autores=[autor], libros=[libro], socios=[socio],
        ejemplares=[ejemplar], prestamos=[prestamo],
    )


# =====================================================================
# PARTE 2: pruebas de integración contra biblioteca_test
# =====================================================================
@pytest.fixture(scope="session")
def engine_test():
    """Engine de biblioteca_test. Se niega a funcionar con otra base de datos."""
    nombre_bd = os.getenv("DB_NAME", "biblioteca_test")
    if not nombre_bd.endswith("_test"):
        raise RuntimeError(
            "Las pruebas de integración solo pueden usar una base _test "
            f"(DB_NAME actual: {nombre_bd!r})."
        )
    engine = create_engine(obtener_url_bd())
    yield engine
    engine.dispose()


@pytest.fixture
def conexion_test(engine_test):
    """Conexión con una transacción exterior que SIEMPRE se revierte al final."""
    conexion = engine_test.connect()
    transaccion = conexion.begin()
    try:
        yield conexion
    finally:
        transaccion.rollback()      # deshace todo lo que hizo la prueba
        conexion.close()


@pytest.fixture
def fabrica_sesiones(conexion_test):
    """Sesiones ligadas a la conexión de prueba.

    create_savepoint: cada commit() de una Session solo libera un SAVEPOINT,
    así que la transacción exterior sigue abierta y se puede revertir.
    """
    return sessionmaker(
        bind=conexion_test,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
def session(fabrica_sesiones):
    sesion = fabrica_sesiones()
    try:
        yield sesion
    finally:
        sesion.close()
