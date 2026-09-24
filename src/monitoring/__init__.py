"""Módulo de Monitoreo de Red para TT-2027-A183.

Exporta las clases y funciones principales para la recolección estructurada de
métricas de calidad de red (Ping ICMP, Traceroute e iPerf3), así como el motor
unificado de diagnóstico y recomendaciones iniciales.
"""

from src.monitoring.diagnostics import NetworkDiagnosticsEngine, run_full_diagnostics
from src.monitoring.iperf_collector import (
    IPerfCollector,
    execute_iperf,
    is_iperf_installed,
)
from src.monitoring.models import (
    IPerfInterval,
    IPerfResult,
    NetworkHealthReport,
    PingResult,
    TracerouteHop,
    TracerouteResult,
)
from src.monitoring.ping_collector import PingCollector, execute_ping
from src.monitoring.traceroute_collector import (
    TracerouteCollector,
    execute_traceroute,
)

__all__ = [
    # Modelos DTO
    "PingResult",
    "TracerouteHop",
    "TracerouteResult",
    "IPerfInterval",
    "IPerfResult",
    "NetworkHealthReport",
    # Colectores
    "PingCollector",
    "execute_ping",
    "TracerouteCollector",
    "execute_traceroute",
    "IPerfCollector",
    "execute_iperf",
    "is_iperf_installed",
    # Motor de Diagnóstico y Recomendaciones
    "NetworkDiagnosticsEngine",
    "run_full_diagnostics",
]
