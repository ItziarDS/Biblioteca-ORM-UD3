"""Compara el número de consultas ANTES y DESPUÉS de optimizar (problema N+1).

Ejecutar con la base de datos configurada:   python n_mas_1.py
"""
from sqlalchemy import event, select

from app.conexion import SessionLocal, engine
from app.dto.libros import FiltroLibros
from app.modelos import Autor, Libro, Prestamo
from app.repositorios import AutorRepositorio, LibroRepositorio, PrestamoRepositorio


class Contador:
    """Cuenta (y muestra) cada consulta SQL que se envía a PostgreSQL."""

    def __init__(self) -> None:
        self.total = 0

    def __call__(self, conn, cursor, statement, parameters, context, executemany):
        self.total += 1
        print(f"   SQL {self.total:>2}: {' '.join(statement.split())[:100]}")


def medir(titulo: str, funcion) -> int:
    print(f"\n===== {titulo} =====")
    contador = Contador()
    event.listen(engine, "before_cursor_execute", contador)
    try:
        with SessionLocal() as session:
            funcion(session)
    finally:
        event.remove(engine, "before_cursor_execute", contador)
    print(f">>> {titulo}: {contador.total} consultas")
    return contador.total


# ---- 1. Libros con su autor ----
def libros_antes(session) -> None:
    for libro in session.scalars(select(Libro)).all():
        _ = libro.autor.apellidos            # carga diferida: 1 consulta por autor


def libros_despues(session) -> None:
    filtro = FiltroLibros(tamano=100, solo_activos=False)
    for libro in LibroRepositorio(session).listar(filtro):
        _ = libro.autor.apellidos            # ya cargado con joinedload


# ---- 2. Autores con sus libros ----
def autores_antes(session) -> None:
    for autor in AutorRepositorio(session).listar_todos():
        _ = [libro.titulo for libro in autor.libros]


def autores_despues(session) -> None:
    for autor in AutorRepositorio(session).listar_con_libros():
        _ = [libro.titulo for libro in autor.libros]


# ---- 3. Préstamos abiertos con socio y ejemplares ----
def _recorrer(prestamos) -> None:
    for p in prestamos:
        _ = p.socio.nombre
        for ejemplar in p.ejemplares:
            _ = ejemplar.libro.titulo


def prestamos_antes(session) -> None:
    consulta = select(Prestamo).where(Prestamo.fecha_devolucion.is_(None))
    _recorrer(session.scalars(consulta).all())


def prestamos_despues(session) -> None:
    _recorrer(PrestamoRepositorio(session).listar_abiertos())


if __name__ == "__main__":
    # Calentamiento: la primera conexión hace consultas internas que no cuentan.
    with engine.connect() as conexion:
        conexion.exec_driver_sql("SELECT 1")

    resultados = [
        ("Libros + autor", medir("ANTES libros (carga diferida)", libros_antes),
         medir("DESPUÉS libros (joinedload)", libros_despues)),
        ("Autores + libros", medir("ANTES autores (carga diferida)", autores_antes),
         medir("DESPUÉS autores (selectinload)", autores_despues)),
        ("Préstamos + socio + ejemplares",
         medir("ANTES préstamos (carga diferida)", prestamos_antes),
         medir("DESPUÉS préstamos (joinedload + selectinload)", prestamos_despues)),
    ]

    print("\n===== RESUMEN =====")
    for nombre, antes, despues in resultados:
        print(f"{nombre:<32} antes: {antes:>3} consultas | después: {despues:>3}")