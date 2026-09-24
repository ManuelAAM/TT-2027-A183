"""Colector de rendimiento, throughput y ancho de banda de red mediante iPerf3.

Este módulo implementa la clase IPerfCollector y la función de alto nivel
execute_iperf para medir tasas de transferencia (Mbps), retransmisiones de paquetes,
jitter y pérdida en protocolos TCP y UDP, alineado con las metas del Trabajo Terminal.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

from src.monitoring.models import IPerfInterval, IPerfResult
from src.monitoring.utils import get_operating_system, run_command_safe, validate_target

logger = logging.getLogger(__name__)


def is_iperf_installed(custom_binary_path: Optional[str] = None) -> bool:
    """Verifica si el binario ejecutable de iPerf3 se encuentra disponible en el sistema.

    Args:
        custom_binary_path: Ruta opcional personalizada hacia el ejecutable de iperf3.

    Returns:
        bool: True si el ejecutable está disponible en PATH o ruta dada, False en caso contrario.
    """
    if custom_binary_path:
        return shutil.which(custom_binary_path) is not None
    return shutil.which("iperf3") is not None


class IPerfCollector:
    """Ejecutor y analizador de pruebas de rendimiento de red mediante iPerf3."""

    def __init__(
        self,
        server_host: str,
        server_port: int = 5201,
        duration_seconds: int = 5,
        protocol: str = "TCP",
        bandwidth_limit: Optional[str] = None,
        reverse: bool = False,
        custom_binary_path: Optional[str] = None,
    ) -> None:
        """Inicializa los parámetros de la prueba iPerf3.

        Args:
            server_host: Dirección IP o hostname del servidor iPerf3 activo.
            server_port: Puerto de escucha del servidor iPerf3 (por defecto 5201).
            duration_seconds: Duración de la prueba en segundos (por defecto 5s).
            protocol: 'TCP' (medición de throughput y retransmisiones) o 'UDP' (jitter y pérdida).
            bandwidth_limit: Límite de ancho de banda para UDP (ej. '10M', '50M', '1G').
            reverse: Si es True, realiza prueba en modo inverso (servidor transmite, cliente recibe).
            custom_binary_path: Ruta explícita al binario de iperf3 si no está en el PATH.
        """
        self.server_host = server_host.strip()
        self.server_port = max(1, min(65535, server_port))
        self.duration_seconds = max(1, min(3600, duration_seconds))
        self.protocol = protocol.upper() if protocol.upper() in ["TCP", "UDP"] else "TCP"
        self.bandwidth_limit = bandwidth_limit
        self.reverse = reverse
        self.custom_binary_path = custom_binary_path
        self.os_type = get_operating_system()

    def run(self) -> IPerfResult:
        """Ejecuta la prueba de rendimiento y retorna el objeto IPerfResult estructurado.

        Gestiona los escenarios en los que:
        - El binario iperf3 no está instalado en el sistema operativo.
        - El servidor de pruebas está apagado, inalcanzable o bloqueado por firewall.
        - El servidor está ocupado atendiendo otra prueba.
        - Se produce una interrupción o timeout durante la transferencia.

        Returns:
            IPerfResult: Resultado completo con métricas de ancho de banda y segundo a segundo.
        """
        start_time = time.perf_counter()

        # 1. Validación sintáctica del objetivo
        if not validate_target(self.server_host):
            return IPerfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                protocol=self.protocol,
                duration_seconds=float(self.duration_seconds),
                status="ERROR",
                error_message=f"El objetivo '{self.server_host}' no es una dirección IP o nombre de host válido.",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        # 2. Verificación de existencia del ejecutable iperf3
        binary_cmd = self.custom_binary_path if self.custom_binary_path else "iperf3"
        if not is_iperf_installed(binary_cmd):
            error_msg = (
                f"La utilidad 'iperf3' no está disponible en el PATH del sistema ({self.os_type}). "
                "Para ejecutar pruebas de rendimiento, instale iPerf3 según las instrucciones del README.md "
                "(Windows: descargar iperf3 o winget install BudMan.iPerf3; Linux: sudo apt install iperf3)."
            )
            logger.warning(error_msg)
            return IPerfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                protocol=self.protocol,
                duration_seconds=float(self.duration_seconds),
                status="TOOL_NOT_FOUND",
                error_message=error_msg,
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        cmd = self._build_command(binary_cmd)
        # Timeout del subproceso: duración de prueba + 10 segundos de margen de conexión y buffer
        proc_timeout = self.duration_seconds + 10.0

        try:
            returncode, stdout, stderr = run_command_safe(
                cmd=cmd, timeout_seconds=proc_timeout
            )
        except subprocess.TimeoutExpired:
            return IPerfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                protocol=self.protocol,
                duration_seconds=float(self.duration_seconds),
                status="TIMEOUT",
                error_message=f"La prueba de rendimiento excedió el tiempo máximo permitido ({proc_timeout}s).",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )
        except Exception as exc:
            return IPerfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                protocol=self.protocol,
                duration_seconds=float(self.duration_seconds),
                status="ERROR",
                error_message=f"Fallo durante la invocación de iperf3: {str(exc)}",
                execution_time_seconds=round(time.perf_counter() - start_time, 4),
            )

        duration = round(time.perf_counter() - start_time, 4)

        # 3. Parseo estructurado del JSON devuelto por iPerf3
        result = self._parse_iperf_json(stdout, stderr, returncode)
        result.execution_time_seconds = duration
        return result

    def _build_command(self, binary_cmd: str) -> List[str]:
        """Construye los argumentos para iPerf3 con bandera JSON (-J)."""
        args = [
            binary_cmd,
            "-c",
            self.server_host,
            "-p",
            str(self.server_port),
            "-t",
            str(self.duration_seconds),
            "-J",  # Salida directa y nativa en JSON
        ]

        if self.protocol == "UDP":
            args.append("-u")
            if self.bandwidth_limit:
                args.extend(["-b", self.bandwidth_limit])

        if self.reverse:
            args.append("-R")

        return args

    def _parse_iperf_json(self, stdout: str, stderr: str, returncode: int) -> IPerfResult:
        """Parsea la salida JSON nativa generada por iperf3."""
        # Si la salida está vacía o contiene mensajes de error de consola directos
        raw_output = stdout.strip()
        if not raw_output:
            err_msg = stderr.strip() if stderr.strip() else "El proceso iperf3 no generó ninguna salida."
            return self._build_error_result(err_msg)

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # En raras ocasiones iperf3 escribe errores antes del JSON
            json_match = re.search(r"(\{.*\})", raw_output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    return self._build_error_result(f"Salida de iperf3 corrupta o no parseable: {raw_output[:200]}")
            else:
                return self._build_error_result(f"Respuesta no válida de iperf3: {raw_output[:200]}")

        # 1. Verificar si iperf3 reportó un error a nivel de aplicación (ej. servidor caído)
        if "error" in data:
            error_desc = str(data["error"])
            status = "SERVER_UNREACHABLE"
            if "busy" in error_desc.lower():
                status = "SERVER_BUSY"
            return IPerfResult(
                server_host=self.server_host,
                server_port=self.server_port,
                protocol=self.protocol,
                duration_seconds=float(self.duration_seconds),
                is_success=False,
                status=status,
                error_message=f"Error reportado por iPerf3: {error_desc}",
            )

        # 2. Extraer intervalos segundo a segundo
        intervals: List[IPerfInterval] = []
        raw_intervals = data.get("intervals", [])
        for idx, item in enumerate(raw_intervals, start=1):
            sum_interval = item.get("sum", {})
            start_sec = float(sum_interval.get("start", 0.0))
            end_sec = float(sum_interval.get("end", 0.0))
            bytes_trans = int(sum_interval.get("bytes", 0))
            bps = float(sum_interval.get("bits_per_second", 0.0))
            mbps = round(bps / 1_000_000.0, 2)
            retrans = sum_interval.get("retransmits")
            jitter = sum_interval.get("jitter_ms")
            lost_pct = sum_interval.get("lost_percent")

            intervals.append(
                IPerfInterval(
                    interval_id=idx,
                    start_seconds=round(start_sec, 2),
                    end_seconds=round(end_sec, 2),
                    bytes_transferred=bytes_trans,
                    bits_per_second=round(bps, 2),
                    throughput_mbps=mbps,
                    retransmits=int(retrans) if retrans is not None else None,
                    jitter_ms=round(float(jitter), 3) if jitter is not None else None,
                    packet_loss_percentage=round(float(lost_pct), 2) if lost_pct is not None else None,
                )
            )

        # 3. Extraer métricas consolidadas del bloque 'end'
        end_data = data.get("end", {})
        sum_sent = end_data.get("sum_sent", {})
        sum_received = end_data.get("sum_received", {})

        bytes_sent = int(sum_sent.get("bytes", 0))
        bytes_received = int(sum_received.get("bytes", 0))

        sender_bps = float(sum_sent.get("bits_per_second", 0.0))
        sender_mbps = round(sender_bps / 1_000_000.0, 2)

        receiver_bps = float(sum_received.get("bits_per_second", 0.0))
        receiver_mbps = round(receiver_bps / 1_000_000.0, 2)

        retransmissions = sum_sent.get("retransmits")

        # Variables específicas de UDP o RTT TCP
        mean_rtt_ms: Optional[float] = None
        jitter_ms: Optional[float] = None
        lost_packets: Optional[int] = None
        total_packets: Optional[int] = None
        packet_loss_pct: Optional[float] = None

        if self.protocol == "UDP":
            sum_udp = end_data.get("sum", {})
            jitter_ms = round(float(sum_udp.get("jitter_ms", 0.0)), 3) if "jitter_ms" in sum_udp else None
            lost_packets = int(sum_udp.get("lost_packets", 0)) if "lost_packets" in sum_udp else None
            total_packets = int(sum_udp.get("packets", 0)) if "packets" in sum_udp else None
            packet_loss_pct = round(float(sum_udp.get("lost_percent", 0.0)), 2) if "lost_percent" in sum_udp else None
            # En UDP, si sum_sent no tiene datos de recepción, tomamos sum_udp
            if receiver_bps == 0.0 and "bits_per_second" in sum_udp:
                receiver_bps = float(sum_udp.get("bits_per_second", 0.0))
                receiver_mbps = round(receiver_bps / 1_000_000.0, 2)
        else:
            # En TCP, intentar extraer RTT medio si el sistema operativo lo expone en streams
            streams = end_data.get("streams", [])
            rtt_samples = []
            for stream in streams:
                sender_info = stream.get("sender", {})
                if "mean_rtt" in sender_info:
                    rtt_samples.append(float(sender_info["mean_rtt"]) / 1000.0)  # Convertir a ms si está en µs
            if rtt_samples:
                mean_rtt_ms = round(sum(rtt_samples) / len(rtt_samples), 2)

        return IPerfResult(
            server_host=self.server_host,
            server_port=self.server_port,
            protocol=self.protocol,
            duration_seconds=float(self.duration_seconds),
            bytes_sent=bytes_sent,
            bytes_received=bytes_received,
            sender_bitrate_bps=round(sender_bps, 2),
            sender_throughput_mbps=sender_mbps,
            receiver_bitrate_bps=round(receiver_bps, 2),
            receiver_throughput_mbps=receiver_mbps,
            retransmissions=int(retransmissions) if retransmissions is not None else None,
            mean_rtt_ms=mean_rtt_ms,
            jitter_ms=jitter_ms,
            lost_packets=lost_packets,
            total_packets=total_packets,
            packet_loss_percentage=packet_loss_pct,
            intervals=intervals,
            is_success=True,
            status="SUCCESS",
            error_message=None,
        )

    def _build_error_result(self, error_message: str) -> IPerfResult:
        """Construye un resultado de error estándar."""
        status = "ERROR"
        if "refused" in error_message.lower() or "unreachable" in error_message.lower() or "no route" in error_message.lower():
            status = "SERVER_UNREACHABLE"

        return IPerfResult(
            server_host=self.server_host,
            server_port=self.server_port,
            protocol=self.protocol,
            duration_seconds=float(self.duration_seconds),
            is_success=False,
            status=status,
            error_message=error_message,
        )


def execute_iperf(
    server_host: str,
    server_port: int = 5201,
    duration_seconds: int = 5,
    protocol: str = "TCP",
    bandwidth_limit: Optional[str] = None,
    reverse: bool = False,
    custom_binary_path: Optional[str] = None,
) -> IPerfResult:
    """Función de alto nivel para ejecutar una prueba de rendimiento de red mediante iPerf3.

    Args:
        server_host: IP o nombre de host del servidor iPerf3.
        server_port: Puerto de conexión (por defecto 5201).
        duration_seconds: Duración de la prueba en segundos (por defecto 5s).
        protocol: Protocolo de transporte ('TCP' o 'UDP').
        bandwidth_limit: Límite de ancho de banda para UDP (ej. '10M').
        reverse: Booleano para invertir el sentido de transmisión.
        custom_binary_path: Ruta personalizada al ejecutable iperf3 si no está en PATH.

    Returns:
        IPerfResult: Resultado estructurado con throughput, retransmisiones, etc.
    """
    collector = IPerfCollector(
        server_host=server_host,
        server_port=server_port,
        duration_seconds=duration_seconds,
        protocol=protocol,
        bandwidth_limit=bandwidth_limit,
        reverse=reverse,
        custom_binary_path=custom_binary_path,
    )
    return collector.run()
