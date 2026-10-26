"""Muestra el historial de métricas por semana y por mes, comparado con el periodo anterior.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python examples/historial_periodos.py                  # semanas, todos los destinos
    python examples/historial_periodos.py --periodo mes
    python examples/historial_periodos.py --destino escom.ipn.mx --periodos 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.storage.repository import MonitoreoRepository, conectar  # noqa: E402


def num(valor, sufijo="") -> str:
    return "-" if valor is None else f"{float(valor):.2f}{sufijo}"


def variacion(valor, sufijo) -> str:
    return "-" if valor is None else f"{float(valor):+.1f}{sufijo}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--periodo", choices=["semana", "mes"], default="semana")
    parser.add_argument("--destino", help="Filtra un destino (por omisión, todos)")
    parser.add_argument("--periodos", type=int, default=12, help="Semanas o meses hacia atrás")
    args = parser.parse_args()

    with conectar() as conn:
        filas = MonitoreoRepository(conn).historial_por_periodo(
            args.periodo, host_destino=args.destino, periodos=args.periodos)

    titulo = "SEMANA" if args.periodo == "semana" else "MES"
    print("=" * 112)
    print(f" HISTORIAL POR {titulo} (últimos {args.periodos}) - comparación con el periodo anterior")
    print("=" * 112)
    print(f"{'Inicio':<11} {'Destino':<16} {'Prueba':<11} {'Pruebas':>7} {'Fallas':>6} "
          f"{'Lat. prom.':>10} {'Lat. p95':>9} {'Pérdida':>8} {'Var. lat.':>10} {'Var. pérd.':>11}")
    print("-" * 112)
    for f in filas:
        print(f"{f['inicio_periodo']:%d/%m/%Y} {f['host_destino'][:16]:<16} {f['tipo_prueba']:<11} "
              f"{f['total_pruebas']:>7} {f['pruebas_con_falla']:>6} {num(f['latencia_promedio_ms'], ' ms'):>10} "
              f"{num(f['latencia_p95_ms'], ' ms'):>9} {num(f['perdida_promedio_pct'], ' %'):>8} "
              f"{variacion(f['variacion_latencia_pct'], ' %'):>10} {variacion(f['variacion_perdida_puntos'], ' pts'):>11}")
    if not filas:
        print(" No hay pruebas registradas en el periodo.")
    print("=" * 112)


if __name__ == "__main__":
    main()
