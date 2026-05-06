from __future__ import annotations
import io, zipfile, textwrap
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openpyxl import Workbook
from dvw_parser import DVWParser, attach_team_names, team_names, filter_plays, skill_summary, player_report, EVALS, pct

st.set_page_config(page_title="VolleyVision Hub V2.0", page_icon="🏐", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------- THEME -----------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
:root{--bg:#071018;--panel:#101b29;--panel2:#142235;--line:#2a3b50;--text:#f4f7fb;--muted:#9aa7b7;--accent:#f59e0b;--green:#22c55e;--red:#ef4444;--cyan:#22d3ee;}
html, body, [class*="css"]{font-family:Inter,system-ui,sans-serif!important;}
.stApp{background:radial-gradient(circle at top left,#13243a 0,#071018 32%,#050b11 100%);color:var(--text);} 
.main .block-container{max-width:1500px;padding-top:1rem;padding-bottom:2rem;}
section[data-testid="stSidebar"]{display:none;}
h1,h2,h3{letter-spacing:-.035em} h1{font-weight:900} h2{font-weight:850;margin-top:1.4rem}.muted{color:var(--muted)}
.hero{border:1px solid var(--line);background:linear-gradient(135deg,rgba(20,34,53,.95),rgba(8,16,25,.95));border-radius:26px;padding:2rem;margin:.4rem 0 1.2rem;box-shadow:0 20px 60px rgba(0,0,0,.22)}
.hero h1{font-size:clamp(2rem,4vw,4.2rem);line-height:.95;margin:0}.hero span{color:var(--accent)}.hero p{font-size:1.05rem;color:var(--muted);max-width:850px}
.card{background:linear-gradient(180deg,rgba(20,34,53,.94),rgba(12,22,34,.94));border:1px solid var(--line);border-radius:20px;padding:1.1rem;box-shadow:0 14px 32px rgba(0,0,0,.18);min-height:88px}.card h4{margin:.1rem 0 .6rem;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.11em}.card .big{font-size:clamp(1.5rem,2.4vw,2.3rem);font-weight:900}.ok{color:var(--green)}.bad{color:var(--red)}.accent{color:var(--accent)}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin:.8rem 0 1rem}.pro-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.three-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}
@media(max-width:950px){.pro-grid,.three-grid{grid-template-columns:1fr}.main .block-container{padding-left:.7rem;padding-right:.7rem}.hero{padding:1.2rem}}
.stTabs [data-baseweb="tab-list"]{gap:.35rem;border-bottom:1px solid var(--line);flex-wrap:wrap}.stTabs [data-baseweb="tab"]{height:48px;background:#101a28;border:1px solid var(--line);border-bottom:0;border-radius:12px 12px 0 0;padding:0 1rem;font-weight:800;color:#b6c0cf}.stTabs [aria-selected="true"]{background:var(--accent)!important;color:#071018!important;border-color:var(--accent)!important}
div[data-testid="stSelectbox"] label, div[data-testid="stMultiSelect"] label, div[data-testid="stNumberInput"] label{color:#b7c1ce!important;font-weight:700;font-size:.85rem!important}
.stButton button,.stDownloadButton button{border-radius:14px!important;border:1px solid var(--line)!important;background:#142235!important;color:var(--text)!important;font-weight:800!important;padding:.65rem 1rem!important}.stButton button[kind="primary"]{background:linear-gradient(135deg,#f59e0b,#f97316)!important;color:#071018!important;border:0!important}
[data-testid="stFileUploader"]{border:2px dashed #33475f;border-radius:22px;background:rgba(20,34,53,.6);padding:1rem}[data-testid="stFileUploader"] section{background:transparent!important}
.table-wrap{border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#101b29;margin:.6rem 0 1rem}.section-title{display:flex;align-items:center;gap:.6rem;margin:1.2rem 0 .65rem}.section-title:before{content:"";width:8px;height:28px;border-radius:8px;background:var(--accent)}
.lineup-card{background:#132235;border:1px solid #30445c;border-radius:20px;padding:.75rem;max-width:430px;margin:auto}.court-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;background:#fff;padding:6px;border-radius:10px}.court-cell{background:#f59e0b;min-height:86px;display:flex;align-items:center;justify-content:center;color:#111827;font-weight:900;font-size:1.3rem}.player-dot{background:#f8fafc;border:2px solid #e5e7eb;border-radius:999px;width:58px;height:58px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 18px rgba(0,0,0,.3)}
.print-sheet{background:#fff;color:#111827;border-radius:18px;padding:1.4rem}.print-sheet h2,.print-sheet h3{color:#111827}.footer{color:#8b98aa;text-align:center;margin:2rem 0 0;border-top:1px solid var(--line);padding-top:1rem;font-size:.85rem}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------- CACHE -----------------------------
@st.cache_data(show_spinner=False)
def parse_file_cached(name: str, content_bytes: bytes) -> dict:
    text = content_bytes.decode("latin-1", errors="ignore")
    data = attach_team_names(DVWParser(text).parse())
    data["_filename"] = name
    return data

# ----------------------------- UI HELPERS -----------------------------
def card(title, value, detail="", cls=""):
    st.markdown(f'<div class="card"><h4>{title}</h4><div class="big {cls}">{value}</div><div class="muted">{detail}</div></div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title"><h2>{title}</h2></div>', unsafe_allow_html=True)

def pro_table(df: pd.DataFrame, height: int = 360):
    if df is None or df.empty:
        st.info("No hay datos suficientes con los filtros actuales.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, height=height)

def safe_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

# Court zones coordinates: top row 4-3-2, mid 7-8-9, bottom 5-6-1
ZONE_POS = {
    "Z4": (0.5, 2.5), "Z3": (1.5, 2.5), "Z2": (2.5, 2.5),
    "Z7": (0.5, 1.5), "Z8": (1.5, 1.5), "Z9": (2.5, 1.5),
    "Z5": (0.5, 0.5), "Z6": (1.5, 0.5), "Z1": (2.5, 0.5),
    "Sin zona": (1.5, -0.25)
}
ORDER_ZONES = ["Z4","Z3","Z2","Z7","Z8","Z9","Z5","Z6","Z1"]

def court_heat(zone_df: pd.DataFrame, value_col="Eff%", count_col="Total", title="", show_empty=True):
    fig = go.Figure()
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=40,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title=dict(text=title, font=dict(color="#f4f7fb", size=16)), xaxis=dict(visible=False, range=[0,3]), yaxis=dict(visible=False, range=[0,3]), showlegend=False)
    val_map = {}
    cnt_map = {}
    if zone_df is not None and not zone_df.empty:
        key_col = "origen" if "origen" in zone_df.columns else ("destino" if "destino" in zone_df.columns else "Zona")
        for _, r in zone_df.iterrows():
            z = str(r.get(key_col, ""))
            val_map[z] = float(r.get(value_col, 0) or 0)
            cnt_map[z] = int(r.get(count_col, 0) or r.get("Total", 0) or 0)
    for z in ORDER_ZONES:
        x,y = ZONE_POS[z]
        v = val_map.get(z, 0)
        c = cnt_map.get(z, 0)
        color = "rgba(245,158,11,.88)" if c else "rgba(35,48,64,.55)"
        if c and v < 0: color = "rgba(239,68,68,.75)"
        if c and v >= 40: color = "rgba(34,197,94,.78)"
        fig.add_shape(type="rect", x0=x-.48, x1=x+.48, y0=y-.48, y1=y+.48, line=dict(color="#e5e7eb", width=1), fillcolor=color, layer="below")
        txt = f"<b>{z}</b><br>{v:.0f}%<br><span style='font-size:10px'>Nº {c}</span>" if c else f"<b>{z}</b><br>0%"
        fig.add_annotation(x=x,y=y,text=txt,showarrow=False,font=dict(color="#071018" if c else "#b9c2cf", size=14))
    return fig

def direction_court(df: pd.DataFrame, title="Direcciones", empty_msg="Selecciona un jugador para ver direcciones"):
    fig = go.Figure()
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=45,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title=dict(text=title, font=dict(color="#f4f7fb", size=16)), xaxis=dict(visible=False, range=[0,3]), yaxis=dict(visible=False, range=[0,3]), showlegend=False)
    for z in ORDER_ZONES:
        x,y = ZONE_POS[z]
        fig.add_shape(type="rect", x0=x-.48, x1=x+.48, y0=y-.48, y1=y+.48, line=dict(color="#dbe4ef", width=1), fillcolor="rgba(241,245,249,.08)", layer="below")
        fig.add_annotation(x=x,y=y,text=f"<b>{z}</b>",showarrow=False,font=dict(color="#cbd5e1", size=13))
    if df is None or df.empty:
        fig.add_annotation(x=1.5,y=1.5,text=empty_msg,showarrow=False,font=dict(color="#f59e0b", size=14), bgcolor="rgba(7,16,24,.75)", bordercolor="#2a3b50", borderpad=10)
        return fig
    max_total = max(1, int(df["Total"].max())) if "Total" in df else 1
    for _, r in df.iterrows():
        o, d = str(r.get("origen","")), str(r.get("destino",""))
        if o not in ZONE_POS or d not in ZONE_POS or o == "Sin zona" or d == "Sin zona": continue
        x0,y0 = ZONE_POS[o]; x1,y1 = ZONE_POS[d]
        total = int(r.get("Total",1)); width = 1.5 + 5 * total / max_total
        color = "#22c55e" if float(r.get("Eff%",0)) >= 30 else ("#ef4444" if float(r.get("Eff%",0)) < 0 else "#f59e0b")
        fig.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref="x",yref="y",axref="x",ayref="y",showarrow=True,arrowhead=3,arrowsize=1.2,arrowwidth=width,arrowcolor=color,opacity=.85,text="")
        mx,my=(x0+x1)/2,(y0+y1)/2
        fig.add_annotation(x=mx,y=my,text=str(total),showarrow=False,font=dict(color="#fff",size=11),bgcolor="rgba(0,0,0,.55)",borderpad=3)
    return fig

def lineup_html(data, set_no: int):
    lu = data.get("lineups", {}).get(set_no) or {}
    teams = [("home", data["home_team"]["name"]), ("away", data["away_team"]["name"])]
    cols = st.columns(2)
    for i,(code,name) in enumerate(teams):
        vals = lu.get(code, [])
        rot = lu.get(f"{code}_rotation", "")
        if not vals: vals = ["-","-","-","-","-","-"]
        with cols[i]:
            cells = "".join([f'<div class="court-cell"><div class="player-dot">{v}</div></div>' for v in vals])
            st.markdown(f"""
            <div class="lineup-card"><h3 style="text-align:center;margin:.2rem 0 .6rem;letter-spacing:.08em;font-size:1rem">{name.upper()}</h3>
            <div class="court-grid">{cells}</div><p class="muted" style="margin:.6rem 0 0"><b>{'Saque/Recepción' if not rot else 'Rotación inicial P'+str(rot)}</b></p></div>
            """, unsafe_allow_html=True)

# ----------------------------- DATA LOAD -----------------------------
def landing():
    st.markdown('<div class="hero"><h1>Volley<span>Vision</span> Hub V2.0</h1><p>Sube archivos DataVolley <b>.dvw</b> y genera análisis táctico, match report, rotaciones, recepción, bloqueo, distribución y match plan.</p></div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: card("1 · Sube", ".dvw", "Uno o varios partidos")
    with c2: card("2 · Analiza", "K1 / K2", "Ataque, saque, recepción, bloqueo")
    with c3: card("3 · Exporta", "PDF / Excel", "Informe para staff")
    section("Cargar partidos")
    files = st.file_uploader("Arrastra aquí tus archivos DataVolley", type=["dvw"], accept_multiple_files=True)
    if files and st.button("Analizar partidos", type="primary", use_container_width=True):
        matches = []
        prog = st.progress(0)
        for i,f in enumerate(files):
            prog.progress((i+1)/len(files), f"Procesando {f.name}")
            try:
                data = parse_file_cached(f.name, f.getvalue())
                matches.append(data)
            except Exception as e:
                st.error(f"{f.name}: {e}")
        prog.empty()
        if matches:
            st.session_state.matches = matches
            st.session_state.active_match = 0
            st.rerun()

# ----------------------------- SHARED FILTERS -----------------------------
def filters(data, skill=None, include_player=False, player_label="Jugador"):
    plays = data["plays"]
    teams = ["Todos"] + team_names(data)
    c1,c2,c3,c4 = st.columns(4)
    with c1: team = st.selectbox("Equipo", teams, key=f"team_{skill}_{player_label}")
    with c2: phase = st.selectbox("Fase", ["Total","K1","K2"], key=f"phase_{skill}_{player_label}")
    with c3: rot = st.selectbox("Rotación", ["Todas"]+[f"P{i}" for i in range(1,7)], key=f"rot_{skill}_{player_label}")
    with c4: desde = st.number_input("Desde punto", min_value=0, max_value=40, value=0, step=1, key=f"pt_{skill}_{player_label}")
    player = "Todos"
    if include_player:
        base = filter_plays(plays, team, phase, rot, desde, skill=skill)
        players = ["Todos"] + sorted([x for x in base["Jugador"].dropna().unique().tolist() if x])
        player = st.selectbox(player_label, players, key=f"player_{skill}_{player_label}")
    df = filter_plays(plays, team, phase, rot, desde, player, skill)
    return df, team, phase, rot, desde, player

# ----------------------------- PAGES -----------------------------
def page_general(data):
    section("Resumen del partido")
    sets = data.get("sets", [])
    hs = sum(1 for s in sets if s["home_score"] > s["away_score"]); aws = sum(1 for s in sets if s["away_score"] > s["home_score"])
    st.markdown(f"<h1 style='font-size:2.1rem'>{data['home_team']['name']} <span class='accent'>{hs} - {aws}</span> {data['away_team']['name']}</h1><p class='muted'>{data['match'].get('date','')} · {data['match'].get('league','')}</p>", unsafe_allow_html=True)
    if sets:
        cols = st.columns(len(sets))
        for col,s in zip(cols, sets):
            with col: card(f"Set {s['set']}", f"{s['home_score']}–{s['away_score']}", s.get("duration", ""), "accent")
    rep = player_report(data)
    section("Match Report")
    for team in team_names(data):
        st.markdown(f"### {team}")
        df = rep[rep["Equipo"] == team].copy()
        if not df.empty:
            total = {c: df[c].sum() if pd.api.types.is_numeric_dtype(df[c]) else "" for c in df.columns}
            total["Jugador"] = "TOTAL EQUIPO"; total["#"] = ""; total["Equipo"] = team; total["Posición"] = ""
            show = pd.concat([df, pd.DataFrame([total])], ignore_index=True)
            pro_table(show.drop(columns=["Equipo"]), 420)
    section("Formaciones iniciales")
    if data.get("lineups"):
        set_no = st.radio("Set", sorted(data["lineups"].keys()), horizontal=True, format_func=lambda x:f"Set {x}")
        lineup_html(data, set_no)
    else:
        st.warning("Este archivo no contiene formaciones iniciales detectables.")

    section("Comparativa principal")
    rep2 = rep.groupby("Equipo").agg({"PTS":"sum","AT #":"sum","AT =":"sum","SQ #":"sum","SQ =":"sum","REC Tot":"sum","REC #":"sum","BLQ #":"sum"}).reset_index()
    if not rep2.empty:
        metrics = ["PTS","AT #","AT =","SQ #","SQ =","REC #","BLQ #"]
        fig = go.Figure()
        teams = rep2["Equipo"].tolist()
        for i, t in enumerate(teams):
            vals = [float(rep2[rep2.Equipo==t][m].iloc[0]) for m in metrics]
            if i == 0: vals = [-v for v in vals]
            fig.add_trace(go.Bar(y=metrics, x=vals, orientation="h", name=t, text=[abs(v) for v in vals], textposition="auto"))
        fig.update_layout(height=420, barmode="relative", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#f4f7fb"), xaxis=dict(title="Visitante ← | → Local", zeroline=True, gridcolor="#233244"), yaxis=dict(gridcolor="#233244"))
        st.plotly_chart(fig, use_container_width=True)

def page_attack(data):
    section("Ataque")
    df, team, phase, rot, desde, player = filters(data, "A", True, "Atacante")
    cols = st.columns(5)
    with cols[0]: card("Ataques", len(df))
    with cols[1]: card("#", int((df.eval_code=="#").sum()) if not df.empty else 0, cls="ok")
    with cols[2]: card("=", int((df.eval_code=="=").sum()) if not df.empty else 0, cls="bad")
    with cols[3]: card("Eff%", pct((df.eval_code=="#").sum()-(df.eval_code=="=").sum(), len(df)) if not df.empty else 0)
    with cols[4]: card("#%", pct((df.eval_code=="#").sum(), len(df)) if not df.empty else 0)
    z = skill_summary(df, "A", ["origen"])
    dir_df = skill_summary(df, "A", ["origen","destino"])
    c1,c2 = st.columns(2)
    with c1: st.plotly_chart(court_heat(z, "Eff%", "Total", "Eficiencia por zona de ataque"), use_container_width=True)
    with c2: st.plotly_chart(direction_court(dir_df if player != "Todos" else pd.DataFrame(), "Direcciones de ataque", "Selecciona un atacante para ver direcciones"), use_container_width=True)
    pro_table(dir_df.sort_values("Total", ascending=False) if not dir_df.empty else dir_df, 320)

def page_serve(data):
    section("Saque")
    df, team, phase, rot, desde, player = filters(data, "S", True, "Sacador")
    cols = st.columns(5)
    with cols[0]: card("Saques", len(df))
    with cols[1]: card("#", int((df.eval_code=="#").sum()) if not df.empty else 0, cls="ok")
    with cols[2]: card("=", int((df.eval_code=="=").sum()) if not df.empty else 0, cls="bad")
    with cols[3]: card("Eff%", pct((df.eval_code=="#").sum()-(df.eval_code=="=").sum(), len(df)) if not df.empty else 0)
    with cols[4]: card("Tipo top", df["tipo"].mode().iloc[0] if not df.empty and not df["tipo"].mode().empty else "-")
    z = skill_summary(df, "S", ["origen"])
    dir_df = skill_summary(df, "S", ["origen","destino"])
    c1,c2 = st.columns(2)
    with c1: st.plotly_chart(court_heat(z, "Eff%", "Total", "Eficiencia por zona de saque"), use_container_width=True)
    with c2: st.plotly_chart(direction_court(dir_df if player != "Todos" else pd.DataFrame(), "Direcciones de saque", "Selecciona un sacador para ver direcciones"), use_container_width=True)
    st.markdown("### Saque por tipo")
    pro_table(skill_summary(df, "S", ["tipo"]).sort_values("Total", ascending=False), 260)

def page_reception(data):
    section("Recepción")
    plays = data["plays"]
    df, team, phase, rot, desde, player = filters(data, "R", True, "Receptor")
    serve_types = ["Todos"] + sorted(df["tipo"].dropna().unique().tolist()) if not df.empty else ["Todos"]
    typ = st.selectbox("Tipo de saque recibido", serve_types)
    if typ != "Todos": df = df[df["tipo"] == typ]
    totals = {ev:int((df.eval_code==ev).sum()) if not df.empty else 0 for ev in EVALS}
    cols = st.columns(9)
    labels = [("Recepciones", len(df)), ("#", totals["#"]), ("+", totals["+"]), ("!", totals["!"]), ("-", totals["-"]), ("/", totals["/"]), ("=", totals["="]), ("#+!%", pct(totals["#"]+totals["+"]+totals["!"],len(df))), ("Eff%", pct(totals["#"]-totals["="],len(df)))]
    for col,(a,b) in zip(cols, labels):
        with col: card(a,b)
    st.markdown("### Recepción por tipo de saque")
    pro_table(skill_summary(df, "R", ["tipo"]).sort_values("Total", ascending=False), 240)
    c1,c2 = st.columns(2)
    z = skill_summary(df, "R", ["destino"])
    with c1: st.plotly_chart(court_heat(z.rename(columns={"destino":"origen"}), "Eff%", "Total", "Mapa de recepción"), use_container_width=True)
    with c2:
        st.markdown("### Recepción por zona")
        pro_table(z.sort_values("Total", ascending=False), 420)
    st.markdown("### Recepción según zona de saque")
    # Use origin groups 1/9, 6, 7/5
    for title, zones in [("Saque desde Z1/Z9", ["Z1","Z9"]), ("Saque desde Z6", ["Z6"]), ("Saque desde Z7/Z5", ["Z7","Z5"] )]:
        sub = df[df["origen"].isin(zones)] if not df.empty else df
        st.markdown(f"#### {title}")
        cc1, cc2 = st.columns([1,1.2])
        zz = skill_summary(sub, "R", ["destino"])
        with cc1: st.plotly_chart(court_heat(zz.rename(columns={"destino":"origen"}), "Eff%", "Total", title), use_container_width=True)
        with cc2: pro_table(zz.sort_values("Total", ascending=False), 260)
    st.caption("Zonas de contacto corporal solo se mostrarán cuando el .dvw las incluya de forma explícita. En estos archivos no aparece como campo fiable separado.")

def page_block(data):
    section("Bloqueo")
    df, team, phase, rot, desde, player = filters(data, "B", True, "Bloqueador")
    cols = st.columns(5)
    with cols[0]: card("Bloqueos", len(df))
    with cols[1]: card("BLQ #", int((df.eval_code=="#").sum()) if not df.empty else 0, cls="ok")
    with cols[2]: card("BLQ =", int((df.eval_code=="=").sum()) if not df.empty else 0, cls="bad")
    with cols[3]: card("Balance", int((df.eval_code=="#").sum()-(df.eval_code=="=").sum()) if not df.empty else 0)
    with cols[4]: card("Eff%", pct((df.eval_code=="#").sum()-(df.eval_code=="=").sum(), len(df)) if not df.empty else 0)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### Ranking de bloqueadores")
        pro_table(skill_summary(df, "B", ["Jugador"]).sort_values("#", ascending=False), 360)
    with c2:
        st.markdown("### Bloqueo por rotación")
        pro_table(skill_summary(df, "B", ["rotation_label"]).sort_values("rotation_label"), 360)
    st.markdown("### Cruce ataque rival vs bloqueo")
    rival_att = data["plays"][data["plays"].skill_code=="A"].copy()
    if team != "Todos":
        rival_att = rival_att[rival_att["Equipo"] != team]
    zone = skill_summary(rival_att, "A", ["origen"])
    pro_table(zone.sort_values("Total", ascending=False), 320)

def page_setter(data):
    section("Colocador / Distribución")
    plays = data["plays"]
    df, team, phase, rot, desde, setter = filters(data, "E", True, "Colocador")
    # Distribution based on following attacks with setter context when available
    att = filter_plays(plays, team, phase, rot, desde, skill="A")
    if setter != "Todos" and "setter" in att.columns:
        att = att[att["setter"] == setter]
    # tactical zones: combine back rows
    def tactical_zone(z):
        return {"Z7":"Z5 + Z7", "Z5":"Z5 + Z7", "Z8":"PIPE / Z6 + Z8", "Z6":"PIPE / Z6 + Z8", "Z9":"Z1 + Z9", "Z1":"Z1 + Z9"}.get(z, z)
    att = att.copy()
    if not att.empty: att["salida"] = att["origen"].map(tactical_zone)
    dist = skill_summary(att, "A", ["salida"]).sort_values("Total", ascending=False) if not att.empty else pd.DataFrame()
    total = int(dist["Total"].sum()) if not dist.empty else 0
    if not dist.empty: dist["Distribución %"] = (dist["Total"] / max(total,1) * 100).round(1)
    cols = st.columns(4)
    with cols[0]: card("Colocaciones/ataques", total)
    with cols[1]: card("Salida más usada", dist.iloc[0]["salida"] if not dist.empty else "-")
    with cols[2]: card("Eff salida top", f"{dist.iloc[0]['Eff%']}%" if not dist.empty else "-")
    with cols[3]: card("Rotación", rot)
    c1,c2 = st.columns([1,1.1])
    with c1:
        if not dist.empty:
            zd = dist.rename(columns={"salida":"origen"})
            # Map combined zones to representative positions
            zd["origen"] = zd["origen"].replace({"Z5 + Z7":"Z5", "PIPE / Z6 + Z8":"Z6", "Z1 + Z9":"Z1"})
            st.plotly_chart(court_heat(zd, "Distribución %", "Total", "Distribución táctica"), use_container_width=True)
        else:
            st.info("No hay datos de distribución con estos filtros.")
    with c2:
        st.markdown("### Jugadas más usadas")
        combos = skill_summary(att[att["combo"].astype(str)!=""], "A", ["combo", "rotation_label", "rec_eval", "origen"]) if not att.empty and "combo" in att else pd.DataFrame()
        pro_table(combos.sort_values("Total", ascending=False).head(30) if not combos.empty else combos, 420)

def build_match_plan(data):
    plays = data["plays"]
    teams = team_names(data)
    c1,c2 = st.columns(2)
    with c1: my = st.selectbox("Mi equipo", teams, key="mp_my")
    with c2: rival = st.selectbox("Rival", [t for t in teams if t != my], key="mp_rival")
    rp = plays[plays["Equipo"] == rival]
    myp = plays[plays["Equipo"] == my]
    att = skill_summary(rp, "A", ["origen"]).sort_values("Total", ascending=False)
    rec = skill_summary(rp, "R", ["destino"]).sort_values("Eff%")
    srv_target = rec.iloc[0]["destino"] if not rec.empty else "la zona débil detectada"
    top_att_zone = att.iloc[0]["origen"] if not att.empty else "-"
    eff_zone = att.sort_values("Eff%", ascending=False).iloc[0]["origen"] if not att.empty else "-"
    attackers = skill_summary(rp, "A", ["Jugador"]).sort_values("Total", ascending=False)
    top_attacker = attackers.iloc[0]["Jugador"] if not attackers.empty else "-"
    blockers = skill_summary(rp, "B", ["Jugador"]).sort_values("#", ascending=False)
    top_blocker = blockers.iloc[0]["Jugador"] if not blockers.empty else "-"
    weak_rot = skill_summary(rp, "A", ["rotation_label"]).sort_values("Eff%")
    weak_rot_label = weak_rot.iloc[0]["rotation_label"] if not weak_rot.empty else "-"
    return {"my":my,"rival":rival,"srv_target":srv_target,"top_att_zone":top_att_zone,"eff_zone":eff_zone,"top_attacker":top_attacker,"top_blocker":top_blocker,"weak_rot":weak_rot_label,"att":att,"rec":rec,"attackers":attackers,"blockers":blockers}

def page_match_plan(data):
    section("Match Plan")
    plan = build_match_plan(data)
    st.markdown(f"<h1>Match Plan · {plan['my']} vs <span class='accent'>{plan['rival']}</span></h1>", unsafe_allow_html=True)
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: card("Plan de saque", f"Sacar a {plan['srv_target']}", "Castigar la peor zona de recepción rival")
    with c2: card("Prioridad bloqueo", plan["top_att_zone"], f"Zona más utilizada. Vigilar a {plan['top_attacker']}")
    with c3: card("Zona eficiente rival", plan["eff_zone"], "Preparar bloqueo-defensa específico")
    with c4: card("Rotación a presionar", plan["weak_rot"], "Rotación con peor rendimiento detectado")
    st.markdown('</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Plan de saque", "Bloqueo-defensa", "Ataque rival", "Recepción rival", "Hoja imprimible"])
    with tabs[0]:
        st.markdown("### Objetivo")
        st.success(f"Sacar preferentemente hacia **{plan['srv_target']}** y comprobar si el receptor rival mantiene estabilidad en esa zona.")
        pro_table(plan["rec"], 340)
    with tabs[1]:
        st.markdown("### Claves de bloqueo-defensa")
        st.markdown(f"- Priorizar lectura sobre **{plan['top_att_zone']}**.\n- Preparar ayuda defensiva ante **{plan['top_attacker']}**.\n- Si la recepción rival es negativa, cerrar salida alta y no saltar antes de tiempo.\n- Bloqueador rival a vigilar cuando ataquemos: **{plan['top_blocker']}**.")
        pro_table(plan["blockers"], 300)
    with tabs[2]:
        pro_table(plan["att"], 360)
        pro_table(plan["attackers"], 360)
    with tabs[3]:
        pro_table(plan["rec"], 360)
    with tabs[4]:
        st.markdown(f"""
        <div class='print-sheet'>
        <h2>Match Plan · {plan['my']} vs {plan['rival']}</h2>
        <h3>3 ideas para el partido</h3>
        <ol>
        <li><b>Saque:</b> buscar {plan['srv_target']} y repetir si el rival baja el % de recepción positiva.</li>
        <li><b>Bloqueo:</b> prioridad sobre {plan['top_att_zone']} y sobre {plan['top_attacker']}.</li>
        <li><b>Rotación a presionar:</b> {plan['weak_rot']}.</li>
        </ol>
        <h3>Mensaje para jugadores</h3>
        <p>Ser constantes con el plan de saque, bloquear con disciplina y no cambiar el plan por una acción aislada.</p>
        </div>
        """, unsafe_allow_html=True)

def page_by_set(data):
    section("Por Set")
    plays = data["plays"]
    s = st.selectbox("Set", sorted(plays["set"].unique()), format_func=lambda x:f"Set {x}")
    sp = plays[plays["set"] == s]
    for team in team_names(data):
        st.markdown(f"### {team}")
        pro_table(sp[sp.Equipo==team].groupby(["skill","eval_code"]).size().reset_index(name="Total"), 260)

def page_export(data):
    section("Exportar")
    modules = st.multiselect("Selecciona módulos", ["Match Report","Ataque","Saque","Recepción","Bloqueo","Distribución","Acciones crudas"], default=["Match Report","Ataque","Saque","Recepción","Bloqueo"])
    def make_excel():
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            if "Match Report" in modules: player_report(data).to_excel(writer, sheet_name="Match Report", index=False)
            if "Ataque" in modules: skill_summary(data["plays"], "A", ["Equipo","Jugador","origen","destino"]).to_excel(writer, sheet_name="Ataque", index=False)
            if "Saque" in modules: skill_summary(data["plays"], "S", ["Equipo","Jugador","origen","destino","tipo"]).to_excel(writer, sheet_name="Saque", index=False)
            if "Recepción" in modules: skill_summary(data["plays"], "R", ["Equipo","Jugador","destino","tipo"]).to_excel(writer, sheet_name="Recepcion", index=False)
            if "Bloqueo" in modules: skill_summary(data["plays"], "B", ["Equipo","Jugador","rotation_label"]).to_excel(writer, sheet_name="Bloqueo", index=False)
            if "Distribución" in modules: skill_summary(data["plays"], "A", ["Equipo","combo","origen"]).to_excel(writer, sheet_name="Distribucion", index=False)
            if "Acciones crudas" in modules: data["plays"].to_excel(writer, sheet_name="Acciones", index=False)
        return out.getvalue()
    st.download_button("Descargar Excel", data=make_excel(), file_name="VolleyVision_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    st.info("PDF profesional: en esta versión se recomienda exportar Excel y usar la hoja imprimible del Match Plan desde el navegador. El PDF completo se añadirá cuando cerremos el motor final de informes.")

# ----------------------------- APP ROUTER -----------------------------
def dashboard():
    matches = st.session_state.matches
    if len(matches) > 1:
        labels = [f"{m['home_team']['name']} vs {m['away_team']['name']} · {m['match'].get('date','')}" for m in matches]
        idx = st.selectbox("Partido", range(len(matches)), format_func=lambda i: labels[i])
        st.session_state.active_match = idx
    data = matches[st.session_state.active_match]
    val = data.get("validation", {})
    if not val.get("ok", False):
        with st.expander("Avisos del archivo", expanded=False):
            for issue in val.get("issues", []): st.warning(issue)
    tabs = st.tabs(["General", "Ataque", "Saque", "Recepción", "Bloqueo", "Colocador / Distribución", "Por Set", "Match Plan", "Exportar"])
    with tabs[0]: page_general(data)
    with tabs[1]: page_attack(data)
    with tabs[2]: page_serve(data)
    with tabs[3]: page_reception(data)
    with tabs[4]: page_block(data)
    with tabs[5]: page_setter(data)
    with tabs[6]: page_by_set(data)
    with tabs[7]: page_match_plan(data)
    with tabs[8]: page_export(data)
    st.markdown('<div class="footer">VolleyVision Hub V2.0 · creado por Marc Riverola Castellà</div>', unsafe_allow_html=True)

if "matches" not in st.session_state:
    st.session_state.matches = []
if "active_match" not in st.session_state:
    st.session_state.active_match = 0

if not st.session_state.matches:
    landing()
else:
    top1, top2 = st.columns([5,1])
    with top1: st.markdown("# VolleyVision Hub V2.0")
    with top2:
        if st.button("Nuevo análisis"):
            st.session_state.matches=[]; st.rerun()
    dashboard()
