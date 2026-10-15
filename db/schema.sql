-- ==============================================================================
-- Esquema de Base de Datos - Sistema de Monitoreo de Red (TT-2027-A183)
-- ==============================================================================
-- Motor:   PostgreSQL 17
-- Base:    monitoreo_red (codificación UTF8)
-- Origen:  erd_monitoreo_red.svg, con los ajustes documentados en db/README.md
--
-- Uso:
--   psql -U postgres -d monitoreo_red -f db/schema.sql
--
-- El script es idempotente (CREATE ... IF NOT EXISTS): puede ejecutarse varias
-- veces sin borrar datos. Si se modifica una tabla ya creada, el cambio debe
-- aplicarse con ALTER TABLE o recreando la base de desarrollo.
-- ==============================================================================

-- Oculta los avisos "ya existe, omitiendo" al volver a ejecutar el script.
SET client_min_messages = warning;

BEGIN;

-- ------------------------------------------------------------------------------
-- REDES: segmentos de red del campus (laboratorios, edificios, WLAN).
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS redes (
    id_red          SERIAL          PRIMARY KEY,
    nombre_red      VARCHAR(100)    NOT NULL UNIQUE,
    segmento_red    CIDR,
    vlan            INTEGER         CHECK (vlan BETWEEN 1 AND 4094),
    descripcion     TEXT
);

-- ------------------------------------------------------------------------------
-- DISPOSITIVOS: equipos conocidos de la red. Las sondas que ejecutan las
-- pruebas también se registran aquí (tipo_dispositivo = 'SONDA').
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dispositivos (
    id_dispositivo      SERIAL          PRIMARY KEY,
    id_red              INTEGER         REFERENCES redes (id_red) ON DELETE SET NULL,
    nombre              VARCHAR(100)    NOT NULL,
    direccion_ip        INET,
    direccion_mac       MACADDR,
    tipo_dispositivo    VARCHAR(30)     NOT NULL DEFAULT 'HOST'
                        CHECK (tipo_dispositivo IN
                              ('SONDA', 'SERVIDOR', 'ROUTER', 'SWITCH',
                               'PUNTO_ACCESO', 'HOST')),
    ubicacion           VARCHAR(100),
    fecha_registro      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (nombre, id_red)
);

-- ------------------------------------------------------------------------------
-- PRUEBAS_CONECTIVIDAD: cada ejecución de ping, traceroute o iPerf3.
--   id_dispositivo  -> sonda que ejecutó la prueba.
--   id_ejecucion    -> agrupa las pruebas de un mismo NetworkHealthReport.
--   host_destino    -> objetivo tal como se pidió (puede ser un hostname).
--   ip_destino      -> IP resuelta; NULL si falló la resolución DNS.
--   estado          -> valor 'status' devuelto por el colector.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pruebas_conectividad (
    id_prueba               SERIAL          PRIMARY KEY,
    id_dispositivo          INTEGER         REFERENCES dispositivos (id_dispositivo)
                                            ON DELETE SET NULL,
    id_ejecucion            UUID            NOT NULL,
    tipo_prueba             VARCHAR(20)     NOT NULL
                            CHECK (tipo_prueba IN
                                  ('PING', 'TRACEROUTE', 'IPERF_TCP', 'IPERF_UDP')),
    host_destino            VARCHAR(255)    NOT NULL,
    ip_destino              INET,
    fecha_hora              TIMESTAMPTZ     NOT NULL DEFAULT now(),
    estado                  VARCHAR(20)     NOT NULL,
    duracion_segundos       NUMERIC(10, 3),
    mensaje_error           TEXT
);

CREATE INDEX IF NOT EXISTS idx_pruebas_fecha_hora
    ON pruebas_conectividad (fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_pruebas_dispositivo_fecha
    ON pruebas_conectividad (id_dispositivo, fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_pruebas_ejecucion
    ON pruebas_conectividad (id_ejecucion);

-- ------------------------------------------------------------------------------
-- METRICAS: valores numéricos medidos en una prueba (relación 1:N con la prueba,
-- en la práctica una fila por prueba). Las columnas que no aplican a un tipo de
-- prueba quedan en NULL (p. ej. ancho_banda_mbps en un ping).
--   latencia_ms -> RTT promedio (ping) o RTT medio TCP (iPerf3).
--   detalle     -> JSON completo del colector (saltos de traceroute,
--                  intervalos de iPerf3) para análisis posteriores.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas (
    id_metrica              SERIAL          PRIMARY KEY,
    id_prueba               INTEGER         NOT NULL
                            REFERENCES pruebas_conectividad (id_prueba) ON DELETE CASCADE,
    latencia_ms             NUMERIC(10, 2),
    latencia_min_ms         NUMERIC(10, 2),
    latencia_max_ms         NUMERIC(10, 2),
    perdida_paquetes_pct    NUMERIC(5, 2)   CHECK (perdida_paquetes_pct BETWEEN 0 AND 100),
    jitter_ms               NUMERIC(10, 2),
    ancho_banda_mbps        NUMERIC(10, 2),
    retransmisiones         INTEGER         CHECK (retransmisiones >= 0),
    saltos                  INTEGER         CHECK (saltos >= 0),
    detalle                 JSONB
);

CREATE INDEX IF NOT EXISTS idx_metricas_prueba ON metricas (id_prueba);

-- ------------------------------------------------------------------------------
-- DIAGNOSTICOS: resultado del motor de diagnóstico para una ejecución.
--   id_metrica      -> métrica que originó la anomalía (NULL si no aplica).
--   estado_global   -> overall_status del NetworkHealthReport.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diagnosticos (
    id_diagnostico      SERIAL          PRIMARY KEY,
    id_dispositivo      INTEGER         REFERENCES dispositivos (id_dispositivo)
                                        ON DELETE SET NULL,
    id_metrica          INTEGER         REFERENCES metricas (id_metrica)
                                        ON DELETE SET NULL,
    id_ejecucion        UUID            NOT NULL,
    estado_global       VARCHAR(20)     NOT NULL
                        CHECK (estado_global IN
                              ('OPTIMAL', 'DEGRADED', 'CRITICAL', 'UNREACHABLE', 'UNKNOWN')),
    tipo_anomalia       VARCHAR(50)     NOT NULL,
    severidad           VARCHAR(20)     NOT NULL
                        CHECK (severidad IN ('INFO', 'BAJA', 'MEDIA', 'ALTA', 'CRITICA')),
    descripcion         TEXT,
    fecha_deteccion     TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diagnosticos_fecha
    ON diagnosticos (fecha_deteccion DESC);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_ejecucion
    ON diagnosticos (id_ejecucion);

-- ------------------------------------------------------------------------------
-- RECOMENDACIONES: acciones iniciales sugeridas para un diagnóstico.
--   orden  -> posición en la lista initial_recommendations.
--   estado -> seguimiento por parte del usuario o personal técnico.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recomendaciones (
    id_recomendacion    SERIAL          PRIMARY KEY,
    id_diagnostico      INTEGER         NOT NULL
                        REFERENCES diagnosticos (id_diagnostico) ON DELETE CASCADE,
    orden               SMALLINT        NOT NULL DEFAULT 1,
    accion_sugerida     TEXT            NOT NULL,
    prioridad           VARCHAR(20)     NOT NULL DEFAULT 'MEDIA'
                        CHECK (prioridad IN ('BAJA', 'MEDIA', 'ALTA')),
    estado              VARCHAR(20)     NOT NULL DEFAULT 'PENDIENTE'
                        CHECK (estado IN ('PENDIENTE', 'APLICADA', 'DESCARTADA')),
    fecha_generacion    TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recomendaciones_diagnostico
    ON recomendaciones (id_diagnostico);

COMMIT;
