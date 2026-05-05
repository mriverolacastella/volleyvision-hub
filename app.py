"""
VolleyVision Hub V3 — Plataforma profesional de análisis de voleibol
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
    st.caption("V4 · creado por Marc Riverola Castellà")

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
.rotation-card{{background:{P['card']};border:1px solid {P['border']};border-radius:18px;padding:1rem;box-shadow:0 10px 28px rgba(0,0,0,.14)}}
.rotation-title{{font-weight:950;color:{P['text']};margin-bottom:.4rem}}
.rotation-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:.7rem}}
.rotation-cell{{border:1px solid {P['border']};border-radius:12px;padding:.7rem;text-align:center;background:{P['bg2']};font-weight:900}}
.rotation-badge{{display:inline-block;border-radius:999px;padding:.25rem .65rem;font-weight:950;background:{P['accent1']};color:#111827;margin-top:.35rem}}
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

def direction_chart(df, title, value_col="total"):
    """Campo vertical con flechas estilo scouting: origen y destino por zonas."""
    if df.empty:
        st.info("No hay direcciones detectadas con estos filtros."); return
    pos = {
        "Z4": (1, 2.65), "Z3": (2, 2.65), "Z2": (3, 2.65),
        "Z7": (1, 2.05), "Z8": (2, 2.05), "Z9": (3, 2.05),
        "Z5": (1, 1.25), "Z6": (2, 1.25), "Z1": (3, 1.25),
    }
    fig = go.Figure()
    fig.add_shape(type="rect", x0=.45, x1=3.55, y0=.65, y1=3.05, line=dict(color="#e7e5e4", width=3), fillcolor="rgba(245,158,11,0.42)")
    fig.add_shape(type="line", x0=.45, x1=3.55, y0=2.25, y1=2.25, line=dict(color="#e7e5e4", width=2))
    fig.add_shape(type="line", x0=.45, x1=3.55, y0=1.45, y1=1.45, line=dict(color="#e7e5e4", width=2))
    fig.add_shape(type="line", x0=2, x1=2, y0=.65, y1=3.05, line=dict(color="#111827", width=2, dash="dash"))
    for z,(x,y) in pos.items():
        fig.add_annotation(x=x, y=y, text=z.replace('Z',''), showarrow=False, font=dict(size=14, color=P["text"]))
    max_n = max(int(df[value_col].max() if value_col in df else df["total"].max()), 1)
    for _, r in df.iterrows():
        o, d = r.get("origen"), r.get("destino")
        if o not in pos or d not in pos: continue
        x0,y0 = pos[o]; x1,y1 = pos[d]
        n = int(r.get(value_col, r.get("total", 1)))
        width = max(1.2, min(7, 1 + 6*n/max_n))
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3, arrowsize=1.25, arrowwidth=width, arrowcolor="#111827", text=f"{n}", font=dict(color="white", size=11), bgcolor="rgba(17,24,39,.72)")
    fig.update_xaxes(range=[.25,3.75], visible=False); fig.update_yaxes(range=[.45,3.25], visible=False, scaleanchor="x")
    fig.update_layout(title=title, height=560, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=50,b=20,l=20,r=20))
    st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# CONTEXTO TÁCTICO APROXIMADO
# ──────────────────────────────────────────────────────────────
def _plays_with_context(data: dict) -> pd.DataFrame:
    plays = data.get("plays", pd.DataFrame()).copy()
    if plays.empty: return plays
    for c, val in {"fase":"Total","recepcion_eval":"Sin recepción","recepcion_zona":"Sin zona","colocador":"Sin colocador","rotacion":"Todas"}.items(): plays[c] = val
    plays["origen"] = plays["zona_inicio"].apply(lambda z: f"Z{z}" if str(z).strip() else "Sin zona")
    plays["destino"] = plays["zona_fin"].apply(lambda z: f"Z{z}" if str(z).strip() else "Sin zona")
    # Contexto de rally por equipo. La rotación es una estimación si el DVW no trae lineups/rotaciones explícitas.
    for (equipo, setn, rally), grp in plays.groupby(["equipo","set","rally"], sort=False):
        recs = grp[grp["skill_code"] == "R"]; sets = grp[grp["skill_code"] == "E"]
        fase = "K1" if not recs.empty else "K2"
        rec_eval = recs.iloc[-1]["eval_code"] if not recs.empty else "Sin recepción"
        rec_zone = f"Z{recs.iloc[-1]['zona_inicio']}" if not recs.empty and str(recs.iloc[-1]["zona_inicio"]).strip() else "Sin zona"
        setter = sets.iloc[-1]["jugador"] if not sets.empty else "Sin colocador"
        base_score = int(grp.iloc[0].get("home_score",0) if equipo == "home" else grp.iloc[0].get("away_score",0) or 0)
        rot = f"P{(base_score % 6) + 1}"
        plays.loc[grp.index, ["fase","recepcion_eval","recepcion_zona","colocador","rotacion"]] = [fase,rec_eval,rec_zone,setter,rot]
    return plays

def _filter_df(df, col, value):
    if value in (None, "Todos", "Todas", "Total"): return df
    if col not in df.columns: return df
    return df[df[col] == value]

def filtered_context(data, key, team_default=None):
    plays = _plays_with_context(data)
    if plays.empty: return plays, ""
    teams = {data["home_team"]["name"]:"home", data["away_team"]["name"]:"away"}
    c1,c2,c3 = st.columns(3)
    with c1: team_label = st.selectbox("Equipo", list(teams.keys()), key=f"{key}_team", index=0)
    df = plays[plays["equipo"] == teams[team_label]].copy()
    with c2: fase = st.selectbox("Fase", ["Total","K1","K2"], key=f"{key}_fase")
    with c3: rot = st.selectbox("Rotación", ["Todas"] + sorted([x for x in df["rotacion"].dropna().unique() if x != "Todas"]), key=f"{key}_rot")
    df = _filter_df(_filter_df(df, "fase", fase), "rotacion", rot)
    return df, team_label

# ──────────────────────────────────────────────────────────────
# RESUMEN
# ──────────────────────────────────────────────────────────────
def horizontal_mirror_comparison(data):
    hn, an = data["home_team"]["name"], data["away_team"]["name"]
    s = resumen_equipo(data); h, a = s.get("home",{}), s.get("away",{})
    metrics = [("Puntos","puntos"),("Ataque Eff%","att_eff"),("Ataque Kill%","att_kill_pct"),("Recepción +%","rec_pos_pct"),("Aces","srv_aces"),("Errores saque","srv_errors"),("Bloqueos","blk_kills")]
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
    metrics = [("Puntos", "puntos"), ("Ataques K", "att_kills"), ("Ataques Err", "att_errors"), ("Ataques Tot", "att_total"), ("AT Eff%", "att_eff"), ("AT Kill%", "att_kill_pct"), ("Aces", "srv_aces"), ("Err Saque", "srv_errors"), ("REC +%", "rec_pos_pct"), ("REC Perf%", "rec_perf_pct"), ("Bloqueos", "blk_kills")]
    for label, key in metrics:
        rows.append({"Métrica": label, data["home_team"]["name"]: s["home"].get(key,0), data["away_team"]["name"]: s["away"].get(key,0)})
    st.markdown("#### Tabellino total del partido")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def set_rotation_summary(data):
    plays = _plays_with_context(data)
    if plays.empty: return
    sets = sorted(plays["set"].dropna().unique())
    sel = st.selectbox("Ver rotaciones del set", sets, format_func=lambda x: f"Set {x}", key=f"rot_set_{id(data)}")
    sp = plays[plays["set"] == sel]
    st.markdown("#### Rotaciones por set · saque/recepción")
    cols = st.columns(2)
    for i,(tc,nm) in enumerate([("home", data["home_team"]["name"]), ("away", data["away_team"]["name"]) ]):
        team = sp[sp["equipo"] == tc]
        first = team.head(1)
        rot = first.iloc[0]["rotacion"] if not first.empty else "-"
        first_skill = first.iloc[0]["skill_code"] if not first.empty else ""
        estado = "Recepción" if first_skill == "R" else ("Saque" if first_skill == "S" else "Sin detectar")
        players = team[team["dorsal"] != 0].groupby(["dorsal","jugador"]).size().reset_index(name="n").sort_values("n", ascending=False).head(6)
        labels = []
        for _,r in players.iterrows():
            labels.append(f"#{int(r['dorsal'])}<br>{str(r['jugador'])[:11]}")
        while len(labels)<6: labels.append("-")
        order = [labels[3], labels[2], labels[1], labels[4], labels[5], labels[0]]
        html = f'<div class="rotation-card"><div class="rotation-title">{nm}</div><div>Set {sel} · <span class="rotation-badge">{rot}</span> · {estado}</div><div class="rotation-grid">'
        for lab in order:
            html += f'<div class="rotation-cell">{lab}</div>'
        html += '</div><div style="font-size:.72rem;color:%s;margin-top:.5rem">Visual estimado a partir del scout. Cuando el DVW incluya lineup/rotaciones oficiales, se puede hacer exacto.</div></div>' % P['muted']
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

def render_players(data):
    stats = stats_por_jugador(data)
    if stats.empty: st.info("Sin datos de jugadores"); return
    stats = player_score_table(stats)
    hn, an = data["home_team"]["name"], data["away_team"]["name"]
    st.markdown("#### Cápsulas destacadas")
    row1 = st.columns(3)
    with row1[0]: player_pill("MVP partido", stats.sort_values("MVP Score", ascending=False).head(1))
    with row1[1]: player_pill(f"MVP {hn}", stats[stats["Equipo"] == hn].sort_values("MVP Score", ascending=False).head(1))
    with row1[2]: player_pill(f"MVP {an}", stats[stats["Equipo"] == an].sort_values("MVP Score", ascending=False).head(1))
    row2 = st.columns(4)
    with row2[0]: player_pill("Máx. anotador", stats.sort_values("Pts", ascending=False).head(1))
    with row2[1]: player_pill("Máx. bloqueo", stats.sort_values("BLQ K", ascending=False).head(1))
    with row2[2]: player_pill("Mejor recepción", stats[stats["REC Tot"]>0].sort_values(["REC%","REC Tot"], ascending=False).head(1))
    with row2[3]: player_pill("Mejor saque", stats[stats["SQ Tot"]>0].sort_values(["SQ Ace","SQ Eff%"], ascending=False).head(1))
    st.markdown("---")
    st.caption("Tablas totales del partido: todas las acciones de cada jugador, sin filtros.")
    ordered_cols = ["Equipo","Dorsal","Jugador","Posicion","Pts","Err","Balance","MVP Score","AT K","AT Err","AT Tot","AT Eff%","AT Kill%","SQ Ace","SQ Err","SQ Tot","SQ Eff%","REC Pos","REC Perf","REC Err","REC Tot","REC%","REC Perf%","BLQ K","BLQ Err","DEF Pos","DEF Err","DEF Tot"]
    for team in [hn, an]:
        st.markdown(f"#### {team}")
        st.dataframe(stats[stats["Equipo"] == team][ordered_cols].sort_values("Pts", ascending=False), use_container_width=True, height=360, hide_index=True)

# ──────────────────────────────────────────────────────────────
# ATAQUE / SAQUE-RECEPCIÓN / DISTRIBUCIÓN
# ──────────────────────────────────────────────────────────────
def render_attack(data, key="att"):
    df, team_label = filtered_context(data, key)
    att = df[df["skill_code"] == "A"].copy()
    if att.empty: st.info("No hay ataques con estos filtros."); return
    c1,c2 = st.columns(2)
    with c1:
        player = st.selectbox("Atacante", ["Todos"] + sorted(att["jugador"].dropna().unique()), key=f"{key}_player")
    with c2:
        zone = st.selectbox("Zona origen", ["Todas"] + sorted([z for z in att["origen"].dropna().unique() if z != "Sin zona"]), key=f"{key}_zone")
    att = _filter_df(_filter_df(att, "jugador", player), "origen", zone)
    st.markdown("#### Eficiencia de ataque por zona")
    zg = att[att["origen"] != "Sin zona"].groupby("origen").agg(total=("skill_code","count"), kills=("es_punto","sum"), errores=("es_error","sum")).reset_index()
    if not zg.empty:
        zg["Eff%"] = ((zg["kills"]-zg["errores"])/zg["total"].replace(0,1)*100).round(1)
    eff_map = dict(zip(zg["origen"], zg["Eff%"].fillna(0).astype(int))) if not zg.empty else {}
    st.markdown(court_svg(eff_map, f"Eff% ataque · {team_label}", value_suffix="%"), unsafe_allow_html=True)
    st.dataframe(zg.sort_values("total", ascending=False) if not zg.empty else zg, use_container_width=True, hide_index=True)
    st.markdown("#### Direcciones de ataque")
    dirs = att[(att["origen"]!="Sin zona") & (att["destino"]!="Sin zona")].groupby(["origen","destino"]).agg(total=("skill_code","count"), kills=("es_punto","sum"), errores=("es_error","sum")).reset_index()
    if not dirs.empty: dirs["Eff%"] = ((dirs["kills"]-dirs["errores"])/dirs["total"].replace(0,1)*100).round(1)
    direction_chart(dirs, "Direcciones de ataque · origen → destino")
    st.dataframe(dirs.sort_values("total", ascending=False) if not dirs.empty else dirs, use_container_width=True, hide_index=True)

def render_serve_receive(data, key="sr"):
    df, team_label = filtered_context(data, key)
    sub = st.tabs(["Saque", "Recepción"])
    with sub[0]:
        srv = df[df["skill_code"] == "S"].copy()
        if srv.empty: st.info("Sin saques"); return
        c1,c2 = st.columns(2)
        with c1: player = st.selectbox("Sacador", ["Todos"] + sorted(srv["jugador"].dropna().unique()), key=f"{key}_srv_player")
        with c2: tipo = st.selectbox("Tipo de saque", ["Todos"] + sorted([x for x in srv["tipo"].dropna().unique() if x]), key=f"{key}_srv_type")
        srv = _filter_df(_filter_df(srv, "jugador", player), "tipo", tipo)
        dirs = srv[(srv["origen"]!="Sin zona") & (srv["destino"]!="Sin zona")].groupby(["origen","destino","tipo"]).agg(total=("skill_code","count"), aces=("es_punto","sum"), errores=("es_error","sum")).reset_index()
        if not dirs.empty: dirs["Eff%"] = ((dirs["aces"]-dirs["errores"])/dirs["total"].replace(0,1)*100).round(1)
        direction_chart(dirs, "Direcciones de saque")
        st.dataframe(dirs.sort_values("total", ascending=False) if not dirs.empty else dirs, use_container_width=True, hide_index=True)
    with sub[1]:
        rec = df[df["skill_code"] == "R"].copy()
        if rec.empty: st.info("Sin recepciones"); return
        receptor = st.selectbox("Receptor", ["Todos"] + sorted(rec["jugador"].dropna().unique()), key=f"{key}_rec_player")
        rec = _filter_df(rec, "jugador", receptor)
        zones = rec.groupby("origen").agg(total=("skill_code","count"), perfectas=("eval_code", lambda x: (x=="#").sum()), positivas=("eval_code", lambda x: x.isin(["#","+","!"]).sum()), errores=("eval_code", lambda x: (x=="=").sum())).reset_index()
        zones["REC+%"] = ((zones["positivas"] / zones["total"].replace(0,1))*100).round(1)
        zones["Perf%"] = ((zones["perfectas"] / zones["total"].replace(0,1))*100).round(1)
        zones["Eff%"] = (((zones["positivas"]-zones["errores"]) / zones["total"].replace(0,1))*100).round(1)
        c1,c2,c3,c4 = st.columns(4)
        with c1: kpi("Recepciones", int(rec.shape[0]))
        with c2: kpi("Errores", int((rec["eval_code"]=="=").sum()))
        with c3: kpi("REC+%", f"{round(rec['eval_code'].isin(['#','+','!']).sum()/max(len(rec),1)*100,1)}%")
        with c4: kpi("Perf%", f"{round((rec['eval_code']=='#').sum()/max(len(rec),1)*100,1)}%")
        st.markdown(court_svg(dict(zip(zones["origen"], zones["Eff%"].fillna(0).astype(int))), f"Eficiencia recepción · {team_label}", value_suffix="%"), unsafe_allow_html=True)
        st.dataframe(zones.sort_values("total", ascending=False), use_container_width=True, hide_index=True)
        st.markdown("#### Lectura por zona corporal")
        st.caption("El DVW estándar no siempre guarda derecha/izquierda/medio/arriba/abajo. Dejo el módulo preparado: cuando el código del scout lo traiga, se podrá mapear aquí.")
        body = pd.DataFrame({"Zona corporal":["Derecha","Izquierda","Medio","Arriba","Abajo"], "Recepciones detectadas":[0,0,0,0,0], "Nota":["Pendiente de mapeo DVW"]*5})
        st.dataframe(body, use_container_width=True, hide_index=True)

def distribution_grid(attacks: pd.DataFrame, title: str):
    total = len(attacks)
    zones = [("Z4","ZONA 4"),("Z3","ZONA 3"),("Z2","ZONA 2"),("Z5","ZONA 5"),("Z6","PIPE/Z6"),("Z1","ZONA 1")]
    html = f'<div class="tactic-title">{title}</div><div style="display:grid;grid-template-columns:repeat(3,minmax(150px,1fr));gap:10px;max-width:760px;margin:auto;">'
    for z, lab in zones:
        zd = attacks[attacks["origen"] == z]; n=len(zd); pct=round(n/max(total,1)*100); kills=int((zd["eval_code"]=="#").sum()); errs=int((zd["eval_code"]=="=").sum()); eff=round((kills-errs)/max(n,1)*100)
        bg = P["accent1"] if n else ("#332616" if DARK else "#fff4dd")
        html += f'''<div style="background:{bg};border:1px solid {P['border']};border-radius:18px;min-height:150px;display:flex;flex-direction:column;justify-content:center;align-items:center;"><div style="font-weight:950;letter-spacing:.08em;color:{'#111827' if n else P['muted']}">{lab}</div><div style="font-size:2.2rem;font-weight:950;color:{'#111827' if n else P['text']};margin:.35rem 0">{pct}%</div><div style="background:rgba(0,0,0,.25);border-radius:999px;padding:.35rem .7rem;color:white;font-weight:800">Nº {n} | Eff {eff}%</div></div>'''
    st.markdown(html + "</div>", unsafe_allow_html=True)

def render_distribution(data, key="dist"):
    df, team_label = filtered_context(data, key)
    c1,c2,c3 = st.columns(3)
    with c1: setter = st.selectbox("Colocador", ["Todos"] + sorted([x for x in df["colocador"].dropna().unique() if x != "Sin colocador"]), key=f"{key}_setter")
    with c2: recq = st.multiselect("Calidades de recepción acumulables", sorted([x for x in df["recepcion_eval"].dropna().unique() if x]), default=sorted([x for x in df["recepcion_eval"].dropna().unique() if x]), key=f"{key}_recq")
    with c3: recz = st.multiselect("Zonas de recepción acumulables", sorted([x for x in df["recepcion_zona"].dropna().unique() if x]), default=sorted([x for x in df["recepcion_zona"].dropna().unique() if x]), key=f"{key}_recz")
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
            zone_table = attacks.groupby("origen").agg(Balones=("skill_code","count"), Kills=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            zone_table["Distribución %"] = (zone_table["Balones"] / max(len(attacks),1) * 100).round(1)
            zone_table["Eff%"] = ((zone_table["Kills"]-zone_table["Errores"])/zone_table["Balones"].replace(0,1)*100).round(1)
            st.dataframe(zone_table.sort_values("Balones", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Sin colocaciones/ataques con estos filtros.")
    st.markdown("---")
    st.markdown("#### Detalle completo")
    if not attacks.empty:
        table = attacks.groupby(["origen","jugador","recepcion_eval","recepcion_zona"]).agg(Balones=("skill_code","count"), Kills=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
        table["Eff%"] = ((table["Kills"]-table["Errores"])/table["Balones"].replace(0,1)*100).round(1)
        st.dataframe(table.sort_values("Balones", ascending=False), use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────────────────────
# EXPORTS
# ──────────────────────────────────────────────────────────────
def excel_bytes(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([resumen_equipo(data)["home"], resumen_equipo(data)["away"]], index=[data["home_team"]["name"], data["away_team"]["name"]]).to_excel(writer, sheet_name="Tabellino")
        stats_por_jugador(data).to_excel(writer, sheet_name="Jugadores", index=False)
        _plays_with_context(data).to_excel(writer, sheet_name="Acciones", index=False)
    return output.getvalue()

def pdf_bytes(data):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        return None
    buf = BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4); styles=getSampleStyleSheet(); story=[]
    story.append(Paragraph("VolleyVision Hub · Resumen · creado por Marc Riverola Castellà", styles["Title"])); story.append(Spacer(1,12))
    story.append(Paragraph(f"{data['home_team']['name']} vs {data['away_team']['name']}", styles["Heading2"]))
    s=resumen_equipo(data); rows=[["Métrica", data['home_team']['name'], data['away_team']['name']]]
    for label,key in [("Puntos","puntos"),("AT Eff%","att_eff"),("AT Kill%","att_kill_pct"),("REC+%","rec_pos_pct"),("Aces","srv_aces"),("Bloqueos","blk_kills")]: rows.append([label, s['home'].get(key,0), s['away'].get(key,0)])
    t=Table(rows); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey)])); story.append(t); story.append(Spacer(1,12))
    stp=stats_por_jugador(data).sort_values("Pts", ascending=False).head(12)
    if not stp.empty:
        story.append(Paragraph("Top jugadores", styles["Heading2"])); rows=[list(stp[["Equipo","Dorsal","Jugador","Pts","AT Eff%","REC%","BLQ K"]].columns)] + stp[["Equipo","Dorsal","Jugador","Pts","AT Eff%","REC%","BLQ K"]].values.tolist(); t=Table(rows); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.4,colors.grey),('FONTSIZE',(0,0),(-1,-1),7)])); story.append(t)
    doc.build(story); return buf.getvalue()

# ──────────────────────────────────────────────────────────────
# VISTAS PRINCIPALES
# ──────────────────────────────────────────────────────────────
def view_landing():
    st.markdown('<div class="hero"><h1>Volley<span>Vision</span> Hub</h1><p>Scouting, táctica y análisis acumulado de voleibol</p></div>', unsafe_allow_html=True)
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

def render_single_match(data, prefix="single"):
    score_bar(data)
    tabs = st.tabs(["Resumen", "Jugadores", "Ataque", "Saque y Recepción", "Colocador / Distribución", "Por Set", "Exportar"])
    with tabs[0]: horizontal_mirror_comparison(data); tabellino(data); set_rotation_summary(data)
    with tabs[1]: render_players(data)
    with tabs[2]: render_attack(data, key=f"{prefix}_att")
    with tabs[3]: render_serve_receive(data, key=f"{prefix}_sr")
    with tabs[4]: render_distribution(data, key=f"{prefix}_dist")
    with tabs[5]:
        plays=data.get("plays", pd.DataFrame())
        if plays.empty: st.info("Sin datos por set")
        else:
            sel=st.selectbox("Set", sorted(plays["set"].unique()), format_func=lambda x:f"Set {x}", key=f"{prefix}_set")
            for tc,nm in [("home",data["home_team"]["name"]),("away",data["away_team"]["name"] )]:
                st.markdown(f"#### {nm}"); tp=plays[(plays["set"]==sel)&(plays["equipo"]==tc)&(plays["dorsal"]!=0)]
                if not tp.empty: st.dataframe(tp.groupby("skill").agg(Total=("skill","count"), Puntos=("es_punto","sum"), Errores=("es_error","sum")).reset_index(), use_container_width=True, hide_index=True)
    with tabs[6]:
        st.download_button("Descargar Excel completo", excel_bytes(data), file_name="VolleyVision_resumen.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document")
        pdf = pdf_bytes(data)
        if pdf: st.download_button("Descargar PDF resumen", pdf, file_name="VolleyVision_resumen.pdf", mime="application/pdf")
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
    st.markdown('<footer>VolleyVision Hub V4 · creado por Marc Riverola Castellà</footer>', unsafe_allow_html=True)

if __name__ == "__main__": main()
