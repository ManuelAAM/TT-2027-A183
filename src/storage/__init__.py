"""Módulo de Almacenamiento Histórico para TT-2027-A183.

Persiste en PostgreSQL los reportes generados por el Módulo de Monitoreo
(NetworkHealthReport) y ofrece consultas sobre el historial de pruebas,
métricas, diagnósticos y recomendaciones.

Submódulos:
    config:     Lectura de la configuración de conexión desde .env.
    mapper:     Conversión de los DTOs del monitoreo a filas de las tablas
                (sin dependencia de psycopg, probado de forma unitaria).
    repository: Acceso a datos con psycopg 3 (guardar y consultar).

Uso:
    from src.storage.repository import MonitoreoRepository, conectar

    with conectar() as conn:
        repo = MonitoreoRepository(conn)
        id_ejecucion = repo.guardar_reporte(reporte)
"""
