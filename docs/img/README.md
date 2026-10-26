# Repositorio de Evidencias Gráficas y Capturas (TT No. 2027-A183)

Esta carpeta está destinada a almacenar las capturas de pantalla de evidencia técnica para la documentación del proyecto en GitHub, los manuales técnicos y el Reporte Técnico del Trabajo Terminal.

## Convención de Nomenclatura de Capturas de Pantalla

Para mantener la trazabilidad con los objetivos específicos del Trabajo Terminal, utilice los siguientes nombres estándar al guardar las capturas:

| Archivo de Imagen | Fase / Módulo Evaluado | Comando a Ejecutar para la Evidencia |
| :--- | :--- | :--- |
| `01_unit_tests_suite.png` | Pruebas Unitarias de Arquitectura | `python -m unittest discover -s tests -p "test_*.py" -v` |
| `02_ping_connectivity_success.png` | Colector ICMP Ping (Conexión Exitosa) | `python examples/run_evidence_suite.py --step 1` |
| `03_ping_unreachable_handling.png` | Manejo de Excepciones y Host Inalcanzable | `python examples/run_evidence_suite.py --step 2` |
| `04_traceroute_topology_hops.png` | Colector Traceroute (Mapeo de Topología IPN) | `python examples/run_evidence_suite.py --step 3` |
| `05_iperf3_throughput_metrics.png` | Colector iPerf3 (Rendimiento y Throughput) | `python examples/run_evidence_suite.py --step 4` |
| `06_unified_diagnostic_report.png` | Motor de Diagnóstico y Recomendaciones | `python examples/run_evidence_suite.py --step 5` |
| `07_db_esquema_tablas.png` | Almacenamiento: creación de la base y sus 6 tablas | `powershell -ExecutionPolicy Bypass -File db/crear_base.ps1` |
| `08_storage_tests.png` | Almacenamiento: pruebas unitarias y de integración | `python -m unittest tests.test_storage -v` |
| `09_storage_historial.png` | Almacenamiento: diagnóstico guardado y consulta del historial | `python examples/guardar_diagnostico.py escom.ipn.mx` |
| `10_pgadmin_registros.png` | Almacenamiento: registros vistos en pgAdmin 4 | Consulta en pgAdmin (ver db/README.md) |
| `11_historial_semanal.png` | Ampliación: historial agrupado por semana | `python examples/historial_periodos.py` |
| `12_historial_mensual.png` | Ampliación: historial agrupado por mes | `python examples/historial_periodos.py --periodo mes` |
| `13_pgadmin_capturas_paquetes.png` | Ampliación: tabla capturas_paquetes creada (7 tablas) | `powershell -ExecutionPolicy Bypass -File db/crear_base.ps1` y pgAdmin |

## Pautas de Captura para el Reporte Técnico (ESCOM - IPN)
1. **Resolución y Legibilidad:** Ajuste la fuente de su terminal a un tamaño visible (14pt - 16pt) con fondo oscuro contrastado (PowerShell o Windows Terminal).
2. **Formato:** Guardar siempre en formato `.png` para evitar pérdida de nitidez en el texto.
3. **Incrustación en README:** Las capturas se encuentran preconfiguradas con etiquetas markdown y bloques alternativos en el archivo principal `README.md`.
