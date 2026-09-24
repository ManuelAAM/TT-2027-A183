"""Motor de orquestación de diagnóstico y recomendaciones de red.

Este módulo integra los colectores de Ping ICMP, Traceroute e iPerf3 para
generar un reporte unificado de salud de red (NetworkHealthReport) con
recomendaciones de acciones iniciales, satisfaciendo el objetivo principal
del Trabajo Terminal No. 2027-A183.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from src.monitoring.iperf_collector import execute_iperf
from src.monitoring.models import NetworkHealthReport
from src.monitoring.ping_collector import execute_ping
from src.monitoring.traceroute_collector import execute_traceroute

logger = logging.getLogger(__name__)


class NetworkDiagnosticsEngine:
    """Orquestador de pruebas de conectividad y generador de recomendaciones iniciales."""

    def __init__(self, target: str, iperf_server: Optional[str] = None) -> None:
        """Inicializa el motor de diagnóstico para un objetivo.

        Args:
            target: Host o dirección IP destino para pruebas de conectividad (ping y traceroute).
            iperf_server: Servidor opcional para pruebas de ancho de banda con iPerf3.
                          Si no se especifica, se utiliza 'target' como servidor iperf.
        """
        self.target = target.strip()
        self.iperf_server = (iperf_server or self.target).strip()

    def run_diagnostics(
        self,
        include_ping: bool = True,
        include_traceroute: bool = True,
        include_iperf: bool = False,
        ping_count: int = 4,
        traceroute_max_hops: int = 15,
        iperf_duration: int = 5,
        iperf_protocol: str = "TCP",
    ) -> NetworkHealthReport:
        """Ejecuta la batería de pruebas seleccionada y formula diagnósticos iniciales.

        Returns:
            NetworkHealthReport: Reporte consolidado con todas las métricas y recomendaciones.
        """
        logger.info("Iniciando batería de diagnósticos sobre objetivo: %s", self.target)

        report = NetworkHealthReport(target=self.target)

        # 1. Ejecutar prueba de conectividad y latencia ICMP
        if include_ping:
            report.ping = execute_ping(target=self.target, count=ping_count)

        # 2. Ejecutar prueba de ruta topológica si se solicita
        if include_traceroute:
            report.traceroute = execute_traceroute(
                target=self.target, max_hops=traceroute_max_hops
            )

        # 3. Ejecutar prueba de rendimiento iPerf3 si se solicita
        if include_iperf:
            report.iperf = execute_iperf(
                server_host=self.iperf_server,
                duration_seconds=iperf_duration,
                protocol=iperf_protocol,
            )

        # 4. Motor de Reglas de Diagnóstico y Generación de Acciones Iniciales
        self._analyze_and_recommend(report)

        return report

    def _analyze_and_recommend(self, report: NetworkHealthReport) -> None:
        """Aplica heurísticas de calidad de servicio para diagnosticar la red."""
        recommendations: List[str] = []
        status = "OPTIMAL"

        ping = report.ping
        trace = report.traceroute
        iperf = report.iperf

        # Evaluación de Conectividad Base (ICMP Ping)
        if ping:
            if not ping.is_reachable or ping.packet_loss_percentage >= 100.0:
                status = "UNREACHABLE"
                recommendations.append(
                    "FALLO TOTAL DE CONECTIVIDAD: El host objetivo no responde a solicitudes ICMP Echo."
                )
                recommendations.append(
                    "Acción 1: Verifique el estado físico de la conexión (cable de red Ethernet conectado o enlace Wi-Fi asociado)."
                )
                recommendations.append(
                    "Acción 2: Valide si la puerta de enlace predeterminada (default gateway) responde localmente."
                )
                recommendations.append(
                    "Acción 3: Compruebe que las políticas de firewall o listas de control de acceso (ACLs) del campus no estén bloqueando ICMP."
                )
            elif ping.packet_loss_percentage > 0:
                status = "DEGRADED"
                recommendations.append(
                    f"INTERMITENCIA DETECTADA: Pérdida del {ping.packet_loss_percentage}% de paquetes hacia el objetivo."
                )
                recommendations.append(
                    "Acción: Verifique si existe interferencia en canales Wi-Fi o posible daño físico en el cableado estructurado del laboratorio."
                )
                recommendations.append(
                    "Acción: Renueve la configuración de red y concesión DHCP de su interfaz (ej. 'ipconfig /renew' o reiniciar interfaz)."
                )
            elif ping.avg_rtt_ms and ping.avg_rtt_ms > 120.0:
                status = "DEGRADED"
                recommendations.append(
                    f"LATENCIA ELEVADA: RTT promedio de {ping.avg_rtt_ms} ms supera el umbral óptimo de red académica LAN (<50 ms)."
                )
                recommendations.append(
                    "Acción: Compruebe si existen transferencias masivas de datos o descargas no académicas saturando el canal local."
                )

        # Evaluación de Topología y Saltos (Traceroute)
        if trace:
            if not trace.reached_destination and ping and ping.is_reachable:
                recommendations.append(
                    "DISCREPANCIA EN RUTA: El destino responde a Ping pero el Traceroute no completó la traza. Esto sugiere que los routers perimetrales filtran sondeos UDP/ICMP con TTL bajo."
                )
            elif not trace.reached_destination and status == "UNREACHABLE":
                if trace.hops:
                    last_hop = trace.hops[-1]
                    hop_ip = last_hop.ip_address or "Nodo desconocido"
                    recommendations.append(
                        f"PUNTO DE CORTE IDENTIFICADO: La traza se detuvo en el salto #{last_hop.hop_number} ({hop_ip}). El fallo se localiza a partir de este segmento de red."
                    )

        # Evaluación de Rendimiento y Ancho de Banda (iPerf3)
        if iperf and iperf.is_success:
            if iperf.retransmissions and iperf.retransmissions > 50:
                status = "DEGRADED" if status == "OPTIMAL" else status
                recommendations.append(
                    f"CONGESTIÓN DETECTADA EN CAPA DE TRANSPORTE: {iperf.retransmissions} retransmisiones de paquetes TCP registradas durante la prueba."
                )
                recommendations.append(
                    "Acción: Posible saturación de buffers de conmutador (switch) o desajuste de dúplex (duplex mismatch) en la tarjeta de red."
                )
            if iperf.packet_loss_percentage and iperf.packet_loss_percentage > 5.0:
                status = "DEGRADED" if status == "OPTIMAL" else status
                recommendations.append(
                    f"PÉRDIDA EN FLUJO UDP: {iperf.packet_loss_percentage}% de paquetes descartados en la prueba de ancho de banda."
                )

        if not recommendations:
            recommendations.append(
                "CONEXIÓN ÓPTIMA: Los indicadores de latencia, pérdida y disponibilidad se encuentran dentro de los parámetros normales de operación."
            )

        report.overall_status = status
        report.initial_recommendations = recommendations


def run_full_diagnostics(
    target: str,
    iperf_server: Optional[str] = None,
    include_traceroute: bool = True,
    include_iperf: bool = False,
) -> NetworkHealthReport:
    """Función de alto nivel para ejecutar el diagnóstico completo de conectividad.

    Args:
        target: Host o dirección IP destino.
        iperf_server: Servidor iperf3 opcional.
        include_traceroute: Ejecutar traza de saltos (por defecto True).
        include_iperf: Ejecutar prueba de rendimiento iPerf3 (por defecto False).

    Returns:
        NetworkHealthReport: Reporte de salud y recomendaciones generado.
    """
    engine = NetworkDiagnosticsEngine(target=target, iperf_server=iperf_server)
    return engine.run_diagnostics(
        include_ping=True,
        include_traceroute=include_traceroute,
        include_iperf=include_iperf,
    )
