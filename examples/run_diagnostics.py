"""Script de prueba y diagnóstico rápido de red.

Este script ilustra el uso del Módulo de Monitoreo ejecutando pruebas de conectividad
ICMP (ping) y trazado de rutas (traceroute) sobre destinos locales e Internet,
imprimiendo métricas estructuradas en consola y en formato JSON.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH para permitir ejecuciones directas
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.monitoring import execute_ping, execute_traceroute

# Configuración básica de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("NetworkDiagnostics")


def print_separator(title: str) -> None:
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def run_demo() -> None:
    print_separator("SISTEMA DE MONITOREO DE RED - EJECUCIÓN DE PRUEBAS INICIALES (TT-2027-A183)")
    print("Iniciando pruebas automatizadas de diagnóstico...\n")

    # 1. Prueba de Ping a Servidor Público DNS (Cloudflare)
    target_dns = "1.1.1.1"
    print(f"[*] Ejecutando ICMP Ping hacia {target_dns} (4 paquetes)...")
    ping_res = execute_ping(target=target_dns, count=4, timeout_seconds=2)
    print(f"    - Estado: {ping_res.status}")
    print(f"    - IP Resuelta: {ping_res.destination_ip}")
    print(f"    - Paquetes: Tx={ping_res.packets_transmitted}, Rx={ping_res.packets_received}, Pérdida={ping_res.packet_loss_percentage}%")
    print(f"    - RTT: Min={ping_res.min_rtt_ms}ms, Avg={ping_res.avg_rtt_ms}ms, Max={ping_res.max_rtt_ms}ms, Jitter={ping_res.jitter_ms}ms")
    print(f"    - Duración de prueba: {ping_res.execution_time_seconds}s")
    print("\n[JSON generado para Backend/Base de Datos]:")
    print(ping_res.to_json(indent=2))

    # 2. Prueba de Ping a Destino Inalcanzable (Manejo de Errores)
    unreachable_target = "192.0.2.1"  # Rango TEST-NET-1 (RFC 5737)
    print_separator("PRUEBA DE MANEJO DE ERRORES (HOST INALCANZABLE)")
    print(f"[*] Ejecutando ICMP Ping hacia objetivo simulado inalcanzable ({unreachable_target})...")
    unreach_res = execute_ping(target=unreachable_target, count=2, timeout_seconds=1)
    print(f"    - Estado detectado: {unreach_res.status}")
    print(f"    - Pérdida de paquetes: {unreach_res.packet_loss_percentage}%")
    print(f"    - Mensaje de diagnóstico: {unreach_res.error_message}")
    print(f"    - ¿Alcanzable?: {unreach_res.is_reachable}")

    # 3. Prueba de Traceroute (Salto a Salto)
    target_trace = "1.1.1.1"
    print_separator("PRUEBA DE TRACEROUTE (TOPOLOGÍA Y SALTOS)")
    print(f"[*] Trazando ruta hacia {target_trace} (máximo 6 saltos para diagnóstico rápido)...")
    trace_res = execute_traceroute(target=target_trace, max_hops=6, timeout_per_hop_ms=800)
    print(f"    - Estado: {trace_res.status}")
    print(f"    - Saltos totales registrados: {trace_res.total_hops}")
    print(f"    - ¿Alcanzó el destino final?: {trace_res.reached_destination}")
    print(f"    - Duración: {trace_res.execution_time_seconds}s\n")
    print("    Detalle de saltos:")
    print("    {:<6} {:<20} {:<24} {:<10} {:<10}".format("Salto", "IP Nodo", "RTTs (ms)", "Pérdida", "Avg RTT"))
    print("    " + "-" * 72)
    for hop in trace_res.hops:
        ip_str = hop.ip_address if hop.ip_address else "* * * (Timeout)"
        rtts_str = ", ".join([f"{r:.1f}ms" if r is not None else "*" for r in hop.rtt_ms])
        avg_str = f"{hop.avg_rtt_ms:.2f}ms" if hop.avg_rtt_ms is not None else "N/A"
        loss_str = f"{hop.packet_loss_percentage:.0f}%"
        print("    {:<6} {:<20} {:<24} {:<10} {:<10}".format(
            hop.hop_number, ip_str, rtts_str, loss_str, avg_str
        ))

    print("\n[JSON de Traceroute generado]:")
    print(trace_res.to_json(indent=2))

    print_separator("FIN DE PRUEBAS DE DIAGNÓSTICO")


if __name__ == "__main__":
    run_demo()
