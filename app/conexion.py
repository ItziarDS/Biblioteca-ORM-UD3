"""Engine y fábrica de sesiones de la aplicación."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.configuracion import obtener_url_bd

# SQL_ECHO=1 muestra en consola el SQL que genera SQLAlchemy.
engine = create_engine(obtener_url_bd(), echo=os.getenv("SQL_ECHO") == "1")

SessionLocal = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)