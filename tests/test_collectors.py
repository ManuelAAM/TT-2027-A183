"""Pruebas unitarias para el Módulo de Monitoreo de Red (TT-2027-A183).

Implementado usando unittest de la librería estándar para garantizar ejecución
sin requerir dependencias de terceros instaladas.
"""

from __future__ import annotations

import json
import unittest

from src.monitoring.iperf_collector import IPerfCollector, execute_iperf
from src.monitoring.models import (
    IPerfInterval,
    IPerfResult,
    NetworkHealthReport,
    PingResult,
    TracerouteHop,
    TracerouteResult,
)
from src.monitoring.ping_collector import PingCollector, execute_ping
from src.monitoring.traceroute_collector import TracerouteCollector
from src.monitoring.utils import get_operating_system, validate_target


class TestUtils(unittest.TestCase):
    """Pruebas para funciones de utilidad y validación."""

    def test_validate_target_valid_ipv4(self):
        self.assertTrue(validate_target("127.0.0.1"))
        self.assertTrue(validate_target("8.8.8.8"))
        self.assertTrue(validate_target("192.168.1.254"))

    def test_validate_target_valid_domain(self):
        self.assertTrue(validate_target("ipn.mx"))
        self.assertTrue(validate_target("escom.ipn.mx"))
        self.assertTrue(validate_target("google.com"))

    def test_validate_target_invalid_inputs(self):
        self.assertFalse(validate_target(""))
        self.assertFalse(validate_target("   "))
        self.assertFalse(validate_target("invalid; rm -rf /"))
        self.assertFalse(validate_target("999.999.999.999"))

    def test_get_operating_system(self):
        os_name = get_operating_system()
        self.assertIn(os_name, ["windows", "linux", "darwin"])


class TestModels(unittest.TestCase):
    """Pruebas para serialización y consistencia de modelos de datos."""

    def test_ping_result_serialization(self):
        res = PingResult(
            target="8.8.8.8",
            destination_ip="8.8.8.8",
            packets_transmitted=4,
            packets_received=4,
            packets_lost=0,
            packet_loss_percentage=0.0,
            min_rtt_ms=10.0,
            avg_rtt_ms=12.5,
            max_rtt_ms=15.0,
            jitter_ms=5.0,
            is_reachable=True,
            status="SUCCESS",
        )
        d = res.to_dict()
        self.assertEqual(d["target"], "8.8.8.8")
        self.assertTrue(d["is_reachable"])
        self.assertEqual(d["avg_rtt_ms"], 12.5)

        json_str = res.to_json()
        loaded = json.loads(json_str)
        self.assertEqual(loaded["status"], "SUCCESS")
        self.assertIn("timestamp", loaded)

    def test_traceroute_result_serialization(self):
        hop1 = TracerouteHop(
            hop_number=1,
            ip_address="192.168.1.1",
            rtt_ms=[1.2, 1.1, 1.3],
            packet_loss_percentage=0.0,
            avg_rtt_ms=1.2,
        )
        hop2 = TracerouteHop(
            hop_number=2,
            ip_address="10.0.0.1",
            rtt_ms=[5.5, None, 5.8],
            packet_loss_percentage=33.33,
            avg_rtt_ms=5.65,
        )
        trace = TracerouteResult(
            target="10.0.0.1",
            destination_ip="10.0.0.1",
            total_hops=2,
            hops=[hop1, hop2],
            reached_destination=True,
            status="SUCCESS",
        )
        d = trace.to_dict()
        self.assertEqual(d["total_hops"], 2)
        self.assertEqual(len(d["hops"]), 2)
        self.assertEqual(d["hops"][1]["rtt_ms"], [5.5, None, 5.8])

        json_str = trace.to_json()
        self.assertIn("192.168.1.1", json_str)


class TestPingCollectorParsing(unittest.TestCase):
    """Pruebas de parseo simulado de salidas de consola Windows y Linux."""

    def test_parse_windows_ping_spanish(self):
        sample_output = """
Haciendo ping a 1.1.1.1 con 32 bytes de datos:
Respuesta desde 1.1.1.1: bytes=32 tiempo=12ms TTL=57
Respuesta desde 1.1.1.1: bytes=32 tiempo=14ms TTL=57

Estadísticas de ping para 1.1.1.1:
    Paquetes: enviados = 2, recibidos = 2, perdidos = 0
    (0% perdidos),
Tiempos aproximados de ida y vuelta en milisegundos:
    Mínimo = 12ms, Máximo = 14ms, Media = 13ms
"""
        collector = PingCollector(target="1.1.1.1", count=2)
        res = collector._parse_windows_output(sample_output, returncode=0)

        self.assertEqual(res.packets_transmitted, 2)
        self.assertEqual(res.packets_received, 2)
        self.assertEqual(res.packets_lost, 0)
        self.assertEqual(res.packet_loss_percentage, 0.0)
        self.assertEqual(res.min_rtt_ms, 12.0)
        self.assertEqual(res.avg_rtt_ms, 13.0)
        self.assertEqual(res.max_rtt_ms, 14.0)
        self.assertTrue(res.is_reachable)
        self.assertEqual(res.status, "SUCCESS")

    def test_parse_linux_ping(self):
        sample_output = """
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=14.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=15.1 ms

--- 8.8.8.8 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 14.200/14.650/15.100/0.450 ms
"""
        collector = PingCollector(target="8.8.8.8", count=2)
        res = collector._parse_linux_output(sample_output, returncode=0)

        self.assertEqual(res.destination_ip, "8.8.8.8")
        self.assertEqual(res.packets_transmitted, 2)
        self.assertEqual(res.packets_received, 2)
        self.assertEqual(res.packet_loss_percentage, 0.0)
        self.assertEqual(res.min_rtt_ms, 14.2)
        self.assertEqual(res.avg_rtt_ms, 14.65)
        self.assertEqual(res.max_rtt_ms, 15.1)
        self.assertEqual(res.jitter_ms, 0.45)
        self.assertTrue(res.is_reachable)
        self.assertEqual(res.status, "SUCCESS")

    def test_invalid_target_handling(self):
        res = execute_ping("invali$$d target")
        self.assertEqual(res.status, "ERROR")
        self.assertFalse(res.is_reachable)
        self.assertIn("no es una IP", res.error_message)


class TestTracerouteCollectorParsing(unittest.TestCase):
    """Pruebas de parseo simulado de tracert y traceroute."""

    def test_parse_windows_tracert(self):
        sample_output = """
Traza a 1.1.1.1 sobre caminos de 3 saltos como máximo.

  1     2 ms     2 ms     2 ms  192.168.1.1 
  2     *        *        *     Tiempo de espera agotado.
  3    12 ms    11 ms    13 ms  1.1.1.1 

Traza completa.
"""
        collector = TracerouteCollector(target="1.1.1.1", max_hops=3)
        res = collector._parse_windows_tracert(sample_output)

        self.assertEqual(res.total_hops, 3)
        self.assertTrue(res.reached_destination)
        self.assertEqual(res.status, "SUCCESS")

        hop1 = res.hops[0]
        self.assertEqual(hop1.hop_number, 1)
        self.assertEqual(hop1.ip_address, "192.168.1.1")
        self.assertEqual(hop1.packet_loss_percentage, 0.0)

        hop2 = res.hops[1]
        self.assertEqual(hop2.hop_number, 2)
        self.assertIsNone(hop2.ip_address)
        self.assertEqual(hop2.packet_loss_percentage, 100.0)

        hop3 = res.hops[2]
        self.assertEqual(hop3.ip_address, "1.1.1.1")
        self.assertEqual(hop3.avg_rtt_ms, 12.0)


class TestIPerfCollectorParsing(unittest.TestCase):
    """Pruebas de parseo simulado de salidas JSON de iPerf3 (TCP y UDP)."""

    def test_parse_iperf_tcp_json(self):
        sample_json = json.dumps({
            "start": {"connected": [{"socket": 4, "local_host": "192.168.1.50", "remote_host": "192.168.1.100"}]},
            "intervals": [
                {
                    "sum": {
                        "start": 0.0,
                        "end": 1.0,
                        "bytes": 12500000,
                        "bits_per_second": 100000000.0,
                        "retransmits": 1,
                        "omitted": False
                    }
                },
                {
                    "sum": {
                        "start": 1.0,
                        "end": 2.0,
                        "bytes": 11875000,
                        "bits_per_second": 95000000.0,
                        "retransmits": 0,
                        "omitted": False
                    }
                }
            ],
            "end": {
                "sum_sent": {
                    "start": 0.0,
                    "end": 2.0,
                    "bytes": 24375000,
                    "bits_per_second": 97500000.0,
                    "retransmits": 1
                },
                "sum_received": {
                    "start": 0.0,
                    "end": 2.0,
                    "bytes": 24375000,
                    "bits_per_second": 97500000.0
                },
                "streams": [
                    {
                        "sender": {
                            "mean_rtt": 12500
                        }
                    }
                ]
            }
        })
        collector = IPerfCollector(server_host="192.168.1.100", duration_seconds=2, protocol="TCP")
        res = collector._parse_iperf_json(sample_json, stderr="", returncode=0)

        self.assertTrue(res.is_success)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.sender_throughput_mbps, 97.5)
        self.assertEqual(res.receiver_throughput_mbps, 97.5)
        self.assertEqual(res.retransmissions, 1)
        self.assertEqual(res.mean_rtt_ms, 12.5)
        self.assertEqual(len(res.intervals), 2)
        self.assertEqual(res.intervals[0].throughput_mbps, 100.0)

    def test_parse_iperf_udp_json(self):
        sample_json = json.dumps({
            "end": {
                "sum_sent": {
                    "bytes": 12500000,
                    "bits_per_second": 10000000.0
                },
                "sum": {
                    "bytes": 12500000,
                    "bits_per_second": 9950000.0,
                    "jitter_ms": 0.852,
                    "lost_packets": 5,
                    "packets": 500,
                    "lost_percent": 1.0
                }
            }
        })
        collector = IPerfCollector(server_host="192.168.1.100", duration_seconds=5, protocol="UDP")
        res = collector._parse_iperf_json(sample_json, stderr="", returncode=0)

        self.assertTrue(res.is_success)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.jitter_ms, 0.852)
        self.assertEqual(res.lost_packets, 5)
        self.assertEqual(res.total_packets, 500)
        self.assertEqual(res.packet_loss_percentage, 1.0)
        self.assertEqual(res.receiver_throughput_mbps, 9.95)

    def test_parse_iperf_server_unreachable_error(self):
        sample_json = json.dumps({
            "error": "unable to connect to server: Connection refused"
        })
        collector = IPerfCollector(server_host="192.168.1.100")
        res = collector._parse_iperf_json(sample_json, stderr="", returncode=1)

        self.assertFalse(res.is_success)
        self.assertEqual(res.status, "SERVER_UNREACHABLE")
        self.assertIn("Connection refused", res.error_message)

    def test_iperf_tool_not_found(self):
        collector = IPerfCollector(
            server_host="192.168.1.100",
            custom_binary_path="nonexistent_binary_xyz_123"
        )
        res = collector.run()
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, "TOOL_NOT_FOUND")
        self.assertIn("no está disponible en el PATH", res.error_message)


class TestNetworkDiagnosticsEngine(unittest.TestCase):
    """Pruebas del motor de diagnósticos y heurísticas de recomendación."""

    def test_heuristics_unreachable_target(self):
        from src.monitoring.diagnostics import NetworkDiagnosticsEngine
        from src.monitoring.models import NetworkHealthReport

        engine = NetworkDiagnosticsEngine(target="192.0.2.1")
        report = NetworkHealthReport(target="192.0.2.1")
        report.ping = PingResult(
            target="192.0.2.1",
            packets_transmitted=4,
            packets_received=0,
            packets_lost=4,
            packet_loss_percentage=100.0,
            is_reachable=False,
            status="UNREACHABLE",
        )
        engine._analyze_and_recommend(report)

        self.assertEqual(report.overall_status, "UNREACHABLE")
        self.assertTrue(any("FALLO TOTAL" in rec for rec in report.initial_recommendations))
        self.assertTrue(any("gateway" in rec.lower() for rec in report.initial_recommendations))

    def test_heuristics_degraded_packet_loss(self):
        from src.monitoring.diagnostics import NetworkDiagnosticsEngine
        from src.monitoring.models import NetworkHealthReport

        engine = NetworkDiagnosticsEngine(target="10.0.0.1")
        report = NetworkHealthReport(target="10.0.0.1")
        report.ping = PingResult(
            target="10.0.0.1",
            packets_transmitted=4,
            packets_received=3,
            packets_lost=1,
            packet_loss_percentage=25.0,
            avg_rtt_ms=15.0,
            is_reachable=True,
            status="PARTIAL_LOSS",
        )
        engine._analyze_and_recommend(report)

        self.assertEqual(report.overall_status, "DEGRADED")
        self.assertTrue(any("INTERMITENCIA DETECTADA" in rec for rec in report.initial_recommendations))

    def test_heuristics_optimal(self):
        from src.monitoring.diagnostics import NetworkDiagnosticsEngine
        from src.monitoring.models import NetworkHealthReport

        engine = NetworkDiagnosticsEngine(target="1.1.1.1")
        report = NetworkHealthReport(target="1.1.1.1")
        report.ping = PingResult(
            target="1.1.1.1",
            packets_transmitted=4,
            packets_received=4,
            packets_lost=0,
            packet_loss_percentage=0.0,
            avg_rtt_ms=18.5,
            is_reachable=True,
            status="SUCCESS",
        )
        engine._analyze_and_recommend(report)

        self.assertEqual(report.overall_status, "OPTIMAL")
        self.assertTrue(any("CONEXIÓN ÓPTIMA" in rec or "CONEXI" in rec for rec in report.initial_recommendations))


if __name__ == "__main__":
    unittest.main()

