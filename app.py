"""
VoleiVision Hub — Plataforma de Analisis de Voleibol
Visualizacion profesional de archivos DataVolley (.dvw)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dvw_parser import DVWParser, stats_por_jugador, resumen_equipo, distribucion_ataque, mapa_ataque_destino

st.set_page_config(page_title="VoleiVision Hub", page_icon="assets/favicon.ico",
                   layout="wide", initial_sidebar_state="collapsed")

# ─── Tema visual día/noche ─────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Noche"

with st.sidebar:
    st.session_state.theme_mode = st.radio("Modo visual", ["Noche", "Día"], horizontal=True)

DARK = st.session_state.theme_mode == "Noche"
P = {
    "bg": "#090d14" if DARK else "#f4f7fb",
    "bg2": "#101722" if DARK else "#ffffff",
    "bg3": "#171f2c" if DARK else "#e9eef6",
    "card": "#151b26" if DARK else "#ffffff",
    "border": "#2b3444" if DARK else "#d8e0ec",
    "text": "#f4f7fb" if DARK else "#101722",
    "muted": "#aab3c2" if DARK else "#637083",
    "subtle": "#717b8d" if DARK else "#8290a3",
    "accent1": "#f59e0b", "accent2": "#22d3ee", "accent3": "#fb7185",
    "home": "#22c55e", "away": "#f97316",
    "kill": "#22c55e", "error": "#ef4444", "pos": "#38bdf8",
    "white": "#ffffff", "surface": "#090d14" if DARK else "#f4f7fb",
}

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}
.stApp,.main{{background:{P['surface']};color:{P['text']}}}
.main .block-container{{padding-top:.8rem;max-width:1480px}}
section[data-testid="stSidebar"]{{background:{P['bg2']};border-right:1px solid {P['border']}}}
.hero{{text-align:left;padding:1.4rem 0 1rem}}
.hero h1{{font-size:2.4rem;font-weight:900;color:{P['text']};margin:0;letter-spacing:-1px}}
.hero h1 span{{color:{P['accent1']}}}
.hero p{{color:{P['muted']};font-size:1rem;margin-top:.3rem}}
.pro-card{{background:{P['card']};border:1px solid {P['border']};border-radius:18px;padding:1rem;box-shadow:0 12px 30px rgba(0,0,0,.18)}}
.score-bar{{background:linear-gradient(135deg,{P['bg2']},{P['bg3']});border:1px solid {P['border']};border-radius:20px;padding:1.7rem;color:{P['text']};text-align:center;margin-bottom:1.4rem;box-shadow:0 14px 30px rgba(0,0,0,.22)}}
.score-bar .teams{{display:flex;align-items:center;justify-content:center;gap:1.5rem;flex-wrap:wrap}}
.score-bar .tname{{font-size:1.15rem;font-weight:800;min-width:150px}}
.score-bar .tname.home{{color:{P['home']};text-align:right}}
.score-bar .tname.away{{color:{P['away']};text-align:left}}
.score-bar .result{{font-size:2.8rem;font-weight:900;letter-spacing:.12em;color:{P['text']}}}
.score-bar .sets,.score-bar .meta{{color:{P['muted']};font-size:.82rem}}
.kpi{{background:{P['card']};border-radius:16px;padding:1rem;text-align:center;border:1px solid {P['border']};box-shadow:0 10px 24px rgba(0,0,0,.12)}}
.kpi .label{{color:{P['muted']};font-size:.68rem;text-transform:uppercase;letter-spacing:.7px;font-weight:800}}
.kpi .value{{font-size:1.7rem;font-weight:900;color:{P['text']};margin:.18rem 0}}
.kpi .detail{{font-size:.68rem;color:{P['subtle']}}}
.stTabs [data-baseweb="tab"]{{background:{P['card']};color:{P['muted']};border-radius:12px 12px 0 0;padding:9px 17px;font-weight:800;font-size:.82rem;border:1px solid {P['border']};border-bottom:none}}
.stTabs [aria-selected="true"]{{background:{P['accent1']} !important;color:#111827 !important;border-color:{P['accent1']} !important}}
div[data-baseweb="select"]>div, .stMultiSelect div[data-baseweb="select"]>div{{background:{P['card']};border-color:{P['border']};color:{P['text']};border-radius:12px}}
.stDataFrame{{border-radius:16px;overflow:hidden}}
.tactic-title{{text-align:center;font-weight:900;letter-spacing:.08em;color:{P['muted']};margin:.8rem 0 1.2rem}}
footer{{text-align:center;padding:1.5rem;color:{P['muted']};font-size:.72rem;border-top:1px solid {P['border']};margin-top:2rem}}
@media(max-width:768px){{.hero h1{{font-size:1.8rem}}.main .block-container{{padding:.5rem .7rem}}}}
</style>""", unsafe_allow_html=True)

# ─── State ────────────────────────────────────────────────────
if "matches" not in st.session_state:
    st.session_state.matches = []  # List of parsed match dicts
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "active_match" not in st.session_state:
    st.session_state.active_match = 0


# ═══════════════════════════════════════════════════════════════
# COMPONENTS
# ═══════════════════════════════════════════════════════════════

def kpi(label, value, detail=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="detail">{detail}</div></div>', unsafe_allow_html=True)

def score_bar(data):
    h = data["home_team"]["name"]; a = data["away_team"]["name"]
    sets = data["sets"]
    hs = sum(1 for s in sets if s["home_score"] > s["away_score"])
    aws = sum(1 for s in sets if s["away_score"] > s["home_score"])
    det = " | ".join(f"{s['home_score']}-{s['away_score']}" for s in sets) or "-"
    lg = data["match"].get("league",""); dt = data["match"].get("date","")
    st.markdown(f'''<div class="score-bar">
        <div class="meta">{dt} {"  /  "+lg if lg else ""}</div>
        <div class="teams">
            <div class="tname home">{h}</div>
            <div class="result">{hs} - {aws}</div>
            <div class="tname away">{a}</div>
        </div>
        <div class="sets">Sets: {det}</div>
    </div>''', unsafe_allow_html=True)


def court_svg(zone_data: dict, title: str = "", max_val: float = 0) -> str:
    """Genera SVG de cancha con zonas coloreadas por intensidad."""
    # Zonas del campo (posiciones relativas)
    zones = {
        "Z4": (30, 20, 100, 80), "Z3": (130, 20, 100, 80), "Z2": (230, 20, 100, 80),
        "Z5": (30, 100, 100, 80), "Z6": (130, 100, 100, 80), "Z1": (230, 100, 100, 80),
        "Z7": (30, 180, 100, 40), "Z8": (130, 180, 100, 40), "Z9": (230, 180, 100, 40),
    }
    if max_val == 0:
        max_val = max(zone_data.values()) if zone_data else 1

    rects = ""
    for zone, (x, y, w, h) in zones.items():
        val = zone_data.get(zone, 0)
        intensity = val / max_val if max_val > 0 else 0
        r = int(0 + intensity * 0)
        g = int(60 + intensity * 152)
        b = int(80 + intensity * 90)
        fill = f"rgb({r},{g},{b})"
        text_color = "white" if intensity > 0.3 else "#8899aa"
        rects += f'''<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="4" stroke="#2d4255" stroke-width="1"/>
        <text x="{x+w//2}" y="{y+h//2-8}" text-anchor="middle" fill="{text_color}" font-size="11" font-weight="600">{zone}</text>
        <text x="{x+w//2}" y="{y+h//2+10}" text-anchor="middle" fill="{text_color}" font-size="14" font-weight="800">{val}</text>'''

    return f'''<svg viewBox="0 0 360 230" xmlns="http://www.w3.org/2000/svg" style="max-width:360px;width:100%">
        <rect width="360" height="230" fill="{P['bg']}" rx="10"/>
        <text x="180" y="228" text-anchor="middle" fill="{P['muted']}" font-size="8">{title}</text>
        <line x1="30" y1="100" x2="330" y2="100" stroke="{P['border']}" stroke-width="1" stroke-dasharray="4"/>
        {rects}
    </svg>'''


def plotly_defaults(fig, height=380):
    fig.update_layout(
        height=height, template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(t=30, b=40, l=50, r=20),
        legend=dict(orientation="h", y=1.08, x=.5, xanchor="center"),
    )
    return fig


# ═══════════════════════════════════════════════════════════════
# LANDING PAGE
# ═══════════════════════════════════════════════════════════════

def view_landing():
    st.markdown('<div class="hero"><h1>Volei<span>Vision</span> Hub</h1><p>Plataforma de analisis y scouting de voleibol</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    files = st.file_uploader(
        "Sube archivos DataVolley (.dvw) para comenzar el analisis",
        type=["dvw"], accept_multiple_files=True,
        help="Compatible con DataVolley 4, VolleyStation Pro, Click & Scout. Puedes subir multiples partidos."
    )

    if files:
        if st.button("Analizar partidos", type="primary", use_container_width=True):
            matches = []
            bar = st.progress(0)
            for i, f in enumerate(files):
                bar.progress((i+1)/len(files), f"Procesando {f.name}...")
                try:
                    content = f.read().decode("latin-1")
                    data = DVWParser(content).parse()
                    if not data["plays"].empty:
                        data["_filename"] = f.name
                        matches.append(data)
                        st.success(f"{data['home_team']['name']} vs {data['away_team']['name']} — {len(data['plays'])} acciones")
                    else:
                        st.warning(f"{f.name}: sin datos de juego detectados")
                except Exception as e:
                    st.error(f"{f.name}: {e}")
            bar.empty()

            if matches:
                st.session_state.matches = matches
                st.session_state.view = "dashboard"
                st.session_state.active_match = 0
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

def view_dashboard():
    matches = st.session_state.matches
    if not matches:
        st.session_state.view = "landing"
        st.rerun()
        return

    # Header
    col_title, col_action = st.columns([5, 1])
    with col_title:
        st.markdown('<div class="hero" style="padding:1rem 0"><h1>Volei<span>Vision</span> Hub</h1></div>', unsafe_allow_html=True)
    with col_action:
        st.write("")
        if st.button("Cargar nuevos archivos"):
            st.session_state.matches = []
            st.session_state.view = "landing"
            st.rerun()

    # Selector de partidos
    if len(matches) > 1:
        options = [f"{m['home_team']['name']} vs {m['away_team']['name']} ({m['match']['date']})" for m in matches]
        tabs_main = ["Partido individual", "Acumulados multi-partido"]
        mode = st.radio("", tabs_main, horizontal=True, label_visibility="collapsed")

        if mode == "Acumulados multi-partido":
            render_multi_match(matches)
            return

        idx = st.selectbox("Seleccionar partido", range(len(options)), format_func=lambda i: options[i])
        st.session_state.active_match = idx

    data = matches[st.session_state.active_match]
    render_single_match(data)


# ═══════════════════════════════════════════════════════════════
# TÁCTICA AVANZADA
# ═══════════════════════════════════════════════════════════════

def _plays_with_context(data: dict) -> pd.DataFrame:
    """Añade contexto aproximado de rally: fase, recepción previa, colocador previo y rotación estimada."""
    plays = data.get("plays", pd.DataFrame()).copy()
    if plays.empty:
        return plays
    plays["fase"] = "Total"
    plays["recepcion_eval"] = "Todas"
    plays["recepcion_zona"] = "Todas"
    plays["colocador"] = "Todos"
    plays["rotacion"] = "Todas"
    plays["destino"] = plays["zona_fin"].apply(lambda z: f"Z{z}" if str(z).strip() else "Sin zona")
    plays["origen"] = plays["zona_inicio"].apply(lambda z: f"Z{z}" if str(z).strip() else "Sin zona")

    for (equipo, setn, rally), grp in plays.groupby(["equipo", "set", "rally"], sort=False):
        idxs = list(grp.index)
        recs = grp[grp["skill_code"] == "R"]
        sets = grp[grp["skill_code"] == "E"]
        rec_eval = recs.iloc[-1]["eval_code"] if not recs.empty else ""
        rec_zone = recs.iloc[-1]["zona_inicio"] if not recs.empty else ""
        setter = sets.iloc[-1]["jugador"] if not sets.empty else "Todos"
        fase = "K1" if not recs.empty else "K2"
        rot = "Todas"
        if not grp.empty:
            hs = int(grp.iloc[0].get("home_score", 0) or 0)
            as_ = int(grp.iloc[0].get("away_score", 0) or 0)
            rot_num = ((hs if equipo == "home" else as_) % 6) + 1
            rot = f"P{rot_num}"
        plays.loc[idxs, "fase"] = fase
        plays.loc[idxs, "recepcion_eval"] = rec_eval if rec_eval else "Sin recepción"
        plays.loc[idxs, "recepcion_zona"] = f"Z{rec_zone}" if str(rec_zone).strip() else "Sin zona"
        plays.loc[idxs, "colocador"] = setter
        plays.loc[idxs, "rotacion"] = rot
    return plays


def _filter_df(df, col, value):
    if value in ("Todos", "Todas", None):
        return df
    return df[df[col] == value]


def distribution_grid(df: pd.DataFrame, title: str):
    attacks = df[df["skill_code"] == "A"].copy()
    total = len(attacks)
    zones = [("Z4", "ZONA 4"), ("Z3", "ZONA 3"), ("Z2", "ZONA 2"), ("Z5", "ZONA 5"), ("Z6", "PIPE (Z6)"), ("Z1", "ZONA 1")]
    html = f'<div class="tactic-title">{title}</div><div style="display:grid;grid-template-columns:repeat(3, minmax(150px, 1fr));gap:10px;max-width:760px;margin:auto;">'
    for z, label in zones:
        zd = attacks[attacks["origen"] == z]
        n = len(zd)
        pct = round(n / total * 100) if total else 0
        kills = int((zd["eval_code"] == "#").sum()) if n else 0
        errs = int((zd["eval_code"] == "=").sum()) if n else 0
        eff = round((kills - errs) / max(n, 1) * 100)
        active = n > 0
        bg = P["accent1"] if active else ("#382a18" if DARK else "#fff7e6")
        txt = "#ffffff" if active and DARK else ("#111827" if active else P["text"])
        border = P["border"]
        html += f'''<div style="background:{bg};border:1px solid {border};border-radius:16px;min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 10px 24px rgba(0,0,0,.18);">
            <div style="font-size:.78rem;font-weight:900;letter-spacing:.08em;color:{txt};opacity:.9">{label}</div>
            <div style="font-size:2.2rem;font-weight:950;color:{txt};margin:.4rem 0;text-shadow:0 2px 8px rgba(0,0,0,.25)">{pct}%</div>
            <div style="background:rgba(0,0,0,.28);border-radius:999px;padding:.35rem .7rem;font-size:.78rem;font-weight:800;color:{txt}">Nº {n} &nbsp;|&nbsp; <span style="color:#4ade80">Eff {eff}%</span></div>
        </div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_team_comparison_bar(data):
    hn, an = data["home_team"]["name"], data["away_team"]["name"]
    summary = resumen_equipo(data)
    h, a = summary["home"], summary["away"]
    metrics = ["puntos", "att_eff", "att_kill_pct", "rec_pos_pct", "srv_aces", "srv_errors", "blk_kills"]
    labels = ["Puntos", "AT Eff%", "AT Kill%", "REC+%", "Aces", "Errores saque", "Bloqueos"]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=hn, x=labels, y=[h[m] for m in metrics], marker_color=P["home"], text=[h[m] for m in metrics], textposition="outside"))
    fig.add_trace(go.Bar(name=an, x=labels, y=[a[m] for m in metrics], marker_color=P["away"], text=[a[m] for m in metrics], textposition="outside"))
    plotly_defaults(fig, 430)
    fig.update_layout(barmode="group", title="Comparativa principal de equipos", yaxis_title="Valor")
    st.plotly_chart(fig, use_container_width=True)


def render_tactical_module(data, key_prefix="tact"):
    plays = _plays_with_context(data)
    if plays.empty:
        st.info("No hay datos tácticos disponibles.")
        return

    teams = {data["home_team"]["name"]: "home", data["away_team"]["name"]: "away"}
    c1, c2, c3 = st.columns(3)
    with c1:
        team_label = st.selectbox("Equipo", list(teams.keys()), key=f"{key_prefix}_team")
    team_code = teams[team_label]
    df = plays[plays["equipo"] == team_code].copy()
    with c2:
        fase = st.selectbox("Fase", ["Total", "K1", "K2"], key=f"{key_prefix}_fase")
    with c3:
        rot = st.selectbox("Rotación", ["Todas"] + sorted([x for x in df["rotacion"].dropna().unique() if x != "Todas"]), key=f"{key_prefix}_rot")
    df = _filter_df(df, "fase", fase if fase != "Total" else "Todos")
    df = _filter_df(df, "rotacion", rot)

    sub = st.tabs(["Distribución colocador", "Direcciones saque", "Direcciones ataque"])

    with sub[0]:
        setters = ["Todos"] + sorted([x for x in df["colocador"].dropna().unique() if x and x != "Todos"])
        recq = ["Todas"] + sorted([x for x in df["recepcion_eval"].dropna().unique() if x])
        recz = ["Todas"] + sorted([x for x in df["recepcion_zona"].dropna().unique() if x])
        a,b,c = st.columns(3)
        with a: setter = st.selectbox("Colocador", setters, key=f"{key_prefix}_setter")
        with b: rq = st.selectbox("Calidad recepción", recq, key=f"{key_prefix}_rq")
        with c: rz = st.selectbox("Zona recepción", recz, key=f"{key_prefix}_rz")
        view = _filter_df(_filter_df(_filter_df(df, "colocador", setter), "recepcion_eval", rq), "recepcion_zona", rz)
        distribution_grid(view, f"Distribución real | {team_label} | {fase} | Rot: {rot}")
        at = view[view["skill_code"] == "A"]
        if not at.empty:
            table = at.groupby(["origen", "jugador"]).agg(Balones=("skill_code","count"), Kills=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            table["Eff%"] = round((table["Kills"] - table["Errores"]) / table["Balones"].replace(0,1) * 100, 1)
            st.dataframe(table.sort_values(["Balones","Eff%"], ascending=False), use_container_width=True, hide_index=True)

    with sub[1]:
        srv = df[df["skill_code"] == "S"].copy()
        players = ["Todos"] + sorted(srv["jugador"].dropna().unique().tolist()) if not srv.empty else ["Todos"]
        player = st.selectbox("Sacador", players, key=f"{key_prefix}_srv_player")
        srv = _filter_df(srv, "jugador", player)
        if srv.empty:
            st.info("No hay saques con zonas detectadas para estos filtros.")
        else:
            dirs = srv.groupby(["origen", "destino", "tipo"]).agg(Saques=("skill_code","count"), Aces=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            dirs["Eff%"] = round((dirs["Aces"] - dirs["Errores"]) / dirs["Saques"].replace(0,1) * 100, 1)
            fig = px.sunburst(dirs, path=["origen", "destino"], values="Saques", color="Eff%", title="Mapa de direcciones de saque")
            plotly_defaults(fig, 430)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(dirs.sort_values("Saques", ascending=False), use_container_width=True, hide_index=True)

    with sub[2]:
        att = df[df["skill_code"] == "A"].copy()
        players = ["Todos"] + sorted(att["jugador"].dropna().unique().tolist()) if not att.empty else ["Todos"]
        zones = ["Todas"] + sorted(att["origen"].dropna().unique().tolist()) if not att.empty else ["Todas"]
        a,b = st.columns(2)
        with a: player = st.selectbox("Atacante", players, key=f"{key_prefix}_att_player")
        with b: zone = st.selectbox("Zona de ataque", zones, key=f"{key_prefix}_att_zone")
        att = _filter_df(_filter_df(att, "jugador", player), "origen", zone)
        if att.empty:
            st.info("No hay ataques con zonas detectadas para estos filtros.")
        else:
            dirs = att.groupby(["origen", "destino"]).agg(Ataques=("skill_code","count"), Kills=("es_punto","sum"), Errores=("es_error","sum")).reset_index()
            dirs["Eff%"] = round((dirs["Kills"] - dirs["Errores"]) / dirs["Ataques"].replace(0,1) * 100, 1)
            fig = px.density_heatmap(dirs, x="destino", y="origen", z="Ataques", text_auto=True, title="Direcciones de ataque")
            plotly_defaults(fig, 420)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(dirs.sort_values("Ataques", ascending=False), use_container_width=True, hide_index=True)


def build_accumulated_match(matches, team_name=None):
    plays_list = []
    for i, m in enumerate(matches):
        pl = m.get("plays", pd.DataFrame()).copy()
        if pl.empty:
            continue
        hn = m["home_team"]["name"]
        an = m["away_team"]["name"]
        if team_name and team_name in (hn, an):
            selected_code = "home" if hn == team_name else "away"
            pl["equipo"] = pl["equipo"].apply(lambda x: "home" if x == selected_code else "away")
        pl["match_id"] = i
        plays_list.append(pl)
    plays = pd.concat(plays_list, ignore_index=True) if plays_list else pd.DataFrame()
    return {
        "match": {"date": "Acumulado", "league": "Temporada"},
        "sets": [],
        "home_team": {"name": team_name or "Equipo acumulado"},
        "away_team": {"name": "Rivales"},
        "home_players": pd.DataFrame(),
        "away_players": pd.DataFrame(),
        "plays": plays,
    }

def render_single_match(data):
    score_bar(data)
    hn = data["home_team"]["name"]; an = data["away_team"]["name"]
    summary = resumen_equipo(data)

    tabs = st.tabs(["Resumen", "Jugadores", "Ataque", "Saque y Recepción", "Táctica Avanzada", "Por Set"])

    # ── RESUMEN ──
    with tabs[0]:
        render_team_comparison_bar(data)
        st.markdown("---")
        for tc, nm in [("home", hn), ("away", an)]:
            s = summary[tc]
            color = P["home"] if tc == "home" else P["away"]
            st.markdown(f"**{nm}**")
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            with c1: kpi("Puntos totales", s["puntos"])
            with c2: kpi("AT Eficiencia", f"{s['att_eff']}%", f"{s['att_kills']}/{s['att_total']}")
            with c3: kpi("AT Kill%", f"{s['att_kill_pct']}%")
            with c4: kpi("REC Positiva", f"{s['rec_pos_pct']}%", f"Perfecta: {s['rec_perf_pct']}%")
            with c5: kpi("Aces", s["srv_aces"], f"Errores: {s['srv_errors']}")
            with c6: kpi("Bloqueos", s["blk_kills"])
            st.markdown("---")

        # Comparativa
        h, a = summary["home"], summary["away"]
        met = ["att_eff", "att_kill_pct", "rec_pos_pct", "srv_aces", "blk_kills", "puntos"]
        lab = ["AT Eff%", "AT Kill%", "REC+%", "Aces", "Bloqueos", "Puntos"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name=hn, x=lab, y=[h[m] for m in met], marker_color=P["home"], text=[h[m] for m in met], textposition="auto"))
        fig.add_trace(go.Bar(name=an, x=lab, y=[a[m] for m in met], marker_color=P["away"], text=[a[m] for m in met], textposition="auto"))
        plotly_defaults(fig)
        fig.update_layout(barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    # ── JUGADORES ──
    with tabs[1]:
        stats = stats_por_jugador(data)
        if stats.empty:
            st.info("Sin datos de jugadores"); return

        c1, c2 = st.columns(2)
        with c1: tf = st.selectbox("Equipo", ["Todos", hn, an], key="jt")
        with c2: sf = st.selectbox("Ordenar por", ["Pts", "AT Eff%", "AT Kill%", "SQ Ace", "REC%", "BLQ K"], key="jo")

        view_df = stats if tf == "Todos" else stats[stats["Equipo"] == tf]
        st.dataframe(
            view_df.sort_values(sf, ascending=False),
            use_container_width=True, height=420, hide_index=True,
            column_config={
                "Dorsal": st.column_config.NumberColumn("#", width="small"),
                "AT Eff%": st.column_config.NumberColumn("AT Eff%", format="%.1f"),
                "REC%": st.column_config.NumberColumn("REC%", format="%.1f"),
            },
        )

        # Top anotadores
        st.markdown("#### Top anotadores")
        top = stats.nlargest(8, "Pts")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ataque", x=top["Jugador"], y=top["AT K"], marker_color=P["accent1"]))
        fig.add_trace(go.Bar(name="Ace", x=top["Jugador"], y=top["SQ Ace"], marker_color=P["accent2"]))
        fig.add_trace(go.Bar(name="Bloqueo", x=top["Jugador"], y=top["BLQ K"], marker_color=P["accent3"]))
        plotly_defaults(fig)
        fig.update_layout(barmode="stack", xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    # ── ATAQUE ──
    with tabs[2]:
        att_dist = distribucion_ataque(data)
        if att_dist.empty:
            st.info("Sin datos de zonas de ataque"); return

        for tc, nm in [("home", hn), ("away", an)]:
            st.markdown(f"#### {nm}")
            td = att_dist[att_dist["equipo"] == tc]
            if td.empty:
                continue

            c1, c2 = st.columns([1, 1.5])
            with c1:
                # Cancha SVG
                zone_kills = dict(zip(td["zona"], td["kills"].astype(int)))
                zone_total = dict(zip(td["zona"], td["total"].astype(int)))
                st.markdown("**Kills por zona**")
                st.markdown(court_svg(zone_kills, f"Kills - {nm}", max_val=max(zone_kills.values()) if zone_kills else 1), unsafe_allow_html=True)

            with c2:
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Total", x=td["zona"], y=td["total"], marker_color=P["subtle"]))
                fig.add_trace(go.Bar(name="Kills", x=td["zona"], y=td["kills"], marker_color=P["kill"]))
                fig.add_trace(go.Bar(name="Errores", x=td["zona"], y=td["errores"], marker_color=P["error"]))
                plotly_defaults(fig, 280)
                fig.update_layout(barmode="group", title_text="Ataques por zona")
                st.plotly_chart(fig, use_container_width=True)

                # Eficiencia por zona
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=td["zona"], y=td["eff"], marker_color=[P["kill"] if v > 0 else P["error"] for v in td["eff"]],
                    text=td["eff"].apply(lambda x: f"{x}%"), textposition="auto"))
                plotly_defaults(fig2, 250)
                fig2.update_layout(title_text="Eficiencia por zona (%)")
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")

    # ── SAQUE Y RECEPCION ──
    with tabs[3]:
        stats = stats_por_jugador(data)
        if stats.empty:
            return

        st.markdown("#### Analisis de saque")
        srv_cols = ["Equipo", "Dorsal", "Jugador", "SQ Ace", "SQ Err", "SQ Tot", "SQ Eff%"]
        srv_df = stats[stats["SQ Tot"] > 0][srv_cols].sort_values("SQ Ace", ascending=False)
        st.dataframe(srv_df, use_container_width=True, hide_index=True)

        fig = go.Figure()
        top_srv = srv_df.head(10)
        fig.add_trace(go.Bar(name="Aces", x=top_srv["Jugador"], y=top_srv["SQ Ace"], marker_color=P["kill"]))
        fig.add_trace(go.Bar(name="Errores", x=top_srv["Jugador"], y=top_srv["SQ Err"], marker_color=P["error"]))
        plotly_defaults(fig, 300)
        fig.update_layout(barmode="group", xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Analisis de recepcion")
        rec_cols = ["Equipo", "Dorsal", "Jugador", "REC Pos", "REC Perf", "REC Err", "REC Tot", "REC%", "REC Perf%"]
        rec_df = stats[stats["REC Tot"] > 0][rec_cols].sort_values("REC%", ascending=False)
        st.dataframe(rec_df, use_container_width=True, hide_index=True)

    # ── TÁCTICA AVANZADA ──
    with tabs[4]:
        render_tactical_module(data, key_prefix=f"single_{st.session_state.active_match}")

    # ── POR SET ──
    with tabs[5]:
        plays = data["plays"]
        if plays.empty:
            return
        sel_set = st.selectbox("Set", sorted(plays["set"].unique()), format_func=lambda x: f"Set {x}")
        sp = plays[plays["set"] == sel_set]

        for tc, nm in [("home", hn), ("away", an)]:
            st.markdown(f"#### {nm}")
            tp = sp[(sp["equipo"] == tc) & (sp["dorsal"] != 0)]
            if tp.empty:
                continue
            action_summary = tp.groupby("skill").agg(
                total=("skill", "count"),
                puntos=("es_punto", "sum"),
                errores=("es_error", "sum"),
            ).reset_index()
            action_summary.columns = ["Accion", "Total", "Puntos", "Errores"]
            st.dataframe(action_summary, hide_index=True, use_container_width=True)
        st.markdown("---")


# ═══════════════════════════════════════════════════════════════
# MULTI-PARTIDO
# ═══════════════════════════════════════════════════════════════

def render_multi_match(matches):
    st.markdown("### Acumulados multi-partido")

    # Detectar equipos comunes
    all_teams = set()
    for m in matches:
        all_teams.add(m["home_team"]["name"])
        all_teams.add(m["away_team"]["name"])

    team_sel = st.selectbox("Equipo a analizar", sorted(all_teams))

    # Acumular stats
    all_player_stats = []
    team_summaries = []
    for m in matches:
        hn = m["home_team"]["name"]; an = m["away_team"]["name"]
        if team_sel not in (hn, an):
            continue
        tc = "home" if hn == team_sel else "away"
        opponent = an if tc == "home" else hn
        summary = resumen_equipo(m)
        s = summary[tc]
        sets = m["sets"]
        ts = sum(1 for st_s in sets if (st_s["home_score"] > st_s["away_score"]) == (tc == "home"))
        os_ = sum(1 for st_s in sets if (st_s["away_score"] > st_s["home_score"]) == (tc == "home"))

        team_summaries.append({
            "Rival": opponent, "Fecha": m["match"].get("date", ""),
            "Resultado": f"{ts}-{os_}", "Victoria": ts > os_,
            "Pts": s["puntos"], "AT Eff%": s["att_eff"], "AT Kill%": s["att_kill_pct"],
            "REC+%": s["rec_pos_pct"], "Aces": s["srv_aces"], "BLQ": s["blk_kills"],
        })

        ps = stats_por_jugador(m)
        ps_team = ps[ps["Equipo"] == team_sel]
        all_player_stats.append(ps_team)

    if not team_summaries:
        st.info("No hay partidos de este equipo"); return

    # KPIs acumulados
    df_sum = pd.DataFrame(team_summaries)
    wins = df_sum["Victoria"].sum()
    losses = len(df_sum) - wins
    st.markdown(f"**{team_sel}** — {len(df_sum)} partidos  |  {wins}V - {losses}D")

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Balance", f"{wins}V - {losses}D", f"Win%: {round(wins/len(df_sum)*100,1)}%")
    with c2: kpi("AT Eff% medio", f"{round(df_sum['AT Eff%'].mean(),1)}%")
    with c3: kpi("REC+% medio", f"{round(df_sum['REC+%'].mean(),1)}%")
    with c4: kpi("Aces/partido", f"{round(df_sum['Aces'].mean(),1)}")
    with c5: kpi("BLQ/partido", f"{round(df_sum['BLQ'].mean(),1)}")

    # Tabla por partido
    st.markdown("#### Rendimiento por partido")
    st.dataframe(df_sum, use_container_width=True, hide_index=True)

    # Tendencias
    st.markdown("#### Tendencias")
    df_sum["label"] = df_sum.apply(lambda r: f"vs {r['Rival']}", axis=1)
    metr = st.multiselect("Metricas", ["AT Eff%", "AT Kill%", "REC+%", "Aces", "BLQ", "Pts"],
                          default=["AT Eff%", "REC+%"])
    if metr:
        fig = go.Figure()
        colors = [P["accent1"], P["accent3"], P["accent2"], "#ffa502", "#8854d0", "#3867d6"]
        for i, m in enumerate(metr):
            fig.add_trace(go.Scatter(x=df_sum["label"], y=df_sum[m], mode="lines+markers",
                name=m, line=dict(width=3, color=colors[i%len(colors)]), marker=dict(size=9)))
        plotly_defaults(fig)
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    # Jugadores acumulados
    if all_player_stats:
        st.markdown("#### Jugadores — Acumulado de temporada")
        combined = pd.concat(all_player_stats, ignore_index=True)
        numeric_cols = ["Pts","Err","Balance","AT K","AT Err","AT Tot","SQ Ace","SQ Err","SQ Tot",
                        "REC Pos","REC Perf","REC Err","REC Tot","BLQ K","BLQ Err","DEF Pos","DEF Err","DEF Tot"]
        grouped = combined.groupby(["Equipo","Dorsal","Jugador","Posicion"]).agg(
            Partidos=("Pts","count"), **{c: (c, "sum") for c in numeric_cols}
        ).reset_index()
        grouped["AT Eff%"] = round((grouped["AT K"]-grouped["AT Err"])/grouped["AT Tot"].replace(0,1)*100, 1)
        grouped["REC%"] = round(grouped["REC Pos"]/grouped["REC Tot"].replace(0,1)*100, 1)
        grouped["Pts/P"] = round(grouped["Pts"]/grouped["Partidos"], 1)

        sf = st.selectbox("Ordenar", ["Pts","Pts/P","AT Eff%","REC%","SQ Ace","BLQ K"], key="acum_sort")
        st.dataframe(grouped.sort_values(sf, ascending=False), use_container_width=True, height=400, hide_index=True)

    st.markdown("---")
    st.markdown("### Táctica avanzada acumulada")
    st.caption("Mismos filtros del partido individual, pero acumulando todos los partidos cargados del equipo seleccionado.")
    render_tactical_module(build_accumulated_match(matches, team_sel), key_prefix=f"acc_{team_sel}")

    # Excel export
    st.markdown("---")
    if st.button("Descargar Excel"):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_sum.to_excel(writer, sheet_name="Por Partido", index=False)
            if all_player_stats:
                grouped.to_excel(writer, sheet_name="Jugadores Acumulado", index=False)
        st.download_button("Descargar", data=output.getvalue(),
            file_name=f"VoleiVision_{team_sel}_temporada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document")


# ═══════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════

def main():
    if st.session_state.view == "landing" or not st.session_state.matches:
        view_landing()
    else:
        view_dashboard()
    st.markdown('<footer>VoleiVision Hub v1.0 — Plataforma de analisis de voleibol</footer>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
