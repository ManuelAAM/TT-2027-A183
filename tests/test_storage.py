"""Pruebas del Módulo de Almacenamiento Histórico (TT-2027-A183).

- TestMapper: pruebas unitarias del mapeo DTO -> filas (no requieren base de datos).
- TestRepositoryIntegracion: pruebas contra PostgreSQL real. Se omiten si psycopg
  no está instalado o si no hay conexión con la configuración de .env. Cada prueba
  corre dentro de una transacción que se revierte, así que no deja datos.
"""

from __future__ import annotations

import unittest
from datetime import datetime

from src.monitoring.models import (
    IPerfResult,
    NetworkHealthReport,
    PingResult,
    TracerouteHop,
    TracerouteResult,
)
from src.storage.mapper import (
    clasificar_diagnostico,
    diagnostico_desde_reporte,
    ip_o_none,
    parse_timestamp,
    prueba_desde_iperf,
    prueba_desde_ping,
    pruebas_desde_reporte,
)


def _ping(**cambios) -> PingResult:
    valores = dict(
        target="escom.ipn.mx",
        destination_ip="148.204.103.2",
        packets_transmitted=4,
        packets_received=4,
        packets_lost=0,
        packet_loss_percentage=0.0,
        min_rtt_ms=10.0,
        avg_rtt_ms=12.5,
        max_rtt_ms=15.0,
        jitter_ms=1.2,
        is_reachable=True,
        status="SUCCESS",
        execution_time_seconds=3.1,
        timestamp="2026-10-14T18:00:00+00:00",
    )
    valores.update(cambios)
    return PingResult(**valores)


def _traceroute() -> TracerouteResult:
    return TracerouteResult(
        target="escom.ipn.mx",
        destination_ip="148.204.103.2",
        total_hops=2,
        hops=[
            TracerouteHop(hop_number=1, ip_address="10.100.95.254", rtt_ms=[1.0, 2.0, 3.0],
                          packet_loss_percentage=0.0, avg_rtt_ms=2.0),
            TracerouteHop(hop_number=2, ip_address="148.204.103.2", rtt_ms=[9.0, 10.0, 11.0],
                          packet_loss_percentage=0.0, avg_rtt_ms=10.0),
        ],
        reached_destination=True,
        status="SUCCESS",
        execution_time_seconds=5.0,
        timestamp="2026-10-14T18:00:05+00:00",
    )


def _iperf(**cambios) -> IPerfResult:
    valores = dict(
        server_host="192.168.1.100",
        protocol="TCP",
        duration_seconds=5,
        sender_throughput_mbps=94.1,
        receiver_throughput_mbps=93.8,
        retransmissions=3,
        mean_rtt_ms=1.4,
        is_success=True,
        status="SUCCESS",
        execution_time_seconds=6.0,
        timestamp="2026-10-14T18:00:12+00:00",
    )
    valores.update(cambios)
    return IPerfResult(**valores)


def _reporte(estado: str, **pruebas) -> NetworkHealthReport:
    return NetworkHealthReport(
        target="escom.ipn.mx",
        overall_status=estado,
        initial_recommendations=["HALLAZGO PRINCIPAL", "Acción: revisar el enlace."],
        timestamp="2026-10-14T18:00:15+00:00",
        **pruebas,
    )


class TestMapper(unittest.TestCase):
    """Conversión de DTOs del monitoreo a filas de la base de datos."""

    def test_parse_timestamp_conserva_zona_horaria(self):
        fecha = parse_timestamp("2026-10-14T18:00:00+00:00")
        self.assertEqual(fecha, datetime.fromisoformat("2026-10-14T18:00:00+00:00"))
        self.assertIsNotNone(parse_timestamp("no es fecha").tzinfo)

    def test_ip_o_none_descarta_hostnames(self):
        self.assertEqual(ip_o_none("8.8.8.8"), "8.8.8.8")
        self.assertEqual(ip_o_none("2001:db8::1"), "2001:db8::1")
        self.assertIsNone(ip_o_none("escom.ipn.mx"))
        self.assertIsNone(ip_o_none(None))

    def test_ping_exitoso_llena_latencias(self):
        fila = prueba_desde_ping(_ping())
        self.assertEqual(fila.tipo_prueba, "PING")
        self.assertEqual(fila.ip_destino, "148.204.103.2")
        self.assertEqual(fila.metrica.latencia_ms, 12.5)
        self.assertEqual(fila.metrica.latencia_min_ms, 10.0)
        self.assertEqual(fila.metrica.perdida_paquetes_pct, 0.0)
        self.assertEqual(fila.metrica.detalle["target"], "escom.ipn.mx")

    def test_ping_con_error_no_registra_perdida(self):
        fila = prueba_desde_ping(_ping(status="ERROR", destination_ip=None,
                                       packet_loss_percentage=100.0, is_reachable=False))
        self.assertIsNone(fila.metrica.perdida_paquetes_pct)
        self.assertIsNone(fila.ip_destino)

    def test_iperf_fallido_solo_guarda_detalle(self):
        fila = prueba_desde_iperf(_iperf(is_success=False, status="SERVER_UNREACHABLE",
                                         receiver_throughput_mbps=0.0))
        self.assertEqual(fila.tipo_prueba, "IPERF_TCP")
        self.assertIsNone(fila.metrica.ancho_banda_mbps)
        self.assertIsNotNone(fila.metrica.detalle)

    def test_iperf_udp_usa_tipo_correcto(self):
        fila = prueba_desde_iperf(_iperf(protocol="udp", packet_loss_percentage=1.5))
        self.assertEqual(fila.tipo_prueba, "IPERF_UDP")
        self.assertEqual(fila.metrica.ancho_banda_mbps, 93.8)

    def test_reporte_genera_una_prueba_por_colector(self):
        reporte = _reporte("OPTIMAL", ping=_ping(), traceroute=_traceroute(), iperf=_iperf())
        tipos = [p.tipo_prueba for p in pruebas_desde_reporte(reporte)]
        self.assertEqual(tipos, ["PING", "TRACEROUTE", "IPERF_TCP"])
        traza = pruebas_desde_reporte(reporte)[1]
        self.assertEqual(traza.metrica.saltos, 2)
        self.assertEqual(traza.metrica.latencia_ms, 10.0)

    def test_clasificacion_sigue_reglas_del_motor(self):
        casos = [
            (_reporte("UNREACHABLE", ping=_ping(packet_loss_percentage=100.0, is_reachable=False)),
             ("SIN_CONECTIVIDAD", "CRITICA", "PING")),
            (_reporte("DEGRADED", ping=_ping(packet_loss_percentage=25.0)),
             ("PERDIDA_PAQUETES", "ALTA", "PING")),
            (_reporte("DEGRADED", ping=_ping(avg_rtt_ms=180.0)),
             ("LATENCIA_ELEVADA", "MEDIA", "PING")),
            (_reporte("DEGRADED", ping=_ping(), iperf=_iperf(retransmissions=80)),
             ("CONGESTION_TCP", "MEDIA", "IPERF_TCP")),
            (_reporte("OPTIMAL", ping=_ping()), ("NINGUNA", "INFO", "PING")),
            (_reporte("UNKNOWN"), ("SIN_DATOS", "INFO", None)),
        ]
        for reporte, esperado in casos:
            with self.subTest(esperado=esperado[0]):
                self.assertEqual(clasificar_diagnostico(reporte), esperado)

    def test_diagnostico_conserva_orden_y_prioridad(self):
        fila = diagnostico_desde_reporte(
            _reporte("UNREACHABLE", ping=_ping(packet_loss_percentage=100.0, is_reachable=False))
        )
        self.assertEqual(fila.descripcion, "HALLAZGO PRINCIPAL")
        self.assertEqual(
            fila.recomendaciones,
            [("HALLAZGO PRINCIPAL", "ALTA"), ("Acción: revisar el enlace.", "ALTA")],
        )


def _conexion_de_prueba():
    """Devuelve una conexión a la base o None si no está disponible."""
    try:
        from src.storage.repository import conectar
    except ImportError:
        return None
    try:
        return conectar()
    except Exception:  # noqa: BLE001 - cualquier fallo de conexión omite las pruebas
        return None


class TestRepositoryIntegracion(unittest.TestCase):
    """Escritura y consultas contra PostgreSQL (transacción revertida al final)."""

    @classmethod
    def setUpClass(cls):
        cls.conn = _conexion_de_prueba()
        if cls.conn is None:
            raise unittest.SkipTest("PostgreSQL no disponible (revisa .env y el servicio)")
        from src.storage.repository import MonitoreoRepository

        cls.repo = MonitoreoRepository(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        self._tx = self.conn.transaction(force_rollback=True)
        self._tx.__enter__()

    def tearDown(self):
        self._tx.__exit__(None, None, None)

    def test_guardar_reporte_completo(self):
        id_red = self.repo.registrar_red("LAB-PRUEBAS", "10.100.95.0/24", vlan=95)
        id_sonda = self.repo.registrar_dispositivo("sonda-pruebas", id_red=id_red,
                                                   direccion_ip="10.100.95.10")
        reporte = _reporte("OPTIMAL", ping=_ping(), traceroute=_traceroute(), iperf=_iperf())

        id_ejecucion = self.repo.guardar_reporte(reporte, id_dispositivo=id_sonda)

        pruebas = self.conn.execute(
            "SELECT tipo_prueba, id_dispositivo FROM pruebas_conectividad "
            "WHERE id_ejecucion = %s ORDER BY id_prueba",
            (id_ejecucion,),
        ).fetchall()
        self.assertEqual([p["tipo_prueba"] for p in pruebas], ["PING", "TRACEROUTE", "IPERF_TCP"])
        self.assertTrue(all(p["id_dispositivo"] == id_sonda for p in pruebas))

        diagnostico = self.conn.execute(
            "SELECT d.tipo_anomalia, m.latencia_ms FROM diagnosticos d "
            "JOIN metricas m ON m.id_metrica = d.id_metrica WHERE d.id_ejecucion = %s",
            (id_ejecucion,),
        ).fetchone()
        self.assertEqual(diagnostico["tipo_anomalia"], "NINGUNA")
        self.assertEqual(float(diagnostico["latencia_ms"]), 12.5)

    def test_registrar_es_idempotente(self):
        id_red = self.repo.registrar_red("LAB-IDEMPOTENTE")
        self.assertEqual(self.repo.registrar_red("LAB-IDEMPOTENTE"), id_red)
        id_disp = self.repo.registrar_dispositivo("sonda-x")
        self.assertEqual(self.repo.registrar_dispositivo("sonda-x"), id_disp)

    def test_consultas_de_historial(self):
        # Destino exclusivo de la prueba para no depender de los datos ya guardados.
        destino = "historial.prueba.local"
        self.repo.guardar_reporte(_reporte("OPTIMAL", ping=_ping(target=destino)))
        id_degradado = self.repo.guardar_reporte(
            _reporte("DEGRADED", ping=_ping(target=destino, packet_loss_percentage=50.0,
                                            timestamp="2026-10-14T19:00:00+00:00"))
        )

        historial = self.repo.historial_metricas(host_destino=destino, tipo_prueba="PING")
        self.assertEqual(len(historial), 2)
        self.assertEqual(float(historial[0]["perdida_paquetes_pct"]), 50.0)

        diagnosticos = self.repo.ultimos_diagnosticos(limite=1000)
        degradado = next(d for d in diagnosticos if d["id_ejecucion"] == id_degradado)
        self.assertEqual(degradado["host_destino"], destino)
        self.assertEqual(degradado["tipo_anomalia"], "PERDIDA_PAQUETES")
        self.assertEqual(degradado["recomendaciones"][0], "HALLAZGO PRINCIPAL")

        resumen = self.repo.resumen_por_destino(dias=36500)
        fila = next(r for r in resumen if r["host_destino"] == destino)
        self.assertEqual(fila["total_pruebas"], 2)
        self.assertEqual(float(fila["perdida_promedio_pct"]), 25.0)


if __name__ == "__main__":
    unittest.main()
