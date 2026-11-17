"""Pruebas UNITARIAS del servicio de catálogo (repositorios y UoW falsos)."""
from decimal import Decimal

import pytest

from app.dto.libros import DatosLibro, FiltroLibros
from app.excepciones import (
    AutorNoEncontrado,
    DatosInvalidos,
    IsbnDuplicado,
    LibroNoEncontrado,
    PrecioInvalido,
)
from app.servicios.catalogo import CatalogoServicio


def datos_libro(**cambios) -> DatosLibro:
    base = dict(
        isbn="9780000009999",
        titulo="Libro nuevo",
        precio=Decimal("25.00"),
        id_autor=1,
    )
    base.update(cambios)
    return DatosLibro(**base)


@pytest.mark.parametrize("precio", [Decimal("0"), Decimal("-1"), Decimal("-19.90")])
def test_rechaza_precio_no_positivo(uow_falsa, precio):
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(PrecioInvalido):
        servicio.crear_libro(datos_libro(precio=precio))

    assert uow_falsa.commits == 0


def test_no_crea_libro_si_el_autor_no_existe(uow_falsa):
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(AutorNoEncontrado):
        servicio.crear_libro(datos_libro(id_autor=99))

    assert uow_falsa.commits == 0
    assert uow_falsa.rollbacks == 1       # el with deshizo la operación


def test_rechaza_isbn_duplicado(uow_falsa, libro):
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(IsbnDuplicado):
        servicio.crear_libro(datos_libro(isbn=libro.isbn))

    assert uow_falsa.commits == 0


def test_crear_libro_correcto_confirma_la_operacion(uow_falsa):
    servicio = CatalogoServicio(uow_falsa)

    id_libro = servicio.crear_libro(datos_libro())

    assert id_libro == 2                              # el libro 1 ya existía
    assert uow_falsa.libros.buscar(2).publicado is True
    assert uow_falsa.commits == 1
    assert uow_falsa.cerrada is True


def test_actualizar_precio_correcto(uow_falsa, libro):
    servicio = CatalogoServicio(uow_falsa)

    servicio.actualizar_precio(1, Decimal("29.95"))

    assert libro.precio == Decimal("29.95")
    assert uow_falsa.commits == 1


def test_actualizar_precio_de_libro_inexistente(uow_falsa):
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(LibroNoEncontrado):
        servicio.actualizar_precio(99, Decimal("10"))

    assert uow_falsa.commits == 0


def test_desactivar_libro_es_eliminacion_logica(uow_falsa, libro):
    servicio = CatalogoServicio(uow_falsa)

    servicio.desactivar_libro(1)

    assert libro.publicado is False
    assert uow_falsa.libros.buscar(1) is libro        # sigue existiendo
    assert uow_falsa.commits == 1


@pytest.mark.parametrize(
    "filtro",
    [
        FiltroLibros(pagina=0),
        FiltroLibros(tamano=0),
        FiltroLibros(precio_minimo=Decimal("50"), precio_maximo=Decimal("10")),
    ],
)
def test_rechaza_filtros_invalidos(uow_falsa, filtro):
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(DatosInvalidos):
        servicio.listar_libros(filtro)