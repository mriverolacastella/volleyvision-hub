"""
VolleyVision Hub V2 — Plataforma profesional de análisis de voleibol
"""

from io import BytesIO
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dvw_parser import DVWParser, stats_por_jugador, resumen_equipo, distribucion_ataque

st.set_page_config(page_title="VolleyVision Hub", page_icon="🏐", layout="wide", initial_sidebar_state="expanded")

# ──────────────────────────────────────────────────────────────
# TEMA VISUAL
# ──────────────────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Noche"

with st.sidebar:
    st.markdown("### ⚙️ VolleyVision Hub")
    st.session_state.theme_mode = st.radio("Modo", ["Noche", "Día"], horizontal=True)
    st.caption("V2 · creado por Marc Riverola Castellà")

DARK = st.session_state.theme_mode == "Noche"
P = {
    "bg": "#080d14" if DARK else "#f3f6fb",
    "bg2": "#101722" if DARK else "#ffffff",
    "bg3": "#172233" if DARK else "#e9eef7",
    "card": "#121a27" if DARK else "#ffffff",
    "border": "#2b3445" if DARK else "#d7deea",
    "text": "#f5f7fb" if DARK else "#101722",
    "muted": "#a7b0c0" if DARK else "#647083",
    "subtle": "#737f91" if DARK else "#8491a3",
    "accent1": "#f59e0b", "accent2": "#22d3ee", "accent3": "#fb7185",
    "home": "#22c55e", "away": "#f97316", "kill": "#22c55e", "error": "#ef4444", "neutral": "#94a3b8",
}

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"]{{font-family:Inter, sans-serif}}
.stApp,.main{{background:{P['bg']};color:{P['text']}}}
.main .block-container{{padding-top:1rem;max-width:1480px}}
section[data-testid="stSidebar"]{{background:{P['bg2']};border-right:1px solid {P['border']}}}
.hero{{padding:1.2rem 0 .6rem}}
.hero h1{{font-size:2.4rem;font-weight:900;color:{P['text']};letter-spacing:-1px;margin:0}}
.hero h1 span{{color:{P['accent1']}}}
.hero p{{color:{P['muted']};margin:.2rem 0 0}}
.score-bar,.pro-card,.kpi,.player-pill{{background:{P['card']};border:1px solid {P['border']};border-radius:20px;box-shadow:0 12px 32px rgba(0,0,0,.18)}}
.score-bar{{padding:1.5rem;text-align:center;margin-bottom:1.2rem;background:linear-gradient(135deg,{P['bg2']},{P['bg3']})}}
.score-teams{{display:flex;align-items:center;justify-content:center;gap:1.6rem;flex-wrap:wrap}}
.tname{{font-size:1.15rem;font-weight:900;min-width:170px}}
.home{{color:{P['home']}}}.away{{color:{P['away']}}}
.result{{font-size:2.9rem;font-weight:950;color:{P['text']};letter-spacing:.12em}}
.meta,.sets{{color:{P['muted']};font-size:.82rem}}
.kpi{{padding:1rem;text-align:center}}
.kpi .label{{color:{P['muted']};font-size:.68rem;text-transform:uppercase;letter-spacing:.7px;font-weight:900}}
.kpi .value{{font-size:1.65rem;font-weight:950;color:{P['text']};margin:.15rem 0}}
.kpi .detail{{font-size:.68rem;color:{P['subtle']}}}
.player-pill{{padding:1rem;min-height:120px}}
.player-pill .tag{{color:{P['accent1']};font-weight:900;font-size:.76rem;text-transform:uppercase;letter-spacing:.08em}}
.player-pill .name{{font-size:1.05rem;font-weight:900;color:{P['text']};margin:.35rem 0}}
.player-pill .num{{color:{P['muted']};font-size:.78rem}}
.stTabs [data-baseweb="tab"]{{background:{P['card']};color:{P['muted']};border:1px solid {P['border']};border-radius:12px 12px 0 0;padding:9px 16px;font-weight:800}}
.stTabs [aria-selected="true"]{{background:{P['accent1']} !important;color:#111827 !important;border-color:{P['accent1']} !important}}
div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div{{background:{P['card']};border-color:{P['border']};border-radius:12px;color:{P['text']}}}
.tactic-title{{text-align:center;font-weight:950;color:{P['muted']};letter-spacing:.08em;margin:1rem 0}}
footer{{text-align:center;padding:1.4rem;color:{P['muted']};font-size:.72rem;border-top:1px solid {P['border']};margin-top:2rem}}
.phase-help{{background:{P['card']};border:1px solid {P['border']};border-radius:14px;padding:.75rem 1rem;color:{P['muted']};font-size:.82rem;margin:.4rem 0 1rem}}
.rotation-card{{background:{P['card']};border:1px solid {P['border']};border-radius:18px;padding:1rem;box-shadow:0 10px 28px rgba(0,0,0,.14)}}
.rotation-title{{font-weight:950;color:{P['text']};margin-bottom:.4rem}}
.rotation-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:.7rem}}
.rotation-cell{{border:1px solid {P['border']};border-radius:12px;padding:.7rem;text-align:center;background:{P['bg2']};font-weight:900}}
.rotation-badge{{display:inline-block;border-radius:999px;padding:.25rem .65rem;font-weight:950;background:{P['accent1']};color:#111827;margin-top:.35rem}}
.pro-table-wrap{{border:1px solid {P['border']};border-radius:18px;overflow:auto;box-shadow:0 12px 34px rgba(0,0,0,.16);margin:.45rem 0 1.1rem;background:{P['card']};max-height:520px}}
table.pro-table{{width:100%;border-collapse:separate;border-spacing:0;font-size:.84rem;color:{P['text']}}}
table.pro-table thead th{{position:sticky;top:0;z-index:2;background:linear-gradient(135deg,{P['bg2']},{P['bg3']});color:{P['muted']};font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;font-weight:950;padding:.78rem .85rem;border-bottom:1px solid {P['border']};text-align:left;white-space:nowrap}}
table.pro-table tbody td{{padding:.68rem .85rem;border-bottom:1px solid {P['border']};white-space:nowrap}}
table.pro-table tbody tr:nth-child(even){{background:{P['bg2']}}}
table.pro-table tbody tr:hover{{background:rgba(245,158,11,.14)}}
table.pro-table td.num{{font-variant-numeric:tabular-nums;text-align:right;font-weight:800}}
.table-caption{{color:{P['muted']};font-size:.75rem;margin:.25rem 0 .25rem;font-weight:700}}
.manual-card{{background:{P['card']};border:1px solid {P['border']};border-radius:18px;padding:1rem 1.15rem;margin:.75rem 0;box-shadow:0 10px 26px rgba(0,0,0,.12)}}
.manual-card h3{{margin:.1rem 0 .4rem;font-size:1.05rem;color:{P['text']}}}
.manual-card p,.manual-card li{{color:{P['muted']};font-size:.9rem;line-height:1.45}}
.insight-card{{background:linear-gradient(135deg,{P['card']},{P['bg3']});border:1px solid {P['border']};border-radius:18px;padding:1rem;min-height:115px}}
.insight-card .big{{font-size:1.85rem;font-weight:950;color:{P['accent1']};line-height:1.1}}
.insight-card .label{{font-size:.74rem;text-transform:uppercase;letter-spacing:.08em;color:{P['muted']};font-weight:900}}
.insight-card .note{{font-size:.8rem;color:{P['subtle']};margin-top:.35rem}}

/* ── Rediseño PRO V2.1 ───────────────────────────────────── */
.block-container{{padding-left:2.2rem!important;padding-right:2.2rem!important}}
.stButton>button{{border-radius:14px!important;font-weight:900!important;border:1px solid {P['border']}!important;box-shadow:0 10px 24px rgba(0,0,0,.12)!important}}
.stDownloadButton>button{{border-radius:14px!important;font-weight:900!important}}
.upload-panel{{background:linear-gradient(135deg,{P['card']},{P['bg3']});border:1px solid {P['border']};border-radius:26px;padding:1.35rem 1.5rem;margin:1rem 0 1.2rem;box-shadow:0 20px 48px rgba(0,0,0,.18)}}
.upload-panel h2{{margin:0 0 .35rem;color:{P['text']};font-size:1.55rem;font-weight:950;letter-spacing:-.03em}}
.upload-panel p{{margin:.2rem 0;color:{P['muted']};font-size:.95rem}}
.quick-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;margin:1rem 0}}
.quick-card{{background:{P['bg2']};border:1px solid {P['border']};border-radius:18px;padding:.9rem;min-height:92px}}
.quick-card b{{display:block;color:{P['accent1']};font-size:.82rem;text-transform:uppercase;letter-spacing:.07em;margin-bottom:.25rem}}
.quick-card span{{color:{P['muted']};font-size:.82rem;line-height:1.35}}
.match-report-title{{font-size:1.55rem;font-weight:950;color:{P['accent1']};margin:1.6rem 0 .8rem;letter-spacing:-.02em}}
.match-report-wrap{{border:1px solid {P['border']};border-radius:22px;overflow:auto;margin:.6rem 0 1.8rem;background:{P['card']};box-shadow:0 18px 46px rgba(0,0,0,.22)}}
table.match-report{{width:100%;border-collapse:separate;border-spacing:0;font-size:.78rem;color:{P['text']};min-width:1280px}}
table.match-report th{{background:linear-gradient(180deg,{P['bg3']},{P['bg2']});color:{P['muted']};text-transform:uppercase;font-weight:950;letter-spacing:.05em;padding:.72rem .6rem;border-bottom:1px solid {P['border']};border-right:1px solid {P['border']};text-align:center;position:sticky;top:0;z-index:2}}
table.match-report td{{padding:.62rem .6rem;border-bottom:1px solid {P['border']};border-right:1px solid {P['border']};text-align:center;font-weight:760;background:{P['card']}}}
table.match-report tbody tr:nth-child(even) td{{background:{P['bg2']}}}
table.match-report td.name{{text-align:left;font-weight:950;max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;background:{P['bg2']}}}
table.match-report td.good{{background:rgba(34,197,94,.28)!important;color:{P['text']}}}
table.match-report td.bad{{background:rgba(239,68,68,.30)!important;color:{P['text']}}}
table.match-report tr.total td{{background:{P['bg3']}!important;font-weight:950;color:{P['text']}}}
@media(max-width:900px){{.quick-grid{{grid-template-columns:1fr 1fr}}.block-container{{padding-left:1rem!important;padding-right:1rem!important}}}}

/* ── V2.2 professional layout fixes ───────────────────────── */
.main .block-container{{max-width:1600px!important;padding-top:1.4rem!important;}}
section.main > div{{overflow:visible!important;}}
.stTabs [data-baseweb="tab-list"]{{gap:.35rem;flex-wrap:wrap;}}
.stTabs [data-baseweb="tab-panel"]{{padding-top:1.15rem;}}
.pro-section{{background:linear-gradient(135deg,rgba(255,255,255,.025),rgba(255,255,255,.01));border:1px solid {P['border']};border-radius:24px;padding:1.15rem;margin:1rem 0 1.35rem;box-shadow:0 16px 42px rgba(0,0,0,.14);clear:both;overflow:visible;}}
.pro-section h3,.pro-section h4{{margin-top:.2rem!important;}}
.compact-metrics{{display:grid;grid-template-columns:repeat(10,minmax(84px,1fr));gap:.55rem;margin:.7rem 0 1rem;}}
.metric-mini{{background:{P['card']};border:1px solid {P['border']};border-radius:16px;padding:.75rem;text-align:center;min-height:76px;box-shadow:0 10px 24px rgba(0,0,0,.10)}}
.metric-mini .m-label{{color:{P['muted']};font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:950}}.metric-mini .m-value{{color:{P['text']};font-size:1.35rem;font-weight:950;margin-top:.15rem}}
.mp-header{{background:linear-gradient(135deg,{P['card']},{P['bg3']});border:1px solid {P['border']};border-radius:26px;padding:1.2rem 1.35rem;margin:.6rem 0 1.25rem;}}
.mp-header h1{{font-size:2rem!important;line-height:1.08;margin:0 0 .35rem!important;letter-spacing:-.04em}}.mp-header p{{color:{P['muted']};margin:0;font-weight:750}}
.mp-card-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.85rem;margin:.85rem 0 1.3rem;align-items:stretch;}}
.mp-print{{background:{P['card']};border:1px solid {P['border']};border-radius:22px;padding:1.15rem 1.25rem;margin:.85rem 0;}}
.mp-print h3{{margin:.1rem 0 .8rem;font-size:1.25rem}}.mp-print li{{margin:.38rem 0;color:{P['text']};line-height:1.35}}
.volley-panel{{background:{P['card']};border:1px solid {P['border']};border-radius:22px;padding:1rem;box-shadow:0 14px 36px rgba(0,0,0,.16);min-height:420px;overflow:hidden;}}
.volley-panel-title{{font-weight:950;color:{P['text']};margin:.1rem 0 .55rem;font-size:1.05rem;}}
@media(max-width:1200px){{.compact-metrics{{grid-template-columns:repeat(5,1fr)}}.mp-card-grid{{grid-template-columns:1fr 1fr}}}}
@media(max-width:760px){{.compact-metrics{{grid-template-columns:repeat(2,1fr)}}.mp-card-grid{{grid-template-columns:1fr}}.main .block-container{{padding-left:.75rem!important;padding-right:.75rem!important}}}}

</style>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────
for k, v in {"matches": [], "view": "landing", "active_match": 0}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# HELPERS VISUALES
# ──────────────────────────────────────────────────────────────
def kpi(label, value, detail=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="detail">{detail}</div></div>', unsafe_allow_html=True)



def format_table_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra columnas para que las evaluaciones se vean con símbolos DataVolley."""
    if df is None or df.empty:
        return df
    rename = {
        "Posicion": "Posición",
        "AT K": "AT #", "AT Err": "AT =",
        "SQ Ace": "SQ #", "SQ Err": "SQ =",
        "REC Pos": "REC #+!", "REC Perf": "REC #", "REC Err": "REC =",
        "BLQ K": "BLQ #", "BLQ Err": "BLQ =",
        "DEF Pos": "DEF #+!", "DEF Err": "DEF =",
        "perfectas": "#", "positivas": "#+!", "errores": "=",
        "Kills": "#", "Errores": "=", "errores": "=", "errors": "=", "aces": "#", "Aces": "#",
        "errores_saque": "=", "Err": "=", "Error": "=",
        "Perf%": "#%", "REC+%": "#+!%", "Eff%": "Eff%",
        "eval_code": "Eval.", "recepcion_eval": "Recepción", "recepcion_zona": "Zona recepción",
        "origen": "Origen", "destino": "Destino", "jugador": "Jugador", "total": "Total",
    }
    return df.rename(columns={k:v for k,v in rename.items() if k in df.columns})

def score_bar(data):
    h, a = data["home_team"]["name"], data["away_team"]["name"]
    sets = data.get("sets", [])
    hs = sum(1 for s in sets if s.get("home_score",0) > s.get("away_score",0))
    aws = sum(1 for s in sets if s.get("away_score",0) > s.get("home_score",0))
    det = " | ".join(f"{s['home_score']}-{s['away_score']}" for s in sets) or "Acumulado"
    meta = f"{data.get('match',{}).get('date','')} · {data.get('match',{}).get('league','')}".strip(" ·")
    st.markdown(f'''<div class="score-bar"><div class="meta">{meta}</div><div class="score-teams"><div class="tname home">{h}</div><div class="result">{hs} - {aws}</div><div class="tname away">{a}</div></div><div class="sets">Sets: {det}</div></div>''', unsafe_allow_html=True)

def plotly_defaults(fig, height=380):
    fig.update_layout(height=height, template="plotly_dark" if DARK else "plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", size=12, color=P["text"]), margin=dict(t=45,b=45,l=70,r=25), legend=dict(orientation="h", y=1.08, x=.5, xanchor="center"))
    return fig

def pro_table(df: pd.DataFrame, height: int = 420, caption: str = ""):
    """Tabla HTML con look profesional, cabecera fija y números alineados.
    Para DataFrames muy grandes sigue siendo desplazable dentro del contenedor.
    """
    if df is None or df.empty:
        st.info("Sin datos para mostrar con estos filtros.")
        return
    view = format_table_labels(df).copy()
    # Limpieza visual: redondeo de decimales y sustitución de NaN
    for col in view.select_dtypes(include=["float", "float64"]).columns:
        view[col] = view[col].round(1)
    view = view.fillna("")
    num_cols = set(view.select_dtypes(include=["number", "int64", "float64"]).columns)
    html = view.to_html(index=False, classes="pro-table", border=0, escape=True)
    # Añadimos clase num a celdas numéricas mediante una transformación ligera sobre el HTML.
    # Pandas no permite clases por columna de forma simple sin Styler, así que dejamos CSS general y wrapper.
    cap = f'<div class="table-caption">{caption}</div>' if caption else ""
    st.markdown(f"{cap}<div class='pro-table-wrap' style='max-height:{height}px'>{html}</div>", unsafe_allow_html=True)

ZONE_POS = {
    "Z4": (1, 3), "Z3": (2, 3), "Z2": (3, 3),
    "Z7": (1, 2), "Z8": (2, 2), "Z9": (3, 2),
    "Z5": (1, 1), "Z6": (2, 1), "Z1": (3, 1),
}

def court_svg(zone_data: dict, title="", value_suffix=""):
    max_val = max(zone_data.values()) if zone_data else 1
    cells = []
    labels = [("Z4","ZONA 4"),("Z3","ZONA 3"),("Z2","ZONA 2"),("Z7","ZONA 7"),("Z8","ZONA 8"),("Z9","ZONA 9"),("Z5","ZONA 5"),("Z6","ZONA 6"),("Z1","ZONA 1")]
    for z, lab in labels:
        col, row = ZONE_POS[z]
        x, y = 30 + (col-1)*110, 25 + (3-row)*70
        h = 48 if z in ("Z7","Z8","Z9") else 68
        val = int(zone_data.get(z, 0))
        inten = val / max(max_val, 1)
        fill = P["accent1"] if val else ("#342617" if DARK else "#fff4dd")
        opacity = .35 + inten*.65 if val else .55
        txt = "#111827" if val else P["muted"]
        cells.append(f'''<rect x="{x}" y="{y}" width="100" height="{h}" rx="10" fill="{fill}" opacity="{opacity}" stroke="{P['border']}"/><text x="{x+50}" y="{y+20}" text-anchor="middle" fill="{txt}" font-size="11" font-weight="900">{lab}</text><text x="{x+50}" y="{y+47}" text-anchor="middle" fill="{txt}" font-size="22" font-weight="950">{val}{value_suffix}</text>''')
    return f'''<svg viewBox="0 0 380 255" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:520px"><rect width="380" height="255" rx="18" fill="{P['bg2']}" stroke="{P['border']}"/><line x1="25" y1="96" x2="355" y2="96" stroke="{P['border']}" stroke-dasharray="5 5"/><line x1="25" y1="166" x2="355" y2="166" stroke="{P['border']}" stroke-dasharray="5 5"/>{''.join(cells)}<text x="190" y="244" text-anchor="middle" fill="{P['muted']}" font-size="10">{title}</text></svg>'''

def _dv_zone_xy(zone: str, side: str = "target", skill: str = "A"):
    """Coordenadas DataVolley simplificadas para dibujar direcciones.
    side='source' sitúa el origen en nuestro campo; side='target' sitúa destino en campo rival.
    En saque el origen usa las zonas de fondo 1,9,6,7,5 del manual DV.
    """
    z = str(zone).replace("Z", "").strip()
    # X: izquierda -> derecha desde la perspectiva del equipo que ejecuta
    x_map = {"4": 1.0, "7": 1.0, "5": 1.0, "3": 2.0, "8": 2.0, "6": 2.0, "2": 3.0, "9": 3.0, "1": 3.0}
    # destino en campo rival, red arriba, fondo arriba
    y_target = {"4": 4.65, "3": 4.65, "2": 4.65, "7": 5.25, "8": 5.25, "9": 5.25, "5": 5.95, "6": 5.95, "1": 5.95}
    # origen en campo propio, red abajo, fondo abajo
    y_source = {"4": 2.35, "3": 2.35, "2": 2.35, "7": 1.75, "8": 1.75, "9": 1.75, "5": 1.05, "6": 1.05, "1": 1.05}
    # zonas de inicio de saque DataVolley: 1,9,6,7,5 detrás de línea de fondo
    serve_start_x = {"5": .75, "7": 1.35, "6": 2.0, "9": 2.65, "1": 3.25}
    if skill == "S" and side == "source":
        return serve_start_x.get(z, x_map.get(z, 2.0)), .35
    return x_map.get(z, 2.0), (y_source if side == "source" else y_target).get(z, 1.0 if side == "source" else 5.8)


def _base_direction_court(title: str, skill: str = "A"):
    """Campo vertical profesional: origen abajo, destino arriba, red en medio."""
    fig = go.Figure()
    bg = "#f8fafc" if not DARK else "#111827"
    court = "#f59e0b" if not DARK else "#d97706"
    line = "#ffffff"
    muted = "#334155" if not DARK else "#cbd5e1"
    # field background
    fig.add_shape(type="rect", x0=.25, x1=3.75, y0=.25, y1=6.75, line=dict(color=P["border"], width=2), fillcolor=bg, layer="below")
    # our court and rival court
    fig.add_shape(type="rect", x0=.55, x1=3.45, y0=.65, y1=3.15, line=dict(color=line, width=3), fillcolor=court, opacity=.92, layer="below")
    fig.add_shape(type="rect", x0=.55, x1=3.45, y0=3.85, y1=6.35, line=dict(color=line, width=3), fillcolor=court, opacity=.92, layer="below")
    # net
    fig.add_shape(type="line", x0=.42, x1=3.58, y0=3.5, y1=3.5, line=dict(color="#111827" if not DARK else "#f8fafc", width=5))
    fig.add_shape(type="line", x0=.42, x1=3.58, y0=3.5, y1=3.5, line=dict(color=line, width=1, dash="dot"))
    # attack lines and grid
    for y in [1.48, 2.32, 4.68, 5.52]:
        fig.add_shape(type="line", x0=.55, x1=3.45, y0=y, y1=y, line=dict(color=line, width=1.4, dash="dot"), layer="below")
    for x in [1.52, 2.48]:
        fig.add_shape(type="line", x0=x, x1=x, y0=.65, y1=3.15, line=dict(color=line, width=1, dash="dot"), layer="below")
        fig.add_shape(type="line", x0=x, x1=x, y0=3.85, y1=6.35, line=dict(color=line, width=1, dash="dot"), layer="below")
    fig.add_annotation(x=2, y=.38, text="ORIGEN", showarrow=False, font=dict(size=11, color=muted, family="Inter"))
    fig.add_annotation(x=2, y=6.62, text="DESTINO", showarrow=False, font=dict(size=11, color=muted, family="Inter"))
    for z in ["Z4","Z3","Z2","Z7","Z8","Z9","Z5","Z6","Z1"]:
        xt, yt = _dv_zone_xy(z, "target", skill)
        xs, ys = _dv_zone_xy(z, "source", "A")
        fig.add_annotation(x=xt, y=yt, text=z, showarrow=False, font=dict(size=12, color="#111827", family="Inter Black"), bgcolor="rgba(255,255,255,.65)", borderpad=2)
        fig.add_annotation(x=xs, y=ys, text=z, showarrow=False, font=dict(size=12, color="#111827", family="Inter Black"), bgcolor="rgba(255,255,255,.65)", borderpad=2)
    if skill == "S":
        for z in ["Z5","Z7","Z6","Z9","Z1"]:
            xs, ys = _dv_zone_xy(z, "source", "S")
            fig.add_annotation(x=xs, y=ys, text=f"S{z[-1]}", showarrow=False, font=dict(size=11, color="#111827"), bgcolor="#fef3c7", borderpad=2)
    fig.update_xaxes(range=[.15,3.85], visible=False)
    fig.update_yaxes(range=[.1,6.9], visible=False, scaleanchor="x")
    fig.update_layout(title=dict(text=title, x=.02, font=dict(size=17, color=P["text"])), height=560, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=50,b=10,l=10,r=10))
    return fig


def direction_chart(df, title, value_col="total", skill="A", empty_message: str = "Selecciona un jugador para ver sus direcciones."):
    fig = _base_direction_court(title, skill=skill)
    if df is None or df.empty:
        fig.add_annotation(x=2, y=3.5, text=empty_message, showarrow=False, font=dict(size=14, color=P["muted"]), bgcolor="rgba(15,23,42,.55)" if DARK else "rgba(255,255,255,.85)", bordercolor=P["border"], borderpad=10)
        st.plotly_chart(fig, use_container_width=True)
        return
    view = df.copy()
    view = view[view["origen"].astype(str).str.startswith("Z") & view["destino"].astype(str).str.startswith("Z")]
    if view.empty:
        fig.add_annotation(x=2, y=3.5, text="No hay origen/destino suficiente para dibujar flechas.", showarrow=False, font=dict(size=14, color=P["muted"]), bgcolor="rgba(15,23,42,.55)" if DARK else "rgba(255,255,255,.85)", borderpad=10)
        st.plotly_chart(fig, use_container_width=True)
        return
    view = view.sort_values(value_col if value_col in view.columns else "total", ascending=False).head(10)
    max_n = max(int(view[value_col].max() if value_col in view else view["total"].max()), 1)
    for _, r in view.iterrows():
        x0, y0 = _dv_zone_xy(r.get("origen"), "source", skill)
        x1, y1 = _dv_zone_xy(r.get("destino"), "target", skill)
        n = int(r.get(value_col, r.get("total", 1)))
        width = max(2, min(8, 1.5 + 6*n/max_n))
        color = "#0f172a" if not DARK else "#f8fafc"
        if "Eff%" in r and pd.notna(r.get("Eff%")):
            color = "#22c55e" if float(r.get("Eff%")) >= 35 else ("#ef4444" if float(r.get("Eff%")) < 0 else "#f59e0b")
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=width, arrowcolor=color, text=f"{n}", font=dict(color="#fff", size=10), bgcolor="rgba(15,23,42,.85)", borderpad=2)
    st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# CONTEXTO TÁCTICO APROXIMADO
# ──────────────────────────────────────────────────────────────
def _plays_with_context(data: dict) -> pd.DataFrame:
    plays = data.get("plays", pd.DataFrame()).copy()
    if plays.empty:
        return plays

    # Orden estable para poder buscar la colocación inmediatamente anterior al ataque.
    plays["_order"] = range(len(plays))
    for c, val in {
        "fase": "Total",
        "fase_detalle": "",
        "recepcion_eval": "Sin recepción",
        "recepcion_zona": "Sin zona",
        "colocador": "Sin colocador",
        "rotacion": "Todas",
        "saque_origen": "Sin zona de saque",
        "saque_tipo": "Sin tipo",
    }.items():
        plays[c] = val

    # En recepción la zona útil para análisis es donde se recibe/llega la pelota (zona_fin).
    # En saque y ataque usamos origen → destino.
    plays["origen"] = plays.apply(
        lambda r: f"Z{r['zona_fin']}" if r.get("skill_code") == "R" and str(r.get("zona_fin", "")).strip()
        else (f"Z{r['zona_inicio']}" if str(r.get("zona_inicio", "")).strip() else "Sin zona"), axis=1
    )
    plays["destino"] = plays.apply(
        lambda r: f"Z{r['zona_fin']}" if str(r.get("zona_fin", "")).strip() else "Sin zona", axis=1
    )

    # Definición táctica usada:
    # K1 = acciones del equipo que recibe el saque: recepción → colocación → ataque.
    # K2 = acciones del equipo que saca/defiende: saque, defensa, bloqueo y contraataque.
    for (setn, rally), rally_grp in plays.groupby(["set", "rally"], sort=False):
        serves = rally_grp[rally_grp["skill_code"] == "S"].sort_values("_order")
        serve_context = {}
        if not serves.empty:
            for _, sv in serves.iterrows():
                receiver = "away" if sv.get("equipo") == "home" else "home"
                serve_context[receiver] = {
                    "saque_origen": f"Z{sv.get('zona_inicio')}" if str(sv.get("zona_inicio", "")).strip() else "Sin zona de saque",
                    "saque_tipo": sv.get("tipo", "Sin tipo") or "Sin tipo",
                }
        for equipo, grp in rally_grp.groupby("equipo", sort=False):
            grp = grp.sort_values("_order")
            has_reception = (grp["skill_code"] == "R").any()
            has_serve = (grp["skill_code"] == "S").any()
            fase = "K1" if has_reception else "K2"
            detalle = "K1 · recepción" if has_reception else ("K2 · saque" if has_serve else "K2 · defensa/contraataque")

            recs = grp[grp["skill_code"] == "R"]
            if not recs.empty:
                rec_eval = recs.iloc[0]["eval_code"] or "Sin recepción"
                rec_zone = f"Z{recs.iloc[0]['zona_fin']}" if str(recs.iloc[0].get("zona_fin", "")).strip() else "Sin zona"
            else:
                rec_eval = "Sin recepción"
                rec_zone = "Sin zona"

            rv = grp.iloc[0].get("rotation", None)
            if pd.notna(rv) and str(rv).strip() not in ("", "None"):
                try:
                    rot = f"P{int(rv)}"
                except Exception:
                    rot = f"P{rv}"
            else:
                base_score = int(grp.iloc[0].get("home_score",0) if equipo == "home" else grp.iloc[0].get("away_score",0) or 0)
                rot = f"P{(base_score % 6) + 1}"

            # Base contextual para todas las acciones del equipo en ese rally.
            sc = serve_context.get(equipo, {"saque_origen": "Sin zona de saque", "saque_tipo": "Sin tipo"})
            plays.loc[grp.index, ["fase","fase_detalle","recepcion_eval","recepcion_zona","rotacion","saque_origen","saque_tipo"]] = [fase, detalle, rec_eval, rec_zone, rot, sc["saque_origen"], sc["saque_tipo"]]

            # Colocador por ataque: buscamos la última acción E anterior dentro del mismo rally/equipo.
            last_setter = "Sin colocador"
            for idx, row in grp.iterrows():
                if row.get("skill_code") == "E":
                    last_setter = row.get("jugador", "Sin colocador") or "Sin colocador"
                    plays.loc[idx, "colocador"] = last_setter
                elif row.get("skill_code") == "A":
                    plays.loc[idx, "colocador"] = last_setter
                else:
                    plays.loc[idx, "colocador"] = last_setter

    return plays.drop(columns=["_order"], errors="ignore")

def _filter_df(df, col, value):
    if value in (None, "Todos", "Todas", "Total"): return df
    if col not in df.columns: return df
    return df[df[col] == value]

def filtered_context(data, key, team_default=None):
    plays = _plays_with_context(data)
    if plays.empty: return plays, ""
    teams = {data["home_team"]["name"]:"home", data["away_team"]["name"]:"away"}
    c1,c2,c3,c4 = st.columns([1.2, .9, .9, .9])
    with c1:
        team_label = st.selectbox("Equipo", list(teams.keys()), key=f"{key}_team", index=0)
    team_code = teams[team_label]
    df = plays[plays["equipo"] == team_code].copy()
    with c2:
        fase = st.selectbox("Fase", ["Total","K1","K2"], key=f"{key}_fase", help="K1 = tu equipo recibe. K2 = tu equipo saca/defiende/contraataca.")
    with c3:
        rot = st.selectbox("Rotación", ["Todas"] + sorted([x for x in df["rotacion"].dropna().unique() if x != "Todas"]), key=f"{key}_rot")
    with c4:
        desde_punto = st.selectbox("Desde punto", list(range(0, 31)), index=0, key=f"{key}_from_point", help="Filtra las acciones a partir del punto del equipo seleccionado. Ejemplo: desde 18 para analizar money time.")
    df = _filter_df(_filter_df(df, "fase", fase), "rotacion", rot)
    score_col = "home_score" if team_code == "home" else "away_score"
    if score_col in df.columns and desde_punto > 0:
        df = df[pd.to_numeric(df[score_col], errors="coerce").fillna(0) >= desde_punto]
        st.caption(f"Filtro activo: {team_label} desde el punto {desde_punto}.")
    return df, team_label

# ──────────────────────────────────────────────────────────────
# RESUMEN
# ──────────────────────────────────────────────────────────────
def horizontal_mirror_comparison(data):
    hn, an = data["home_team"]["name"], data["away_team"]["name"]
    s = resumen_equipo(data); h, a = s.get("home",{}), s.get("away",{})
    metrics = [("Puntos","puntos"),("Ataque Eff%","att_eff"),("Ataque Kill%","att_kill_pct"),("Recepción #+!%","rec_pos_pct"),("Aces","srv_aces"),("Saque =","srv_errors"),("Bloqueos","blk_kills")]
    labels = [m[0] for m in metrics]; hv = [h.get(m[1],0) for m in metrics]; av = [-a.get(m[1],0) for m in metrics]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=av, orientation="h", name=an, marker_color=P["away"], text=[abs(x) for x in av], textposition="outside"))
    fig.add_trace(go.Bar(y=labels, x=hv, orientation="h", name=hn, marker_color=P["home"], text=hv, textposition="outside"))
    maxx = max([abs(x) for x in av] + hv + [10]) * 1.25
    fig.update_layout(barmode="relative", title="Comparativa principal · local derecha / visitante izquierda", xaxis=dict(range=[-maxx,maxx], tickvals=[-maxx/2,0,maxx/2], ticktext=[an,"0",hn]), yaxis=dict(autorange="reversed"))
    plotly_defaults(fig, 440)
    st.plotly_chart(fig, use_container_width=True)

def tabellino(data):
    rows = []
    s = resumen_equipo(data)
    metrics = [("Puntos", "puntos"), ("Ataques #", "att_kills"), ("Ataques =", "att_errors"), ("Ataques Tot", "att_total"), ("AT Eff%", "att_eff"), ("AT Kill%", "att_kill_pct"), ("Saque #", "srv_aces"), ("Saque =", "srv_errors"), ("Recepción #+!%", "rec_pos_pct"), ("Recepción #%", "rec_perf_pct"), ("Bloqueo #", "blk_kills")]
    for label, key in metrics:
        rows.append({"Métrica": label, data["home_team"]["name"]: s["home"].get(key,0), data["away_team"]["name"]: s["away"].get(key,0)})
    st.markdown("#### Tabellino total del partido")
    pro_table(pd.DataFrame(rows), height=320, caption='Tabellino total DataVolley')


def _pct(num, den):
    return round(num / max(den, 1) * 100, 1)

def _team_match_report(stats: pd.DataFrame, team: str):
    t = stats[stats["Equipo"] == team].copy()
    if t.empty: return
    t["AT /"] = 0
    cols = [("Dorsal","#"),("Jugador","Jugador"),("Pts","PTS<br>Total"),("Balance","PTS<br>W-L"),("SQ Tot","SAQUE<br>Tot"),("SQ Err","SAQUE<br>="),("SQ Ace","SAQUE<br>#"),("REC Tot","RECEP<br>Tot"),("REC Err","RECEP<br>="),("REC%","RECEP<br>#+!%"),("REC Perf%","RECEP<br>#%"),("AT Tot","ATAQUE<br>Tot"),("AT Err","ATAQUE<br>="),("AT /","ATAQUE<br>/"),("AT K","ATAQUE<br>#"),("AT Kill%","ATAQUE<br>#%"),("AT Eff%","ATAQUE<br>Eff%"),("BLQ K","BLOQUEO<br>#")]
    header=''.join(f'<th>{h}</th>' for _,h in cols)
    rows=''
    for _,r in t.sort_values(["Pts","Balance"], ascending=False).iterrows():
        rows+='<tr>'
        for c,h in cols:
            val=r.get(c,'')
            if isinstance(val,float): val=f"{val:.1f}%" if '%' in h else f"{val:.1f}"
            cls=''
            try: x=float(str(val).replace('%',''))
            except: x=0
            if c in ['Pts','Balance','SQ Ace','REC%','REC Perf%','AT K','AT Kill%','AT Eff%','BLQ K'] and x>0: cls='good'
            if c in ['SQ Err','REC Err','AT Err','AT /'] and x>0: cls='bad'
            rows += f'<td class="{cls} name">{val}</td>' if c=='Jugador' else f'<td class="{cls}">{val}</td>'
        rows+='</tr>'
    total={'Dorsal':'','Jugador':'TOTAL EQUIPO','Pts':t['Pts'].sum(),'Balance':t['Balance'].sum(),'SQ Tot':t['SQ Tot'].sum(),'SQ Err':t['SQ Err'].sum(),'SQ Ace':t['SQ Ace'].sum(),'REC Tot':t['REC Tot'].sum(),'REC Err':t['REC Err'].sum(),'REC%':_pct(t['REC Pos'].sum(),t['REC Tot'].sum()),'REC Perf%':_pct(t['REC Perf'].sum(),t['REC Tot'].sum()),'AT Tot':t['AT Tot'].sum(),'AT Err':t['AT Err'].sum(),'AT /':0,'AT K':t['AT K'].sum(),'AT Kill%':_pct(t['AT K'].sum(),t['AT Tot'].sum()),'AT Eff%':round((t['AT K'].sum()-t['AT Err'].sum())/max(t['AT Tot'].sum(),1)*100,1),'BLQ K':t['BLQ K'].sum()}
    rows+='<tr class="total">'
    for c,h in cols:
        val=total.get(c,'')
        if isinstance(val,float): val=f"{val:.1f}%" if '%' in h else f"{val:.1f}"
        rows += f'<td class="name">{val}</td>' if c=='Jugador' else f'<td>{val}</td>'
    rows+='</tr>'
    st.markdown(f'<div class="match-report-title">{team}</div><div class="match-report-wrap"><table class="match-report"><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

def render_match_report(data):
    st.markdown("## Match Report")
    stats = stats_por_jugador(data)
    if stats.empty: st.info("Sin datos para Match Report"); return
    _team_match_report(stats, data["home_team"]["name"])
    _team_match_report(stats, data["away_team"]["name"])

def render_general(data):
    horizontal_mirror_comparison(data)
    render_match_report(data)
    render_players(data)
    set_rotation_summary(data)

def set_rotation_summary(data):
    plays = _plays_with_context(data)
    st.markdown("#### Rotaciones por set · saque/recepción")
    if plays.empty:
        st.info("Sin acciones para estimar rotaciones.")
        return
    detected_sets = sorted([int(x) for x in plays["set"].dropna().unique()])
    # Mostrar mínimo 3 y máximo 5 sets, aunque el parser solo haya detectado 1-2 marcadores.
    max_detected = max(detected_sets) if detected_sets else 1
    n_sets = min(5, max(3, max_detected))
    set_options = list(range(1, n_sets + 1))
    sel = st.radio("Set", set_options, format_func=lambda x: f"Set {x}", horizontal=True, key=f"rot_set_{id(data)}")
    sp = plays[plays["set"] == sel]
    if sp.empty:
        st.info(f"No hay acciones detectadas para el set {sel}. Se mantiene visible para partidos a 3-5 sets.")
    cols = st.columns(2)
    for i,(tc,nm) in enumerate([("home", data["home_team"]["name"]), ("away", data["away_team"]["name"]) ]):
        team = sp[sp["equipo"] == tc] if not sp.empty else pd.DataFrame()
        first = team.head(1)
        rot = first.iloc[0]["rotacion"] if not first.empty else "-"
        first_skill = first.iloc[0]["skill_code"] if not first.empty else ""
        estado = "Recepción" if first_skill == "R" else ("Saque" if first_skill == "S" else "Sin detectar")
        players = team[team["dorsal"] != 0].groupby(["dorsal","jugador"]).size().reset_index(name="n").sort_values("n", ascending=False).head(6) if not team.empty else pd.DataFrame()
        labels = []
        for _,r in players.iterrows():
            labels.append(f"#{int(r['dorsal'])}<br>{str(r['jugador'])[:11]}")
        while len(labels)<6: labels.append("-")
        # posición visual: red arriba, fondo abajo. Sin badge naranja P1.
        order = [labels[3], labels[2], labels[1], labels[4], labels[5], labels[0]]
        html = f'<div class="rotation-card"><div class="rotation-title">{nm}</div><div style="color:{P["muted"]};font-weight:800">Set {sel} · Rotación estimada: {rot} · {estado}</div><div class="rotation-grid">'
        for lab in order:
            html += f'<div class="rotation-cell">{lab}</div>'
        html += '</div><div style="font-size:.72rem;color:%s;margin-top:.5rem">Rotación leída del DVW cuando está disponible. Se muestran sets 1-3 mínimo y hasta 5.</div></div>' % P['muted']
        with cols[i]: st.markdown(html, unsafe_allow_html=True)
# ──────────────────────────────────────────────────────────────
# JUGADORES
# ──────────────────────────────────────────────────────────────
def player_score_table(stats):
    df = stats.copy()
    df["MVP Score"] = (df["Pts"]*2 + df["Balance"]*1.5 + df["AT Eff%"]*0.15 + df["REC%"]*0.08 + df["BLQ K"]*1.5 + df["SQ Ace"]*1.2 - df["Err"]*1.3).round(1)
    return df

def player_pill(title, row):
    if row is None or row.empty: return
    r = row.iloc[0] if isinstance(row, pd.DataFrame) else row
    st.markdown(f'''<div class="player-pill"><div class="tag">{title}</div><div class="name">#{int(r.get('Dorsal',0))} · {r.get('Jugador','')}</div><div class="num">{r.get('Equipo','')} · Pts {r.get('Pts',0)} · Balance {r.get('Balance',0)} · MVP {r.get('MVP Score',0)}</div></div>''', unsafe_allow_html=True)

def _roster_table(data, team_code: str) -> pd.DataFrame:
    df = data.get(f"{team_code}_players", pd.DataFrame())
    if df is None or df.empty:
        return pd.DataFrame(columns=["Dorsal", "Jugador", "Posición", "Líbero"])
    out = df.copy()
    out["Jugador"] = out.get("nombre_completo", out.get("nombre_corto", ""))
    out["Posición"] = out.get("posicion", "")
    out["Líbero"] = out.get("es_libero", False).map(lambda x: "Sí" if bool(x) else "")
    return out.rename(columns={"dorsal":"Dorsal"})[["Dorsal", "Jugador", "Posición", "Líbero"]].sort_values("Dorsal")


def render_players(data):
    stats = stats_por_jugador(data)
    if stats.empty:
        st.info("Sin datos de jugadores")
        return
    stats = player_score_table(stats)
    hn, an = data["home_team"]["name"], data["away_team"]["name"]
    st.markdown("#### Jugadores destacados")
    row1 = st.columns(3)
    with row1[0]: player_pill("MVP partido", stats.sort_values("MVP Score", ascending=False).head(1))
    with row1[1]: player_pill(f"MVP {hn}", stats[stats["Equipo"] == hn].sort_values("MVP Score", ascending=False).head(1))
    with row1[2]: player_pill(f"MVP {an}", stats[stats["Equipo"] == an].sort_values("MVP Score", ascending=False).head(1))
    for team in [hn, an]:
        st.markdown(f"##### Especialistas · {team}")
        tdf = stats[stats["Equipo"] == team]
        c = st.columns(4)
        with c[0]: player_pill("Máx. anotador", tdf.sort_values("Pts", ascending=False).head(1))
        with c[1]: player_pill("Máx. bloqueo", tdf.sort_values("BLQ K", ascending=False).head(1))
        with c[2]: player_pill("Mejor recepción", tdf[tdf["REC Tot"]>0].sort_values(["REC%","REC Tot"], ascending=False).head(1))
        with c[3]: player_pill("Mejor saque", tdf[tdf["SQ Tot"]>0].sort_values(["SQ Ace","SQ Eff%"], ascending=False).head(1))
    st.markdown("#### Plantillas")
    r1, r2 = st.columns(2)
    with r1:
        st.markdown(f"##### {hn}")
        pro_table(_roster_table(data, "home"), height=260, caption='Plantilla local')
    with r2:
        st.markdown(f"##### {an}")
        pro_table(_roster_table(data, "away"), height=260, caption='Plantilla visitante')
# ──────────────────────────────────────────────────────────────
# ATAQUE / SAQUE-RECEPCIÓN / DISTRIBUCIÓN
# ──────────────────────────────────────────────────────────────
def render_attack(data, key="att"):
    df, team_label = filtered_context(data, key)
    att_all = df[df["skill_code"] == "A"].copy()
    if att_all.empty:
        st.info("No hay ataques con estos filtros.")
        return
    c1, c2 = st.columns(2)
    attackers = sorted(att_all["jugador"].dropna().unique())
    with c1: player = st.selectbox("Atacante", ["Selecciona atacante"] + attackers, key=f"{key}_player")
    with c2: zone = st.selectbox("Zona origen", ["Todas"] + sorted([z for z in att_all["origen"].dropna().unique() if z != "Sin zona"]), key=f"{key}_zone")
    view = _filter_df(att_all, "origen", zone)
    if player != "Selecciona atacante": view = view[view["jugador"] == player]
    left, right = st.columns(2)
    with left:
        st.markdown("#### Eficiencia de ataque por zona")
        zg = view[view["origen"] != "Sin zona"].groupby("origen").agg(total=("skill_code","count"), **{"#":("eval_code", lambda x:(x=="#").sum()), "=":("eval_code", lambda x:(x=="=").sum()), "/":("eval_code", lambda x:x.isin(["/","-"]).sum())}).reset_index()
        if not zg.empty: zg["Eff%"] = ((zg["#"]-zg["="])/zg["total"].replace(0,1)*100).round(1)
        st.markdown(court_svg(dict(zip(zg["origen"], zg["Eff%"].fillna(0).astype(int))) if not zg.empty else {}, f"Eff% ataque · {team_label}", value_suffix="%"), unsafe_allow_html=True)
    with right:
        st.markdown("#### Direcciones de ataque")
        if player == "Selecciona atacante":
            direction_chart(pd.DataFrame(), "Direcciones de ataque", skill="A", empty_message="Selecciona un atacante para activar las flechas.")
            dirs = pd.DataFrame()
        else:
            dirs = view[(view["origen"]!="Sin zona") & (view["destino"]!="Sin zona")].groupby(["origen","destino"]).agg(total=("skill_code","count"), **{"#":("eval_code", lambda x:(x=="#").sum()), "=":("eval_code", lambda x:(x=="=").sum()), "/":("eval_code", lambda x:x.isin(["/","-"]).sum())}).reset_index()
            if not dirs.empty: dirs["Eff%"] = ((dirs["#"]-dirs["="])/dirs["total"].replace(0,1)*100).round(1)
            direction_chart(dirs, f"Direcciones · {player}", skill="A")
    st.markdown("#### Datos del ataque")
    if not zg.empty: pro_table(zg.sort_values("total", ascending=False), height=260, caption='Eficiencia por zona')
    if player != "Selecciona atacante" and not dirs.empty: pro_table(dirs.sort_values("total", ascending=False), height=300, caption='Direcciones de ataque')

def render_serve(data, key="srv"):
    df, team_label = filtered_context(data, key)
    srv_all = df[df["skill_code"] == "S"].copy()
    if srv_all.empty: st.info("Sin saques con estos filtros."); return
    c1,c2=st.columns(2); servers=sorted(srv_all["jugador"].dropna().unique())
    with c1: player=st.selectbox("Sacador", ["Selecciona sacador"]+servers, key=f"{key}_player")
    with c2: tipo=st.selectbox("Tipo de saque", ["Todos"]+sorted([x for x in srv_all["tipo"].dropna().unique() if x]), key=f"{key}_type")
    view=_filter_df(srv_all,"tipo",tipo)
    if player!="Selecciona sacador": view=view[view["jugador"]==player]
    left,right=st.columns(2)
    with left:
        st.markdown("#### Eficiencia de saque por zona")
        zg=view[view["origen"]!="Sin zona"].groupby("origen").agg(total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()),"=":("eval_code",lambda x:(x=="=").sum())}).reset_index()
        if not zg.empty: zg["Eff%"] = ((zg["#"]-zg["="])/zg["total"].replace(0,1)*100).round(1)
        st.markdown(court_svg(dict(zip(zg["origen"], zg["Eff%"].fillna(0).astype(int))) if not zg.empty else {}, f"Eff% saque · {team_label}", value_suffix="%"), unsafe_allow_html=True)
    with right:
        st.markdown("#### Direcciones de saque")
        if player=="Selecciona sacador":
            direction_chart(pd.DataFrame(), "Direcciones de saque", skill="S", empty_message="Selecciona un sacador para activar las flechas.")
            dirs=pd.DataFrame()
        else:
            dirs=view[(view["origen"]!="Sin zona")&(view["destino"]!="Sin zona")].groupby(["origen","destino","tipo"]).agg(total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()),"=":("eval_code",lambda x:(x=="=").sum())}).reset_index()
            if not dirs.empty: dirs["Eff%"] = ((dirs["#"]-dirs["="])/dirs["total"].replace(0,1)*100).round(1)
            direction_chart(dirs, f"Direcciones · {player}", skill="S")
    if not zg.empty: pro_table(zg.sort_values("total", ascending=False), height=260, caption='Eficiencia por zona de saque')
    if player!="Selecciona sacador" and not dirs.empty: pro_table(dirs.sort_values("total", ascending=False), height=300, caption='Direcciones de saque')

def _eval_counts(df: pd.DataFrame) -> dict:
    return {sym: int((df["eval_code"] == sym).sum()) for sym in ["#", "+", "!", "-", "/", "="]}

def _metric_strip(items):
    html = "<div class='compact-metrics'>"
    for label, value in items:
        html += f"<div class='metric-mini'><div class='m-label'>{label}</div><div class='m-value'>{value}</div></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def _reception_zone_summary(rec: pd.DataFrame, group_col: str = "origen") -> pd.DataFrame:
    if rec.empty:
        return pd.DataFrame()
    out = rec[rec[group_col] != "Sin zona"].groupby(group_col).agg(
        Total=("skill_code", "count"),
        **{"#": ("eval_code", lambda x:(x=="#").sum()), "+": ("eval_code", lambda x:(x=="+").sum()), "!": ("eval_code", lambda x:(x=="!").sum()), "-": ("eval_code", lambda x:(x=="-").sum()), "/": ("eval_code", lambda x:(x=="/").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}
    ).reset_index().rename(columns={group_col:"Zona"})
    if not out.empty:
        out["#%"] = (out["#"] / out["Total"].replace(0,1) * 100).round(1)
        out["#+!%"] = ((out["#"]+out["+"]+out["!"]) / out["Total"].replace(0,1) * 100).round(1)
        out["=%"] = (out["="] / out["Total"].replace(0,1) * 100).round(1)
        out["Eff%"] = (((out["#"]+out["+"]+out["!"]) - out["="]) / out["Total"].replace(0,1) * 100).round(1)
    return out

def render_reception(data, key="rec"):
    df, team_label = filtered_context(data, key)
    rec = df[df["skill_code"] == "R"].copy()
    if rec.empty:
        st.info("Sin recepciones con estos filtros."); return
    c1,c2 = st.columns(2)
    with c1:
        receptor = st.selectbox("Receptor", ["Todos"] + sorted(rec["jugador"].dropna().unique()), key=f"{key}_player")
    with c2:
        tipo_saque = st.selectbox("Tipo de saque recibido", ["Todos"] + sorted([x for x in rec["saque_tipo"].dropna().unique() if x and x != "Sin tipo"]), key=f"{key}_type")
    rec = _filter_df(rec, "jugador", receptor)
    rec = _filter_df(rec, "saque_tipo", tipo_saque)
    if rec.empty:
        st.info("No hay recepciones con esta selección."); return
    cnt = _eval_counts(rec); total = len(rec)
    pos = cnt["#"] + cnt["+"] + cnt["!"]
    _metric_strip([
        ("Recepciones", total), ("#", cnt["#"]), ("+", cnt["+"]), ("!", cnt["!"]), ("-", cnt["-"]), ("/", cnt["/"]), ("=", cnt["="]), ("#%", f"{round(cnt['#']/max(total,1)*100,1)}%"), ("#+!%", f"{round(pos/max(total,1)*100,1)}%"), ("Eff%", f"{round((pos-cnt['='])/max(total,1)*100,1)}%")
    ])
    st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
    st.markdown("#### Recepción por tipo de saque")
    type_col = st.columns(3)
    labels = ["Potencia / salto", "Flotante / salto", "Saque suelo / otros"]
    types = list(sorted([x for x in rec["saque_tipo"].dropna().unique() if x and x != "Sin tipo"]))
    buckets = []
    for name in labels:
        if "pot" in name.lower():
            buckets.append((name, rec[rec["saque_tipo"].astype(str).str.lower().str.contains("pot|jump|salto|q", regex=True, na=False)]))
        elif "flot" in name.lower():
            buckets.append((name, rec[rec["saque_tipo"].astype(str).str.lower().str.contains("float|flot|tenso|h", regex=True, na=False)]))
        else:
            used = pd.concat([b[1] for b in buckets]) if buckets else pd.DataFrame()
            buckets.append((name, rec.drop(used.index, errors="ignore")))
    for col, (label, subset) in zip(type_col, buckets):
        c = _eval_counts(subset) if not subset.empty else {sym:0 for sym in ["#","+","!","-","/","="]}
        t = len(subset); p = c["#"]+c["+"]+c["!"]
        with col:
            st.markdown(f"<div class='insight-card'><div class='label'>{label}</div><div class='big'>{t}</div><div class='note'># {c['#']} · + {c['+']} · ! {c['!']} · - {c['-']} · / {c['/']} · = {c['=']}<br>#+! {round(p/max(t,1)*100,1)}% · Eff {round((p-c['='])/max(t,1)*100,1)}%</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    zones = _reception_zone_summary(rec, "origen")
    left,right = st.columns([1,1.25])
    with left:
        st.markdown("<div class='volley-panel'><div class='volley-panel-title'>Mapa de eficiencia de recepción</div>", unsafe_allow_html=True)
        st.markdown(court_svg(dict(zip(zones["Zona"], zones["Eff%"].fillna(0).astype(int))) if not zones.empty else {}, f"Eff% recepción · {team_label}", value_suffix="%"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        pro_table(zones.sort_values("Total", ascending=False) if not zones.empty else zones, height=420, caption="Recepción por zona")

    st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
    st.markdown("#### Recepción según zona de saque")
    rec2 = rec.copy()
    def serve_group(z):
        z = str(z).replace("Z", "")
        if z in ["1", "9"]: return "Saque desde Z1/Z9"
        if z == "6": return "Saque desde Z6"
        if z in ["7", "5"]: return "Saque desde Z7/Z5"
        return "Sin zona de saque"
    rec2["Grupo saque"] = rec2["saque_origen"].apply(serve_group)
    cols = st.columns(3)
    full_rows=[]
    for col, group in zip(cols, ["Saque desde Z1/Z9", "Saque desde Z6", "Saque desde Z7/Z5"]):
        sub = rec2[rec2["Grupo saque"] == group]
        summ = _reception_zone_summary(sub, "origen")
        if not summ.empty:
            tmp=summ.copy(); tmp.insert(0,"Grupo saque",group); full_rows.append(tmp)
        with col:
            st.markdown(f"<div class='volley-panel'><div class='volley-panel-title'>{group}</div>", unsafe_allow_html=True)
            st.markdown(court_svg(dict(zip(summ["Zona"], summ["Eff%"].fillna(0).astype(int))) if not summ.empty else {}, group, value_suffix="%"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    if full_rows:
        pro_table(pd.concat(full_rows, ignore_index=True).sort_values(["Grupo saque","Total"], ascending=[True,False]), height=360, caption="Detalle de recepción por zona de saque")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Zonas de contacto")
    st.caption("El archivo .dvw analizado no siempre incluye derecha/izquierda/medio/arriba/abajo. Cuando venga codificado, este bloque se activará automáticamente.")

def render_serve_receive(data, key="sr"):
    st.info("Saque y Recepción ahora están separados en dos pestañas principales.")


# ──────────────────────────────────────────────────────────────
# BLOQUEO
# ──────────────────────────────────────────────────────────────
def render_block(data, key="blk"):
    """Módulo de bloqueo: puntos, errores, balance, rotaciones y relación con ataque rival."""
    df, team_label = filtered_context(data, key)
    teams = {data["home_team"]["name"]: "home", data["away_team"]["name"]: "away"}
    team_code = teams.get(team_label, "home")
    opp_code = "away" if team_code == "home" else "home"
    ctx = _plays_with_context(data)

    # Reaplicamos los mismos filtros al rival para poder comparar con su ataque.
    fase = st.session_state.get(f"{key}_fase", "Total")
    rot = st.session_state.get(f"{key}_rot", "Todas")
    desde = st.session_state.get(f"{key}_desde", 0)
    opp = ctx[ctx["equipo"] == opp_code].copy() if not ctx.empty else pd.DataFrame()
    opp = _filter_df(opp, "fase", fase)
    opp = _filter_df(opp, "rotacion", rot)
    score_col = "home_score" if opp_code == "home" else "away_score"
    if desde and score_col in opp.columns:
        opp = opp[pd.to_numeric(opp[score_col], errors="coerce").fillna(0) >= desde]

    blk_all = df[df["skill_code"] == "B"].copy()
    rival_att = opp[opp["skill_code"] == "A"].copy() if not opp.empty else pd.DataFrame()

    c1, c2 = st.columns([1, 1])
    blockers = sorted([x for x in blk_all["jugador"].dropna().unique() if x]) if not blk_all.empty else []
    with c1:
        blocker = st.selectbox("Bloqueador", ["Todos"] + blockers, key=f"{key}_player")
    with c2:
        st.caption("El bloqueo se analiza con las acciones B del .dvw y se cruza con el volumen de ataque rival.")

    view = blk_all.copy()
    if blocker != "Todos":
        view = view[view["jugador"] == blocker]

    total = len(view)
    pts = int((view["eval_code"] == "#").sum()) if not view.empty else 0
    errs = int((view["eval_code"] == "=").sum()) if not view.empty else 0
    cont = int(view["eval_code"].isin(["+", "!", "-"]).sum()) if not view.empty else 0
    balance = pts - errs
    sets_played = max(len(data.get("sets", [])), 1)
    per_set = round(pts / sets_played, 2)
    eff = round(balance / max(total, 1) * 100, 1)
    _metric_strip([
        ("BLQ acciones", total),
        ("BLQ #", pts),
        ("BLQ =", errs),
        ("Continuidad +!-", cont),
        ("Balance", balance),
        ("BLQ#/set", per_set),
        ("Eff%", f"{eff}%"),
    ])

    st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
    st.markdown("### Mapa y ranking de bloqueo")
    left, right = st.columns([1, 1.25])
    with left:
        zone = pd.DataFrame()
        if not view.empty:
            zone = view[view["origen"] != "Sin zona"].groupby("origen").agg(
                Total=("skill_code", "count"),
                **{"#": ("eval_code", lambda x: (x == "#").sum()), "=": ("eval_code", lambda x: (x == "=").sum())}
            ).reset_index()
            zone["Eff%"] = ((zone["#"] - zone["="]) / zone["Total"].replace(0, 1) * 100).round(1)
        st.markdown("<div class='volley-panel'><div class='volley-panel-title'>Bloqueos punto por zona</div>", unsafe_allow_html=True)
        st.markdown(court_svg(dict(zip(zone["origen"], zone["#"].fillna(0).astype(int))) if not zone.empty else {}, f"BLQ # · {team_label}"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        if not blk_all.empty:
            players = blk_all.groupby(["jugador", "dorsal", "rotacion"]).agg(
                Acciones=("skill_code", "count"),
                **{"#": ("eval_code", lambda x: (x == "#").sum()), "=": ("eval_code", lambda x: (x == "=").sum()), "+! -": ("eval_code", lambda x: x.isin(["+", "!", "-"]).sum())}
            ).reset_index()
            # Resumen por jugador con rotación más productiva
            base = blk_all.groupby(["jugador", "dorsal"]).agg(
                Acciones=("skill_code", "count"),
                **{"#": ("eval_code", lambda x: (x == "#").sum()), "=": ("eval_code", lambda x: (x == "=").sum()), "+! -": ("eval_code", lambda x: x.isin(["+", "!", "-"]).sum())}
            ).reset_index()
            base["Balance"] = base["#"] - base["="]
            base["Eff%"] = (base["Balance"] / base["Acciones"].replace(0, 1) * 100).round(1)
            rot_best = players.sort_values(["#", "Acciones"], ascending=[False, False]).drop_duplicates(["jugador", "dorsal"])[["jugador", "dorsal", "rotacion"]].rename(columns={"rotacion": "Rotación más fuerte"})
            base = base.merge(rot_best, on=["jugador", "dorsal"], how="left")
            base = base.rename(columns={"jugador": "Jugador", "dorsal": "# jugador"})
            pro_table(base.sort_values(["#", "Balance", "Acciones"], ascending=[False, False, False]), height=420, caption="Ranking de bloqueadores")
        else:
            st.info("No hay acciones de bloqueo con estos filtros.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
    st.markdown("### Bloqueo por rotación y lectura del rival")
    l2, r2 = st.columns(2)
    with l2:
        if not view.empty:
            rot_df = view.groupby("rotacion").agg(
                Acciones=("skill_code", "count"),
                **{"#": ("eval_code", lambda x: (x == "#").sum()), "=": ("eval_code", lambda x: (x == "=").sum())}
            ).reset_index()
            rot_df["Balance"] = rot_df["#"] - rot_df["="]
            rot_df["BLQ#/acción"] = (rot_df["#"] / rot_df["Acciones"].replace(0, 1) * 100).round(1)
            pro_table(rot_df.sort_values(["#", "Balance"], ascending=[False, False]), height=320, caption="Bloqueo por rotación")
        else:
            st.info("Sin bloqueos por rotación.")
    with r2:
        if not rival_att.empty:
            ra = rival_att[rival_att["origen"] != "Sin zona"].groupby("origen").agg(
                Ataques_rival=("skill_code", "count"),
                **{"Rival #": ("eval_code", lambda x: (x == "#").sum()), "Rival =": ("eval_code", lambda x: (x == "=").sum())}
            ).reset_index().rename(columns={"origen": "Zona rival"})
            bz = zone.rename(columns={"origen": "Zona rival", "#": "BLQ #", "=": "BLQ =", "Total": "Acciones BLQ"}) if not zone.empty else pd.DataFrame(columns=["Zona rival", "BLQ #", "BLQ =", "Acciones BLQ"])
            scout = ra.merge(bz[["Zona rival", "BLQ #", "BLQ =", "Acciones BLQ"]], on="Zona rival", how="left").fillna(0)
            scout["Ataque rival Eff%"] = ((scout["Rival #"] - scout["Rival ="]) / scout["Ataques_rival"].replace(0, 1) * 100).round(1)
            scout["Prioridad"] = scout.apply(lambda r: "Alta" if r["Ataques_rival"] >= scout["Ataques_rival"].max() or r["Ataque rival Eff%"] > 35 else "Media", axis=1)
            pro_table(scout.sort_values(["Prioridad", "Ataques_rival"], ascending=[True, False]), height=320, caption="Ataque rival vs nuestro bloqueo")
        else:
            st.info("Sin ataques rivales para cruzar con bloqueo.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
    st.markdown("### Recomendaciones de bloqueo-defensa")
    recs = []
    if not rival_att.empty:
        rz = rival_att[rival_att["origen"] != "Sin zona"].groupby("origen").agg(Total=("skill_code", "count"), Kills=("es_punto", "sum"), Errores=("es_error", "sum")).reset_index()
        if not rz.empty:
            rz["Eff%"] = ((rz["Kills"] - rz["Errores"]) / rz["Total"].replace(0, 1) * 100).round(1)
            top_vol = rz.sort_values("Total", ascending=False).iloc[0]
            top_eff = rz.sort_values(["Eff%", "Total"], ascending=False).iloc[0]
            recs.append(("Prioridad de lectura", f"El rival carga más por {top_vol['origen']}", f"{int(top_vol['Total'])} ataques detectados."))
            recs.append(("Zona de riesgo", f"La zona más eficiente rival es {top_eff['origen']}", f"Eff {top_eff['Eff%']}%."))
    if not blk_all.empty:
        bp = blk_all.groupby("jugador").agg(**{"#": ("eval_code", lambda x: (x == "#").sum()), "=": ("eval_code", lambda x: (x == "=").sum()), "Acciones": ("skill_code", "count")}).reset_index()
        if not bp.empty:
            best = bp.sort_values(["#", "Acciones"], ascending=[False, False]).iloc[0]
            recs.append(("Referencia propia", f"Nuestro bloqueador más productivo es {best['jugador']}", f"{int(best['#'])} bloqueos punto."))
    if not recs:
        recs.append(("Sin muestra suficiente", "Carga más partidos o revisa filtros", "El bloqueo necesita volumen para sacar conclusiones fiables."))
    st.markdown("<div class='mp-card-grid'>", unsafe_allow_html=True)
    for title, action, evidence in recs[:6]:
        st.markdown(f"<div class='insight-card'><div class='label'>{title}</div><div style='font-size:1.02rem;font-weight:950;color:{P['text']};margin:.35rem 0'>{action}</div><div class='note'>{evidence}</div></div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

DISTRIBUTION_ZONE_GROUPS = {
    "Z4": "Z4", "Z3": "Z3", "Z2": "Z2",
    "Z5": "Z5+Z7", "Z7": "Z5+Z7",
    "Z6": "Z6+Z8", "Z8": "Z6+Z8",
    "Z1": "Z1+Z9", "Z9": "Z1+Z9",
}
DISTRIBUTION_ZONE_LABELS = {
    "Z4": "ZONA 4", "Z3": "ZONA 3", "Z2": "ZONA 2",
    "Z5+Z7": "ZONA 5 + 7",
    "Z6+Z8": "PIPE / Z6 + Z8",
    "Z1+Z9": "ZONA 1 + 9",
}

def _distribution_zone_group(z):
    z = str(z).strip()
    return DISTRIBUTION_ZONE_GROUPS.get(z, z if z and z != "nan" else "Sin zona")

def distribution_grid(attacks: pd.DataFrame, title: str):
    # Distribución del colocador en 6 ventanas tácticas: Z1+Z9, Z6+Z8 y Z5+Z7 se suman.
    total = len(attacks)
    view = attacks.copy()
    if not view.empty:
        view["zona_tactica"] = view["origen"].apply(_distribution_zone_group)
    zones = [
        ("Z4", "ZONA 4"), ("Z3", "ZONA 3"), ("Z2", "ZONA 2"),
        ("Z5+Z7", "ZONA 5 + 7"), ("Z6+Z8", "PIPE / Z6 + Z8"), ("Z1+Z9", "ZONA 1 + 9"),
    ]
    html = f'<div class="tactic-title">{title}</div><div style="display:grid;grid-template-columns:repeat(3,minmax(170px,1fr));gap:12px;max-width:900px;margin:auto;">'
    for z, lab in zones:
        zd = view[view["zona_tactica"] == z] if not view.empty else pd.DataFrame()
        n = len(zd)
        pct = round(n / max(total, 1) * 100)
        kills = int((zd["eval_code"] == "#").sum()) if not zd.empty else 0
        errs = int((zd["eval_code"] == "=").sum()) if not zd.empty else 0
        eff = round((kills - errs) / max(n, 1) * 100)
        bg = P["accent1"] if n else ("#332616" if DARK else "#fff4dd")
        txt = "#111827" if n else P["muted"]
        pct_txt = "#111827" if n else P["text"]
        html += f'''<div style="background:{bg};border:1px solid {P['border']};border-radius:20px;min-height:150px;display:flex;flex-direction:column;justify-content:center;align-items:center;box-shadow:0 12px 26px rgba(0,0,0,.16);"><div style="font-weight:950;letter-spacing:.08em;color:{txt};font-size:.9rem">{lab}</div><div style="font-size:2.25rem;font-weight:950;color:{pct_txt};margin:.25rem 0">{pct}%</div><div style="background:rgba(0,0,0,.28);border-radius:999px;padding:.38rem .78rem;color:white;font-weight:850">Nº {n} | # {kills} | = {errs} | Eff {eff}%</div></div>'''
    st.markdown(html + "</div>", unsafe_allow_html=True)

def render_distribution(data, key="dist"):
    df, team_label = filtered_context(data, key)
    c1,c2,c3 = st.columns(3)
    with c1: setter = st.selectbox("Colocador", ["Todos"] + sorted([x for x in df["colocador"].dropna().unique() if x != "Sin colocador"]), key=f"{key}_setter")
    rec_eval_options = sorted([x for x in df["recepcion_eval"].dropna().unique() if x])
    rec_zone_options = sorted([x for x in df["recepcion_zona"].dropna().unique() if x])
    with c2: recq = st.multiselect("Recepciones acumulables", rec_eval_options, default=rec_eval_options, key=f"{key}_recq", help="Puedes sumar varias calidades: #, +, !, -, /, = o Sin recepción para K2.")
    with c3: recz = st.multiselect("Zonas de recepción acumulables", rec_zone_options, default=rec_zone_options, key=f"{key}_recz")
    view = _filter_df(df, "colocador", setter)
    if recq: view = view[view["recepcion_eval"].isin(recq)]
    if recz: view = view[view["recepcion_zona"].isin(recz)]
    attacks = view[view["skill_code"] == "A"].copy()
    left, right = st.columns([1.35, 1])
    with left:
        distribution_grid(attacks, f"Distribución colocador · {team_label}")
    with right:
        st.markdown("#### Resumen de distribución")
        if not attacks.empty:
            attacks_view = attacks.copy()
            attacks_view["zona_tactica"] = attacks_view["origen"].apply(_distribution_zone_group)
            zone_table = attacks_view.groupby("zona_tactica").agg(Balones=("skill_code","count"), Kills=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            zone_table["Zona"] = zone_table["zona_tactica"].map(DISTRIBUTION_ZONE_LABELS).fillna(zone_table["zona_tactica"])
            zone_table["Distribución %"] = (zone_table["Balones"] / max(len(attacks_view),1) * 100).round(1)
            zone_table["Eff%"] = ((zone_table["Kills"]-zone_table["Errores"])/zone_table["Balones"].replace(0,1)*100).round(1)
            zone_table = zone_table[["Zona","Balones","Kills","Errores","Distribución %","Eff%"]]
            pro_table(zone_table.sort_values("Balones", ascending=False), height=340, caption='Resumen de distribución por zona táctica')
        else:
            st.info("Sin colocaciones/ataques con estos filtros.")
    st.markdown("---")
    st.markdown("#### Jugadas más usadas")
    if not attacks.empty:
        detail = attacks.copy()
        detail["Jugada"] = detail["combo"].fillna("").replace("", "Sin jugada") if "combo" in detail.columns else "Sin jugada"
        detail["Zona táctica"] = detail["origen"].apply(_distribution_zone_group).map(DISTRIBUTION_ZONE_LABELS).fillna(detail["origen"])
        combo = detail.groupby(["Jugada"]).agg(Total=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index()
        combo["Distribución %"] = (combo["Total"] / max(len(detail),1) * 100).round(1)
        combo["Eff%"] = ((combo["#"]-combo["="]) / combo["Total"].replace(0,1) * 100).round(1)
        ctx=[]
        for jugada in combo["Jugada"]:
            d=detail[detail["Jugada"]==jugada]
            rot=d["rotacion"].mode().iloc[0] if "rotacion" in d and not d["rotacion"].mode().empty else "-"
            rec=d["recepcion_eval"].mode().iloc[0] if "recepcion_eval" in d and not d["recepcion_eval"].mode().empty else "-"
            zona=d["Zona táctica"].mode().iloc[0] if not d["Zona táctica"].mode().empty else "-"
            ctx.append((rot,rec,zona))
        combo["Rotación más usada"]=[x[0] for x in ctx]
        combo["Recepción habitual"]=[x[1] for x in ctx]
        combo["Salida habitual"]=[x[2] for x in ctx]
        pro_table(combo.sort_values(["Total","Eff%"], ascending=[False,False]), height=420, caption='Jugadas/combinaciones más utilizadas por el colocador')
# ──────────────────────────────────────────────────────────────
# MANUAL Y ANÁLISIS PRO
# ──────────────────────────────────────────────────────────────
def render_user_manual():
    st.markdown("### Inicio rápido")
    st.markdown("""
    <div class='manual-card'>
      <h3>1. Sube un archivo .dvw</h3>
      <p>Arrastra uno o varios archivos de DataVolley y pulsa <b>Analizar partidos</b>. La app no necesita nada más para empezar.</p>
    </div>
    <div class='manual-card'>
      <h3>2. Trabaja por módulos</h3>
      <p><b>General</b> muestra el Match Report y formaciones. <b>Ataque</b>, <b>Saque</b>, <b>Recepción</b> y <b>Distribución</b> permiten filtrar por equipo, rotación, fase y punto. <b>Match Plan</b> prepara un informe imprimible contra el rival.</p>
    </div>
    """, unsafe_allow_html=True)

def _zone_matrix(df, zone_col, value_col):
    order = [["Z4","Z3","Z2"],["Z7","Z8","Z9"],["Z5","Z6","Z1"]]
    return [[float(df.loc[df[zone_col]==z, value_col].iloc[0]) if (zone_col in df and value_col in df and (df[zone_col]==z).any()) else 0 for z in row] for row in order]

def render_heatmap(title, zone_df, zone_col="origen", value_col="Eff%"):
    zmat = _zone_matrix(zone_df, zone_col, value_col)
    fig = go.Figure(data=go.Heatmap(z=zmat, x=["Izquierda","Centro","Derecha"], y=["Red","Media","Fondo"], text=[["Z4","Z3","Z2"],["Z7","Z8","Z9"],["Z5","Z6","Z1"]], texttemplate="%{text}<br>%{z}", colorbar=dict(title=value_col)))
    fig.update_layout(title=title, height=360, margin=dict(t=45,b=35,l=45,r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=P["text"]))
    st.plotly_chart(fig, use_container_width=True)

def _insight_card(label, big, note=""):
    st.markdown(f"<div class='insight-card'><div class='label'>{label}</div><div class='big'>{big}</div><div class='note'>{note}</div></div>", unsafe_allow_html=True)

def render_pro_analysis(data, key="pro"):
    st.markdown("### Centro de mando táctico")
    st.caption("Vista ejecutiva para detectar patrones: K1/K2, rotaciones débiles, mapas de calor y alertas tácticas.")
    ctx = _plays_with_context(data)
    if ctx.empty:
        st.info("Sin datos.")
        return
    teams = {data["home_team"]["name"]:"home", data["away_team"]["name"]:"away"}
    c1,c2,c3 = st.columns([1.2,.9,.9])
    with c1: team_label = st.selectbox("Equipo", list(teams.keys()), key=f"{key}_team")
    with c2: fase = st.selectbox("Fase", ["Total","K1","K2"], key=f"{key}_fase")
    with c3: desde = st.selectbox("Desde punto", list(range(0,31)), key=f"{key}_desde")
    team_code = teams[team_label]
    df = ctx[ctx["equipo"] == team_code].copy()
    df = _filter_df(df, "fase", fase)
    score_col = "home_score" if team_code == "home" else "away_score"
    if desde > 0 and score_col in df.columns:
        df = df[pd.to_numeric(df[score_col], errors="coerce").fillna(0) >= desde]
    att = df[df["skill_code"]=="A"].copy()
    rec = df[df["skill_code"]=="R"].copy()
    srv = df[df["skill_code"]=="S"].copy()
    col = st.columns(4)
    with col[0]: _insight_card("Ataque Eff", f"{round(((att['eval_code']=='#').sum()-(att['eval_code']=='=').sum())/max(len(att),1)*100,1)}%", f"{len(att)} ataques")
    with col[1]: _insight_card("Recepción #+!", f"{round(rec['eval_code'].isin(['#','+','!']).sum()/max(len(rec),1)*100,1)}%", f"{len(rec)} recepciones")
    with col[2]: _insight_card("Saque # / =", f"{int((srv['eval_code']=='#').sum())}/{int((srv['eval_code']=='=').sum())}", f"{len(srv)} saques")
    with col[3]: _insight_card("Puntos por acción", int(df["es_punto"].sum()), "Suma de # detectados")
    st.markdown("---")
    left,right = st.columns(2)
    with left:
        st.markdown("#### Ranking de rotaciones")
        if not df.empty:
            rot = df.groupby(["rotacion","fase"]).agg(Acciones=("skill_code","count"), Puntos=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            rot["Balance"] = rot["Puntos"] - rot["Errores"]
            pro_table(rot.sort_values(["Balance","Acciones"], ascending=[True,False]), height=360, caption="Rotaciones débiles arriba")
        else: st.info("Sin datos")
    with right:
        st.markdown("#### Alertas tácticas")
        alerts=[]
        if not att.empty:
            zag=att.groupby("origen").size().sort_values(ascending=False)
            if not zag.empty:
                topz=zag.index[0]; pct=round(zag.iloc[0]/max(len(att),1)*100,1)
                alerts.append(f"El ataque se concentra en {topz}: {pct}% de los balones.")
            neg=att[att["recepcion_eval"].isin(["-","/","="])]
            if not neg.empty:
                zn=neg.groupby("origen").size().sort_values(ascending=False)
                if not zn.empty: alerts.append(f"Con recepción negativa, la salida más usada es {zn.index[0]}.")
        if not rec.empty:
            rz=rec.groupby("origen").agg(Total=("skill_code","count"), Error=("eval_code", lambda x:(x=='=').sum())).reset_index()
            rz["Error%"]=(rz["Error"]/rz["Total"].replace(0,1)*100).round(1)
            worst=rz.sort_values(["Error%","Total"], ascending=False).head(1)
            if not worst.empty: alerts.append(f"Zona de recepción más castigada por error: {worst.iloc[0]['origen']} ({worst.iloc[0]['Error%']}%).")
        if not alerts: alerts=["No hay ninguna alerta fuerte con estos filtros."]
        for a in alerts[:5]: st.warning(a)
    st.markdown("---")
    hm1,hm2 = st.columns(2)
    with hm1:
        if not att.empty:
            z=att[att["origen"]!="Sin zona"].groupby("origen").agg(total=("skill_code","count"), kills=("es_punto","sum"), errores=("es_error","sum")).reset_index()
            z["Eff%"] = ((z["kills"]-z["errores"])/z["total"].replace(0,1)*100).round(1)
            render_heatmap("Mapa de calor · Eff ataque", z, "origen", "Eff%")
    with hm2:
        if not rec.empty:
            z=rec[rec["origen"]!="Sin zona"].groupby("origen").agg(total=("skill_code","count"), positivas=("eval_code", lambda x:x.isin(['#','+','!']).sum()), errores=("eval_code", lambda x:(x=='=').sum())).reset_index()
            z["Eff%"] = ((z["positivas"]-z["errores"])/z["total"].replace(0,1)*100).round(1)
            render_heatmap("Mapa de calor · Eff recepción", z, "origen", "Eff%")


# ──────────────────────────────────────────────────────────────
# MATCH PLAN AUTOMÁTICO
# ──────────────────────────────────────────────────────────────
def _apply_matchplan_filters(ctx: pd.DataFrame, team_code: str, fase: str, desde: int) -> pd.DataFrame:
    df = ctx[ctx["equipo"] == team_code].copy()
    df = _filter_df(df, "fase", fase)
    score_col = "home_score" if team_code == "home" else "away_score"
    if desde > 0 and score_col in df.columns:
        df = df[pd.to_numeric(df[score_col], errors="coerce").fillna(0) >= desde]
    return df


def generate_match_plan(data: dict, my_team: str, rival_team: str, fase: str = "Total", desde: int = 0) -> dict:
    teams = {data["home_team"]["name"]:"home", data["away_team"]["name"]:"away"}
    ctx = _plays_with_context(data)
    rival_code = teams.get(rival_team, "away"); my_code = teams.get(my_team, "home")
    rival = _apply_matchplan_filters(ctx, rival_code, fase, desde)
    mine = _apply_matchplan_filters(ctx, my_code, fase, desde)
    att = rival[rival["skill_code"] == "A"].copy()
    rec = rival[rival["skill_code"] == "R"].copy()
    srv = mine[mine["skill_code"] == "S"].copy()
    blk = rival[rival["skill_code"] == "B"].copy()
    plan = {"mi_equipo": my_team, "rival": rival_team, "fase": fase, "desde": desde, "claves": [], "acciones": [], "tablas": {}}
    if not att.empty:
        az = att[att["origen"]!="Sin zona"].groupby("origen").agg(Total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()), "=":("eval_code",lambda x:(x=="=").sum()), "/-":("eval_code",lambda x:x.isin(["/","-"]).sum())}).reset_index()
        az["Volumen %"]=(az["Total"]/max(len(att),1)*100).round(1); az["Eff%"]=((az["#"]-az["="])/az["Total"].replace(0,1)*100).round(1)
        plan["tablas"]["ataque_rival"] = az.sort_values("Total", ascending=False)
        top = az.sort_values("Total", ascending=False).iloc[0]
        best = az.sort_values(["Eff%","Total"], ascending=False).iloc[0]
        plan["claves"].append(("Prioridad de bloqueo", f"Cerrar primero {top['origen']}", f"{int(top['Total'])} ataques · {top['Volumen %']}% del volumen rival"))
        plan["claves"].append(("Zona más eficiente", f"Atención a {best['origen']}", f"Eff {best['Eff%']}%"))
        byp = att.groupby("jugador").agg(Total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()), "=":("eval_code",lambda x:(x=="=").sum()), "/-":("eval_code",lambda x:x.isin(["/","-"]).sum())}).reset_index()
        byp["Volumen %"]=(byp["Total"]/max(len(att),1)*100).round(1); byp["Eff%"]=((byp["#"]-byp["="])/byp["Total"].replace(0,1)*100).round(1)
        plan["tablas"]["atacantes_rival"] = byp.sort_values("Total", ascending=False)
        if not byp.empty:
            p = byp.sort_values("Total", ascending=False).iloc[0]
            plan["acciones"].append(("Bloqueo", f"Priorizar lectura sobre {p['jugador']}", f"{int(p['Total'])} ataques · Eff {p['Eff%']}%"))
        dirs = att[(att["origen"]!="Sin zona")&(att["destino"]!="Sin zona")].groupby(["origen","destino"]).agg(Total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()), "=":("eval_code",lambda x:(x=="=").sum())}).reset_index()
        if not dirs.empty:
            dirs["Eff%"] = ((dirs["#"]-dirs["="])/dirs["Total"].replace(0,1)*100).round(1)
            plan["tablas"]["direcciones_ataque"] = dirs.sort_values("Total", ascending=False)
            d = dirs.sort_values("Total", ascending=False).iloc[0]
            plan["acciones"].append(("Defensa", f"Preparar defensa {d['origen']} → {d['destino']}", f"Dirección más repetida: {int(d['Total'])} balones"))
    if not rec.empty:
        rz = _reception_zone_summary(rec, "origen").sort_values(["=%","Total"], ascending=[False,False])
        plan["tablas"]["recepcion_rival"] = rz
        if not rz.empty:
            worst = rz.iloc[0]
            plan["claves"].append(("Plan de saque", f"Sacar hacia {worst['Zona']}", f"= {worst['=%']}% · #+! {worst['#+!%']}%"))
            plan["acciones"].append(("Saque", f"Buscar {worst['Zona']} en recepción rival", f"Zona con mayor daño/error: = {worst['=%']}%"))
        rp = rec.groupby("jugador").agg(Total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()), "+":("eval_code",lambda x:(x=="+").sum()), "!":("eval_code",lambda x:(x=="!").sum()), "=":("eval_code",lambda x:(x=="=").sum())}).reset_index()
        rp["#+!%"] = ((rp["#"]+rp["+"]+rp["!"])/rp["Total"].replace(0,1)*100).round(1); rp["=%"]=(rp["="]/rp["Total"].replace(0,1)*100).round(1)
        plan["tablas"]["receptores_rival"] = rp.sort_values(["=%","Total"], ascending=[False,False])
        if not rp.empty:
            r = rp.sort_values(["=%","Total"], ascending=[False,False]).iloc[0]
            plan["acciones"].append(("Saque", f"Presionar al receptor {r['jugador']}", f"{int(r['Total'])} recepciones · = {r['=%']}%"))
    if not blk.empty:
        bp = blk.groupby("jugador").agg(Total=("skill_code","count"), **{"#":("eval_code",lambda x:(x=="#").sum()), "=":("eval_code",lambda x:(x=="=").sum())}).reset_index()
        bp["Eff%"] = ((bp["#"]-bp["="])/bp["Total"].replace(0,1)*100).round(1)
        plan["tablas"]["bloqueo_rival"] = bp.sort_values("#", ascending=False)
        if not bp.empty:
            b=bp.sort_values("#", ascending=False).iloc[0]
            plan["claves"].append(("Bloqueo rival", f"Evitar jugar cómodo contra {b['jugador']}", f"{int(b['#'])} bloqueos punto"))
    if not rival.empty:
        rot = rival.groupby("rotacion").agg(Acciones=("skill_code","count"), Puntos=("es_punto","sum"), **{"=":("es_error","sum")}).reset_index()
        rot["Balance"] = rot["Puntos"]-rot["="]
        plan["tablas"]["rotaciones_rival"] = rot.sort_values(["Balance","Acciones"], ascending=[True,False])
        weak = rot.sort_values(["Balance","Acciones"], ascending=[True,False]).iloc[0]
        strong = rot.sort_values(["Balance","Acciones"], ascending=[False,False]).iloc[0]
        plan["claves"].append(("Rotación a presionar", f"Apretar en {weak['rotacion']}", f"Balance {int(weak['Balance'])}"))
        plan["acciones"].append(("Gestión del set", f"Arriesgar saque cuando el rival esté en {weak['rotacion']}", f"Rotación más vulnerable por balance"))
        plan["acciones"].append(("Alerta", f"Cuidar side-out cuando rival esté en {strong['rotacion']}", f"Rotación más fuerte por balance"))
    if not plan["claves"]:
        plan["claves"].append(("Muestra insuficiente", "No hay suficientes datos con estos filtros", "Carga más partidos o usa fase Total"))
    return plan


def render_match_plan(data, key="mp"):
    teams=[data["home_team"]["name"], data["away_team"]["name"]]
    c1,c2,c3,c4=st.columns([1.1,1.1,.8,.8])
    with c1: my_team=st.selectbox("Mi equipo", teams, key=f"{key}_my")
    with c2: rival_team=st.selectbox("Equipo rival", teams, index=1 if len(teams)>1 else 0, key=f"{key}_rival")
    with c3: fase=st.selectbox("Fase", ["Total","K1","K2"], key=f"{key}_fase")
    with c4: desde=st.selectbox("Desde punto", list(range(0,31)), key=f"{key}_desde")
    if my_team==rival_team:
        st.warning("Elige equipos diferentes para generar un match plan real."); return
    plan=generate_match_plan(data,my_team,rival_team,fase,desde)
    st.markdown(f"<div class='mp-header'><h1>Match Plan · {my_team} vs {rival_team}</h1><p>Informe táctico imprimible · Fase {fase} · Desde punto {desde} · creado por Marc Riverola Castellà</p></div>", unsafe_allow_html=True)
    st.markdown("#### Resumen ejecutivo")
    st.markdown("<div class='mp-card-grid'>", unsafe_allow_html=True)
    for title,action,evidence in plan.get('claves', [])[:6]:
        st.markdown(f"<div class='insight-card'><div class='label'>{title}</div><div style='font-size:1.02rem;font-weight:950;color:{P['text']};margin:.35rem 0'>{action}</div><div class='note'>{evidence}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    tabs=st.tabs(["Plan de saque", "Bloqueo-defensa", "Ataque rival", "Recepción rival", "Rotaciones", "Hoja para imprimir"])
    with tabs[0]:
        st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
        if 'recepcion_rival' in plan['tablas']: pro_table(plan['tablas']['recepcion_rival'], height=320, caption='Dónde sacar: zonas donde el rival recibe peor')
        if 'receptores_rival' in plan['tablas']: pro_table(plan['tablas']['receptores_rival'], height=320, caption='A quién sacar: receptores vulnerables')
        st.markdown("</div>", unsafe_allow_html=True)
    with tabs[1]:
        st.markdown("<div class='pro-section'>", unsafe_allow_html=True)
        cols=st.columns(2)
        with cols[0]:
            if 'ataque_rival' in plan['tablas']: pro_table(plan['tablas']['ataque_rival'], height=300, caption='Prioridades de bloqueo por zona')
        with cols[1]:
            if 'direcciones_ataque' in plan['tablas']: pro_table(plan['tablas']['direcciones_ataque'], height=300, caption='Direcciones más repetidas')
        if 'bloqueo_rival' in plan['tablas']: pro_table(plan['tablas']['bloqueo_rival'], height=260, caption='Bloqueadores rivales a vigilar')
        st.markdown("</div>", unsafe_allow_html=True)
    with tabs[2]:
        if 'atacantes_rival' in plan['tablas']: pro_table(plan['tablas']['atacantes_rival'], height=420, caption='Atacantes rivales por volumen y eficiencia')
        if 'ataque_rival' in plan['tablas']: pro_table(plan['tablas']['ataque_rival'], height=300, caption='Zonas de ataque rival')
    with tabs[3]:
        if 'recepcion_rival' in plan['tablas']: pro_table(plan['tablas']['recepcion_rival'], height=360, caption='Recepción rival por zona')
        if 'receptores_rival' in plan['tablas']: pro_table(plan['tablas']['receptores_rival'], height=320, caption='Receptores rivales')
    with tabs[4]:
        if 'rotaciones_rival' in plan['tablas']: pro_table(plan['tablas']['rotaciones_rival'], height=360, caption='Rotaciones rivales')
    with tabs[5]:
        st.markdown("<div class='mp-print'><h3>Hoja rápida para banquillo / jugadores</h3><ol>", unsafe_allow_html=True)
        for title,action,evidence in plan.get('acciones', plan.get('claves', []))[:10]:
            st.markdown(f"<li><b>{title}:</b> {action}<br><span style='color:{P['muted']}'>{evidence}</span></li>", unsafe_allow_html=True)
        st.markdown("</ol></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# EXPORTS
# ──────────────────────────────────────────────────────────────
def _sheet_safe(name: str) -> str:
    return str(name)[:31].replace("/", "-").replace("\\", "-")


def export_dataframes(data: dict, modules: list[str]) -> dict[str, pd.DataFrame]:
    frames = {}
    if "Resumen" in modules:
        s = resumen_equipo(data)
        frames["Resumen"] = pd.DataFrame([s["home"], s["away"]], index=[data["home_team"]["name"], data["away_team"]["name"]]).reset_index().rename(columns={"index":"Equipo"})
    if "Jugadores" in modules:
        frames["Jugadores"] = stats_por_jugador(data)
    ctx = _plays_with_context(data)
    if "Ataque" in modules and not ctx.empty:
        att = ctx[ctx["skill_code"] == "A"].copy()
        frames["Ataque zonas"] = att.groupby(["equipo","fase","rotacion","origen"]).agg(Total=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index() if not att.empty else pd.DataFrame()
        frames["Ataque direcciones"] = att[(att["origen"]!="Sin zona")&(att["destino"]!="Sin zona")].groupby(["equipo","origen","destino"]).agg(Total=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index() if not att.empty else pd.DataFrame()
    if "Saque" in modules and not ctx.empty:
        srv = ctx[ctx["skill_code"] == "S"].copy()
        frames["Saque direcciones"] = srv[(srv["origen"]!="Sin zona")&(srv["destino"]!="Sin zona")].groupby(["equipo","jugador","origen","destino","tipo"]).agg(Total=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index() if not srv.empty else pd.DataFrame()
    if "Recepción" in modules and not ctx.empty:
        rec = ctx[ctx["skill_code"] == "R"].copy()
        frames["Recepción zonas"] = rec.groupby(["equipo","jugador","rotacion","origen"]).agg(Total=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "#+!": ("eval_code", lambda x:x.isin(["#","+","!"]).sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index() if not rec.empty else pd.DataFrame()
    if "Bloqueo" in modules and not ctx.empty:
        blk = ctx[ctx["skill_code"] == "B"].copy()
        if not blk.empty:
            frames["Bloqueo jugadores"] = blk.groupby(["equipo","jugador","dorsal","rotacion"]).agg(Acciones=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index()
            frames["Bloqueo zonas"] = blk[blk["origen"]!="Sin zona"].groupby(["equipo","fase","rotacion","origen"]).agg(Acciones=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index()
        else:
            frames["Bloqueo"] = pd.DataFrame()
    if "Distribución" in modules and not ctx.empty:
        att = ctx[ctx["skill_code"] == "A"].copy()
        if not att.empty:
            att["zona_tactica"] = att["origen"].apply(_distribution_zone_group)
            frames["Distribución"] = att.groupby(["equipo","fase","rotacion","colocador","recepcion_eval","recepcion_zona","zona_tactica"]).agg(Balones=("skill_code","count"), **{"#": ("eval_code", lambda x:(x=="#").sum()), "=": ("eval_code", lambda x:(x=="=").sum())}).reset_index()
        else:
            frames["Distribución"] = pd.DataFrame()
    if "Match Plan" in modules:
        plans = []
        for team in [data["home_team"]["name"], data["away_team"]["name"]]:
            plan = generate_match_plan(data, data["home_team"]["name"] if team != data["home_team"]["name"] else data["away_team"]["name"], team, "Total", 0)
            for title, action, evidence in plan.get("acciones", plan.get("claves", [])):
                plans.append({"Equipo": team, "Bloque": title, "Acción recomendada": action, "Evidencia": evidence})
        frames["Match Plan"] = pd.DataFrame(plans)
    if "Por Set" in modules:
        plays = data.get("plays", pd.DataFrame())
        frames["Por Set"] = plays.groupby(["set","equipo","skill"]).agg(Total=("skill","count"), Puntos=("es_punto","sum"), **{"=": ("es_error","sum")}).reset_index() if not plays.empty else pd.DataFrame()
    if "Acciones crudas" in modules:
        frames["Acciones"] = ctx
    return frames


def excel_bytes(data, modules=None):
    modules = modules or ["Resumen", "Jugadores", "Acciones crudas"]
    output = BytesIO()
    frames = export_dataframes(data, modules)
    if not frames:
        frames = {"Sin selección": pd.DataFrame({"Info": ["Selecciona al menos un módulo para exportar."]})}
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in frames.items():
            if df is None or df.empty:
                pd.DataFrame({"Info":["Sin datos con esta selección"]}).to_excel(writer, sheet_name=_sheet_safe(name), index=False)
            else:
                format_table_labels(df).to_excel(writer, sheet_name=_sheet_safe(name), index=False)
    return output.getvalue()


def pdf_bytes(data, modules=None):
    modules = modules or ["Resumen", "Jugadores", "Match Plan"]
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        return None
    buf = BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4); styles=getSampleStyleSheet(); story=[]
    story.append(Paragraph("VolleyVision Hub V2 · creado por Marc Riverola Castellà", styles["Title"])); story.append(Spacer(1,12))
    story.append(Paragraph(f"{data['home_team']['name']} vs {data['away_team']['name']}", styles["Heading2"])); story.append(Spacer(1,10))
    frames = export_dataframes(data, modules)
    if not frames:
        story.append(Paragraph("Selecciona al menos un módulo para exportar.", styles["Normal"]))
    for name, df in frames.items():
        if df is None or df.empty:
            continue
        story.append(Paragraph(name, styles["Heading2"]))
        view = format_table_labels(df).head(18).fillna("")
        rows = [list(view.columns)] + view.values.tolist()
        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.35,colors.grey),
            ('FONTSIZE',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'TOP')
        ]))
        story.append(t); story.append(Spacer(1,12))
        if name in ("Jugadores", "Acciones"):
            story.append(PageBreak())
    doc.build(story); return buf.getvalue()

# ──────────────────────────────────────────────────────────────
# VISTAS PRINCIPALES
# ──────────────────────────────────────────────────────────────
def view_landing():
    st.markdown('<div class="hero"><h1>Volley<span>Vision</span> Hub</h1><p>Scouting, táctica y análisis acumulado de voleibol</p></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class='upload-panel'>
      <h2>Sube tus archivos DataVolley (.dvw)</h2>
      <p>Arrastra uno o varios partidos. Cuando pulses <b>Analizar partidos</b>, se activarán General, Ataque, Saque, Recepción, Distribución, Match Plan y Exportación.</p>
      <div class='quick-grid'>
        <div class='quick-card'><b>1 · Cargar</b><span>Sube partido único o varios partidos para acumulado.</span></div>
        <div class='quick-card'><b>2 · Analizar</b><span>Filtra por equipo, rotación, fase K1/K2 y desde punto.</span></div>
        <div class='quick-card'><b>3 · Preparar</b><span>Genera match plan contra un rival.</span></div>
        <div class='quick-card'><b>4 · Exportar</b><span>Descarga Excel o PDF seleccionando módulos.</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    files = st.file_uploader("Sube archivos DataVolley (.dvw)", type=["dvw"], accept_multiple_files=True)
    if files and st.button("Analizar partidos", type="primary", use_container_width=True):
        matches=[]; bar=st.progress(0)
        for i,f in enumerate(files):
            bar.progress((i+1)/len(files), f"Procesando {f.name}...")
            try:
                data = DVWParser(f.read().decode("latin-1")).parse(); data["_filename"] = f.name
                if not data["plays"].empty: matches.append(data); st.success(f"{f.name}: {len(data['plays'])} acciones")
                else: st.warning(f"{f.name}: sin acciones detectadas")
            except Exception as e: st.error(f"{f.name}: {e}")
        if matches: st.session_state.matches=matches; st.session_state.view="dashboard"; st.session_state.active_match=0; st.rerun()
    st.markdown("---")
    render_user_manual()

def render_single_match(data, prefix="single"):
    score_bar(data)
    tabs = st.tabs(["Inicio / Manual", "General", "Ataque", "Saque", "Recepción", "Bloqueo", "Colocador / Distribución", "Match Plan", "Por Set", "Exportar"])
    with tabs[0]: render_user_manual()
    with tabs[1]: render_general(data)
    with tabs[2]: render_attack(data, key=f"{prefix}_att")
    with tabs[3]: render_serve(data, key=f"{prefix}_srv")
    with tabs[4]: render_reception(data, key=f"{prefix}_rec")
    with tabs[5]: render_block(data, key=f"{prefix}_blk")
    with tabs[6]: render_distribution(data, key=f"{prefix}_dist")
    with tabs[7]: render_match_plan(data, key=f"{prefix}_mp")
    with tabs[8]:
        plays=data.get("plays", pd.DataFrame())
        if plays.empty: st.info("Sin datos por set")
        else:
            sel=st.selectbox("Set", sorted(plays["set"].unique()), format_func=lambda x:f"Set {x}", key=f"{prefix}_set")
            for tc,nm in [("home",data["home_team"]["name"]),("away",data["away_team"]["name"] )]:
                st.markdown(f"#### {nm}"); tp=plays[(plays["set"]==sel)&(plays["equipo"]==tc)&(plays["dorsal"]!=0)]
                if not tp.empty:
                    pro_table(tp.groupby("skill").agg(Total=("skill","count"), Puntos=("es_punto","sum"), **{"=":("es_error","sum")}).reset_index(), height=260, caption=f'Resumen por acción · {nm}')
    with tabs[9]:
        st.markdown("### Exportar informe")
        st.caption("Selecciona qué módulos quieres incluir. El Excel crea una hoja por módulo y el PDF genera un resumen limpio para compartir.")
        default_modules = ["Resumen", "Ataque", "Saque", "Recepción", "Bloqueo", "Distribución", "Match Plan"]
        export_modules = st.multiselect(
            "Módulos a exportar",
            ["Resumen", "Ataque", "Saque", "Recepción", "Bloqueo", "Distribución", "Match Plan", "Por Set", "Acciones crudas"],
            default=default_modules,
            key=f"{prefix}_export_modules"
        )
        c1,c2 = st.columns(2)
        with c1:
            st.download_button("Descargar Excel seleccionado", excel_bytes(data, export_modules), file_name="VolleyVision_export_seleccionado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document", use_container_width=True)
        with c2:
            pdf = pdf_bytes(data, export_modules)
            if pdf: st.download_button("Descargar PDF seleccionado", pdf, file_name="VolleyVision_export_seleccionado.pdf", mime="application/pdf", use_container_width=True)
            else: st.warning("Para PDF añade reportlab en requirements.txt")

def build_accumulated_match(matches, team_name):
    plays=[]; home_players=[]; away_players=[]
    for i,m in enumerate(matches):
        hn,an=m["home_team"]["name"],m["away_team"]["name"]
        if team_name not in (hn,an): continue
        code = "home" if hn == team_name else "away"
        opp = "away" if code == "home" else "home"
        pl=m["plays"].copy(); pl["match_id"]=i; pl["equipo_original"]=pl["equipo"]; pl["equipo"]=pl["equipo"].apply(lambda x:"home" if x==code else "away"); plays.append(pl)
    allplays=pd.concat(plays, ignore_index=True) if plays else pd.DataFrame()
    return {"match":{"date":"Acumulado","league":"Temporada"},"sets":[],"home_team":{"name":team_name},"away_team":{"name":"Rivales"},"home_players":pd.DataFrame(),"away_players":pd.DataFrame(),"plays":allplays}

def render_multi_match(matches):
    teams=sorted(set([m["home_team"]["name"] for m in matches]+[m["away_team"]["name"] for m in matches]))
    team=st.selectbox("Equipo a analizar", teams)
    acc=build_accumulated_match(matches, team)
    st.caption("Vista acumulada con las mismas pestañas que un partido individual.")
    render_single_match(acc, prefix=f"acc_{abs(hash(team))}")

def view_dashboard():
    matches=st.session_state.matches
    col1,col2=st.columns([5,1])
    with col1: st.markdown('<div class="hero"><h1>Volley<span>Vision</span> Hub</h1><p>Análisis avanzado</p></div>', unsafe_allow_html=True)
    with col2:
        st.write("")
        if st.button("Nueva carga", use_container_width=True): st.session_state.matches=[]; st.session_state.view="landing"; st.rerun()
    if len(matches)>1:
        mode=st.radio("Modo de análisis", ["Partido individual","Acumulado multipartits"], horizontal=True)
        if mode=="Acumulado multipartits": render_multi_match(matches); return
        opts=[f"{m['home_team']['name']} vs {m['away_team']['name']} ({m['match'].get('date','')})" for m in matches]
        idx=st.selectbox("Seleccionar partido", range(len(opts)), format_func=lambda i:opts[i]); st.session_state.active_match=idx
    render_single_match(matches[st.session_state.active_match])

def main():
    if st.session_state.view == "landing" or not st.session_state.matches: view_landing()
    else: view_dashboard()
    st.markdown('<footer>VolleyVision Hub V2 · creado por Marc Riverola Castellà</footer>', unsafe_allow_html=True)

if __name__ == "__main__": main()
