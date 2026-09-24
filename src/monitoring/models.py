"""Modelos de datos para el Módulo de Monitoreo de Red.

Este módulo define las estructuras de datos (Data Transfer Objects) que
estandarizan los resultados de las pruebas de conectividad (ping y traceroute),
permitiendo su posterior serialización a JSON, almacenamiento en base de datos
o transmisión a servicios backend.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PingResult:
    """Representa el resultado estructurado de una prueba de conectividad ICMP (Ping).

    Attributes:
        target: Host o dirección IP objetivo original.
        destination_ip: Dirección IP resuelta del objetivo (si está disponible).
        packets_transmitted: Total de paquetes ICMP Echo Request enviados.
        packets_received: Total de paquetes ICMP Echo Reply recibidos.
        packets_lost: Cantidad de paquetes perdidos.
        packet_loss_percentage: Porcentaje de paquetes perdidos (0.0 a 100.0).
        min_rtt_ms: Tiempo mínimo de ida y vuelta (RTT) en milisegundos.
        avg_rtt_ms: Tiempo promedio de ida y vuelta (RTT) en milisegundos.
        max_rtt_ms: Tiempo máximo de ida y vuelta (RTT) en milisegundos.
        jitter_ms: Variación estimada de latencia (mdev/jitter) en milisegundos.
        is_reachable: Indica si el objetivo respondió al menos a un paquete.
        status: Estado de la prueba ('SUCCESS', 'PARTIAL_LOSS', 'UNREACHABLE', 'ERROR').
        execution_time_seconds: Duración total de la prueba en segundos.
        error_message: Mensaje explicativo en caso de fallo o excepción.
        timestamp: Marca de tiempo en formato ISO 8601 UTC.
    """

    target: str
    destination_ip: Optional[str] = None
    packets_transmitted: int = 0
    packets_received: int = 0
    packets_lost: int = 0
    packet_loss_percentage: float = 100.0
    min_rtt_ms: Optional[float] = None
    avg_rtt_ms: Optional[float] = None
    max_rtt_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    is_reachable: bool = False
    status: str = "UNREACHABLE"
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia a un diccionario nativo de Python."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializa la instancia a una cadena en formato JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class TracerouteHop:
    """Representa un salto individual (nodo intermedio) dentro de una traza de red.

    Attributes:
        hop_number: Número secuencial del salto en la ruta.
        ip_address: Dirección IP del nodo intermedio (None si hubo timeout total).
        hostname: Nombre DNS del nodo intermedio (si se habilitó resolución).
        rtt_ms: Lista de tiempos de ida y vuelta para cada sondeo en este salto.
                Contiene None para sondeos individuales que no respondieron (*).
        packet_loss_percentage: Porcentaje de pérdida de paquetes en los sondeos del salto.
        avg_rtt_ms: Promedio de los RTTs válidos en este salto.
    """

    hop_number: int
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    rtt_ms: List[Optional[float]] = field(default_factory=list)
    packet_loss_percentage: float = 100.0
    avg_rtt_ms: Optional[float] = None


@dataclass
class TracerouteResult:
    """Representa el resultado completo y estructurado de una prueba de traceroute.

    Attributes:
        target: Host o dirección IP de destino original.
        destination_ip: Dirección IP resuelta del destino.
        total_hops: Cantidad total de saltos registrados.
        hops: Lista ordenada de objetos TracerouteHop.
        reached_destination: Indica si la traza alcanzó exitosamente el destino final.
        status: Estado general ('SUCCESS', 'TIMEOUT', 'MAX_HOPS_EXCEEDED', 'ERROR').
        execution_time_seconds: Duración total de la prueba en segundos.
        error_message: Mensaje explicativo en caso de error crítico.
        timestamp: Marca de tiempo en formato ISO 8601 UTC.
    """

    target: str
    destination_ip: Optional[str] = None
    total_hops: int = 0
    hops: List[TracerouteHop] = field(default_factory=list)
    reached_destination: bool = False
    status: str = "ERROR"
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia y sus saltos a un diccionario nativo de Python."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializa el resultado de la traza a formato JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class IPerfInterval:
    """Representa el rendimiento registrado en un intervalo de 1 segundo de iPerf3.

    Attributes:
        interval_id: Índice secuencial del intervalo.
        start_seconds: Segundo de inicio del intervalo dentro de la prueba.
        end_seconds: Segundo de fin del intervalo.
        bytes_transferred: Cantidad de bytes transferidos en este intervalo.
        bits_per_second: Tasa de bits por segundo instantánea.
        throughput_mbps: Rendimiento en Megabits por segundo (Mbps).
        retransmits: Cantidad de retransmisiones TCP en este intervalo (None para UDP).
        jitter_ms: Jitter en milisegundos (para UDP).
        packet_loss_percentage: Porcentaje de paquetes perdidos (para UDP).
    """

    interval_id: int
    start_seconds: float
    end_seconds: float
    bytes_transferred: int
    bits_per_second: float
    throughput_mbps: float
    retransmits: Optional[int] = None
    jitter_ms: Optional[float] = None
    packet_loss_percentage: Optional[float] = None


@dataclass
class IPerfResult:
    """Representa el resultado estructurado de una prueba de rendimiento con iPerf3.

    Soporta mediciones tanto en protocolo TCP (throughput, retransmisiones, RTT medio)
    como en UDP (ancho de banda efectivo, jitter, pérdida de paquetes en tiempo real).

    Attributes:
        server_host: Dirección IP o hostname del servidor iPerf3 evaluado.
        server_port: Puerto TCP/UDP utilizado (por defecto 5201).
        protocol: Protocolo de transporte evaluado ('TCP' o 'UDP').
        duration_seconds: Duración programada de la prueba en segundos.
        bytes_sent: Total de bytes transmitidos por el emisor.
        bytes_received: Total de bytes recibidos en el extremo receptor.
        sender_bitrate_bps: Tasa de transferencia del emisor en bits por segundo.
        sender_throughput_mbps: Tasa del emisor en Megabits por segundo (Mbps).
        receiver_bitrate_bps: Tasa de recepción en bits por segundo.
        receiver_throughput_mbps: Tasa del receptor en Megabits por segundo (Mbps).
        retransmissions: Conteo total de paquetes TCP retransmitidos por congestión.
        mean_rtt_ms: RTT promedio estimado por el stack TCP en milisegundos.
        jitter_ms: Jitter promedio medido en milisegundos (UDP).
        lost_packets: Paquetes descartados o no recibidos (UDP).
        total_packets: Paquetes totales transmitidos durante la prueba UDP.
        packet_loss_percentage: Porcentaje total de pérdida de paquetes UDP (0.0 a 100.0).
        intervals: Desglose segundo a segundo de la transferencia.
        is_success: Booleano que indica si la prueba completó la transferencia de datos.
        status: Estado general ('SUCCESS', 'SERVER_UNREACHABLE', 'TOOL_NOT_FOUND', 'TIMEOUT', 'ERROR').
        execution_time_seconds: Duración real de la ejecución del proceso en segundos.
        error_message: Detalle en caso de fallo de conexión o ejecución.
        timestamp: Marca de tiempo en formato ISO 8601 UTC.
    """

    server_host: str
    server_port: int = 5201
    protocol: str = "TCP"
    duration_seconds: float = 0.0
    bytes_sent: int = 0
    bytes_received: int = 0
    sender_bitrate_bps: float = 0.0
    sender_throughput_mbps: float = 0.0
    receiver_bitrate_bps: float = 0.0
    receiver_throughput_mbps: float = 0.0
    retransmissions: Optional[int] = None
    mean_rtt_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    lost_packets: Optional[int] = None
    total_packets: Optional[int] = None
    packet_loss_percentage: Optional[float] = None
    intervals: List[IPerfInterval] = field(default_factory=list)
    is_success: bool = False
    status: str = "ERROR"
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado y sus intervalos a un diccionario nativo."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializa el resultado de rendimiento a una cadena JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class NetworkHealthReport:
    """Reporte unificado de salud y diagnóstico de conectividad de red.

    Consolida las métricas de Ping ICMP, Traceroute e iPerf3 para un host objetivo,
    determinando un estado de salud global y sugerencias preliminares de resolución.

    Attributes:
        target: Host o dirección IP evaluada.
        ping: Resultado de la prueba ICMP (si fue ejecutada).
        traceroute: Resultado de la prueba de ruta (si fue ejecutada).
        iperf: Resultado de la prueba de rendimiento (si fue ejecutada).
        overall_status: Estado consolidado ('OPTIMAL', 'DEGRADED', 'CRITICAL', 'UNREACHABLE').
        initial_recommendations: Lista de acciones iniciales recomendadas.
        timestamp: Marca de tiempo ISO 8601 UTC.
    """

    target: str
    ping: Optional[PingResult] = None
    traceroute: Optional[TracerouteResult] = None
    iperf: Optional[IPerfResult] = None
    overall_status: str = "UNKNOWN"
    initial_recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el reporte completo a un diccionario nativo."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializa el reporte unificado a JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

