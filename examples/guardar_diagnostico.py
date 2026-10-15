"""Ejecuta un diagnóstico, lo guarda en PostgreSQL y muestra el historial.

Demuestra el flujo completo del almacenamiento histórico (Objetivo Específico 2):
medición -> diagnóstico -> persistencia -> consulta.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python examples/guardar_diagnostico.py                 # objetivo por defecto 8.8.8.8
    python examples/guardar_diagnostico.py escom.ipn.mx
    python examples/guardar_diagnostico.py 8.8.8.8 --sin-traceroute
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH para permitir ejecuciones directas
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.monitoring import NetworkDiagnosticsEngine
from src.storage.repository import MonitoreoRepository, conectar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def print_separator(title: str) -> None:
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("objetivo", nargs="?", default="8.8.8.8", help="Host o IP a evaluar")
    parser.add_argument("--sin-traceroute", action="store_true", help="Omitir traceroute")
    parser.add_argument("--iperf", metavar="SERVIDOR", help="Servidor iPerf3 para medir throughput")
    args = parser.parse_args()

    print_separator(f"DIAGNÓSTICO Y ALMACENAMIENTO - {args.objetivo}")
    engine = NetworkDiagnosticsEngine(target=args.objetivo, iperf_server=args.iperf)
    reporte = engine.run_diagnostics(
        include_traceroute=not args.sin_traceroute,
        include_iperf=bool(args.iperf),
    )
    print(f"Estado global: {reporte.overall_status}")

    with conectar() as conn:
        repo = MonitoreoRepository(conn)
        id_sonda = repo.registrar_dispositivo(socket.gethostname(), tipo_dispositivo="SONDA")
        id_ejecucion = repo.guardar_reporte(reporte, id_dispositivo=id_sonda)
        print(f"Reporte guardado con id_ejecucion = {id_ejecucion}")

        print_separator("ÚLTIMAS 5 PRUEBAS REGISTRADAS")
        print(f"{'Fecha (hora local)':<20}{'Tipo':<11} {'Destino':<18} {'Estado':<13} "
              f"{'Lat. ms':>8} {'Pérd. %':>8} {'Mbps':>8}")
        for fila in repo.historial_metricas(limite=5):
            print(
                f"{fila['fecha_hora']:%Y-%m-%d %H:%M:%S}  {fila['tipo_prueba']:<11} "
                f"{fila['host_destino'][:18]:<18} {fila['estado']:<13} "
                f"{_num(fila['latencia_ms']):>8} {_num(fila['perdida_paquetes_pct']):>8} "
                f"{_num(fila['ancho_banda_mbps']):>8}"
            )

        print_separator("RESUMEN DE LOS ÚLTIMOS 7 DÍAS POR DESTINO")
        for fila in repo.resumen_por_destino(dias=7):
            print(
                f"{fila['host_destino']:<20} {fila['tipo_prueba']:<11} "
                f"pruebas={fila['total_pruebas']:<4} "
                f"latencia_prom={_num(fila['latencia_promedio_ms'])} ms  "
                f"pérdida_prom={_num(fila['perdida_promedio_pct'])} %"
            )

        print_separator("ÚLTIMO DIAGNÓSTICO")
        ultimo = repo.ultimos_diagnosticos(limite=1)[0]
        print(f"{ultimo['estado_global']} | {ultimo['tipo_anomalia']} | severidad {ultimo['severidad']}")
        for i, accion in enumerate(ultimo["recomendaciones"], start=1):
            print(f"  {i}. {accion}")


def _num(valor) -> str:
    return "-" if valor is None else f"{float(valor):.2f}"


if __name__ == "__main__":
    main()
