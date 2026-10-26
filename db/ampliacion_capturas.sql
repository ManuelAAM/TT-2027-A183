-- ==============================================================================
-- Ampliación del esquema: análisis de paquetes e historial por periodos
-- Sistema de Monitoreo de Red (TT-2027-A183)
-- ==============================================================================
-- Ampliación acordada con los sinodales (octubre de 2026):
--   1. Tabla capturas_paquetes: resultados del análisis con tshark (Wireshark) de
--      los paquetes de cada prueba (paquetes dañados, tiempo delta, códigos ICMP).
--   2. Vistas historial_semanal e historial_mensual para consultar el historial
--      por periodos desde pgAdmin (src/storage usa la misma lógica en
--      MonitoreoRepository.historial_por_periodo).
--
-- Uso (lo ejecuta db/crear_base.ps1 después de schema.sql):
--   psql -U postgres -d monitoreo_red -f db/ampliacion_capturas.sql
-- Es idempotente: puede ejecutarse varias veces sin borrar datos.
-- ==============================================================================

SET client_min_messages = warning;

BEGIN;

-- ------------------------------------------------------------------------------
-- CAPTURAS_PAQUETES: una captura por prueba (relación 1:1 con la prueba).
-- Solo se capturan los paquetes de la propia prueba mediante un filtro BPF
-- (p. ej. "icmp and host 8.8.8.8"), sin inspeccionar el tráfico de otros usuarios.
--   paquetes_danados -> paquetes con checksum incorrecto o marcados como mal
--                       formados por el analizador (_ws.malformed).
--   codigos_icmp     -> conteo por tipo/código ICMP, p. ej. {"3/1": 2, "11/0": 5}.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS capturas_paquetes (
    id_captura          SERIAL          PRIMARY KEY,
    id_prueba           INTEGER         NOT NULL UNIQUE
                        REFERENCES pruebas_conectividad (id_prueba) ON DELETE CASCADE,
    herramienta         VARCHAR(20)     NOT NULL DEFAULT 'tshark',
    interfaz            VARCHAR(100),
    filtro_captura      TEXT            NOT NULL,
    paquetes_totales    INTEGER         NOT NULL CHECK (paquetes_totales >= 0),
    paquetes_perdidos   INTEGER         CHECK (paquetes_perdidos >= 0),
    paquetes_danados    INTEGER         NOT NULL DEFAULT 0 CHECK (paquetes_danados >= 0),
    retransmisiones_tcp INTEGER         CHECK (retransmisiones_tcp >= 0),
    duplicados          INTEGER         CHECK (duplicados >= 0),
    fuera_de_orden      INTEGER         CHECK (fuera_de_orden >= 0),
    delta_promedio_ms   NUMERIC(10, 3)  CHECK (delta_promedio_ms >= 0),
    delta_maximo_ms     NUMERIC(10, 3)  CHECK (delta_maximo_ms >= 0),
    codigos_icmp        JSONB,
    archivo_pcap        TEXT,
    fecha_captura       TIMESTAMPTZ     NOT NULL DEFAULT now(),
    CHECK (paquetes_danados <= paquetes_totales)
);

-- ------------------------------------------------------------------------------
-- Historial por periodos (las semanas inician en lunes).
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW historial_semanal AS
SELECT date_trunc('week', p.fecha_hora)          AS inicio_semana,
       p.host_destino, p.tipo_prueba,
       count(*)                                  AS total_pruebas,
       count(*) FILTER (WHERE p.estado <> 'SUCCESS') AS pruebas_con_falla,
       round(avg(m.latencia_ms), 2)              AS latencia_promedio_ms,
       round(max(m.latencia_ms), 2)              AS latencia_maxima_ms,
       round(avg(m.perdida_paquetes_pct), 2)     AS perdida_promedio_pct,
       round(avg(m.jitter_ms), 2)                AS jitter_promedio_ms,
       round(avg(m.ancho_banda_mbps), 2)         AS ancho_banda_promedio_mbps,
       sum(c.paquetes_danados)                   AS paquetes_danados
FROM pruebas_conectividad p
JOIN metricas m ON m.id_prueba = p.id_prueba
LEFT JOIN capturas_paquetes c ON c.id_prueba = p.id_prueba
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW historial_mensual AS
SELECT date_trunc('month', p.fecha_hora)         AS inicio_mes,
       p.host_destino, p.tipo_prueba,
       count(*)                                  AS total_pruebas,
       count(*) FILTER (WHERE p.estado <> 'SUCCESS') AS pruebas_con_falla,
       round(avg(m.latencia_ms), 2)              AS latencia_promedio_ms,
       round(max(m.latencia_ms), 2)              AS latencia_maxima_ms,
       round(avg(m.perdida_paquetes_pct), 2)     AS perdida_promedio_pct,
       round(avg(m.jitter_ms), 2)                AS jitter_promedio_ms,
       round(avg(m.ancho_banda_mbps), 2)         AS ancho_banda_promedio_mbps,
       sum(c.paquetes_danados)                   AS paquetes_danados
FROM pruebas_conectividad p
JOIN metricas m ON m.id_prueba = p.id_prueba
LEFT JOIN capturas_paquetes c ON c.id_prueba = p.id_prueba
GROUP BY 1, 2, 3;

COMMIT;
