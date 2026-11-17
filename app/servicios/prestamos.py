"""Servicio de préstamos: cada caso de uso es una única transacción atómica."""
from datetime import date, timedelta

from app.dto.prestamos import PrestamoResumen
from app.excepciones import (
    EjemplarNoDisponible,
    EjemplarNoEncontrado,
    PrestamoNoEncontrado,
    PrestamoYaDevuelto,
    SocioInactivo,
    SocioNoEncontrado,
)
from app.modelos import Prestamo
from app.modelos.ejemplar import DISPONIBLE, PRESTADO

DIAS_PRESTAMO = 15


class PrestamoServicio:
    def __init__(self, unidad_trabajo) -> None:
        self.unidad_trabajo = unidad_trabajo

    def registrar_prestamo(self, id_socio: int, id_ejemplar: int) -> int:
        with self.unidad_trabajo as uow:
            socio = uow.socios.buscar(id_socio)
            if socio is None:
                raise SocioNoEncontrado(f"No existe el socio {id_socio}.")
            if not socio.activo:
                raise SocioInactivo(f"El socio {id_socio} no está activo.")

            ejemplar = uow.ejemplares.buscar(id_ejemplar)
            if ejemplar is None:
                raise EjemplarNoEncontrado(f"No existe el ejemplar {id_ejemplar}.")
            if ejemplar.estado != DISPONIBLE:
                raise EjemplarNoDisponible(
                    f"El ejemplar {id_ejemplar} no está disponible "
                    f"(estado: {ejemplar.estado})."
                )

            hoy = date.today()
            prestamo = Prestamo(
                socio=socio,
                fecha_prestamo=hoy,
                fecha_limite=hoy + timedelta(days=DIAS_PRESTAMO),
            )
            prestamo.ejemplares.append(ejemplar)
            ejemplar.estado = PRESTADO

            uow.prestamos.añadir(prestamo)
            uow.flush()                         # la BD asigna id_prestamo
            id_prestamo = prestamo.id_prestamo
            uow.commit()                        # UN único commit
            return id_prestamo

    def devolver_prestamo(self, id_prestamo: int) -> None:
        with self.unidad_trabajo as uow:
            prestamo = uow.prestamos.buscar(id_prestamo)
            if prestamo is None:
                raise PrestamoNoEncontrado(f"No existe el préstamo {id_prestamo}.")
            if prestamo.fecha_devolucion is not None:
                raise PrestamoYaDevuelto(
                    f"El préstamo {id_prestamo} ya se devolvió el "
                    f"{prestamo.fecha_devolucion}."
                )

            prestamo.fecha_devolucion = date.today()
            for ejemplar in prestamo.ejemplares:
                ejemplar.estado = DISPONIBLE
            uow.commit()                        # todo junto o nada

    def listar_prestamos_abiertos(self) -> list[PrestamoResumen]:
        with self.unidad_trabajo as uow:
            return [
                PrestamoResumen(
                    id_prestamo=p.id_prestamo,
                    socio=f"{p.socio.nombre} {p.socio.apellidos}",
                    ejemplares=tuple(
                        f"{e.codigo_inventario} - {e.libro.titulo}"
                        for e in p.ejemplares
                    ),
                    fecha_prestamo=p.fecha_prestamo,
                    fecha_limite=p.fecha_limite,
                    fecha_devolucion=p.fecha_devolucion,
                )
                for p in uow.prestamos.listar_abiertos()
            ]