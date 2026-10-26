"""Pruebas funcionales preliminares (Sección 4.7.2 del reporte, Tabla 4.17).

Ejecuta los escenarios PF-01 a PF-09 contra destinos reales y muestra una tabla con el
resultado esperado, el obtenido y si cumple. Para las pruebas de iPerf3 inicia un servidor
local temporal en el puerto 5202 (no interfiere con otro servidor en el 5201).

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python examples/pruebas_funcionales.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.monitoring import NetworkDiagnosticsEngine, execute_iperf, execute_ping  # noqa: E402

PUERTO_IPERF = 5202
PUERTO_SIN_SERVIDOR = 5299


def puerta_de_enlace() -> str:
    """Obtiene la puerta de enlace predeterminada (Windows) o usa 192.168.1.254."""
    try:
        salida = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | "
             "Select-Object -First 1).NextHop"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        return salida or "192.168.1.254"
    except (OSError, subprocess.SubprocessError):
        return "192.168.1.254"


def ms(valor) -> str:
    return "-" if valor is None else f"{valor:g}"


def pf_diagnostico(destino: str, esperado: str, traceroute: bool = True):
    reporte = NetworkDiagnosticsEngine(destino).run_diagnostics(
        include_traceroute=traceroute, traceroute_max_hops=15)
    p = reporte.ping
    detalle = (f"{reporte.overall_status}; RTT {ms(p.min_rtt_ms)}/{ms(p.avg_rtt_ms)}/{ms(p.max_rtt_ms)} ms; "
               f"pérdida {p.packet_loss_percentage:g} %")
    if reporte.traceroute:
        detalle += f"; traza: {reporte.traceroute.total_hops} salto(s)"
    return reporte.overall_status == esperado, detalle


def pf_ping_error(destino: str, descripcion: str):
    p = execute_ping(destino)
    return p.status == "ERROR", f"{p.status}: {descripcion}" if p.status == "ERROR" else p.status


def pf_iperf(protocolo: str, ancho: str | None = None):
    binario = shutil.which("iperf3")
    if not binario:
        return False, "iperf3 no está instalado"
    servidor = subprocess.Popen([binario, "-s", "-1", "-p", str(PUERTO_IPERF)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        r = execute_iperf("127.0.0.1", server_port=PUERTO_IPERF, duration_seconds=5,
                          protocol=protocolo, bandwidth_limit=ancho)
    finally:
        try:
            servidor.wait(timeout=15)
        except subprocess.TimeoutExpired:
            servidor.kill()
    if protocolo == "UDP":
        detalle = (f"{r.status}; {r.receiver_throughput_mbps:g} Mbps; jitter {ms(r.jitter_ms)} ms; "
                   f"{r.lost_packets} de {r.total_packets} perdidos")
    else:
        detalle = f"{r.status}; {r.sender_throughput_mbps:g} Mbps; {len(r.intervals)} intervalos"
    return r.status == "SUCCESS", detalle


def pf_iperf_sin_servidor():
    r = execute_iperf("127.0.0.1", server_port=PUERTO_SIN_SERVIDOR, duration_seconds=3)
    return r.status == "SERVER_UNREACHABLE", r.status


def main() -> None:
    gw = puerta_de_enlace()
    escenarios = [
        ("PF-01", f"Puerta de enlace ({gw})", "OPTIMAL", lambda: pf_diagnostico(gw, "OPTIMAL")),
        ("PF-02", "Destino externo (8.8.8.8)", "OPTIMAL", lambda: pf_diagnostico("8.8.8.8", "OPTIMAL")),
        ("PF-03", "Servidor ESCOM (escom.ipn.mx)", "OPTIMAL",
         lambda: pf_diagnostico("escom.ipn.mx", "OPTIMAL", traceroute=False)),
        ("PF-04", "Host sin respuesta (192.0.2.1)", "UNREACHABLE",
         lambda: pf_diagnostico("192.0.2.1", "UNREACHABLE", traceroute=False)),
        ("PF-05", "Nombre inexistente", "ERROR",
         lambda: pf_ping_error("sitio-inexistente.invalid", "no se pudo resolver el nombre (DNS)")),
        ("PF-06", "Entrada '8.8.8.8 & whoami'", "ERROR (rechazo)",
         lambda: pf_ping_error("8.8.8.8 & whoami", "destino inválido; no se ejecutó ningún comando")),
        ("PF-07", "iPerf3 TCP 5 s (local)", "SUCCESS", lambda: pf_iperf("TCP")),
        ("PF-08", "iPerf3 UDP 50 Mbps (local)", "SUCCESS", lambda: pf_iperf("UDP", "50M")),
        ("PF-09", "iPerf3 sin servidor", "SERVER_UNREACHABLE", pf_iperf_sin_servidor),
    ]

    print("=" * 110)
    print(" PRUEBAS FUNCIONALES PRELIMINARES - TT 2027-A183 (Tabla 4.17)")
    print(f" Fecha: {time.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 110)
    print(f"{'ID':<6} {'Escenario':<34} {'Esperado':<19} {'Cumple':<7} Resultado obtenido")
    print("-" * 110)
    aprobados = 0
    for clave, nombre, esperado, prueba in escenarios:
        try:
            ok, detalle = prueba()
        except Exception as exc:  # noqa: BLE001 - se reporta como fallo del escenario
            ok, detalle = False, f"excepción: {exc}"
        aprobados += ok
        print(f"{clave:<6} {nombre:<34} {esperado:<19} {'SÍ' if ok else 'NO':<7} {detalle[:70]}")
    print("-" * 110)
    print(f" Resultado: {aprobados} de {len(escenarios)} escenarios cumplen lo esperado.")
    print("=" * 110)


if __name__ == "__main__":
    main()
