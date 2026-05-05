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

# ─── Paleta ───────────────────────────────────────────────────
P = {
    "bg": "#0f1923", "bg2": "#1a2634", "bg3": "#243447",
    "card": "#1e2d3d", "border": "#2d4255",
    "text": "#e8edf2", "muted": "#8899aa", "subtle": "#5a6f82",
    "accent1": "#00d4aa", "accent2": "#0099ff", "accent3": "#ff6b35",
    "home": "#00d4aa", "away": "#ff6b35",
    "kill": "#00d4aa", "error": "#ff4757", "pos": "#2ed573",
    "white": "#ffffff", "surface": "#f5f7fa",
}

# ─── CSS ──────────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}
.main{{background:{P['surface']}}}
.main .block-container{{padding-top:.8rem;max-width:1400px}}
section[data-testid="stSidebar"]{{display:none}}
.hero{{text-align:center;padding:3rem 1rem 1.5rem}}
.hero h1{{font-size:2.8rem;font-weight:800;color:{P['bg']};margin:0}}
.hero h1 span{{color:{P['accent1']}}}
.hero p{{color:{P['muted']};font-size:1.1rem;margin-top:.3rem}}
.score-bar{{background:linear-gradient(135deg,{P['bg']},{P['bg2']});border-radius:14px;padding:1.8rem;color:white;text-align:center;margin-bottom:1.5rem}}
.score-bar .teams{{display:flex;align-items:center;justify-content:center;gap:1.5rem;flex-wrap:wrap}}
.score-bar .tname{{font-size:1.2rem;font-weight:700;min-width:140px}}
.score-bar .tname.home{{color:{P['home']};text-align:right}}
.score-bar .tname.away{{color:{P['accent3']};text-align:left}}
.score-bar .result{{font-size:2.6rem;font-weight:900;letter-spacing:.12em;color:white}}
.score-bar .sets{{color:{P['muted']};font-size:.85rem;margin-top:.4rem}}
.score-bar .meta{{color:{P['subtle']};font-size:.78rem;margin-bottom:.5rem}}
.kpi{{background:white;border-radius:10px;padding:.9rem;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06);border-top:3px solid {P['accent1']}}}
.kpi .label{{color:{P['muted']};font-size:.68rem;text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
.kpi .value{{font-size:1.6rem;font-weight:700;color:{P['bg']};margin:.15rem 0}}
.kpi .detail{{font-size:.65rem;color:{P['subtle']}}}
.stTabs [data-baseweb="tab"]{{background:white;border-radius:8px 8px 0 0;padding:8px 16px;font-weight:600;font-size:.82rem;border:1px solid #e2e8f0;border-bottom:none}}
.stTabs [aria-selected="true"]{{background:{P['bg']} !important;color:{P['accent1']} !important;border-color:{P['bg']} !important}}
.match-item{{background:white;border-radius:10px;padding:.8rem 1rem;margin-bottom:.5rem;border-left:4px solid {P['accent1']};box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.match-item:hover{{box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.match-item .title{{font-weight:600;color:{P['bg']};font-size:.9rem}}
.match-item .sub{{color:{P['muted']};font-size:.75rem}}
footer{{text-align:center;padding:1.5rem;color:{P['muted']};font-size:.7rem;border-top:1px solid #e2e8f0;margin-top:2rem}}
@media(max-width:768px){{.hero h1{{font-size:1.8rem}}.main .block-container{{padding:.5rem .6rem}}}}
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


def render_single_match(data):
    score_bar(data)
    hn = data["home_team"]["name"]; an = data["away_team"]["name"]
    summary = resumen_equipo(data)

    tabs = st.tabs(["Resumen", "Jugadores", "Ataque", "Saque y Recepcion", "Por Set"])

    # ── RESUMEN ──
    with tabs[0]:
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

    # ── POR SET ──
    with tabs[4]:
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
