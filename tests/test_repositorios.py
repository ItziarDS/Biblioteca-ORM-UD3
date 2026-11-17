"""Pruebas de INTEGRACIÓN: PostgreSQL real (biblioteca_test).

Cada prueba se ejecuta dentro de una transacción que se revierte al terminar:
la base de datos queda exactamente igual que antes.
"""
from decimal import Decimal

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from app.dto.libros import FiltroLibros
from app.modelos import Autor, Ejemplar, Libro, Socio
from app.repositorios import LibroRepositorio, PrestamoRepositorio
from app.servicios.prestamos import PrestamoServicio
from app.unidad_trabajo import UnidadTrabajoSQLAlchemy


def un_autor(session) -> Autor:
    autor = session.scalars(select(Autor)).first()
    assert autor is not None, "biblioteca_test debe tener al menos un autor"
    return autor


def test_insertar_y_buscar_libro(session):
    autor = un_autor(session)
    repo = LibroRepositorio(session)

    libro = Libro(
        isbn="9780000099991",
        titulo="Libro de integración",
        precio=Decimal("19.90"),
        id_autor=autor.id_autor,
        publicado=True,
    )
    repo.añadir(libro)
    session.flush()                         # la BD asigna id_libro

    encontrado = repo.buscar(libro.id_libro)
    assert encontrado is not None
    assert encontrado.titulo == "Libro de integración"
    assert encontrado.precio == Decimal("19.90")
    assert encontrado.autor.id_autor == autor.id_autor


def test_isbn_duplicado(session):
    autor = un_autor(session)
    repo = LibroRepositorio(session)
    repo.añadir(Libro(isbn="9780000099992", titulo="Original",
                      precio=Decimal("10.00"), id_autor=autor.id_autor))
    session.flush()

    repo.añadir(Libro(isbn="9780000099992", titulo="Copia",
                      precio=Decimal("12.00"), id_autor=autor.id_autor))

    with pytest.raises(IntegrityError):
        session.flush()                     # aquí PostgreSQL rechaza el ISBN


def test_registrar_prestamo_cambia_el_estado_del_ejemplar(fabrica_sesiones):
    # Preparación: un socio activo y un ejemplar que sabemos DISPONIBLE.
    with UnidadTrabajoSQLAlchemy(fabrica_sesiones) as uow:
        socio = uow.session.scalars(
            select(Socio).where(Socio.activo.is_(True))
        ).first()
        ejemplar = uow.session.scalars(
            select(Ejemplar).where(Ejemplar.estado != "BAJA")
        ).first()
        ejemplar.estado = "DISPONIBLE"
        uow.commit()
        id_socio, id_ejemplar = socio.id_socio, ejemplar.id_ejemplar

    # Acción: el servicio registra el préstamo (un único commit).
    servicio = PrestamoServicio(UnidadTrabajoSQLAlchemy(fabrica_sesiones))
    id_prestamo = servicio.registrar_prestamo(id_socio, id_ejemplar)

    # Comprobación: leemos desde una sesión nueva.
    with UnidadTrabajoSQLAlchemy(fabrica_sesiones) as uow:
        assert uow.ejemplares.buscar(id_ejemplar).estado == "PRESTADO"
        prestamo = uow.prestamos.buscar(id_prestamo)
        assert prestamo.id_socio == id_socio
        assert prestamo.fecha_devolucion is None
        assert [e.id_ejemplar for e in prestamo.ejemplares] == [id_ejemplar]


def test_devolver_prestamo_libera_el_ejemplar(fabrica_sesiones):
    with UnidadTrabajoSQLAlchemy(fabrica_sesiones) as uow:
        socio = uow.session.scalars(
            select(Socio).where(Socio.activo.is_(True))
        ).first()
        ejemplar = uow.session.scalars(
            select(Ejemplar).where(Ejemplar.estado != "BAJA")
        ).first()
        ejemplar.estado = "DISPONIBLE"
        uow.commit()
        id_socio, id_ejemplar = socio.id_socio, ejemplar.id_ejemplar

    servicio = PrestamoServicio(UnidadTrabajoSQLAlchemy(fabrica_sesiones))
    id_prestamo = servicio.registrar_prestamo(id_socio, id_ejemplar)
    servicio.devolver_prestamo(id_prestamo)

    with UnidadTrabajoSQLAlchemy(fabrica_sesiones) as uow:
        assert uow.ejemplares.buscar(id_ejemplar).estado == "DISPONIBLE"
        assert uow.prestamos.buscar(id_prestamo).fecha_devolucion is not None


def test_paginacion_sin_solapar_paginas(session):
    repo = LibroRepositorio(session)
    filtro = FiltroLibros(solo_activos=False, tamano=2)

    pagina_1 = repo.listar(filtro)
    pagina_2 = repo.listar(FiltroLibros(solo_activos=False, tamano=2, pagina=2))

    assert len(pagina_1) == 2
    assert len(pagina_2) >= 1
    ids_1 = {libro.id_libro for libro in pagina_1}
    ids_2 = {libro.id_libro for libro in pagina_2}
    assert ids_1.isdisjoint(ids_2)
    assert repo.contar(filtro) >= len(ids_1) + len(ids_2)


def registrar_selects(conexion, consultas: list):
    """Guarda cada SELECT que se envía a la base de datos (ignora SAVEPOINT)."""

    def contar(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            consultas.append(statement)

    event.listen(conexion, "before_cursor_execute", contar)
    return contar


def test_listado_de_libros_no_produce_n_mas_1(session, conexion_test):
    consultas = []
    session.connection()                    # abre la transacción antes de contar
    contar = registrar_selects(conexion_test, consultas)
    try:
        libros = LibroRepositorio(session).listar(
            FiltroLibros(solo_activos=False, tamano=50)
        )
        for libro in libros:
            _ = libro.autor.apellidos       # ya cargado con joinedload: sin consulta extra
    finally:
        event.remove(conexion_test, "before_cursor_execute", contar)

    assert len(libros) > 1
    assert len(consultas) == 1              # libros + autor en una sola consulta


def test_prestamos_abiertos_se_cargan_con_dos_consultas(session, conexion_test):
    consultas = []
    session.connection()
    contar = registrar_selects(conexion_test, consultas)
    try:
        abiertos = PrestamoRepositorio(session).listar_abiertos()
        for p in abiertos:
            _ = p.socio.nombre
            for ejemplar in p.ejemplares:
                _ = ejemplar.libro.titulo
    finally:
        event.remove(conexion_test, "before_cursor_execute", contar)

    assert len(consultas) <= 2              # préstamos+socio, y ejemplares+libro