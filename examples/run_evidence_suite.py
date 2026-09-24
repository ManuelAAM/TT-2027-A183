"""Suite interactiva de demostración y captura de evidencias (TT No. 2027-A183).

Este script permite ejecutar de forma secuencial o modular cada una de las pruebas
desarrolladas en el Módulo de Monitoreo (Ping ICMP, Traceroute, iPerf3 y Diagnóstico Unificado),
imprimiendo encabezados claros y resultados estructurados idóneos para tomar capturas
de pantalla destinadas al README.md y al Reporte Técnico de Titulación (ESCOM - IPN).

Uso:
    python examples/run_evidence_suite.py           # Ejecuta todas las pruebas en orden
    python examples/run_evidence_suite.py --step 1  # Solo Ping exitoso
    python examples/run_evidence_suite.py --step 2  # Solo Manejo de errores / Inalcanzable
    python examples/run_evidence_suite.py --step 3  # Solo Traceroute topológico
    python examples/run_evidence_suite.py --step 4  # Solo iPerf3 / Rendimiento
    python examples/run_evidence_suite.py --step 5  # Solo Diagnóstico y Recomendaciones
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Asegurar que el directorio raíz del proyecto se encuentre en el PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.monitoring import (
    execute_iperf,
    execute_ping,
    execute_traceroute,
    is_iperf_installed,
    run_full_diagnostics,
)


# Configurar stdout para evitar fallos con encodings legados de consola en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner(step_num: int, title: str, description: str) -> None:
    border = "=" * 80
    sub_border = "-" * 80
    print(f"\n{border}")
    print(f" [EVIDENCIA {step_num}] {title.upper()}")
    print(f"{border}")
    print(f" Objetivo : {description}")
    print(f"{sub_border}\n")


def run_step_1_ping_success() -> None:
    print_banner(
        1,
        "Prueba de Conectividad ICMP (Ping) - Flujo Exitoso",
        "Medicion de latencia (min/avg/max/jitter) y porcentaje de perdida hacia nodo de referencia."
    )
    target = "1.1.1.1"
    print(f"[*] Enviando 4 paquetes ICMP Echo Request hacia '{target}'...")
    res = execute_ping(target=target, count=4, timeout_seconds=2)

    print(f"    +-- [METRICAS CAPTURADAS]")
    print(f"    |-- Objetivo Evaluado       : {res.target} (IP Resuelta: {res.destination_ip})")
    print(f"    |-- Paquetes Transmitidos   : {res.packets_transmitted}")
    print(f"    |-- Paquetes Recibidos      : {res.packets_received}")
    print(f"    |-- Perdida de Paquetes     : {res.packet_loss_percentage}%")
    print(f"    |-- Latencia Minima (RTT)   : {res.min_rtt_ms} ms")
    print(f"    |-- Latencia Promedio (RTT) : {res.avg_rtt_ms} ms")
    print(f"    |-- Latencia Maxima (RTT)   : {res.max_rtt_ms} ms")
    print(f"    |-- Jitter Estimado         : {res.jitter_ms} ms")
    print(f"    |-- Disponibilidad (Reachable): {res.is_reachable}")
    print(f"    |-- Estado del Colector     : {res.status}")
    print(f"    \\-- Tiempo de Ejecucion     : {res.execution_time_seconds} s")

    print("\n[DTO Serializado a JSON (Listo para Backend/PostgreSQL)]:")
    print(res.to_json(indent=2))


def run_step_2_ping_errors() -> None:
    print_banner(
        2,
        "Manejo de Excepciones y Host Inalcanzable",
        "Validación de resiliencia del software ante nodos caídos y nombres DNS inválidos."
    )
    # Caso 1: Host Inalcanzable en bloque reservado RFC 5737
    unreachable_ip = "192.0.2.1"
    print(f"[*] Caso A: Evaluando host inalcanzable '{unreachable_ip}'...")
    res_unreach = execute_ping(target=unreachable_ip, count=2, timeout_seconds=1)
    print(f"    |-- Estado Detectado        : {res_unreach.status}")
    print(f"    |-- Pérdida Registrada      : {res_unreach.packet_loss_percentage}%")
    print(f"    |-- ¿Nodo Disponible?       : {res_unreach.is_reachable}")
    print(f"    \\-- Mensaje de Diagnóstico  : {res_unreach.error_message}")

    # Caso 2: Hostname inexistente (Fallo DNS)
    invalid_dns = "host.academico.inexistente.ipn"
    print(f"\n[*] Caso B: Evaluando fallo en resolución DNS con '{invalid_dns}'...")
    res_dns = execute_ping(target=invalid_dns, count=2)
    print(f"    |-- Estado Detectado        : {res_dns.status}")
    print(f"    |-- ¿Nodo Disponible?       : {res_dns.is_reachable}")
    print(f"    \\-- Mensaje de Excepción    : {res_dns.error_message}")


def run_step_3_traceroute() -> None:
    print_banner(
        3,
        "Mapeo de Topología de Red y Saltos (Traceroute)",
        "Detección nodo a nodo de enrutadores intermedios, latencias individuales y puntos de descarte."
    )
    target = "1.1.1.1"
    max_hops = 6
    print(f"[*] Trazando ruta hacia '{target}' (Límite: {max_hops} saltos para captura rápida)...")
    res = execute_traceroute(target=target, max_hops=max_hops, timeout_per_hop_ms=800)

    print(f"    |-- Destino Objetivo        : {res.target}")
    print(f"    |-- Saltos Registrados      : {res.total_hops}")
    print(f"    |-- ¿Alcanzó Destino Final? : {res.reached_destination}")
    print(f"    |-- Estado de la Traza      : {res.status}")
    print(f"    \\-- Duración del Sondeo     : {res.execution_time_seconds} s\n")

    print("    [TABLA DE SALTOS INTERMEDIOS]")
    print("    {:<6} {:<22} {:<24} {:<10} {:<10}".format("Salto", "Dirección IP", "Tiempos RTT (ms)", "Pérdida", "Avg RTT"))
    print("    " + "-" * 74)
    for hop in res.hops:
        ip_str = hop.ip_address if hop.ip_address else "* * * (Timeout)"
        rtts_str = ", ".join([f"{r:.1f}ms" if r is not None else "*" for r in hop.rtt_ms])
        avg_str = f"{hop.avg_rtt_ms:.2f}ms" if hop.avg_rtt_ms is not None else "N/A"
        loss_str = f"{hop.packet_loss_percentage:.0f}%"
        print("    {:<6} {:<22} {:<24} {:<10} {:<10}".format(
            hop.hop_number, ip_str, rtts_str, loss_str, avg_str
        ))


def run_step_4_iperf() -> None:
    print_banner(
        4,
        "Colector de Ancho de Banda y Rendimiento (iPerf3)",
        "Medición de throughput en Mbps, retransmisiones de paquetes TCP y jitter/pérdida UDP."
    )
    installed = is_iperf_installed()
    print(f"[*] Verificación de binario 'iperf3' en el PATH del sistema: {installed}")

    server = "127.0.0.1"
    print(f"[*] Invocando colector para servidor iPerf3 '{server}:5201' (TCP, 5 segundos)...")
    res = execute_iperf(server_host=server, server_port=5201, duration_seconds=5)

    print(f"    |-- Estado del Colector     : {res.status}")
    print(f"    |-- ¿Completó con Éxito?    : {res.is_success}")
    if res.is_success:
        print(f"    |-- Throughput Emisor       : {res.sender_throughput_mbps} Mbps")
        print(f"    |-- Throughput Receptor     : {res.receiver_throughput_mbps} Mbps")
        print(f"    |-- Retransmisiones TCP     : {res.retransmissions}")
        print(f"    \\-- RTT Medio en Conexión   : {res.mean_rtt_ms} ms")
    else:
        print(f"    \\-- Detalle/Recomendación   : {res.error_message}")

    print("\n[DTO Serializado a JSON]:")
    print(res.to_json(indent=2))


def run_step_5_diagnostics() -> None:
    print_banner(
        5,
        "Motor Unificado de Diagnóstico y Generación de Acciones Iniciales",
        "Evaluación heurística integral con consolidación de métricas y sugerencias técnicas."
    )
    target = "1.1.1.1"
    print(f"[*] Ejecutando batería de diagnóstico sobre '{target}'...")
    report = run_full_diagnostics(target=target, include_traceroute=False, include_iperf=False)

    print(f"    +-- [REPORTE UNIFICADO DE SALUD DE RED]")
    print(f"    |-- Nodo Evaluado           : {report.target}")
    print(f"    |-- Estado Global de Salud  : {report.overall_status}")
    print(f"    \\-- Marca de Tiempo UTC     : {report.timestamp}")

    print("\n    [ACCIONES INICIALES SUGERIDAS (RECOMENDACIONES)]:")
    for idx, rec in enumerate(report.initial_recommendations, start=1):
        print(f"     [{idx}] {rec}")

    print("\n[JSON Consolidado para Envío al Backend]:")
    print(report.to_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Suite de captura de evidencias para TT No. 2027-A183")
    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Número específico de prueba a ejecutar (1 a 5). Si se omite, se ejecutan todas.",
    )
    args = parser.parse_args()

    steps = {
        1: run_step_1_ping_success,
        2: run_step_2_ping_errors,
        3: run_step_3_traceroute,
        4: run_step_4_iperf,
        5: run_step_5_diagnostics,
    }

    if args.step:
        steps[args.step]()
    else:
        print("\n" + "#" * 88)
        print("  INICIANDO EJECUCIÓN COMPLETA DE EVIDENCIAS TÉCNICAS (TT No. 2027-A183)")
        print("  Instituto Politécnico Nacional - Escuela Superior de Cómputo")
        print("#" * 88)
        for step_idx in range(1, 6):
            steps[step_idx]()
            time.sleep(0.5)

    print("\n" + "=" * 88)
    print(" [FIN DE LA SUITE DE EVIDENCIAS] Guarde las capturas en la carpeta 'docs/img/'")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
