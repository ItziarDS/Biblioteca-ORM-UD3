from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.configuracion import obtener_url_bd
from app.modelos import Base

config = context.config

# La URL sale de las variables de entorno. Los "%" se duplican porque
# ConfigParser usa "%" como carácter especial.
config.set_main_option("sqlalchemy.url", obtener_url_bd().replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos del modelo: es lo que compara --autogenerate con la base de datos.
target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Ignora tablas y columnas que existen en la BD pero no están mapeadas
    (por ejemplo id_editorial o renovaciones), para que --autogenerate no
    intente borrarlas."""
    if type_ in ("table", "column") and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()