"""Genera el diagrama entidad-relación completo de monitoreo_red (erd_completo.svg).

Incluye las seis tablas de db/schema.sql y la tabla CAPTURAS_PAQUETES de db/ampliacion_capturas.sql.
Para obtener el PNG se abre el SVG con Microsoft Edge en modo headless.

Uso: python docs/uml/generar_erd.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 1220, 860
FILA, CAB = 19, 34
ANCHO = 340
AZUL, GRIS = "#2F4A7A", "#333333"

# nombre: (x, y, columnas [(nombre, tipo, marca)], color de encabezado, nota)
TABLAS = {
    "REDES": (20, 80, [("id_red", "SERIAL", "PK"), ("nombre_red", "VARCHAR(100)", "UQ"), ("segmento_red", "CIDR", ""),
                       ("vlan", "INTEGER", ""), ("descripcion", "TEXT", "")], AZUL, None),
    "DISPOSITIVOS": (20, 280, [("id_dispositivo", "SERIAL", "PK"), ("id_red", "INTEGER", "FK"),
                               ("nombre", "VARCHAR(100)", ""), ("direccion_ip", "INET", ""),
                               ("direccion_mac", "MACADDR", ""), ("tipo_dispositivo", "VARCHAR(30)", ""),
                               ("ubicacion", "VARCHAR(100)", ""), ("fecha_registro", "TIMESTAMPTZ", "")], AZUL, None),
    "PRUEBAS_CONECTIVIDAD": (440, 80, [("id_prueba", "SERIAL", "PK"), ("id_dispositivo", "INTEGER", "FK"),
                                       ("id_ejecucion", "UUID", ""), ("tipo_prueba", "VARCHAR(20)", ""),
                                       ("host_destino", "VARCHAR(255)", ""), ("ip_destino", "INET", ""),
                                       ("fecha_hora", "TIMESTAMPTZ", ""), ("estado", "VARCHAR(20)", ""),
                                       ("duracion_segundos", "NUMERIC(10,3)", ""), ("mensaje_error", "TEXT", "")], AZUL, None),
    "METRICAS": (440, 380, [("id_metrica", "SERIAL", "PK"), ("id_prueba", "INTEGER", "FK"),
                            ("latencia_ms", "NUMERIC(10,2)", ""), ("latencia_min_ms", "NUMERIC(10,2)", ""),
                            ("latencia_max_ms", "NUMERIC(10,2)", ""), ("perdida_paquetes_pct", "NUMERIC(5,2)", ""),
                            ("jitter_ms", "NUMERIC(10,2)", ""), ("ancho_banda_mbps", "NUMERIC(10,2)", ""),
                            ("retransmisiones", "INTEGER", ""), ("saltos", "INTEGER", ""), ("detalle", "JSONB", "")], AZUL, None),
    "CAPTURAS_PAQUETES": (860, 80, [("id_captura", "SERIAL", "PK"), ("id_prueba", "INTEGER", "FK"),
                                    ("herramienta", "VARCHAR(20)", ""), ("interfaz", "VARCHAR(100)", ""),
                                    ("filtro_captura", "TEXT", ""), ("paquetes_totales", "INTEGER", ""),
                                    ("paquetes_perdidos", "INTEGER", ""), ("paquetes_danados", "INTEGER", ""),
                                    ("retransmisiones_tcp", "INTEGER", ""), ("duplicados", "INTEGER", ""),
                                    ("fuera_de_orden", "INTEGER", ""), ("delta_promedio_ms", "NUMERIC(10,3)", ""),
                                    ("delta_maximo_ms", "NUMERIC(10,3)", ""), ("codigos_icmp", "JSONB", ""),
                                    ("archivo_pcap", "TEXT", ""), ("fecha_captura", "TIMESTAMPTZ", "")], AZUL, None),
    "DIAGNOSTICOS": (20, 560, [("id_diagnostico", "SERIAL", "PK"), ("id_dispositivo", "INTEGER", "FK"),
                               ("id_metrica", "INTEGER", "FK"), ("id_ejecucion", "UUID", ""),
                               ("estado_global", "VARCHAR(20)", ""), ("tipo_anomalia", "VARCHAR(50)", ""),
                               ("severidad", "VARCHAR(20)", ""), ("descripcion", "TEXT", ""),
                               ("fecha_deteccion", "TIMESTAMPTZ", "")], AZUL, None),
    "RECOMENDACIONES": (440, 660, [("id_recomendacion", "SERIAL", "PK"), ("id_diagnostico", "INTEGER", "FK"),
                                   ("orden", "SMALLINT", ""), ("accion_sugerida", "TEXT", ""),
                                   ("prioridad", "VARCHAR(20)", ""), ("estado", "VARCHAR(20)", ""),
                                   ("fecha_generacion", "TIMESTAMPTZ", "")], AZUL, None),
}

out = []


def t(x, y, s, size=13, weight="normal", color=GRIS, anchor="start", italic=False, mono=False):
    fam = ' font-family="Consolas, Courier New, monospace"' if mono else ""
    it = ' font-style="italic"' if italic else ""
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
               f'text-anchor="{anchor}"{fam}{it}>{escape(s)}</text>')


def alto(nombre):
    return CAB + FILA * len(TABLAS[nombre][2]) + 8


def tabla(nombre):
    x, y, cols, color, nota = TABLAS[nombre]
    h = alto(nombre)
    out.append(f'<rect x="{x}" y="{y}" width="{ANCHO}" height="{h}" rx="8" fill="white" stroke="{color}" stroke-width="1.8"/>')
    out.append(f'<path d="M{x} {y+8} Q{x} {y} {x+8} {y} L{x+ANCHO-8} {y} Q{x+ANCHO} {y} {x+ANCHO} {y+8} '
               f'L{x+ANCHO} {y+CAB} L{x} {y+CAB} Z" fill="{color}"/>')
    t(x + 12, y + 22, nombre, 14, "bold", "white")
    if nota:
        t(x + ANCHO - 12, y + 22, nota, 11.5, color="#F3D9E2", anchor="end", italic=True)
    for i, (col, tipo, marca) in enumerate(cols):
        yy = y + CAB + 16 + i * FILA
        if i % 2 == 1:
            out.append(f'<rect x="{x+1}" y="{yy-14}" width="{ANCHO-2}" height="{FILA}" fill="#F5F6F9"/>')
        if marca in ("PK", "FK", "UQ"):
            fondo = {"PK": "#F4C430", "FK": "#9DB4DD", "UQ": "#C9CED8"}[marca]
            out.append(f'<rect x="{x+8}" y="{yy-12}" width="24" height="15" rx="3" fill="{fondo}"/>')
            t(x + 20, yy - 1, marca, 9.5, "bold", "#1C2333", anchor="middle")
        t(x + 40, yy, col, 13, "bold" if marca == "PK" else "normal", GRIS, mono=True)
        t(x + ANCHO - 12, yy, tipo, 12, color="#6B7385", anchor="end", mono=True)


def linea(puntos, card_ini, card_fin, etiqueta=None, pos_et=None):
    d = "M" + " L".join(f"{a} {b}" for a, b in puntos)
    out.append(f'<path d="{d}" fill="none" stroke="#3A4256" stroke-width="1.6"/>')
    (x0, y0), (x1, y1) = puntos[0], puntos[1]
    (xa, ya), (xb, yb) = puntos[-2], puntos[-1]

    def etiqueta_card(px, py, qx, qy, txt):
        """Cardinalidad junto al extremo (px, py) del segmento que va hacia (qx, qy)."""
        if qy == py:  # segmento horizontal: arriba de la línea, del lado del segmento
            if qx > px:
                t(px + 6, py - 6, txt, 12, "bold", "#1C2333")
            else:
                t(px - 6, py - 6, txt, 12, "bold", "#1C2333", anchor="end")
        else:          # segmento vertical: a la derecha de la línea
            t(px + 8, py + (16 if qy > py else -6), txt, 12, "bold", "#1C2333")
    etiqueta_card(x0, y0, x1, y1, card_ini)
    etiqueta_card(xb, yb, xa, ya, card_fin)
    if etiqueta:
        t(pos_et[0], pos_et[1], etiqueta, 12, color="#3A4256", anchor="middle", italic=True)


def caja(n):
    x, y, *_ = TABLAS[n]
    return x, y, x + ANCHO, y + alto(n)


out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Arial, Helvetica, sans-serif">')
out.append(f'<rect width="{W}" height="{H}" fill="white"/>')
t(20, 34, "Diagrama entidad-relación · base de datos monitoreo_red (PostgreSQL 17)", 19, "bold", "#1C2333")
t(20, 58, "Esquema de db/schema.sql ampliado con la tabla CAPTURAS_PAQUETES para el análisis de paquetes (db/ampliacion_capturas.sql)",
  12.5, color="#6B7385")

# Relaciones (1 = uno, N = muchos, 0..1 = cero o uno)
rx0, ry0, rx1, ry1 = caja("REDES"); dx0, dy0, dx1, dy1 = caja("DISPOSITIVOS")
px0, py0, px1, py1 = caja("PRUEBAS_CONECTIVIDAD"); mx0, my0, mx1, my1 = caja("METRICAS")
cx0, cy0, cx1, cy1 = caja("CAPTURAS_PAQUETES"); gx0, gy0, gx1, gy1 = caja("DIAGNOSTICOS")
kx0, ky0, kx1, ky1 = caja("RECOMENDACIONES")
linea([(190, ry1), (190, dy0)], "1", "N", "agrupa", (230, (ry1 + dy0) / 2 + 4))
linea([(dx1, dy0 + 60), (400, dy0 + 60), (400, py0 + 120), (px0, py0 + 120)], "1", "N", "ejecuta", (372, py0 + 175))
linea([(610, py1), (610, my0)], "1", "N", "produce", (662, (py1 + my0) / 2 + 4))
linea([(px1, py0 + 60), (cx0, py0 + 60)], "1", "0..1", None)
t((px1 + cx0) / 2, py0 + 78, "se analiza en", 11, color="#3A4256", anchor="middle", italic=True)
linea([(190, dy1), (190, gy0)], "1", "N", "recibe", (230, (dy1 + gy0) / 2 + 4))
linea([(mx0, my0 + 200), (gx1, my0 + 200)], "1", "N", "origina", (400, my0 + 218))
linea([(gx1, ky0 + 60), (kx0, ky0 + 60)], "1", "N", None)
t((gx1 + kx0) / 2, ky0 + 78, "sugiere", 11, color="#3A4256", anchor="middle", italic=True)

for n in TABLAS:
    tabla(n)

# Leyenda
ly = 790
out.append(f'<rect x="860" y="{ly-20}" width="340" height="66" rx="8" fill="#F5F6F9"/>')
for i, (m, c, txt) in enumerate([("PK", "#F4C430", "llave primaria"), ("FK", "#9DB4DD", "llave foránea"),
                                 ("UQ", "#C9CED8", "valor único")]):
    out.append(f'<rect x="{874}" y="{ly-8+i*20}" width="24" height="15" rx="3" fill="{c}"/>')
    t(886, ly + 3 + i * 20, m, 9.5, "bold", "#1C2333", anchor="middle")
    t(906, ly + 4 + i * 20, txt, 12)
t(1030, ly + 4, "1 / N: uno a muchos", 12)
t(1030, ly + 24, "0..1: cero o uno", 12)
out.append("</svg>")

destino = Path(__file__).resolve().parent / "erd_completo.svg"
destino.write_text("\n".join(out), encoding="utf-8")
print("generado", destino.name)
