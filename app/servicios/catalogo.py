"""Servicio de catálogo: reglas de negocio de libros. No usa print() ni input()."""
from decimal import Decimal

from app.dto.libros import DatosLibro, FiltroLibros, LibroResumen
from app.excepciones import (
    AutorNoEncontrado,
    DatosInvalidos,
    IsbnDuplicado,
    LibroNoEncontrado,
    PrecioInvalido,
)
from app.modelos import Libro


def _a_resumen(libro: Libro) -> LibroResumen:
    """Convierte la entidad ORM en un DTO (se hace DENTRO del with)."""
    return LibroResumen(
        id_libro=libro.id_libro,
        titulo=libro.titulo,
        autor=f"{libro.autor.nombre} {libro.autor.apellidos}",
        precio=libro.precio,
    )


def _validar_precio(precio: Decimal) -> None:
    if precio <= 0:
        raise PrecioInvalido("El precio debe ser mayor que cero.")


def _validar_filtro(filtro: FiltroLibros) -> None:
    if filtro.pagina < 1:
        raise DatosInvalidos("La página debe ser 1 o mayor.")
    if filtro.tamano < 1:
        raise DatosInvalidos("El tamaño de página debe ser 1 o mayor.")
    if (
        filtro.precio_minimo is not None
        and filtro.precio_maximo is not None
        and filtro.precio_minimo > filtro.precio_maximo
    ):
        raise DatosInvalidos("El precio mínimo no puede superar al máximo.")


class CatalogoServicio:
    def __init__(self, unidad_trabajo) -> None:
        self.unidad_trabajo = unidad_trabajo

    # ---------- Lecturas ----------
    def listar_libros(self, filtro: FiltroLibros | None = None) -> list[LibroResumen]:
        filtro = filtro or FiltroLibros()
        _validar_filtro(filtro)
        with self.unidad_trabajo as uow:
            return [_a_resumen(libro) for libro in uow.libros.listar(filtro)]

    def contar_libros(self, filtro: FiltroLibros | None = None) -> int:
        filtro = filtro or FiltroLibros()
        _validar_filtro(filtro)
        with self.unidad_trabajo as uow:
            return uow.libros.contar(filtro)

    def buscar_libro(self, id_libro: int) -> LibroResumen:
        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                raise LibroNoEncontrado(f"No existe el libro {id_libro}.")
            return _a_resumen(libro)

    # ---------- Escrituras ----------
    def crear_libro(self, datos: DatosLibro) -> int:
        # Validaciones que no necesitan la base de datos: antes del with.
        if not datos.isbn.strip():
            raise DatosInvalidos("El ISBN es obligatorio.")
        if not datos.titulo.strip():
            raise DatosInvalidos("El título es obligatorio.")
        _validar_precio(datos.precio)

        with self.unidad_trabajo as uow:
            if uow.autores.buscar(datos.id_autor) is None:
                raise AutorNoEncontrado(f"No existe el autor {datos.id_autor}.")
            if uow.libros.buscar_por_isbn(datos.isbn.strip()) is not None:
                raise IsbnDuplicado(f"Ya existe un libro con el ISBN {datos.isbn}.")

            libro = Libro(
                isbn=datos.isbn.strip(),
                titulo=datos.titulo.strip(),
                precio=datos.precio,
                id_autor=datos.id_autor,
                publicado=True,
            )
            uow.libros.añadir(libro)
            uow.flush()                 # la BD asigna id_libro
            id_libro = libro.id_libro
            uow.commit()
            return id_libro

    def actualizar_precio(self, id_libro: int, nuevo_precio: Decimal) -> None:
        _validar_precio(nuevo_precio)
        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                raise LibroNoEncontrado(f"No existe el libro {id_libro}.")
            libro.precio = nuevo_precio
            uow.commit()

    def desactivar_libro(self, id_libro: int) -> None:
        """Eliminación lógica: el libro sigue en la BD, pero publicado=False."""
        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                raise LibroNoEncontrado(f"No existe el libro {id_libro}.")
            libro.publicado = False
            uow.commit()