"""Pruebas UNITARIAS del servicio de préstamos (repositorios y UoW falsos)."""
from datetime import date

import pytest

from app.excepciones import (
    EjemplarNoDisponible,
    EjemplarNoEncontrado,
    PrestamoNoEncontrado,
    PrestamoYaDevuelto,
    SocioInactivo,
    SocioNoEncontrado,
)
from app.servicios.prestamos import PrestamoServicio


def test_rechaza_socio_inexistente(uow_falsa):
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(SocioNoEncontrado):
        servicio.registrar_prestamo(id_socio=99, id_ejemplar=1)

    assert uow_falsa.commits == 0


def test_rechaza_socio_inactivo(uow_falsa, ejemplar):
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(SocioInactivo):
        servicio.registrar_prestamo(id_socio=2, id_ejemplar=1)

    assert ejemplar.estado == "DISPONIBLE"     # no se tocó nada
    assert uow_falsa.commits == 0
    assert uow_falsa.rollbacks == 1


def test_rechaza_ejemplar_inexistente(uow_falsa):
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(EjemplarNoEncontrado):
        servicio.registrar_prestamo(id_socio=1, id_ejemplar=99)


@pytest.mark.parametrize("estado", ["PRESTADO", "RESERVADO", "BAJA"])
def test_rechaza_ejemplar_no_disponible(uow_falsa, ejemplar, estado):
    ejemplar.estado = estado
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(EjemplarNoDisponible):
        servicio.registrar_prestamo(id_socio=1, id_ejemplar=1)

    assert ejemplar.estado == estado
    assert uow_falsa.commits == 0


def test_registrar_prestamo_correcto(uow_falsa, ejemplar):
    servicio = PrestamoServicio(uow_falsa)

    id_prestamo = servicio.registrar_prestamo(id_socio=1, id_ejemplar=1)

    prestamo = uow_falsa.prestamos.buscar(id_prestamo)
    assert ejemplar.estado == "PRESTADO"
    assert prestamo.ejemplares == [ejemplar]
    assert prestamo.fecha_devolucion is None
    assert (prestamo.fecha_limite - prestamo.fecha_prestamo).days == 15
    assert uow_falsa.commits == 1               # un único commit
    assert uow_falsa.cerrada is True


def test_devolver_prestamo_correcto(uow_con_prestamo, ejemplar):
    servicio = PrestamoServicio(uow_con_prestamo)

    servicio.devolver_prestamo(1)

    prestamo = uow_con_prestamo.prestamos.buscar(1)
    assert prestamo.fecha_devolucion == date.today()
    assert ejemplar.estado == "DISPONIBLE"
    assert uow_con_prestamo.commits == 1


def test_no_se_puede_devolver_dos_veces(uow_con_prestamo):
    servicio = PrestamoServicio(uow_con_prestamo)
    servicio.devolver_prestamo(1)

    with pytest.raises(PrestamoYaDevuelto):
        servicio.devolver_prestamo(1)

    assert uow_con_prestamo.commits == 1        # el segundo intento no confirma


def test_devolver_prestamo_inexistente(uow_con_prestamo):
    servicio = PrestamoServicio(uow_con_prestamo)

    with pytest.raises(PrestamoNoEncontrado):
        servicio.devolver_prestamo(99)