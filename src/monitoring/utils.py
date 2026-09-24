"""Utilidades del sistema y ejecución segura de comandos de red.

Este módulo provee funciones auxiliares para detección del sistema operativo,
validación de direcciones y ejecución segura de utilidades externas mediante subprocess.
"""

from __future__ import annotations

import ipaddress
import logging
import platform
import re
import subprocess
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Expresión regular para validar nombres de host (RFC 1123)
_HOSTNAME_REGEX = re.compile(
    r"^([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
)


def get_operating_system() -> str:
    """Identifica el sistema operativo subyacente.

    Returns:
        str: 'windows', 'linux' o 'darwin' (macOS).
    """
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "linux" in system:
        return "linux"
    if "darwin" in system:
        return "darwin"
    return system


def validate_target(target: str) -> bool:
    """Valida si el objetivo es una dirección IP válida (v4/v6) o un nombre de host válido.

    Previene inyecciones de comandos y fallos por parámetros malformados.

    Args:
        target: Cadena con la dirección IP o nombre de host a validar.

    Returns:
        bool: True si el objetivo tiene una sintaxis válida, False en caso contrario.
    """
    if not target or not isinstance(target, str):
        return False

    cleaned_target = target.strip()
    if not cleaned_target or len(cleaned_target) > 253:
        return False

    # 1. Intentar validar como dirección IPv4 o IPv6
    try:
        ipaddress.ip_address(cleaned_target)
        return True
    except ValueError:
        # Si tiene formato similar a IPv4 (4 bloques solo de números) pero falló, es una IP inválida
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", cleaned_target):
            return False

    # 2. Intentar validar como nombre de dominio / hostname (RFC 1123)
    if _HOSTNAME_REGEX.match(cleaned_target):
        # Un TLD puramente numérico no es válido en Internet
        parts = cleaned_target.split(".")
        if parts[-1].isdigit():
            return False
        return True

    return False


def decode_process_output(raw_bytes: bytes) -> str:
    """Decodifica la salida en bytes de un subproceso probando encodings comunes.

    En Windows, la consola suele usar 'cp850', 'cp1252' o 'utf-8'.
    Esta función garantiza que ningún caracter acentuado o símbolo provoque excepciones.

    Args:
        raw_bytes: Bytes generados por stdout o stderr.

    Returns:
        str: Texto decodificado limpio.
    """
    if not raw_bytes:
        return ""

    encodings = ["utf-8", "cp850", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    # Fallback seguro reemplazando caracteres desconocidos
    return raw_bytes.decode("utf-8", errors="replace")


def run_command_safe(
    cmd: List[str], timeout_seconds: Optional[float] = None
) -> Tuple[int, str, str]:
    """Ejecuta un comando del sistema de forma segura mediante subprocess.

    Garantiza:
    1. Ejecución sin shell (shell=False) para prevenir inyecciones.
    2. Control estricto de timeout para evitar bloqueos del módulo.
    3. Captura y decodificación robusta de stdout y stderr.

    Args:
        cmd: Lista con el comando y sus argumentos, e.g. ['ping', '-n', '4', '1.1.1.1'].
        timeout_seconds: Tiempo límite de espera en segundos antes de abortar el proceso.

    Returns:
        Tuple[int, str, str]: (código de salida, stdout decodificado, stderr decodificado).

    Raises:
        subprocess.TimeoutExpired: Si el comando supera el tiempo asignado.
        FileNotFoundError: Si el ejecutable del comando no existe en el sistema.
        Exception: Ante otros errores de ejecución del sistema operativo.
    """
    logger.debug("Ejecutando comando: %s (Timeout: %ss)", " ".join(cmd), timeout_seconds)

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )

        stdout_decoded = decode_process_output(process.stdout)
        stderr_decoded = decode_process_output(process.stderr)
        return process.returncode, stdout_decoded, stderr_decoded

    except subprocess.TimeoutExpired as exc:
        logger.warning("Comando expiró por timeout (%ss): %s", timeout_seconds, " ".join(cmd))
        stdout_partial = decode_process_output(exc.stdout) if exc.stdout else ""
        stderr_partial = decode_process_output(exc.stderr) if exc.stderr else ""
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=timeout_seconds or 0.0,
            output=stdout_partial,
            stderr=stderr_partial,
        )
    except FileNotFoundError:
        logger.error("Ejecutable no encontrado en PATH: %s", cmd[0])
        raise
    except Exception as exc:
        logger.error("Error inesperado ejecutando comando %s: %s", cmd[0], str(exc))
        raise
