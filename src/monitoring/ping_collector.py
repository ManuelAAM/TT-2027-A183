"""Colector de métricas de conectividad y latencia mediante ICMP (Ping).

Este módulo proporciona la clase PingCollector y la función de alto nivel
execute_ping para medir latencia mínima, media, máxima, pérdida de paquetes y
disponibilidad de nodos tanto en sistemas Windows como Linux/UNIX.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from typing import Optional

from src.monitoring.models import PingResult
from src.monitoring.utils import get_operating_system, run_command_safe, validate_target

logger = logging.getLogger(__name__)


class PingCollector:
    """Ejecutor y analizador de pruebas de conectividad ICMP multiplataforma."""

    def __init__(self, target: str, count: int = 4, timeout_seconds: int = 2) -> None:
        """Inicializa los parámetros de la prueba ping.

        Args:
            target: Dirección IP o nombre de host a evaluar.
            count: Número de paquetes ICMP Echo Request a enviar (por defecto 4).
            timeout_seconds: Tiempo límite de espera por paquete en segundos (por defecto 2).
        """
        self.target = target.strip()
        self.count = max(1, count)
        self.timeout_seconds = max(1, timeout_seconds)
        self.os_type = get_operating_system()

    def run(self) -> PingResult:
        """Ejecuta la prueba de ping y retorna un objeto PingResult estructurado.

        Captura excepciones de red, timeouts y errores del sistema para asegurar
        que el flujo del sistema nunca colapse.

        Returns:
            PingResult: Objeto con todas las métricas procesadas.
        """
        start_time = time.perf_counter()

        # 1. Validación previa del objetivo
        if not validate_target(self.target):
            return PingResult(
                target=self.target,
                status="ERROR",
                error_message=f"El objetivo '{self.target}' no es una IP o nombre de host válido.",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        cmd = self._build_command()

        # El tiempo total máximo para el subproceso considera el número de paquetes más un margen
        total_proc_timeout = (self.count * self.timeout_seconds) + 5.0

        try:
            returncode, stdout, stderr = run_command_safe(
                cmd=cmd, timeout_seconds=total_proc_timeout
            )
        except subprocess.TimeoutExpired:
            return PingResult(
                target=self.target,
                packets_transmitted=self.count,
                packets_received=0,
                packets_lost=self.count,
                packet_loss_percentage=100.0,
                is_reachable=False,
                status="TIMEOUT",
                error_message="La prueba excedió el tiempo máximo de espera sin responder.",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )
        except FileNotFoundError:
            return PingResult(
                target=self.target,
                status="ERROR",
                error_message=f"La utilidad 'ping' no está disponible en el PATH del sistema ({self.os_type}).",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )
        except Exception as exc:
            return PingResult(
                target=self.target,
                status="ERROR",
                error_message=f"Error inesperado al ejecutar ping: {str(exc)}",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        execution_duration = round(time.perf_counter() - start_time, 4)

        # 2. Parseo de la salida según el sistema operativo
        result = self._parse_output(stdout, stderr, returncode)
        result.execution_time_seconds = execution_duration
        return result

    def _build_command(self) -> list[str]:
        """Construye los argumentos del comando según el sistema operativo."""
        if self.os_type == "windows":
            # -n count, -w timeout_in_milliseconds
            timeout_ms = self.timeout_seconds * 1000
            return ["ping", "-n", str(self.count), "-w", str(timeout_ms), self.target]
        else:
            # Linux / macOS: -c count, -W timeout_in_seconds
            return ["ping", "-c", str(self.count), "-W", str(self.timeout_seconds), self.target]

    def _parse_output(self, stdout: str, stderr: str, returncode: int) -> PingResult:
        """Determina el método de parseo correspondiente."""
        raw_combined = f"{stdout}\n{stderr}"

        # Detección temprana de fallo en resolución DNS
        if (
            "no pudo encontrar el host" in raw_combined
            or "could not find host" in raw_combined
            or "Name or service not known" in raw_combined
            or "Unknown host" in raw_combined
        ):
            return PingResult(
                target=self.target,
                packets_transmitted=self.count,
                packets_received=0,
                packets_lost=self.count,
                packet_loss_percentage=100.0,
                is_reachable=False,
                status="ERROR",
                error_message=f"No se pudo resolver el nombre de host '{self.target}'.",
            )

        if self.os_type == "windows":
            return self._parse_windows_output(stdout, returncode)
        return self._parse_linux_output(stdout, returncode)

    def _parse_windows_output(self, output: str, returncode: int) -> PingResult:
        """Parsea la salida de ping en sistemas Windows (admite idiomas Español e Inglés)."""
        destination_ip: Optional[str] = None
        packets_transmitted = self.count
        packets_received = 0
        packets_lost = self.count
        loss_percentage = 100.0
        min_rtt: Optional[float] = None
        avg_rtt: Optional[float] = None
        max_rtt: Optional[float] = None

        # 1. Extraer dirección IP resuelta si aplica (ej. Haciendo ping a google.com [142.250.190.46])
        ip_match = re.search(r"\[([0-9a-fA-F:\.]+)\]", output)
        if ip_match:
            destination_ip = ip_match.group(1)
        elif validate_target(self.target) and re.match(r"^[0-9\.]+$", self.target):
            destination_ip = self.target

        # 2. Extraer paquetes (Español e Inglés)
        # Español: Paquetes: enviados = 4, recibidos = 4, perdidos = 0
        # Inglés:  Packets: Sent = 4, Received = 4, Lost = 0
        pkt_match = re.search(
            r"(?:enviados|sent)\s*=\s*(\d+),\s*(?:recibidos|received)\s*=\s*(\d+),\s*(?:perdidos|lost)\s*=\s*(\d+)",
            output,
            re.IGNORECASE,
        )
        if pkt_match:
            packets_transmitted = int(pkt_match.group(1))
            packets_received = int(pkt_match.group(2))
            packets_lost = int(pkt_match.group(3))
            if packets_transmitted > 0:
                loss_percentage = round((packets_lost / packets_transmitted) * 100.0, 2)

        # 3. Extraer tiempos RTT (Español e Inglés)
        # Español: Mínimo = 8ms, Máximo = 9ms, Media = 8ms (o tolerando acentos perdidos)
        # Inglés:  Minimum = 8ms, Maximum = 9ms, Average = 8ms
        rtt_match = re.search(
            r"(?:M.*?nimo|Minimum)\s*=\s*(\d+)ms,\s*(?:M.*?ximo|Maximum)\s*=\s*(\d+)ms,\s*(?:Media|Average)\s*=\s*(\d+)ms",
            output,
            re.IGNORECASE,
        )
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            max_rtt = float(rtt_match.group(2))
            avg_rtt = float(rtt_match.group(3))

        # Determinar estado
        is_reachable = packets_received > 0
        if not is_reachable:
            status = "UNREACHABLE"
            error_msg = "El host objetivo no respondió a las solicitudes ICMP Echo."
        elif loss_percentage > 0:
            status = "PARTIAL_LOSS"
            error_msg = f"Se detectó un {loss_percentage}% de pérdida de paquetes."
        else:
            status = "SUCCESS"
            error_msg = None

        return PingResult(
            target=self.target,
            destination_ip=destination_ip,
            packets_transmitted=packets_transmitted,
            packets_received=packets_received,
            packets_lost=packets_lost,
            packet_loss_percentage=loss_percentage,
            min_rtt_ms=min_rtt,
            avg_rtt_ms=avg_rtt,
            max_rtt_ms=max_rtt,
            jitter_ms=round(max_rtt - min_rtt, 2) if (max_rtt is not None and min_rtt is not None) else None,
            is_reachable=is_reachable,
            status=status,
            error_message=error_msg,
        )

    def _parse_linux_output(self, output: str, returncode: int) -> PingResult:
        """Parsea la salida de ping en sistemas Linux / UNIX."""
        destination_ip: Optional[str] = None
        packets_transmitted = self.count
        packets_received = 0
        packets_lost = self.count
        loss_percentage = 100.0
        min_rtt: Optional[float] = None
        avg_rtt: Optional[float] = None
        max_rtt: Optional[float] = None
        mdev_rtt: Optional[float] = None

        # 1. Extraer dirección IP resuelta: PING host (1.2.3.4)
        ip_match = re.search(r"\(([0-9a-fA-F:\.]+)\)", output)
        if ip_match:
            destination_ip = ip_match.group(1)
        elif validate_target(self.target) and re.match(r"^[0-9\.]+$", self.target):
            destination_ip = self.target

        # 2. Extraer estadísticas de paquetes:
        # "4 packets transmitted, 4 received, 0% packet loss"
        pkt_match = re.search(
            r"(\d+)\s+packets transmitted,\s+(\d+)\s+(?:received|packets received),\s+(?:([0-9\.]+)%\s+packet loss)",
            output,
        )
        if pkt_match:
            packets_transmitted = int(pkt_match.group(1))
            packets_received = int(pkt_match.group(2))
            packets_lost = packets_transmitted - packets_received
            loss_percentage = float(pkt_match.group(3))

        # 3. Extraer RTT:
        # rtt min/avg/max/mdev = 12.345/14.567/16.789/1.234 ms
        rtt_match = re.search(
            r"(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*([0-9\.]+)/([0-9\.]+)/([0-9\.]+)/([0-9\.]+)",
            output,
        )
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            avg_rtt = float(rtt_match.group(2))
            max_rtt = float(rtt_match.group(3))
            mdev_rtt = float(rtt_match.group(4))

        is_reachable = packets_received > 0
        if not is_reachable:
            status = "UNREACHABLE"
            error_msg = "El host objetivo no respondió a las solicitudes ICMP Echo."
        elif loss_percentage > 0:
            status = "PARTIAL_LOSS"
            error_msg = f"Se detectó un {loss_percentage}% de pérdida de paquetes."
        else:
            status = "SUCCESS"
            error_msg = None

        return PingResult(
            target=self.target,
            destination_ip=destination_ip,
            packets_transmitted=packets_transmitted,
            packets_received=packets_received,
            packets_lost=packets_lost,
            packet_loss_percentage=loss_percentage,
            min_rtt_ms=min_rtt,
            avg_rtt_ms=avg_rtt,
            max_rtt_ms=max_rtt,
            jitter_ms=mdev_rtt,
            is_reachable=is_reachable,
            status=status,
            error_message=error_msg,
        )


def execute_ping(target: str, count: int = 4, timeout_seconds: int = 2) -> PingResult:
    """Función de alto nivel para ejecutar una prueba de ping a un objetivo.

    Args:
        target: IP o nombre de dominio del objetivo.
        count: Cantidad de paquetes ICMP a enviar.
        timeout_seconds: Tiempo máximo de espera en segundos por paquete.

    Returns:
        PingResult: Resultado estructurado de la prueba.
    """
    collector = PingCollector(target=target, count=count, timeout_seconds=timeout_seconds)
    return collector.run()
