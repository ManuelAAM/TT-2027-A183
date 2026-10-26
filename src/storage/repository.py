"""Acceso a datos del sistema de monitoreo sobre PostgreSQL (psycopg 3).

Guarda los NetworkHealthReport en las tablas definidas en db/schema.sql y
ofrece las consultas de historial que servirán de base para los reportes y la
interfaz web.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.monitoring.models import NetworkHealthReport
from src.storage.config import DatabaseConfig
from src.storage.mapper import (
    MetricaFila,
    PruebaFila,
    diagnostico_desde_reporte,
    pruebas_desde_reporte,
)

logger = logging.getLogger(__name__)


def conectar(config: Optional[DatabaseConfig] = None) -> psycopg.Connection:
    """Abre una conexión con la configuración de .env (o la indicada).

    La conexión devuelve filas como diccionarios. Úsese como gestor de contexto
    (with conectar() as conn: ...) para confirmar o revertir al salir.
    """
    config = config or DatabaseConfig.from_env()
    return psycopg.connect(**config.conninfo_kwargs(), row_factory=dict_row)


class MonitoreoRepository:
    """Operaciones de escritura y consulta sobre la base monitoreo_red."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    # ------------------------------------------------------------------
    # Catálogos: redes y dispositivos
    # ------------------------------------------------------------------
    def registrar_red(
        self,
        nombre_red: str,
        segmento_red: Optional[str] = None,
        vlan: Optional[int] = None,
        descripcion: Optional[str] = None,
    ) -> int:
        """Crea la red si no existe (por nombre) y devuelve su id_red."""
        fila = self.conn.execute(
            """
            INSERT INTO redes (nombre_red, segmento_red, vlan, descripcion)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (nombre_red) DO UPDATE SET nombre_red = EXCLUDED.nombre_red
            RETURNING id_red
            """,
            (nombre_red, segmento_red, vlan, descripcion),
        ).fetchone()
        return fila["id_red"]

    def registrar_dispositivo(
        self,
        nombre: str,
        tipo_dispositivo: str = "SONDA",
        id_red: Optional[int] = None,
        direccion_ip: Optional[str] = None,
        direccion_mac: Optional[str] = None,
        ubicacion: Optional[str] = None,
    ) -> int:
        """Devuelve el id del dispositivo (nombre, red); lo crea si no existe."""
        with self.conn.transaction():
            fila = self.conn.execute(
                """
                SELECT id_dispositivo FROM dispositivos
                WHERE nombre = %s AND id_red IS NOT DISTINCT FROM %s
                """,
                (nombre, id_red),
            ).fetchone()
            if fila:
                return fila["id_dispositivo"]
            fila = self.conn.execute(
                """
                INSERT INTO dispositivos
                    (id_red, nombre, direccion_ip, direccion_mac, tipo_dispositivo, ubicacion)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_dispositivo
                """,
                (id_red, nombre, direccion_ip, direccion_mac, tipo_dispositivo, ubicacion),
            ).fetchone()
            return fila["id_dispositivo"]

    # ------------------------------------------------------------------
    # Escritura de reportes
    # ------------------------------------------------------------------
    def guardar_reporte(
        self,
        reporte: NetworkHealthReport,
        id_dispositivo: Optional[int] = None,
    ) -> uuid.UUID:
        """Guarda un reporte completo en una sola transacción.

        Args:
            reporte: Resultado de NetworkDiagnosticsEngine.run_diagnostics().
            id_dispositivo: Sonda que ejecutó las pruebas (opcional).

        Returns:
            El id_ejecucion (UUID) que agrupa todas las filas del reporte.
        """
        id_ejecucion = uuid.uuid4()
        diagnostico = diagnostico_desde_reporte(reporte)

        with self.conn.transaction():
            metricas_por_tipo: Dict[str, int] = {}
            for prueba in pruebas_desde_reporte(reporte):
                id_prueba = self._insertar_prueba(prueba, id_ejecucion, id_dispositivo)
                metricas_por_tipo[prueba.tipo_prueba] = self._insertar_metrica(
                    id_prueba, prueba.metrica
                )

            id_diagnostico = self.conn.execute(
                """
                INSERT INTO diagnosticos
                    (id_dispositivo, id_metrica, id_ejecucion, estado_global,
                     tipo_anomalia, severidad, descripcion, fecha_deteccion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_diagnostico
                """,
                (
                    id_dispositivo,
                    metricas_por_tipo.get(diagnostico.tipo_prueba_origen),
                    id_ejecucion,
                    diagnostico.estado_global,
                    diagnostico.tipo_anomalia,
                    diagnostico.severidad,
                    diagnostico.descripcion,
                    diagnostico.fecha_deteccion,
                ),
            ).fetchone()["id_diagnostico"]

            with self.conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO recomendaciones
                        (id_diagnostico, orden, accion_sugerida, prioridad, fecha_generacion)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [
                        (id_diagnostico, orden, texto, prioridad, diagnostico.fecha_deteccion)
                        for orden, (texto, prioridad) in enumerate(
                            diagnostico.recomendaciones, start=1
                        )
                    ],
                )

        logger.info(
            "Reporte de %s guardado (ejecución %s, estado %s)",
            reporte.target,
            id_ejecucion,
            reporte.overall_status,
        )
        return id_ejecucion

    def _insertar_prueba(
        self,
        prueba: PruebaFila,
        id_ejecucion: uuid.UUID,
        id_dispositivo: Optional[int],
    ) -> int:
        return self.conn.execute(
            """
            INSERT INTO pruebas_conectividad
                (id_dispositivo, id_ejecucion, tipo_prueba, host_destino, ip_destino,
                 fecha_hora, estado, duracion_segundos, mensaje_error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_prueba
            """,
            (
                id_dispositivo,
                id_ejecucion,
                prueba.tipo_prueba,
                prueba.host_destino,
                prueba.ip_destino,
                prueba.fecha_hora,
                prueba.estado,
                prueba.duracion_segundos,
                prueba.mensaje_error,
            ),
        ).fetchone()["id_prueba"]

    def _insertar_metrica(self, id_prueba: int, metrica: MetricaFila) -> int:
        return self.conn.execute(
            """
            INSERT INTO metricas
                (id_prueba, latencia_ms, latencia_min_ms, latencia_max_ms,
                 perdida_paquetes_pct, jitter_ms, ancho_banda_mbps,
                 retransmisiones, saltos, detalle)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_metrica
            """,
            (
                id_prueba,
                metrica.latencia_ms,
                metrica.latencia_min_ms,
                metrica.latencia_max_ms,
                metrica.perdida_paquetes_pct,
                metrica.jitter_ms,
                metrica.ancho_banda_mbps,
                metrica.retransmisiones,
                metrica.saltos,
                Jsonb(metrica.detalle) if metrica.detalle is not None else None,
            ),
        ).fetchone()["id_metrica"]

    # ------------------------------------------------------------------
    # Consultas de historial
    # ------------------------------------------------------------------
    def historial_metricas(
        self,
        host_destino: Optional[str] = None,
        tipo_prueba: Optional[str] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limite: int = 100,
    ) -> List[Dict[str, Any]]:
        """Pruebas con sus métricas, de la más reciente a la más antigua."""
        return self.conn.execute(
            """
            SELECT p.id_ejecucion, p.fecha_hora, p.tipo_prueba, p.host_destino,
                   host(p.ip_destino) AS ip_destino, p.estado,
                   m.latencia_ms, m.latencia_min_ms, m.latencia_max_ms,
                   m.perdida_paquetes_pct, m.jitter_ms, m.ancho_banda_mbps,
                   m.retransmisiones, m.saltos
            FROM pruebas_conectividad p
            JOIN metricas m ON m.id_prueba = p.id_prueba
            WHERE (%(host)s::text IS NULL OR p.host_destino = %(host)s)
              AND (%(tipo)s::text IS NULL OR p.tipo_prueba = %(tipo)s)
              AND (%(desde)s::timestamptz IS NULL OR p.fecha_hora >= %(desde)s)
              AND (%(hasta)s::timestamptz IS NULL OR p.fecha_hora < %(hasta)s)
            ORDER BY p.fecha_hora DESC
            LIMIT %(limite)s
            """,
            {
                "host": host_destino,
                "tipo": tipo_prueba,
                "desde": desde,
                "hasta": hasta,
                "limite": limite,
            },
        ).fetchall()

    def ultimos_diagnosticos(self, limite: int = 20) -> List[Dict[str, Any]]:
        """Diagnósticos recientes con el destino evaluado y sus recomendaciones en orden."""
        return self.conn.execute(
            """
            SELECT d.id_ejecucion, d.fecha_deteccion, d.estado_global,
                   d.tipo_anomalia, d.severidad, d.descripcion,
                   (SELECT p.host_destino FROM pruebas_conectividad p
                    WHERE p.id_ejecucion = d.id_ejecucion LIMIT 1) AS host_destino,
                   COALESCE(
                       (SELECT array_agg(r.accion_sugerida ORDER BY r.orden)
                        FROM recomendaciones r
                        WHERE r.id_diagnostico = d.id_diagnostico),
                       '{}'
                   ) AS recomendaciones
            FROM diagnosticos d
            ORDER BY d.fecha_deteccion DESC
            LIMIT %s
            """,
            (limite,),
        ).fetchall()

    def resumen_por_destino(self, dias: int = 7) -> List[Dict[str, Any]]:
        """Promedios por destino y tipo de prueba en los últimos 'dias' días."""
        return self.conn.execute(
            """
            SELECT p.host_destino, p.tipo_prueba,
                   count(*)                              AS total_pruebas,
                   round(avg(m.latencia_ms), 2)          AS latencia_promedio_ms,
                   round(max(m.latencia_ms), 2)          AS latencia_maxima_ms,
                   round(avg(m.perdida_paquetes_pct), 2) AS perdida_promedio_pct,
                   round(avg(m.jitter_ms), 2)            AS jitter_promedio_ms,
                   round(avg(m.ancho_banda_mbps), 2)     AS ancho_banda_promedio_mbps,
                   max(p.fecha_hora)                     AS ultima_prueba
            FROM pruebas_conectividad p
            JOIN metricas m ON m.id_prueba = p.id_prueba
            WHERE p.fecha_hora >= now() - make_interval(days => %s)
            GROUP BY p.host_destino, p.tipo_prueba
            ORDER BY p.host_destino, p.tipo_prueba
            """,
            (dias,),
        ).fetchall()

    def historial_por_periodo(
        self,
        periodo: str = "semana",
        host_destino: Optional[str] = None,
        tipo_prueba: Optional[str] = None,
        periodos: int = 12,
    ) -> List[Dict[str, Any]]:
        """Métricas agregadas por semana o por mes, comparadas con el periodo anterior.

        Cada fila resume un destino y tipo de prueba en un periodo (las semanas inician en
        lunes). Las columnas *_anterior y variacion_* comparan contra el periodo previo del
        mismo destino y tipo, para detectar tendencias de degradación.

        Args:
            periodo: "semana" o "mes".
            host_destino: Filtra un destino; None incluye todos.
            tipo_prueba: Filtra un tipo (PING, TRACEROUTE, IPERF_TCP, IPERF_UDP).
            periodos: Número de semanas o meses hacia atrás, incluido el actual.
        """
        unidades = {"semana": ("week", "1 week"), "mes": ("month", "1 month")}
        if periodo not in unidades:
            raise ValueError("periodo debe ser 'semana' o 'mes'")
        trunc, intervalo = unidades[periodo]
        return self.conn.execute(
            """
            WITH agregado AS (
                SELECT date_trunc(%(trunc)s, p.fecha_hora)          AS inicio_periodo,
                       p.host_destino, p.tipo_prueba,
                       count(*)                                     AS total_pruebas,
                       count(*) FILTER (WHERE p.estado <> 'SUCCESS') AS pruebas_con_falla,
                       round(avg(m.latencia_ms), 2)                 AS latencia_promedio_ms,
                       round(max(m.latencia_ms), 2)                 AS latencia_maxima_ms,
                       round((percentile_cont(0.95) WITHIN GROUP
                              (ORDER BY m.latencia_ms))::numeric, 2) AS latencia_p95_ms,
                       round(avg(m.perdida_paquetes_pct), 2)        AS perdida_promedio_pct,
                       round(avg(m.jitter_ms), 2)                   AS jitter_promedio_ms,
                       round(avg(m.ancho_banda_mbps), 2)            AS ancho_banda_promedio_mbps
                FROM pruebas_conectividad p
                JOIN metricas m ON m.id_prueba = p.id_prueba
                WHERE p.fecha_hora >= date_trunc(%(trunc)s, now())
                                      - (%(periodos)s - 1) * %(intervalo)s::interval
                  AND (%(host)s::text IS NULL OR p.host_destino = %(host)s)
                  AND (%(tipo)s::text IS NULL OR p.tipo_prueba = %(tipo)s)
                GROUP BY 1, 2, 3
            )
            SELECT a.*,
                   lag(latencia_promedio_ms) OVER w AS latencia_anterior_ms,
                   round(100 * (latencia_promedio_ms - lag(latencia_promedio_ms) OVER w)
                         / nullif(lag(latencia_promedio_ms) OVER w, 0), 1) AS variacion_latencia_pct,
                   lag(perdida_promedio_pct) OVER w AS perdida_anterior_pct,
                   perdida_promedio_pct - lag(perdida_promedio_pct) OVER w AS variacion_perdida_puntos
            FROM agregado a
            WINDOW w AS (PARTITION BY host_destino, tipo_prueba ORDER BY inicio_periodo)
            ORDER BY host_destino, tipo_prueba, inicio_periodo DESC
            """,
            {"trunc": trunc, "intervalo": intervalo, "periodos": periodos,
             "host": host_destino, "tipo": tipo_prueba},
        ).fetchall()
