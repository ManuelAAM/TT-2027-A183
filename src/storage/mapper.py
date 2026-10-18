"""Conversión de los DTOs del Módulo de Monitoreo a filas de la base de datos.

Las funciones de este módulo son puras (no abren conexiones ni dependen de
psycopg), por lo que pueden probarse de forma unitaria. El repositorio las usa
para repartir un NetworkHealthReport entre las tablas pruebas_conectividad,
metricas, diagnosticos y recomendaciones.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.monitoring.diagnostics import (
    LATENCIA_ELEVADA_MS,
    PERDIDA_UDP_MAXIMA_PCT,
    RETRANSMISIONES_CONGESTION,
)
from src.monitoring.models import (
    IPerfResult,
    NetworkHealthReport,
    PingResult,
    TracerouteResult,
)

# Longitud de la columna pruebas_conectividad.estado.
_LONGITUD_ESTADO = 20

_PRIORIDAD_POR_SEVERIDAD = {
    "CRITICA": "ALTA",
    "ALTA": "ALTA",
    "MEDIA": "MEDIA",
    "BAJA": "BAJA",
    "INFO": "BAJA",
}


@dataclass
class MetricaFila:
    """Fila de la tabla metricas. Las columnas que no aplican quedan en None."""

    latencia_ms: Optional[float] = None
    latencia_min_ms: Optional[float] = None
    latencia_max_ms: Optional[float] = None
    perdida_paquetes_pct: Optional[float] = None
    jitter_ms: Optional[float] = None
    ancho_banda_mbps: Optional[float] = None
    retransmisiones: Optional[int] = None
    saltos: Optional[int] = None
    detalle: Optional[Dict[str, Any]] = None


@dataclass
class PruebaFila:
    """Fila de la tabla pruebas_conectividad junto con su métrica asociada."""

    tipo_prueba: str
    host_destino: str
    ip_destino: Optional[str]
    fecha_hora: datetime
    estado: str
    duracion_segundos: Optional[float]
    mensaje_error: Optional[str]
    metrica: MetricaFila = field(default_factory=MetricaFila)


@dataclass
class DiagnosticoFila:
    """Fila de la tabla diagnosticos con sus recomendaciones.

    Attributes:
        tipo_prueba_origen: Tipo de prueba cuya métrica originó la anomalía
            (se usa para enlazar id_metrica); None si no aplica.
        recomendaciones: Lista de tuplas (accion_sugerida, prioridad) en orden.
    """

    estado_global: str
    tipo_anomalia: str
    severidad: str
    descripcion: Optional[str]
    fecha_deteccion: datetime
    tipo_prueba_origen: Optional[str]
    recomendaciones: List[tuple] = field(default_factory=list)


def parse_timestamp(valor: Optional[str]) -> datetime:
    """Convierte una marca ISO 8601 de los colectores a datetime con zona horaria."""
    if valor:
        try:
            fecha = datetime.fromisoformat(valor)
            return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def ip_o_none(valor: Optional[str]) -> Optional[str]:
    """Devuelve la IP normalizada si el valor es una dirección válida; si no, None."""
    if not valor:
        return None
    try:
        return str(ipaddress.ip_address(valor.strip()))
    except ValueError:
        return None


def prueba_desde_ping(ping: PingResult) -> PruebaFila:
    """Mapea un PingResult a su fila de prueba y métrica."""
    medido = ping.status != "ERROR"
    return PruebaFila(
        tipo_prueba="PING",
        host_destino=ping.target,
        ip_destino=ip_o_none(ping.destination_ip) or ip_o_none(ping.target),
        fecha_hora=parse_timestamp(ping.timestamp),
        estado=ping.status[:_LONGITUD_ESTADO],
        duracion_segundos=ping.execution_time_seconds,
        mensaje_error=ping.error_message,
        metrica=MetricaFila(
            latencia_ms=ping.avg_rtt_ms,
            latencia_min_ms=ping.min_rtt_ms,
            latencia_max_ms=ping.max_rtt_ms,
            perdida_paquetes_pct=ping.packet_loss_percentage if medido else None,
            jitter_ms=ping.jitter_ms,
            detalle=ping.to_dict(),
        ),
    )


def prueba_desde_traceroute(trace: TracerouteResult) -> PruebaFila:
    """Mapea un TracerouteResult; la latencia es la del último salto si se alcanzó el destino."""
    latencia = None
    if trace.reached_destination and trace.hops:
        latencia = trace.hops[-1].avg_rtt_ms
    return PruebaFila(
        tipo_prueba="TRACEROUTE",
        host_destino=trace.target,
        ip_destino=ip_o_none(trace.destination_ip) or ip_o_none(trace.target),
        fecha_hora=parse_timestamp(trace.timestamp),
        estado=trace.status[:_LONGITUD_ESTADO],
        duracion_segundos=trace.execution_time_seconds,
        mensaje_error=trace.error_message,
        metrica=MetricaFila(
            latencia_ms=latencia,
            saltos=trace.total_hops,
            detalle=trace.to_dict(),
        ),
    )


def prueba_desde_iperf(iperf: IPerfResult) -> PruebaFila:
    """Mapea un IPerfResult; si la prueba falló solo se conserva el detalle."""
    metrica = MetricaFila(detalle=iperf.to_dict())
    if iperf.is_success:
        metrica.ancho_banda_mbps = (
            iperf.receiver_throughput_mbps or iperf.sender_throughput_mbps
        )
        metrica.retransmisiones = iperf.retransmissions
        metrica.latencia_ms = iperf.mean_rtt_ms
        metrica.jitter_ms = iperf.jitter_ms
        metrica.perdida_paquetes_pct = iperf.packet_loss_percentage
    return PruebaFila(
        tipo_prueba=f"IPERF_{iperf.protocol.upper()}",
        host_destino=iperf.server_host,
        ip_destino=ip_o_none(iperf.server_host),
        fecha_hora=parse_timestamp(iperf.timestamp),
        estado=iperf.status[:_LONGITUD_ESTADO],
        duracion_segundos=iperf.execution_time_seconds,
        mensaje_error=iperf.error_message,
        metrica=metrica,
    )


def pruebas_desde_reporte(reporte: NetworkHealthReport) -> List[PruebaFila]:
    """Devuelve una PruebaFila por cada prueba incluida en el reporte."""
    filas: List[PruebaFila] = []
    if reporte.ping:
        filas.append(prueba_desde_ping(reporte.ping))
    if reporte.traceroute:
        filas.append(prueba_desde_traceroute(reporte.traceroute))
    if reporte.iperf:
        filas.append(prueba_desde_iperf(reporte.iperf))
    return filas


def clasificar_diagnostico(reporte: NetworkHealthReport) -> tuple:
    """Determina (tipo_anomalia, severidad, tipo_prueba_origen) del reporte.

    Sigue el mismo orden de reglas que NetworkDiagnosticsEngine para que la
    anomalía registrada corresponda a la que generó las recomendaciones.
    """
    ping = reporte.ping
    iperf = reporte.iperf
    tipo_iperf = f"IPERF_{iperf.protocol.upper()}" if iperf else None
    estado = reporte.overall_status

    if estado == "UNREACHABLE":
        return "SIN_CONECTIVIDAD", "CRITICA", "PING"

    if estado == "DEGRADED":
        if ping and 0 < ping.packet_loss_percentage < 100:
            return "PERDIDA_PAQUETES", "ALTA", "PING"
        if ping and ping.avg_rtt_ms and ping.avg_rtt_ms > LATENCIA_ELEVADA_MS:
            return "LATENCIA_ELEVADA", "MEDIA", "PING"
        if iperf and iperf.is_success:
            if (iperf.retransmissions or 0) > RETRANSMISIONES_CONGESTION:
                return "CONGESTION_TCP", "MEDIA", tipo_iperf
            if (iperf.packet_loss_percentage or 0) > PERDIDA_UDP_MAXIMA_PCT:
                return "PERDIDA_UDP", "MEDIA", tipo_iperf
        return "DEGRADACION", "MEDIA", None

    if estado == "OPTIMAL":
        return "NINGUNA", "INFO", "PING" if ping else None

    return "SIN_DATOS", "INFO", None


def diagnostico_desde_reporte(reporte: NetworkHealthReport) -> DiagnosticoFila:
    """Construye la fila de diagnóstico y sus recomendaciones a partir del reporte."""
    tipo_anomalia, severidad, origen = clasificar_diagnostico(reporte)
    prioridad = _PRIORIDAD_POR_SEVERIDAD[severidad]
    recomendaciones = reporte.initial_recommendations
    return DiagnosticoFila(
        estado_global=reporte.overall_status,
        tipo_anomalia=tipo_anomalia,
        severidad=severidad,
        # El motor coloca el hallazgo principal como primera recomendación.
        descripcion=recomendaciones[0] if recomendaciones else None,
        fecha_deteccion=parse_timestamp(reporte.timestamp),
        tipo_prueba_origen=origen,
        recomendaciones=[(texto, prioridad) for texto in recomendaciones],
    )
