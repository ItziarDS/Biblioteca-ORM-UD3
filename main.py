"""Interfaz de consola. Solo recoge datos, crea DTO, llama a los servicios y
muestra resultados. No contiene consultas ORM ni gestiona la Session."""
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from math import ceil

from app.conexion import SessionLocal
from app.dto.libros import DatosLibro, FiltroLibros
from app.excepciones import (
    AutorNoEncontrado,
    BibliotecaError,
    DatosInvalidos,
    EjemplarNoDisponible,
    EjemplarNoEncontrado,
    IsbnDuplicado,
    LibroNoEncontrado,
    PrecioInvalido,
    PrestamoNoEncontrado,
    PrestamoYaDevuelto,
    SocioInactivo,
    SocioNoEncontrado,
)
from app.servicios.catalogo import CatalogoServicio
from app.servicios.prestamos import PrestamoServicio
from app.unidad_trabajo import UnidadTrabajoSQLAlchemy

TAMANO_PAGINA = 5

# Traducción de excepciones de dominio a mensajes comprensibles.
MENSAJES = {
    SocioNoEncontrado: "No existe ningún socio con ese identificador.",
    SocioInactivo: "El socio está dado de baja y no puede pedir préstamos.",
    EjemplarNoEncontrado: "No existe ningún ejemplar con ese identificador.",
    EjemplarNoDisponible: "El ejemplar no está disponible para préstamo.",
    PrestamoNoEncontrado: "No existe ningún préstamo con ese identificador.",
    PrestamoYaDevuelto: "Ese préstamo ya estaba devuelto.",
    LibroNoEncontrado: "No existe ningún libro con ese identificador.",
    AutorNoEncontrado: "No existe ningún autor con ese identificador.",
    IsbnDuplicado: "Ya hay un libro registrado con ese ISBN.",
    PrecioInvalido: "El precio debe ser mayor que cero.",
    DatosInvalidos: "Los datos introducidos no son válidos.",
}


def traducir(error: BibliotecaError) -> str:
    mensaje = MENSAJES.get(type(error), "Operación no permitida.")
    return f"{mensaje} ({error})"


# ---------- Entrada de datos ----------
def pedir_texto(mensaje: str, obligatorio: bool = True) -> str:
    while True:
        valor = input(mensaje).strip()
        if valor or not obligatorio:
            return valor
        print("Este dato es obligatorio.")


def pedir_entero(mensaje: str, opcional: bool = False) -> int | None:
    while True:
        valor = input(mensaje).strip()
        if not valor and opcional:
            return None
        try:
            return int(valor)
        except ValueError:
            print("Introduce un número entero.")


def pedir_decimal(mensaje: str, opcional: bool = False) -> Decimal | None:
    while True:
        valor = input(mensaje).strip().replace(",", ".")
        if not valor and opcional:
            return None
        try:
            return Decimal(valor)
        except InvalidOperation:
            print("Introduce un número válido (por ejemplo 12.50).")


def confirmar(mensaje: str) -> bool:
    return input(f"{mensaje} (s/n): ").strip().lower() == "s"


# ---------- Salida de datos ----------
def mostrar_libros(libros) -> None:
    print(f"{'ID':>4}  {'TÍTULO':<42} {'AUTOR':<26} {'PRECIO':>9}")
    print("-" * 85)
    for libro in libros:
        print(
            f"{libro.id_libro:>4}  {libro.titulo[:41]:<42} "
            f"{libro.autor[:25]:<26} {libro.precio:>7.2f} €"
        )


def navegar_libros(catalogo: CatalogoServicio, filtro: FiltroLibros) -> None:
    """Muestra una página y permite moverse entre páginas."""
    while True:
        total = catalogo.contar_libros(filtro)
        paginas = max(1, ceil(total / filtro.tamano))
        libros = catalogo.listar_libros(filtro)

        print()
        if not libros:
            print("No hay libros que cumplan el filtro.")
            return
        mostrar_libros(libros)
        print(f"\nPágina {filtro.pagina} de {paginas} ({total} libros)")

        opcion = input("[S]iguiente  [A]nterior  [M]enú: ").strip().lower()
        if opcion == "s" and filtro.pagina < paginas:
            filtro = replace(filtro, pagina=filtro.pagina + 1)
        elif opcion == "a" and filtro.pagina > 1:
            filtro = replace(filtro, pagina=filtro.pagina - 1)
        elif opcion == "m":
            return


# ---------- Opciones del menú ----------
def listar_libros(catalogo, prestamos) -> None:
    navegar_libros(catalogo, FiltroLibros(tamano=TAMANO_PAGINA))


def buscar_libros(catalogo, prestamos) -> None:
    print("Deja vacío lo que no quieras filtrar.")
    filtro = FiltroLibros(
        texto=pedir_texto("Texto del título: ", obligatorio=False) or None,
        id_autor=pedir_entero("ID de autor: ", opcional=True),
        precio_minimo=pedir_decimal("Precio mínimo: ", opcional=True),
        precio_maximo=pedir_decimal("Precio máximo: ", opcional=True),
        solo_activos=confirmar("¿Solo libros activos?"),
        tamano=TAMANO_PAGINA,
    )
    navegar_libros(catalogo, filtro)


def crear_libro(catalogo, prestamos) -> None:
    datos = DatosLibro(
        isbn=pedir_texto("ISBN: "),
        titulo=pedir_texto("Título: "),
        precio=pedir_decimal("Precio: "),
        id_autor=pedir_entero("ID del autor: "),
    )
    id_libro = catalogo.crear_libro(datos)
    print(f"Libro creado con id {id_libro}.")


def actualizar_precio(catalogo, prestamos) -> None:
    id_libro = pedir_entero("ID del libro: ")
    nuevo_precio = pedir_decimal("Nuevo precio: ")
    catalogo.actualizar_precio(id_libro, nuevo_precio)
    print("Precio actualizado.")


def desactivar_libro(catalogo, prestamos) -> None:
    id_libro = pedir_entero("ID del libro: ")
    if confirmar(f"¿Desactivar el libro {id_libro}?"):
        catalogo.desactivar_libro(id_libro)
        print("Libro desactivado.")
    else:
        print("Operación cancelada.")


def registrar_prestamo(catalogo, prestamos) -> None:
    id_socio = pedir_entero("ID del socio: ")
    id_ejemplar = pedir_entero("ID del ejemplar: ")
    id_prestamo = prestamos.registrar_prestamo(id_socio, id_ejemplar)
    print(f"Préstamo registrado con id {id_prestamo}.")


def devolver_prestamo(catalogo, prestamos) -> None:
    id_prestamo = pedir_entero("ID del préstamo: ")
    prestamos.devolver_prestamo(id_prestamo)
    print("Préstamo devuelto. Los ejemplares vuelven a estar disponibles.")


def mostrar_prestamos_abiertos(catalogo, prestamos) -> None:
    abiertos = prestamos.listar_prestamos_abiertos()
    if not abiertos:
        print("No hay préstamos abiertos.")
        return
    for p in abiertos:
        print(
            f"#{p.id_prestamo} | {p.socio} | "
            f"desde {p.fecha_prestamo} hasta {p.fecha_limite}"
        )
        for ejemplar in p.ejemplares:
            print(f"      - {ejemplar}")


OPCIONES = {
    "1": listar_libros,
    "2": buscar_libros,
    "3": crear_libro,
    "4": actualizar_precio,
    "5": desactivar_libro,
    "6": registrar_prestamo,
    "7": devolver_prestamo,
    "8": mostrar_prestamos_abiertos,
}


def mostrar_menu() -> None:
    print(
        "\nBIBLIOTECA ORM\n\n"
        "1. Listar libros\n"
        "2. Buscar libros\n"
        "3. Crear libro\n"
        "4. Actualizar precio\n"
        "5. Desactivar libro\n"
        "6. Registrar préstamo\n"
        "7. Devolver préstamo\n"
        "8. Mostrar préstamos abiertos\n"
        "9. Salir"
    )


def main() -> None:
    catalogo = CatalogoServicio(UnidadTrabajoSQLAlchemy(SessionLocal))
    prestamos = PrestamoServicio(UnidadTrabajoSQLAlchemy(SessionLocal))

    while True:
        mostrar_menu()
        opcion = input("\nOpción: ").strip()

        if opcion == "9":
            print("Hasta pronto.")
            break

        accion = OPCIONES.get(opcion)
        if accion is None:
            print("Opción no válida.")
            continue

        try:
            accion(catalogo, prestamos)
        except BibliotecaError as error:
            print(f"\nERROR: {traducir(error)}")
        except Exception as error:  # fallo técnico: el menú no debe caerse
            print(f"\nERROR inesperado ({type(error).__name__}): {error}")


if __name__ == "__main__":
    main()