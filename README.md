# Biblioteca ORM

Aplicación de consola para administrar una biblioteca (libros, autores, socios,
ejemplares y préstamos) con **Python, SQLAlchemy 2.x y PostgreSQL**. Proyecto
integrador de la Unidad 3 (Persistencia con herramientas ORM) del módulo
0486 Acceso a Datos.

## Autoría y reparto de tareas

Proyecto realizado de forma individual por **Itziar Duran Sánchez**, que ha
asumido los tres roles del enunciado:

| Rol | Responsabilidad | Realizado por |
|---|---|---|
| Modelos y repositorios | Entidades ORM, relaciones, consultas, repositorios, estrategias de carga | Itziar Duran Sánchez |
| Servicios y transacciones | Reglas de negocio, Unit of Work, préstamos, excepciones, `commit()` / `rollback()` | Itziar Duran Sánchez |
| Pruebas, migraciones y documentación | pytest, fixtures, pruebas de integración, diagnóstico de consultas, Alembic, README y evidencias | Itziar Duran Sánchez |

## Requisitos

- Python 3.11 o superior.
- PostgreSQL con la base de datos `biblioteca` (y una copia `biblioteca_test`).
- Paquetes de `requirements.txt`: SQLAlchemy, psycopg, Alembic y pytest.

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Variables de entorno

Las credenciales **no** están en el código ni en el repositorio. Se definen en la
terminal antes de ejecutar nada (PowerShell):

| Variable | Significado | Valor por defecto |
|---|---|---|
| `DB_HOST` | Servidor PostgreSQL | `localhost` |
| `DB_PORT` | Puerto | `5432` |
| `DB_NAME` | Base de datos (`biblioteca` o `biblioteca_test`) | `biblioteca` |
| `DB_USER` | Usuario | *(obligatoria)* |
| `DB_PASSWORD` | Contraseña | *(obligatoria)* |

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "biblioteca"
$env:DB_USER = "usuario"
$env:DB_PASSWORD = "<tu contraseña>"
```

## Creación de `biblioteca_test`

Las pruebas de integración usan una copia de la base de datos para no tocar los
datos reales. Con un usuario administrador y **sin conexiones abiertas** a
`biblioteca`:

```sql
CREATE DATABASE biblioteca_test TEMPLATE biblioteca;
ALTER TABLE libros OWNER TO usuario;   -- ejecutar conectado a biblioteca_test
```

Los permisos que necesita el usuario de la aplicación (en ambas bases):

```sql
GRANT SELECT, INSERT, UPDATE ON libros, prestamos, ejemplares TO usuario;
GRANT SELECT, INSERT ON detalle_prestamo TO usuario;
```

La fixture de pruebas se niega a ejecutarse si `DB_NAME` no termina en `_test`.

## Aplicación de migraciones

```powershell
alembic current          # revisión aplicada
alembic upgrade head     # añade libros.observaciones
alembic downgrade -1     # la elimina
alembic upgrade head     # la vuelve a aplicar (se entrega en la última versión)
alembic history          # historial de revisiones
```

La revisión `6133bce43e8c` añade la columna `observaciones VARCHAR(500)` (opcional)
a `libros`. Las migraciones se guardan en Git: son el historial del esquema.

## Ejecución de la aplicación

```powershell
python main.py
```

## Ejecución de las pruebas

```powershell
$env:DB_NAME = "biblioteca_test"
pytest -q
```

- **Pruebas unitarias** (`test_catalogo_servicio.py`, `test_prestamo_servicio.py`):
  repositorios y Unit of Work falsos, sin base de datos.
- **Pruebas de integración** (`test_repositorios.py`): PostgreSQL real
  (`biblioteca_test`) dentro de una transacción que se revierte al terminar.

Comparación de rendimiento (problema N+1), con la base configurada:

```powershell
python n_mas_1.py
```

## Estructura del proyecto

```
biblioteca_orm/
├── alembic/                 migraciones (env.py, script.py.mako, versions/)
├── app/
│   ├── modelos/             Autor, Libro, Socio, Ejemplar, Prestamo (+ base.py)
│   ├── repositorios/        acceso a datos con la Session
│   ├── servicios/           catalogo.py y prestamos.py (reglas de negocio)
│   ├── dto/                 libros.py y prestamos.py (objetos de transferencia)
│   ├── configuracion.py     URL de la BD desde variables de entorno
│   ├── conexion.py          engine y SessionLocal
│   ├── excepciones.py       excepciones de dominio
│   └── unidad_trabajo.py    Unit of Work
├── tests/                   conftest.py y pruebas unitarias / de integración
├── capturas/                evidencias
├── main.py                  interfaz de consola
├── n_mas_1.py               comparación de consultas antes/después
├── alembic.ini  requirements.txt  pytest.ini  .gitignore  README.md
```

## Arquitectura

```
Interfaz de consola (main.py)
        ↓  DTO / excepciones de dominio
Servicios (catalogo, prestamos)
        ↓
Unit of Work (una Session, una transacción)
        ↓
Repositorios ORM
        ↓
SQLAlchemy  →  PostgreSQL
```

- La **interfaz** pide datos, crea DTO, llama al servicio y muestra el resultado.
  No tiene consultas ni `Session`.
- Los **servicios** aplican las reglas, lanzan excepciones de dominio y no usan
  `print()`. Cada caso de uso abre una Unit of Work y termina con un único
  `commit()` (o `rollback()` si algo falla).
- Los **repositorios** consultan y añaden entidades; nunca hacen `commit()`.
- La **Unit of Work** crea la `Session`, la comparte entre los repositorios y la
  cierra siempre.

## Decisiones principales

- **Eliminación lógica:** desactivar un libro pone `publicado = False`; el
  registro se conserva por su historial de préstamos.
- **Relación N:M** Préstamo–Ejemplar mediante una `Table` (`detalle_prestamo`).
  La columna `renovaciones` existe en la BD con valor por defecto 0 y no se mapea
  porque la aplicación no la usa.
- **DTO inmutables** (`@dataclass(frozen=True)`): las lecturas devuelven datos
  simples, de modo que ninguna entidad ORM sale del servicio.
- **Carga:** `joinedload` para relaciones N:1 (libro→autor, préstamo→socio) y
  `selectinload` para colecciones (autor→libros, préstamo→ejemplares).
- **Pruebas de integración aisladas:** una conexión con transacción exterior que
  se revierte, y sesiones con `join_transaction_mode="create_savepoint"`, de modo
  que los `commit()` de los servicios no llegan a persistirse.
- **Alembic:** `env.py` toma la URL del entorno y filtra con `include_object` las
  tablas y columnas no mapeadas para que `--autogenerate` no intente borrarlas.
- **Estructura:** se añade `app/modelos/base.py` (la `Base` declarativa) y
  `n_mas_1.py` en la raíz (evidencia del control de rendimiento); el resto sigue
  la estructura propuesta.

## Errores conocidos y limitaciones

- El menú no permite dar de alta autores, socios ni ejemplares.
- El estado del ejemplar es un texto (`DISPONIBLE`, `PRESTADO`...), no un `Enum`.
- No hay límite de préstamos por socio ni gestión de renovaciones o retrasos.
- Las pruebas de integración usan datos ya existentes en `biblioteca_test`
  (al menos un autor, un socio activo y un ejemplar).
- El usuario de la BD necesita los permisos indicados arriba; si faltan,
  PostgreSQL responde con `InsufficientPrivilege`.