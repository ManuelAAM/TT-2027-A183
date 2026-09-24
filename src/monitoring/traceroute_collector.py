"""Colector de topología y saltos de red mediante Traceroute.

Este módulo implementa la clase TracerouteCollector y la función de alto nivel
execute_traceroute para mapear la ruta de paquetes hacia un destino, identificando
nodos intermedios, cuellos de botella de latencia y posibles puntos de desconexión.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from typing import List, Optional, Tuple

from src.monitoring.models import TracerouteHop, TracerouteResult
from src.monitoring.utils import get_operating_system, run_command_safe, validate_target

logger = logging.getLogger(__name__)


class TracerouteCollector:
    """Ejecutor y analizador de pruebas traceroute multiplataforma."""

    def __init__(
        self,
        target: str,
        max_hops: int = 30,
        timeout_per_hop_ms: int = 1000,
        resolve_dns: bool = False,
    ) -> None:
        """Inicializa los parámetros de la prueba de traceroute.

        Args:
            target: Dirección IP o nombre de host destino.
            max_hops: Límite máximo de saltos (TTL máximo) a explorar.
            timeout_per_hop_ms: Tiempo de espera en milisegundos por sondeo.
            resolve_dns: Si es False, desactiva la resolución inversa de nombres para
                         acelerar significativamente la prueba (recomendado en LAN).
        """
        self.target = target.strip()
        self.max_hops = min(max(1, max_hops), 64)
        self.timeout_per_hop_ms = max(200, timeout_per_hop_ms)
        self.resolve_dns = resolve_dns
        self.os_type = get_operating_system()

    def run(self) -> TracerouteResult:
        """Ejecuta la traza hacia el objetivo y estructura los saltos intermedios.

        Returns:
            TracerouteResult: Estructura de datos con la lista de saltos, tiempos y estado.
        """
        start_time = time.perf_counter()

        # 1. Validación del objetivo
        if not validate_target(self.target):
            return TracerouteResult(
                target=self.target,
                status="ERROR",
                error_message=f"El objetivo '{self.target}' no es una dirección IP o nombre de host válido.",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        cmd = self._build_command()

        # Cálculo de timeout del proceso global (hops * probes_per_hop * timeout + margen)
        total_timeout_sec = (self.max_hops * 3 * (self.timeout_per_hop_ms / 1000.0)) + 15.0

        try:
            returncode, stdout, stderr = run_command_safe(
                cmd=cmd, timeout_seconds=total_timeout_sec
            )
        except subprocess.TimeoutExpired:
            return TracerouteResult(
                target=self.target,
                status="TIMEOUT",
                error_message=f"La prueba de traceroute superó el tiempo máximo asignado ({total_timeout_sec:.1f}s).",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )
        except FileNotFoundError:
            utility_name = "tracert" if self.os_type == "windows" else "traceroute"
            return TracerouteResult(
                target=self.target,
                status="ERROR",
                error_message=f"La utilidad '{utility_name}' no se encuentra instalada o disponible en el PATH.",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )
        except Exception as exc:
            return TracerouteResult(
                target=self.target,
                status="ERROR",
                error_message=f"Error inesperado al ejecutar traceroute: {str(exc)}",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        duration = round(time.perf_counter() - start_time, 4)

        # 2. Parseo de la salida
        result = self._parse_output(stdout, stderr, returncode)
        result.execution_time_seconds = duration
        return result

    def _build_command(self) -> list[str]:
        """Construye los argumentos para tracert (Windows) o traceroute (Linux)."""
        if self.os_type == "windows":
            # tracert [-d] [-h maximum_hops] [-w timeout] target
            args = ["tracert"]
            if not self.resolve_dns:
                args.append("-d")
            args.extend(["-h", str(self.max_hops)])
            args.extend(["-w", str(self.timeout_per_hop_ms)])
            args.append(self.target)
            return args
        else:
            # traceroute [-n] [-m max_ttl] [-w waittime] target
            args = ["traceroute"]
            if not self.resolve_dns:
                args.append("-n")
            args.extend(["-m", str(self.max_hops)])
            # Linux traceroute -w espera segundos (admite flotantes según versión)
            wait_sec = max(1, int(self.timeout_per_hop_ms / 1000))
            args.extend(["-w", str(wait_sec)])
            args.append(self.target)
            return args

    def _parse_output(self, stdout: str, stderr: str, returncode: int) -> TracerouteResult:
        """Determina el analizador de traza según el sistema operativo."""
        raw_combined = f"{stdout}\n{stderr}"

        # Detección temprana de fallo en resolución de nombre
        if (
            "no pudo encontrar el host" in raw_combined
            or "could not find host" in raw_combined
            or "Cannot handle \"host\" cmdline arg" in raw_combined
            or "Name or service not known" in raw_combined
        ):
            return TracerouteResult(
                target=self.target,
                status="ERROR",
                error_message=f"No fue posible resolver la dirección del host '{self.target}'.",
            )

        if self.os_type == "windows":
            return self._parse_windows_tracert(stdout)
        return self._parse_linux_traceroute(stdout)

    def _parse_windows_tracert(self, output: str) -> TracerouteResult:
        """Parsea la salida del comando tracert de Windows."""
        destination_ip: Optional[str] = None
        hops: List[TracerouteHop] = []

        # Intentar extraer la IP de destino de la cabecera (ej. Traza a 1.1.1.1 sobre...)
        header_ip = re.search(r"(?:Traza a|Tracing route to)\s+(?:[^\s]+)\s*(?:\[([0-9a-fA-F:\.]+)\])?", output)
        if header_ip and header_ip.group(1):
            destination_ip = header_ip.group(1)
        elif validate_target(self.target) and re.match(r"^[0-9\.]+$", self.target):
            destination_ip = self.target

        lines = output.splitlines()
        reached_destination = False

        for line in lines:
            line_clean = line.strip()
            # Un salto de tracert inicia con un número entero seguido de espacios
            match_hop = re.match(r"^(\d+)\s+(.+)$", line_clean)
            if not match_hop:
                continue

            hop_number = int(match_hop.group(1))
            hop_content = match_hop.group(2)

            # Extraer tokens de tiempo (ej. '<1 ms', '15 ms', '*')
            time_tokens = re.findall(r"(?:<\s*\d+\s*ms|\d+\s*ms|\*)", hop_content)

            rtt_values: List[Optional[float]] = []
            for token in time_tokens:
                token_clean = token.replace(" ", "")
                if "*" in token_clean:
                    rtt_values.append(None)
                elif "<" in token_clean:
                    rtt_values.append(0.5)  # Latencia menor a 1ms se normaliza a 0.5ms
                else:
                    num_match = re.search(r"(\d+)", token_clean)
                    if num_match:
                        rtt_values.append(float(num_match.group(1)))

            # Extraer IP y Hostname (si existen al final de la línea)
            ip_address, hostname = self._extract_node_identity(hop_content)

            # Calcular métricas del salto
            valid_rtts = [r for r in rtt_values if r is not None]
            total_probes = len(rtt_values) if rtt_values else 3
            lost_probes = total_probes - len(valid_rtts)
            hop_loss_pct = round((lost_probes / total_probes) * 100.0, 2) if total_probes > 0 else 100.0
            avg_rtt = round(sum(valid_rtts) / len(valid_rtts), 2) if valid_rtts else None

            hop = TracerouteHop(
                hop_number=hop_number,
                ip_address=ip_address,
                hostname=hostname,
                rtt_ms=rtt_values,
                packet_loss_percentage=hop_loss_pct,
                avg_rtt_ms=avg_rtt,
            )
            hops.append(hop)

            # Comprobar si alcanzamos el destino
            if ip_address and destination_ip and ip_address == destination_ip:
                reached_destination = True
            elif ip_address and ip_address == self.target:
                reached_destination = True

        status = "SUCCESS" if reached_destination else ("TIMEOUT" if not hops else "MAX_HOPS_EXCEEDED")

        return TracerouteResult(
            target=self.target,
            destination_ip=destination_ip,
            total_hops=len(hops),
            hops=hops,
            reached_destination=reached_destination,
            status=status,
            error_message=None if reached_destination else "No se alcanzó el nodo final dentro del límite de saltos.",
        )

    def _parse_linux_traceroute(self, output: str) -> TracerouteResult:
        """Parsea la salida de la utilidad traceroute en Linux/UNIX."""
        destination_ip: Optional[str] = None
        hops: List[TracerouteHop] = []

        # Extraer IP de la cabecera: traceroute to host (1.2.3.4), ...
        header_ip = re.search(r"traceroute to \S+\s+\(([0-9a-fA-F:\.]+)\)", output)
        if header_ip:
            destination_ip = header_ip.group(1)
        elif validate_target(self.target) and re.match(r"^[0-9\.]+$", self.target):
            destination_ip = self.target

        lines = output.splitlines()
        reached_destination = False

        for line in lines:
            line_clean = line.strip()
            match_hop = re.match(r"^(\d+)\s+(.+)$", line_clean)
            if not match_hop:
                continue

            hop_number = int(match_hop.group(1))
            hop_content = match_hop.group(2)

            # Extraer tiempos tipo: '12.345 ms' o '*'
            time_tokens = re.findall(r"(?:[0-9.]+\s*ms|\*)", hop_content)
            rtt_values: List[Optional[float]] = []
            for token in time_tokens:
                if "*" in token:
                    rtt_values.append(None)
                else:
                    num_match = re.search(r"([0-9.]+)", token)
                    if num_match:
                        rtt_values.append(float(num_match.group(1)))

            ip_address, hostname = self._extract_node_identity(hop_content)

            valid_rtts = [r for r in rtt_values if r is not None]
            total_probes = len(rtt_values) if rtt_values else 3
            lost_probes = total_probes - len(valid_rtts)
            hop_loss_pct = round((lost_probes / total_probes) * 100.0, 2) if total_probes > 0 else 100.0
            avg_rtt = round(sum(valid_rtts) / len(valid_rtts), 2) if valid_rtts else None

            hop = TracerouteHop(
                hop_number=hop_number,
                ip_address=ip_address,
                hostname=hostname,
                rtt_ms=rtt_values,
                packet_loss_percentage=hop_loss_pct,
                avg_rtt_ms=avg_rtt,
            )
            hops.append(hop)

            if ip_address and destination_ip and ip_address == destination_ip:
                reached_destination = True
            elif ip_address and ip_address == self.target:
                reached_destination = True

        status = "SUCCESS" if reached_destination else ("TIMEOUT" if not hops else "MAX_HOPS_EXCEEDED")

        return TracerouteResult(
            target=self.target,
            destination_ip=destination_ip,
            total_hops=len(hops),
            hops=hops,
            reached_destination=reached_destination,
            status=status,
            error_message=None if reached_destination else "No se alcanzó el nodo final dentro del límite de saltos.",
        )

    def _extract_node_identity(self, line_content: str) -> Tuple[Optional[str], Optional[str]]:
        """Extrae la dirección IP y el nombre de host (si existe) de una línea de salto."""
        # Caso 1: Con hostname e IP entre corchetes o paréntesis (ej. router.lan [192.168.1.1])
        match_with_host = re.search(r"([a-zA-Z0-9\.\-_]+)\s+[\[\(]([0-9a-fA-F:\.]+)[\]\)]", line_content)
        if match_with_host:
            hostname = match_with_host.group(1)
            ip = match_with_host.group(2)
            return ip, hostname

        # Caso 2: Solo IP explícita al final de la línea o tras los tiempos
        ip_candidates = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line_content)
        if ip_candidates:
            return ip_candidates[-1], None

        return None, None


def execute_traceroute(
    target: str,
    max_hops: int = 30,
    timeout_per_hop_ms: int = 1000,
    resolve_dns: bool = False,
) -> TracerouteResult:
    """Función de alto nivel para ejecutar un traceroute a un objetivo.

    Args:
        target: IP o dominio a trazar.
        max_hops: Cantidad máxima de saltos (por defecto 30).
        timeout_per_hop_ms: Milisegundos de espera por sondeo (por defecto 1000).
        resolve_dns: Booleano que define si se resuelven nombres de dominio.

    Returns:
        TracerouteResult: Estructura con la traza analizada.
    """
    collector = TracerouteCollector(
        target=target,
        max_hops=max_hops,
        timeout_per_hop_ms=timeout_per_hop_ms,
        resolve_dns=resolve_dns,
    )
    return collector.run()
