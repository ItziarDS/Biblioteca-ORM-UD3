"""Excepciones de dominio: errores de negocio, no errores técnicos."""


class BibliotecaError(Exception):
    """Clase base: permite capturar cualquier error de negocio de una vez."""


# DATOS DE ENTRADA
class DatosInvalidos(BibliotecaError):
    pass


class PrecioInvalido(DatosInvalidos):
    pass


# CATÁLOGO
class AutorNoEncontrado(BibliotecaError):
    pass


class LibroNoEncontrado(BibliotecaError):
    pass


class IsbnDuplicado(BibliotecaError):
    pass


# PRÉSTAMO
class SocioNoEncontrado(BibliotecaError):
    pass


class SocioInactivo(BibliotecaError):
    pass


class EjemplarNoEncontrado(BibliotecaError):
    pass


class EjemplarNoDisponible(BibliotecaError):
    pass


class PrestamoNoEncontrado(BibliotecaError):
    pass


class PrestamoYaDevuelto(BibliotecaError):
    pass