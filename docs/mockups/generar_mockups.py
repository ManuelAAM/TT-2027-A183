"""Genera los mockups de alta fidelidad de la interfaz web (HTML) del TT 2027-A183.

Cada pantalla es un archivo HTML autónomo de 1440 x 900 px. Para obtener las imágenes PNG se
abren con Microsoft Edge en modo headless (ver render_mockups.ps1).

Uso: python docs/mockups/generar_mockups.py
"""
from __future__ import annotations

from pathlib import Path

SALIDA = Path(__file__).resolve().parent

CSS = """
:root{--guinda:#6E1E3A;--guinda-claro:#8E2D50;--tinta:#1C2333;--texto:#2A3242;--gris:#6B7385;--borde:#E3E6EC;
--fondo:#F4F6F9;--blanco:#FFFFFF;--ok:#1E9E6A;--ok-bg:#E5F6EE;--warn:#D98E04;--warn-bg:#FDF3DC;--err:#D64545;
--err-bg:#FCE8E8;--info:#2F6FD6;--info-bg:#E6EEFB}
*{box-sizing:border-box;margin:0;padding:0}
body{width:1440px;height:900px;overflow:hidden;font-family:"Segoe UI",Arial,sans-serif;color:var(--texto);background:var(--fondo);font-size:14px}
.app{display:flex;height:900px}
.side{width:236px;background:var(--tinta);color:#C9CEDA;padding:22px 16px;display:flex;flex-direction:column;gap:6px}
.logo{display:flex;align-items:center;gap:10px;color:#fff;font-weight:700;font-size:18px;margin:0 6px 22px}
.logo .m{width:34px;height:34px;border-radius:9px;background:var(--guinda);display:grid;place-items:center;font-size:15px}
.logo small{display:block;font-weight:400;font-size:11px;color:#9AA2B4}
.nav{padding:10px 12px;border-radius:9px;display:flex;align-items:center;gap:10px;font-size:14px}
.nav.act{background:rgba(255,255,255,.09);color:#fff;font-weight:600}
.nav .i{width:18px;height:18px;border-radius:5px;border:2px solid currentColor;opacity:.85}
.side .foot{margin-top:auto;font-size:12px;color:#8A93A6;border-top:1px solid rgba(255,255,255,.08);padding-top:14px}
.main{flex:1;padding:24px 30px;display:flex;flex-direction:column;gap:18px;overflow:hidden}
.top{display:flex;align-items:center;justify-content:space-between}
.top h1{font-size:23px;color:var(--tinta)}
.top p{color:var(--gris);margin-top:3px}
.user{display:flex;align-items:center;gap:10px;color:var(--gris);font-size:13px}
.avatar{width:36px;height:36px;border-radius:50%;background:var(--guinda);color:#fff;display:grid;place-items:center;font-weight:700}
.card{background:var(--blanco);border:1px solid var(--borde);border-radius:14px;padding:18px 20px}
.card h3{font-size:15px;color:var(--tinta);margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.card h3 span{font-weight:400;font-size:12px;color:var(--gris)}
.grid{display:grid;gap:16px}
.kpi .v{font-size:28px;font-weight:700;color:var(--tinta);margin-top:6px}
.kpi .l{color:var(--gris);font-size:13px}
.kpi .d{font-size:12px;margin-top:4px}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600}
.b-ok{background:var(--ok-bg);color:var(--ok)}.b-warn{background:var(--warn-bg);color:var(--warn)}
.b-err{background:var(--err-bg);color:var(--err)}.b-info{background:var(--info-bg);color:var(--info)}
.b-gris{background:#EEF0F4;color:var(--gris)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--gris);font-weight:600;font-size:12px;padding:8px 10px;border-bottom:1px solid var(--borde)}
td{padding:9px 10px;border-bottom:1px solid #F0F2F5}
.mono{font-family:Consolas,"Courier New",monospace;font-size:12.5px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-weight:600;font-size:14px;border:1px solid var(--borde);background:#fff;color:var(--texto)}
.btn.p{background:var(--guinda);color:#fff;border-color:var(--guinda)}
.seg{display:inline-flex;background:#EEF0F4;border-radius:10px;padding:3px}
.seg span{padding:6px 14px;border-radius:8px;font-size:13px;color:var(--gris)}
.seg .on{background:#fff;color:var(--tinta);font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.input{border:1px solid var(--borde);border-radius:10px;padding:11px 14px;background:#fff;color:var(--texto);font-size:14px}
.up{color:var(--err)}.down{color:var(--ok)}
.nota{position:absolute;right:16px;bottom:10px;font-size:11px;color:#A0A7B5}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
"""

NAV = ["Inicio", "Diagnóstico", "Historial", "Comparación por periodos", "Análisis de paquetes", "Seguimiento",
       "Administración"]


def pagina(titulo, cuerpo):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{titulo}</title>'
            f'<style>{CSS}</style></head><body>{cuerpo}'
            '<div class="nota">Mockup de alta fidelidad · datos ilustrativos · TT 2027-A183</div></body></html>')


def tecnico(activa, titulo, sub, contenido):
    nav = "".join(f'<div class="nav{" act" if n == activa else ""}"><span class="i"></span>{n}</div>' for n in NAV)
    return pagina(titulo, f"""
<div class="app"><aside class="side">
 <div class="logo"><div class="m">MR</div><div>MonRed<small>Panel técnico · ESCOM</small></div></div>
 {nav}
 <div class="foot">3 sondas en línea<br>Última sincronización 10:42</div>
</aside><main class="main">
 <div class="top"><div><h1>{titulo}</h1><p>{sub}</p></div>
 <div class="user">Encargado de laboratorio <div class="avatar">LR</div></div></div>
 {contenido}
</main></div>""")


def badge(estado):
    clase = {"OPTIMAL": "b-ok", "DEGRADED": "b-warn", "UNREACHABLE": "b-err"}.get(estado, "b-gris")
    return f'<span class="badge {clase}">{estado}</span>'


def linea_svg(series, w=760, h=230, ymax=80, etiquetas=None):
    """Gráfica de líneas sencilla: series = [(nombre, color, [valores])]."""
    pad_l, pad_b, pad_t = 38, 28, 10
    n = len(series[0][2])
    x = lambda i: pad_l + i * (w - pad_l - 30) / (n - 1)
    y = lambda v: pad_t + (h - pad_t - pad_b) * (1 - v / ymax)
    partes = []
    for k in range(0, ymax + 1, 20):
        partes.append(f'<line x1="{pad_l}" y1="{y(k)}" x2="{w-10}" y2="{y(k)}" stroke="#EEF0F4"/>'
                      f'<text x="{pad_l-8}" y="{y(k)+4}" font-size="11" fill="#8A93A6" text-anchor="end">{k}</text>')
    if etiquetas:
        for i, e in enumerate(etiquetas):
            if e:
                partes.append(f'<text x="{x(i)}" y="{h-8}" font-size="11" fill="#8A93A6" text-anchor="middle">{e}</text>')
    for _, color, vals in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        area = f"{x(0)},{y(0)} {pts} {x(n-1)},{y(0)}"
        partes.append(f'<polygon points="{area}" fill="{color}" opacity="0.07"/>'
                      f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"/>')
    return f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block">{"".join(partes)}</svg>'


def barras_svg(grupos, colores, w=760, h=250, ymax=70):
    """Barras agrupadas: grupos = [(etiqueta, [valores])]."""
    pad_l, pad_b = 38, 30
    ancho_grupo = (w - pad_l - 10) / len(grupos)
    nb = len(grupos[0][1])
    bw = min(26, (ancho_grupo - 22) / nb)
    y = lambda v: 10 + (h - 10 - pad_b) * (1 - v / ymax)
    partes = []
    for k in range(0, ymax + 1, 10):
        partes.append(f'<line x1="{pad_l}" y1="{y(k)}" x2="{w-10}" y2="{y(k)}" stroke="#EEF0F4"/>'
                      f'<text x="{pad_l-8}" y="{y(k)+4}" font-size="11" fill="#8A93A6" text-anchor="end">{k}</text>')
    for g, (et, vals) in enumerate(grupos):
        x0 = pad_l + g * ancho_grupo + (ancho_grupo - nb * bw - (nb - 1) * 4) / 2
        for j, v in enumerate(vals):
            xb = x0 + j * (bw + 4)
            partes.append(f'<rect x="{xb:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{y(0)-y(v):.1f}" rx="4" fill="{colores[j]}"/>')
        partes.append(f'<text x="{pad_l + g*ancho_grupo + ancho_grupo/2:.1f}" y="{h-9}" font-size="11.5" fill="#6B7385" text-anchor="middle">{et}</text>')
    return f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;display:block">{"".join(partes)}</svg>'


# ---------------------------------------------------------------------------------
# 1. Panel de usuario: diagnóstico rápido (CU-01, CU-07)
# ---------------------------------------------------------------------------------
recs = [
    ("Verifique que el cable de red esté conectado o que el Wi-Fi esté asociado.", True),
    ("Compruebe si la puerta de enlace del laboratorio responde.", True),
    ("Revise que el firewall del campus no bloquee los paquetes ICMP.", False),
    ("Si el problema continúa, genere un reporte para el personal técnico.", False),
]
lista = "".join(
    f'<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #F0F2F5">'
    f'<div style="width:22px;height:22px;border-radius:6px;border:2px solid {"var(--ok)" if h else "#C5CAD4"};'
    f'background:{"var(--ok)" if h else "#fff"};color:#fff;display:grid;place-items:center;font-size:13px">{"✓" if h else ""}</div>'
    f'<div><b>Paso {i+1}.</b> {t}</div></div>' for i, (t, h) in enumerate(recs))
usuario = pagina("Panel de usuario", f"""
<div style="height:64px;background:#fff;border-bottom:1px solid var(--borde);display:flex;align-items:center;justify-content:space-between;padding:0 40px">
 <div class="logo" style="color:var(--tinta);margin:0"><div class="m" style="color:#fff">MR</div><div>MonRed<small style="color:var(--gris)">Diagnóstico de red · ESCOM</small></div></div>
 <div class="user">Laboratorio de Redes · Equipo PC-LAB2-14 <div class="avatar">AL</div></div></div>
<div style="display:grid;grid-template-columns:520px 1fr;gap:24px;padding:28px 40px">
 <div style="display:flex;flex-direction:column;gap:18px">
  <div class="card" style="padding:26px">
   <h2 style="font-size:24px;color:var(--tinta)">¿Problemas con la red?</h2>
   <p style="color:var(--gris);margin:6px 0 18px">Escriba el sitio o equipo que no responde y el sistema revisará la conexión por usted.</p>
   <div class="input" style="margin-bottom:12px">192.0.2.1</div>
   <div style="display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap">
    <span class="badge b-gris">Puerta de enlace</span><span class="badge b-gris">escom.ipn.mx</span><span class="badge b-gris">8.8.8.8</span></div>
   <div style="display:flex;gap:10px"><span class="btn p">Diagnosticar ahora</span><span class="btn">Medir velocidad (iPerf3)</span></div>
  </div>
  <div class="card"><h3>Mis diagnósticos recientes</h3>
   <table><tr><th>Hora</th><th>Destino</th><th>Resultado</th></tr>
   <tr><td>10:41</td><td>192.0.2.1</td><td>{badge("UNREACHABLE")}</td></tr>
   <tr><td>10:12</td><td>escom.ipn.mx</td><td>{badge("OPTIMAL")}</td></tr>
   <tr><td>09:55</td><td>8.8.8.8</td><td>{badge("OPTIMAL")}</td></tr></table></div>
 </div>
 <div class="card" style="padding:26px">
  <div style="display:flex;align-items:center;gap:18px;padding:18px;border-radius:12px;background:var(--err-bg)">
   <div style="width:58px;height:58px;border-radius:50%;background:var(--err);color:#fff;display:grid;place-items:center;font-size:28px;font-weight:700">!</div>
   <div><div style="font-size:21px;font-weight:700;color:var(--err)">El destino no responde</div>
   <div style="color:#8C3B3B;margin-top:3px">Estado UNREACHABLE · 100 % de paquetes perdidos · diagnóstico a las 10:41</div></div></div>
  <div class="grid" style="grid-template-columns:repeat(3,1fr);margin:18px 0">
   <div class="card kpi"><div class="l">Latencia</div><div class="v">—</div><div class="d" style="color:var(--gris)">sin respuesta</div></div>
   <div class="card kpi"><div class="l">Paquetes perdidos</div><div class="v" style="color:var(--err)">4 / 4</div><div class="d" style="color:var(--gris)">100 %</div></div>
   <div class="card kpi"><div class="l">Puerta de enlace</div><div class="v" style="color:var(--ok)">OK</div><div class="d" style="color:var(--gris)">3 ms</div></div></div>
  <h3 style="font-size:16px;color:var(--tinta);margin-bottom:4px">Qué puede hacer ahora</h3>
  <p style="color:var(--gris);font-size:13px">Siga los pasos en orden y marque los que ya realizó.</p>
  {lista}
  <div style="display:flex;gap:10px;margin-top:18px"><span class="btn p">Volver a diagnosticar</span><span class="btn">Generar reporte para soporte</span></div>
 </div>
</div>""")

# ---------------------------------------------------------------------------------
# 2. Panel técnico: inicio (CU-08, CU-09)
# ---------------------------------------------------------------------------------
horas = ["08:00", "", "", "10:00", "", "", "12:00", "", "", "14:00", "", "", "16:00"]
inicio = tecnico("Inicio", "Estado general de la red", "Resumen de las últimas 24 horas en las sondas del plantel", f"""
<div class="grid" style="grid-template-columns:repeat(4,1fr)">
 <div class="card kpi"><div class="l">Sondas en línea</div><div class="v">3 / 3</div><div class="d down">● todas activas</div></div>
 <div class="card kpi"><div class="l">Pruebas en 24 h</div><div class="v">128</div><div class="d" style="color:var(--gris)">ping · traceroute · iPerf3</div></div>
 <div class="card kpi"><div class="l">Destinos con falla</div><div class="v" style="color:var(--err)">2</div><div class="d up">▲ 1 más que ayer</div></div>
 <div class="card kpi"><div class="l">Latencia promedio</div><div class="v">14.2 ms</div><div class="d down">▼ 8 % vs. semana pasada</div></div>
</div>
<div class="grid" style="grid-template-columns:minmax(0,1fr) 360px">
 <div class="card"><h3>Latencia por destino (ms) <span><span class="dot" style="background:#6E1E3A"></span>escom.ipn.mx
  &nbsp;<span class="dot" style="background:#2F6FD6"></span>8.8.8.8 &nbsp;<span class="dot" style="background:#E8871E"></span>Puerta de enlace</span></h3>
  {linea_svg([("escom", "#6E1E3A", [6, 7, 6, 9, 22, 38, 41, 18, 9, 7, 6, 8, 7]),
              ("google", "#2F6FD6", [14, 15, 13, 16, 19, 27, 30, 21, 16, 15, 14, 15, 14]),
              ("gw", "#E8871E", [3, 3, 4, 3, 5, 9, 11, 6, 4, 3, 3, 4, 3])], w=760, h=240, ymax=60, etiquetas=horas)}
 </div>
 <div class="card"><h3>Estado por destino</h3>
  <div style="display:flex;flex-direction:column;gap:12px">
   <div style="display:flex;justify-content:space-between"><span>escom.ipn.mx</span>{badge("OPTIMAL")}</div>
   <div style="display:flex;justify-content:space-between"><span>8.8.8.8</span>{badge("OPTIMAL")}</div>
   <div style="display:flex;justify-content:space-between"><span>Puerta de enlace Lab 2</span>{badge("OPTIMAL")}</div>
   <div style="display:flex;justify-content:space-between"><span>Servidor iPerf3 Lab 1</span>{badge("DEGRADED")}</div>
   <div style="display:flex;justify-content:space-between"><span>192.0.2.1</span>{badge("UNREACHABLE")}</div>
   <div style="display:flex;justify-content:space-between"><span>Red remota (GNS3)</span><span class="badge b-info">PROPUESTA</span></div>
  </div></div>
</div>
<div class="card"><h3>Diagnósticos recientes <span>ver todos →</span></h3>
 <table><tr><th>Fecha</th><th>Sonda</th><th>Destino</th><th>Estado</th><th>Anomalía</th><th>Severidad</th><th>Recomendación principal</th></tr>
 <tr><td>26/10 10:41</td><td>PC-LAB2-14</td><td>192.0.2.1</td><td>{badge("UNREACHABLE")}</td><td>SIN_CONECTIVIDAD</td><td><span class="badge b-err">CRÍTICA</span></td><td>Verificar el enlace físico</td></tr>
 <tr><td>26/10 10:30</td><td>PC-LAB1-03</td><td>Servidor iPerf3 Lab 1</td><td>{badge("DEGRADED")}</td><td>CONGESTION_TCP</td><td><span class="badge b-warn">MEDIA</span></td><td>Revisar búferes del switch</td></tr>
 <tr><td>26/10 10:12</td><td>PC-LAB2-14</td><td>escom.ipn.mx</td><td>{badge("OPTIMAL")}</td><td>NINGUNA</td><td><span class="badge b-gris">INFO</span></td><td>Conexión óptima</td></tr></table>
</div>""")

# ---------------------------------------------------------------------------------
# 3. Comparación por periodos (CU-15)
# ---------------------------------------------------------------------------------
semanas = [("21/09", [12, 0.0]), ("28/09", [13, 0.5]), ("05/10", [15, 0.2]), ("12/10", [60, 0.0]), ("19/10", [6, 0.0]), ("26/10", [7, 0.0])]
comparacion = tecnico("Comparación por periodos", "Comparación por periodos",
                      "Historial agregado por semana o por mes para detectar tendencias de degradación", f"""
<div style="display:flex;gap:12px;align-items:center">
 <div class="seg"><span class="on">Semana</span><span>Mes</span></div>
 <div class="input" style="padding:8px 12px">Destino: escom.ipn.mx ▾</div>
 <div class="input" style="padding:8px 12px">Prueba: PING ▾</div>
 <div class="input" style="padding:8px 12px">Últimas 6 semanas ▾</div>
 <span class="btn" style="margin-left:auto">Exportar reporte</span></div>
<div class="grid" style="grid-template-columns:minmax(0,1fr) 330px">
 <div class="card"><h3>Latencia promedio por semana (ms) <span><span class="dot" style="background:#6E1E3A"></span>latencia promedio
  &nbsp;<span class="dot" style="background:#E8A317"></span>percentil 95</span></h3>
  {barras_svg([(s, [v[0], v[0]*1.25]) for s, v in semanas], ["#6E1E3A", "#E8A317"], w=780, h=270, ymax=80)}
 </div>
 <div class="card"><h3>Comparación con la semana anterior</h3>
  <div class="kpi"><div class="l">Latencia (semana del 19/10)</div><div class="v">6.00 ms</div><div class="d down">▼ 90.0 % frente a 60.00 ms</div></div>
  <div class="kpi" style="margin-top:16px"><div class="l">Pérdida de paquetes</div><div class="v">0.00 %</div><div class="d" style="color:var(--gris)">sin cambio (+0.0 pts)</div></div>
  <div class="kpi" style="margin-top:16px"><div class="l">Pruebas con falla</div><div class="v">1 de 2</div><div class="d" style="color:var(--gris)">traceroute sin llegar al destino</div></div>
  <div style="margin-top:16px;padding:12px;border-radius:10px;background:var(--info-bg);color:#2A4F94;font-size:13px">
   La semana del 12/10 se midió desde una red externa; desde el 19/10 las mediciones provienen de la red de la ESCOM.</div>
 </div>
</div>
<div class="card"><h3>Detalle por semana</h3>
 <table><tr><th>Semana</th><th>Pruebas</th><th>Fallas</th><th>Latencia prom.</th><th>Latencia p95</th><th>Pérdida</th><th>Jitter</th><th>Variación de latencia</th></tr>
 <tr><td>26/10/2026</td><td>4</td><td>0</td><td>7.00 ms</td><td>8.10 ms</td><td>0.00 %</td><td>1.5 ms</td><td class="up">▲ 16.7 %</td></tr>
 <tr><td>19/10/2026</td><td>2</td><td>1</td><td>6.00 ms</td><td>6.00 ms</td><td>0.00 %</td><td>2.0 ms</td><td class="down">▼ 90.0 %</td></tr>
 <tr><td>12/10/2026</td><td>2</td><td>1</td><td>60.00 ms</td><td>60.00 ms</td><td>0.00 %</td><td>4.0 ms</td><td class="up">▲ 300.0 %</td></tr>
 <tr><td>05/10/2026</td><td>9</td><td>0</td><td>15.00 ms</td><td>18.70 ms</td><td>0.20 %</td><td>3.1 ms</td><td class="up">▲ 15.4 %</td></tr></table>
</div>""")

# ---------------------------------------------------------------------------------
# 4. Análisis de paquetes con tshark (CU-14)
# ---------------------------------------------------------------------------------
deltas = [0, 0.02, 1.00, 0.02, 1.01, 0.02, 2.71, 0.02, 1.00, 0.03, 1.01, 0.02]
paquetes = "".join(
    f'<tr><td>{i+1}</td><td class="mono">{sum(deltas[:i+1]):.3f}</td><td class="mono">{d:.3f}</td>'
    f'<td>{"10.100.95.31" if i % 2 == 0 else "8.8.8.8"}</td><td>{"8.8.8.8" if i % 2 == 0 else "10.100.95.31"}</td>'
    f'<td>{"Echo request (8/0)" if i % 2 == 0 else "Echo reply (0/0)"}</td>'
    f'<td>{"<span class=\"badge b-err\">checksum incorrecto</span>" if i == 9 else ("<span class=\"badge b-warn\">delta alto</span>" if i == 6 else "<span class=\"badge b-ok\">correcto</span>")}</td></tr>'
    for i, d in enumerate(deltas) if 6 <= i <= 9)
barras_delta = "".join(
    f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px">'
    f'<div style="width:100%;height:{max(4, d/2.8*120):.0f}px;background:{"#D64545" if d > 2 else "#2F6FD6"};border-radius:4px 4px 0 0"></div>'
    f'<span style="font-size:11px;color:var(--gris)">{i+1}</span></div>' for i, d in enumerate(deltas))
paquetes_pg = tecnico("Análisis de paquetes", "Análisis de paquetes (tshark)",
                      "Prueba #41 · PING a 8.8.8.8 · sonda PC-LAB2-14 · 26/10/2026 10:52", f"""
<div style="display:flex;gap:12px;align-items:center">
 <div class="input mono" style="padding:8px 12px">Filtro de captura: icmp and host 8.8.8.8</div>
 <span class="badge b-info">Solo tráfico de la prueba</span>
 <span class="btn" style="margin-left:auto">Abrir .pcap en Wireshark</span></div>
<div class="grid" style="grid-template-columns:repeat(5,1fr)">
 <div class="card kpi"><div class="l">Paquetes capturados</div><div class="v">12</div></div>
 <div class="card kpi"><div class="l">Paquetes dañados</div><div class="v" style="color:var(--err)">1</div><div class="d up">checksum incorrecto</div></div>
 <div class="card kpi"><div class="l">Sin respuesta</div><div class="v">0</div></div>
 <div class="card kpi"><div class="l">Delta promedio</div><div class="v">0.62 s</div></div>
 <div class="card kpi"><div class="l">Delta máximo</div><div class="v" style="color:var(--warn)">2.71 s</div><div class="d" style="color:var(--warn)">posible corte breve</div></div>
</div>
<div class="grid" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>Tiempo delta entre paquetes (s) <span>en rojo: hueco mayor a 2 s</span></h3>
  <div style="display:flex;align-items:flex-end;gap:8px;height:150px;padding-top:10px">{barras_delta}</div></div>
 <div class="card"><h3>Códigos ICMP</h3>
  <table><tr><th>Tipo / código</th><th>Significado</th><th>Cantidad</th></tr>
  <tr><td class="mono">8 / 0</td><td>Echo request (solicitud)</td><td>6</td></tr>
  <tr><td class="mono">0 / 0</td><td>Echo reply (respuesta)</td><td>6</td></tr>
  <tr><td class="mono">3 / x</td><td>Destino inalcanzable</td><td>0</td></tr>
  <tr><td class="mono">11 / 0</td><td>Tiempo excedido</td><td>0</td></tr></table>
  <div style="margin-top:12px;padding:10px 12px;border-radius:10px;background:var(--warn-bg);color:#7A5300;font-size:13px">
   Diagnóstico: 1 paquete dañado y un hueco de 2.71 s sugieren interferencia en el enlace inalámbrico.</div></div>
</div>
<div class="card" style="padding-bottom:6px"><h3>Paquetes de la prueba <span>mostrando 7 a 10 de 12</span></h3>
 <table><tr><th>#</th><th>Tiempo (s)</th><th>Delta (s)</th><th>Origen</th><th>Destino</th><th>Tipo ICMP</th><th>Verificación</th></tr>{paquetes}</table></div>
""")

# ---------------------------------------------------------------------------------
# 5. Seguimiento de recomendaciones (CU-11)
# ---------------------------------------------------------------------------------
def tarjeta(dest, texto_, sev, fecha):
    clase = {"CRÍTICA": "b-err", "ALTA": "b-err", "MEDIA": "b-warn", "BAJA": "b-gris"}[sev]
    return (f'<div class="card" style="padding:14px 16px"><div style="display:flex;justify-content:space-between;margin-bottom:8px">'
            f'<b style="color:var(--tinta)">{dest}</b><span class="badge {clase}">{sev}</span></div>'
            f'<div style="font-size:13px">{texto_}</div><div style="font-size:12px;color:var(--gris);margin-top:8px">{fecha}</div></div>')


columnas = [
    ("Pendientes", "var(--warn)", [
        tarjeta("192.0.2.1", "Verificar la conexión física del cable o del enlace Wi-Fi.", "CRÍTICA", "26/10 10:41 · PC-LAB2-14"),
        tarjeta("192.0.2.1", "Comprobar que el firewall no bloquee ICMP.", "CRÍTICA", "26/10 10:41 · PC-LAB2-14"),
        tarjeta("Servidor iPerf3 Lab 1", "Revisar saturación de búferes del switch o desajuste de dúplex.", "MEDIA", "26/10 10:30 · PC-LAB1-03")]),
    ("Aplicadas", "var(--ok)", [
        tarjeta("PC-LAB1-07", "Renovar la concesión DHCP (ipconfig /renew).", "ALTA", "25/10 13:05 · aplicada por L. R."),
        tarjeta("Puerta de enlace Lab 3", "Verificar interferencia en canales Wi-Fi.", "ALTA", "24/10 09:20 · aplicada por L. R.")]),
    ("Descartadas", "var(--gris)", [
        tarjeta("escom.ipn.mx", "Discrepancia de ruta: los routers filtran sondeos con TTL bajo.", "BAJA", "19/10 12:44 · informativa")]),
]
cols_html = "".join(
    f'<div style="background:#EBEEF3;border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:12px">'
    f'<div style="display:flex;justify-content:space-between;align-items:center;font-weight:700;color:var(--tinta)">'
    f'<span><span class="dot" style="background:{c}"></span>{n}</span><span class="badge b-gris">{len(t)}</span></div>{"".join(t)}</div>'
    for n, c, t in columnas)
seguimiento = tecnico("Seguimiento", "Seguimiento de problemas de red",
                      "Estado de las acciones recomendadas por el motor de diagnóstico", f"""
<div style="display:flex;gap:12px"><div class="seg"><span class="on">Todas las sondas</span><span>Lab 1</span><span>Lab 2</span><span>Lab 3</span></div>
 <div class="input" style="padding:8px 12px;margin-left:auto">Buscar destino…</div></div>
<div class="grid" style="grid-template-columns:repeat(3,1fr);align-items:start">{cols_html}</div>
""")

# ---------------------------------------------------------------------------------
# 6. Administración: redes, sondas y pruebas periódicas (CU-12, CU-13)
# ---------------------------------------------------------------------------------
administracion = tecnico("Administración", "Administración",
                         "Redes, sondas y programación de pruebas periódicas", f"""
<div class="grid" style="grid-template-columns:1fr 1fr">
 <div class="card"><h3>Redes registradas <span class="btn p" style="padding:6px 12px;font-size:12px">+ Nueva red</span></h3>
  <table><tr><th>Nombre</th><th>Segmento</th><th>VLAN</th><th>Sondas</th></tr>
  <tr><td>Laboratorio de Redes</td><td class="mono">10.100.95.0/24</td><td>95</td><td>2</td></tr>
  <tr><td>Laboratorio de Programación</td><td class="mono">10.100.96.0/24</td><td>96</td><td>1</td></tr>
  <tr><td>Red remota simulada (GNS3)</td><td class="mono">172.16.10.0/24</td><td>—</td><td><span class="badge b-info">propuesta</span></td></tr></table></div>
 <div class="card"><h3>Sondas <span class="btn p" style="padding:6px 12px;font-size:12px">+ Nueva sonda</span></h3>
  <table><tr><th>Equipo</th><th>Dirección IP</th><th>Sistema</th><th>Estado</th></tr>
  <tr><td>PC-LAB2-14</td><td class="mono">10.100.95.31</td><td>Windows 11</td><td><span class="badge b-ok">en línea</span></td></tr>
  <tr><td>PC-LAB1-03</td><td class="mono">10.100.95.12</td><td>Ubuntu 24.04</td><td><span class="badge b-ok">en línea</span></td></tr>
  <tr><td>PC-PROG-05</td><td class="mono">10.100.96.20</td><td>Windows 10</td><td><span class="badge b-ok">en línea</span></td></tr>
  <tr><td>VM-GNS3-01</td><td class="mono">172.16.10.5</td><td>Máquina virtual</td><td><span class="badge b-info">propuesta</span></td></tr></table></div>
</div>
<div class="card"><h3>Pruebas periódicas</h3>
 <div class="grid" style="grid-template-columns:repeat(4,1fr);margin-bottom:14px">
  <div><div class="l" style="color:var(--gris);font-size:12px;margin-bottom:6px">Sonda</div><div class="input">PC-LAB2-14 ▾</div></div>
  <div><div style="color:var(--gris);font-size:12px;margin-bottom:6px">Destinos</div><div class="input">gateway, escom.ipn.mx, 8.8.8.8</div></div>
  <div><div style="color:var(--gris);font-size:12px;margin-bottom:6px">Intervalo</div><div class="input">Cada 15 minutos ▾</div></div>
  <div><div style="color:var(--gris);font-size:12px;margin-bottom:6px">Opciones</div><div class="input">☑ Traceroute &nbsp; ☑ Captura tshark</div></div></div>
 <table><tr><th>Sonda</th><th>Destinos</th><th>Intervalo</th><th>Próxima ejecución</th><th>Estado</th></tr>
 <tr><td>PC-LAB2-14</td><td>gateway, escom.ipn.mx, 8.8.8.8</td><td>15 min</td><td>10:57</td><td><span class="badge b-ok">activa</span></td></tr>
 <tr><td>PC-LAB1-03</td><td>Servidor iPerf3 Lab 1 (TCP 5 s)</td><td>1 h</td><td>11:00</td><td><span class="badge b-ok">activa</span></td></tr>
 <tr><td>PC-PROG-05</td><td>gateway, escom.ipn.mx</td><td>30 min</td><td>—</td><td><span class="badge b-gris">pausada</span></td></tr></table>
 <div style="margin-top:14px"><span class="btn p">Guardar programación</span></div>
</div>""")

PANTALLAS = {
    "m1_panel_usuario": usuario,
    "m2_tecnico_inicio": inicio,
    "m3_comparacion_periodos": comparacion,
    "m4_analisis_paquetes": paquetes_pg,
    "m5_seguimiento": seguimiento,
    "m6_administracion": administracion,
}
for nombre, html in PANTALLAS.items():
    (SALIDA / f"{nombre}.html").write_text(html, encoding="utf-8")
    print("generado", nombre)
