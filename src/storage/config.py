"""Configuración de conexión a la base de datos PostgreSQL.

Los parámetros se leen de variables de entorno con prefijo MONITOREO_DB_. Si
existe un archivo .env en la raíz del proyecto y python-dotenv está instalado,
se carga automáticamente (sin sobrescribir variables ya definidas).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class DatabaseConfig:
    """Parámetros de conexión a PostgreSQL.

    Attributes:
        host: Servidor de base de datos.
        port: Puerto TCP de PostgreSQL.
        dbname: Nombre de la base de datos.
        user: Usuario de aplicación (no el superusuario 'postgres').
        password: Contraseña del usuario de aplicación.
    """

    host: str = "localhost"
    port: int = 5432
    dbname: str = "monitoreo_red"
    user: str = "monitoreo_app"
    password: str = ""

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "DatabaseConfig":
        """Construye la configuración a partir del entorno y del archivo .env."""
        _cargar_env(env_file or RAIZ_PROYECTO / ".env")
        return cls(
            host=os.getenv("MONITOREO_DB_HOST", cls.host),
            port=int(os.getenv("MONITOREO_DB_PORT", str(cls.port))),
            dbname=os.getenv("MONITOREO_DB_NAME", cls.dbname),
            user=os.getenv("MONITOREO_DB_USER", cls.user),
            password=os.getenv("MONITOREO_DB_PASSWORD", cls.password),
        )

    def conninfo_kwargs(self) -> dict:
        """Devuelve los parámetros en el formato que acepta psycopg.connect()."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "connect_timeout": 5,
            "application_name": "tt2027a183_monitoreo",
        }


def _cargar_env(ruta: Path) -> None:
    """Carga el archivo .env si existe y python-dotenv está disponible."""
    if not ruta.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ruta, override=False, encoding="utf-8")
