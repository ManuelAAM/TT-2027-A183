# Base de Datos — Sistema de Monitoreo de Red (TT-2027-A183)

**Responsable:** Bejarano Balmori David — *Diseño e implementación del almacenamiento de datos*

Este directorio contiene el esquema relacional en PostgreSQL 17 que da cumplimiento al
**Objetivo Específico 2** del protocolo: *"Implementar mecanismos de almacenamiento para
registrar históricamente los resultados obtenidos durante las pruebas de monitoreo."*

| Archivo | Contenido |
| :--- | :--- |
| [`schema.sql`](schema.sql) | Definición de las 6 tablas, restricciones e índices. Idempotente. |
| [`permisos.sql`](permisos.sql) | Crea el usuario de aplicación `monitoreo_app` con permisos solo de lectura y escritura de datos. |
| [`crear_base.ps1`](crear_base.ps1) | Crea la base `monitoreo_red` y aplica el esquema y los permisos (Windows). |

El código que guarda y consulta los datos está en [`src/storage/`](../src/storage/).

---

## 1. Instalación de PostgreSQL 17 (Windows)

```powershell
winget install --id PostgreSQL.PostgreSQL.17 -e --source winget --interactive
```

En el asistente de instalación:
1. **Componentes:** dejar *PostgreSQL Server*, *pgAdmin 4* y *Command Line Tools*. *Stack Builder* no es necesario.
2. **Contraseña del superusuario `postgres`:** elegir una y guardarla; la pedirá `crear_base.ps1`.
3. **Puerto:** `5432` (predeterminado).
4. **Locale:** *Default locale*.

## 2. Creación de la base

1. Copiar `.env.example` como `.env` en la raíz del proyecto y escribir una contraseña
   para `MONITOREO_DB_PASSWORD`. Esa será la contraseña del usuario `monitoreo_app`.
   El archivo `.env` está en `.gitignore` y no se sube al repositorio.
2. Desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File db\crear_base.ps1
```

El script pide la contraseña de `postgres`, crea la base, aplica el esquema y configura
`monitoreo_app`. Al terminar lista las tablas `redes`, `dispositivos`,
`pruebas_conectividad`, `metricas`, `diagnosticos` y `recomendaciones`.

## 3. Uso desde Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Diagnóstico + guardado + consulta del historial
python examples/guardar_diagnostico.py escom.ipn.mx

# Pruebas unitarias y de integración (las de integración requieren la base)
python -m unittest discover -s tests -p "test_*.py" -v
```

La aplicación se conecta como `monitoreo_app`, no como `postgres`: así un error en el
código no puede borrar tablas ni modificar el esquema.

---

## 4. Modelo de datos

Las seis entidades y sus relaciones 1:N son las del diagrama [`erd_monitoreo_red.svg`](../erd_monitoreo_red.svg):

```text
REDES 1──N DISPOSITIVOS 1──N PRUEBAS_CONECTIVIDAD 1──N METRICAS
                 │                                      │
                 └──────────1──N DIAGNOSTICOS N──1──────┘
                                     │
                                     1──N RECOMENDACIONES
```

### Correspondencia con el módulo de monitoreo

Cada `NetworkHealthReport` (ver `src/monitoring/models.py`) se guarda así:

| Objeto en Python | Tabla | Filas por reporte |
| :--- | :--- | :--- |
| `PingResult`, `TracerouteResult`, `IPerfResult` | `pruebas_conectividad` | Una por prueba ejecutada (1 a 3) |
| Valores numéricos de cada prueba | `metricas` | Una por prueba |
| `overall_status` | `diagnosticos` | Una |
| Cada elemento de `initial_recommendations` | `recomendaciones` | Una por recomendación |

Todas las filas de un mismo reporte comparten el mismo `id_ejecucion` (UUID).

### Ajustes respecto al diagrama ER original

| Tabla | Cambio | Motivo |
| :--- | :--- | :--- |
| Todas | `TIMESTAMP` → `TIMESTAMPTZ` | Los colectores registran la hora en UTC (ISO 8601). Así se evitan errores de zona horaria. |
| `pruebas_conectividad` | `+ id_ejecucion UUID` | Agrupa el ping, el traceroute y el iPerf3 de un mismo reporte. |
| `pruebas_conectividad` | `+ host_destino VARCHAR(255)` | El objetivo puede ser un nombre DNS, no solo una IP. Por eso `ip_destino` admite NULL si falla la resolución. |
| `pruebas_conectividad` | `+ duracion_segundos`, `+ mensaje_error` | Conservan `execution_time_seconds` y `error_message` de los colectores. |
| `metricas` | `+ latencia_min_ms`, `+ latencia_max_ms` | El ping reporta RTT mínimo y máximo, además del promedio (`latencia_ms`). |
| `metricas` | `+ retransmisiones` | Indicador de congestión TCP medido por iPerf3. Lo usa el motor de diagnóstico. |
| `metricas` | `+ detalle JSONB` | Guarda la salida completa (saltos de traceroute, intervalos de iPerf3) sin crear más tablas. |
| `diagnosticos` | `+ id_ejecucion`, `+ estado_global` | Liga el diagnóstico con su ejecución y guarda `OPTIMAL`, `DEGRADED` o `UNREACHABLE`. |
| `recomendaciones` | `+ orden` | Conserva el orden en que el motor generó las acciones. |

### Restricciones de dominio (`CHECK`)

| Columna | Valores permitidos |
| :--- | :--- |
| `dispositivos.tipo_dispositivo` | `SONDA`, `SERVIDOR`, `ROUTER`, `SWITCH`, `PUNTO_ACCESO`, `HOST` |
| `pruebas_conectividad.tipo_prueba` | `PING`, `TRACEROUTE`, `IPERF_TCP`, `IPERF_UDP` |
| `diagnosticos.severidad` | `INFO`, `BAJA`, `MEDIA`, `ALTA`, `CRITICA` |
| `recomendaciones.prioridad` | `BAJA`, `MEDIA`, `ALTA` |
| `recomendaciones.estado` | `PENDIENTE`, `APLICADA`, `DESCARTADA` |
| `metricas.perdida_paquetes_pct` | 0 a 100 |
| `redes.vlan` | 1 a 4094 |

### Índices

Están pensados para las consultas de historial de los reportes: pruebas por fecha,
pruebas por dispositivo y fecha, diagnósticos por fecha, y búsqueda por `id_ejecucion`.
