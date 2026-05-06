from __future__ import annotations
import io, zipfile, textwrap
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openpyxl import Workbook
from dvw_parser import DVWParser, attach_team_names, team_names, filter_plays, skill_summary, player_report, EVALS, pct

st.set_page_config(page_title="VolleyVision Hub", page_icon="🏐", layout="wide", initial_sidebar_state="collapsed")

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
.pro-table{max-height:var(--table-height,360px);overflow:auto;border:1px solid var(--line);border-radius:18px;background:linear-gradient(180deg,#111d2c,#0b1420);box-shadow:0 14px 30px rgba(0,0,0,.16);margin:.75rem 0 1.15rem}.pro-table table{width:100%;border-collapse:separate;border-spacing:0;color:#eaf1f8;font-size:.84rem}.pro-table th{position:sticky;top:0;z-index:2;background:#f59e0b;color:#06101a;text-align:center;padding:.72rem .55rem;font-weight:900;white-space:nowrap}.pro-table td{padding:.58rem .55rem;border-bottom:1px solid rgba(148,163,184,.17);text-align:center;white-space:nowrap}.pro-table tr:nth-child(even) td{background:rgba(255,255,255,.025)}.pro-table tr:hover td{background:rgba(245,158,11,.10)}.pro-table td:first-child,.pro-table th:first-child{text-align:left}.cell-good{color:#22c55e!important;font-weight:900}.cell-bad{color:#ef4444!important;font-weight:900}.cell-warn{color:#f59e0b!important;font-weight:900}.match-report-block{border:1px solid #30445c;background:linear-gradient(180deg,rgba(20,34,53,.95),rgba(9,18,30,.95));border-radius:22px;padding:1rem;margin:1rem 0;box-shadow:0 18px 40px rgba(0,0,0,.20)}.match-report-title{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:.8rem}.match-report-title h3{margin:0}.mini-help{border:1px solid #30445c;background:rgba(20,34,53,.7);border-radius:18px;padding:1rem;margin:.75rem 0;color:#c7d2e0}.insight{border-left:4px solid var(--accent);background:rgba(245,158,11,.08);border-radius:14px;padding:.9rem 1rem;margin:.7rem 0;color:#f4f7fb}.court-note{font-size:.78rem;color:#9aa7b7;text-align:center;margin-top:.3rem}
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

def pro_table(df: pd.DataFrame, height: int = 360, title: str = ""):
    """Tabla HTML oscura y compacta para evitar bloques blancos de Streamlit."""
    if df is None or df.empty:
        st.info("No hay datos suficientes con los filtros actuales.")
        return
    show = df.copy()
    # Reducir decimales y convertir NaN
    for c in show.columns:
        if pd.api.types.is_float_dtype(show[c]):
            show[c] = show[c].round(1)
    show = show.fillna("")
    def cls(col, val):
        try:
            v = float(val)
            if col in ("Eff%", "AT Eff%", "SQ Eff%", "REC #+!%", "REC #%", "#%", "#+!%"):
                return "cell-good" if v >= 45 else ("cell-bad" if v < 20 else "cell-warn")
            if col in ("=", "AT =", "SQ =", "REC =", "BLQ =") and v > 0:
                return "cell-bad"
            if col in ("#", "AT #", "SQ #", "REC #", "BLQ #", "PTS", "W-L") and v > 0:
                return "cell-good"
            if col in ("Balance", "W-L"):
                return "cell-good" if v > 0 else ("cell-bad" if v < 0 else "")
        except Exception:
            pass
        return ""
    html = [f'<div class="pro-table" style="--table-height:{height}px">']
    if title:
        html.append(f'<div style="padding:.8rem 1rem;font-weight:900;color:#f4f7fb;border-bottom:1px solid rgba(148,163,184,.2)">{title}</div>')
    html.append('<table><thead><tr>')
    for c in show.columns:
        html.append(f'<th>{c}</th>')
    html.append('</tr></thead><tbody>')
    for _, row in show.iterrows():
        is_total = str(row.get("Jugador", "")).upper().startswith("TOTAL") or str(row.iloc[0]).upper().startswith("TOTAL")
        tr_style = ' style="background:rgba(245,158,11,.14);font-weight:900"' if is_total else ''
        html.append(f'<tr{tr_style}>')
        for c in show.columns:
            val = row[c]
            html.append(f'<td class="{cls(c,val)}">{val}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')
    st.markdown(''.join(html), unsafe_allow_html=True)

def safe_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def combine_matches_for_team(matches, team_name: str) -> dict:
    """Combina varios partidos para una vista acumulada por equipo."""
    if not matches:
        return {}
    plays_parts = []
    home_parts = []
    away_parts = []
    sets = []
    source_files = []
    for m in matches:
        teams_here = team_names(m)
        if team_name not in teams_here:
            continue
        source_files.append(m.get('_filename', ''))
        plays = m['plays'].copy()
        plays['source_match'] = f"{m['home_team']['name']} vs {m['away_team']['name']} · {m['match'].get('date','')}"
        plays_parts.append(plays)
        if m['home_team']['name'] == team_name:
            home_parts.append(m['home_players'].copy())
            away_parts.append(m['away_players'].copy())
        else:
            home_parts.append(m['away_players'].copy())
            away_parts.append(m['home_players'].copy())
        for s in m.get('sets', []):
            sets.append({**s, 'match_label': plays['source_match'].iloc[0] if not plays.empty else ''})
    if not plays_parts:
        return matches[0]
    plays = pd.concat(plays_parts, ignore_index=True)
    # recompute generic labels so filters siguen funcionando
    plays['aggregate_team'] = plays['Equipo'].eq(team_name)
    plays['Equipo'] = plays['Equipo'].where(plays['aggregate_team'], 'Rivales acumulados')
    plays['Rival'] = plays['Rival'].where(plays['aggregate_team'], team_name)
    # normalise team code too for summaries that rely on this
    plays['team_code'] = plays['aggregate_team'].map({True:'home', False:'away'})
    home_players = pd.concat(home_parts, ignore_index=True).drop_duplicates(subset=['Equipo','dorsal']) if home_parts else pd.DataFrame(columns=['Equipo','dorsal'])
    away_players = pd.concat(away_parts, ignore_index=True).drop_duplicates(subset=['Equipo','dorsal']) if away_parts else pd.DataFrame(columns=['Equipo','dorsal'])
    if not home_players.empty:
        home_players = home_players.copy(); home_players['Equipo'] = team_name; home_players['team_code'] = 'home'
    if not away_players.empty:
        away_players = away_players.copy(); away_players['Equipo'] = 'Rivales acumulados'; away_players['team_code'] = 'away'
    plays.loc[plays['aggregate_team'], 'Equipo'] = team_name
    data = {
        'match': {'date': '', 'league': 'Vista acumulada', 'phase': '', 'season': '', 'match_number': '', 'time': ''},
        'sets': sets,
        'home_team': {'name': team_name, 'coach': ''},
        'away_team': {'name': 'Rivales acumulados', 'coach': ''},
        'home_players': home_players,
        'away_players': away_players,
        'players': pd.concat([home_players, away_players], ignore_index=True) if (len(home_players) or len(away_players)) else pd.DataFrame(),
        'attack_combos': {},
        'lineups': {},
        'plays': plays,
        'validation': {'ok': True, 'issues': [f'Vista acumulada basada en {len(source_files)} partidos. Las formaciones iniciales no se muestran en modo acumulado.']},
        'is_aggregate': True,
        'aggregate_team': team_name,
        'aggregate_matches': len(source_files),
        '_filename': 'acumulado'
    }
    return data

# Court zones coordinates: top row 4-3-2, mid 7-8-9, bottom 5-6-1
ZONE_POS = {
    "Z4": (0.5, 2.5), "Z3": (1.5, 2.5), "Z2": (2.5, 2.5),
    "Z7": (0.5, 1.5), "Z8": (1.5, 1.5), "Z9": (2.5, 1.5),
    "Z5": (0.5, 0.5), "Z6": (1.5, 0.5), "Z1": (2.5, 0.5),
    "Sin zona": (1.5, -0.25)
}
ORDER_ZONES = ["Z4","Z3","Z2","Z7","Z8","Z9","Z5","Z6","Z1"]
BOTTOM_POS = {z:(x,y) for z,(x,y) in ZONE_POS.items()}
# Mitad superior rotada 180º para que ambas pistas queden confrontadas con la red en medio
TOP_POS = {"Z2": (0.5, 3.5), "Z3": (1.5, 3.5), "Z4": (2.5, 3.5),
           "Z9": (0.5, 4.5), "Z8": (1.5, 4.5), "Z7": (2.5, 4.5),
           "Z1": (0.5, 5.5), "Z6": (1.5, 5.5), "Z5": (2.5, 5.5),
           "Sin zona": (1.5, 6.25)}

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
    fig.update_layout(height=520, margin=dict(l=10,r=10,t=45,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title=dict(text=title, font=dict(color="#f4f7fb", size=16)), xaxis=dict(visible=False, range=[0,3]), yaxis=dict(visible=False, range=[0,6]), showlegend=False)
    # Pista inferior (origen)
    for z in ORDER_ZONES:
        x,y = BOTTOM_POS[z]
        fig.add_shape(type="rect", x0=x-.48, x1=x+.48, y0=y-.48, y1=y+.48, line=dict(color="#dbe4ef", width=1), fillcolor="rgba(241,245,249,.06)", layer="below")
        fig.add_annotation(x=x,y=y,text=f"<b>{z}</b>",showarrow=False,font=dict(color="#cbd5e1", size=12))
    # Pista superior (destino), confrontada con la inferior
    for z in ORDER_ZONES:
        x,y = TOP_POS[z]
        fig.add_shape(type="rect", x0=x-.48, x1=x+.48, y0=y-.48, y1=y+.48, line=dict(color="#dbe4ef", width=1), fillcolor="rgba(241,245,249,.06)", layer="below")
        fig.add_annotation(x=x,y=y,text=f"<b>{z}</b>",showarrow=False,font=dict(color="#cbd5e1", size=12))
    # Red horizontal en el medio
    fig.add_shape(type="line", x0=0, x1=3, y0=3, y1=3, line=dict(color="#ffffff", width=4))
    fig.add_annotation(x=1.5, y=0.05, text="Origen", showarrow=False, font=dict(color="#9fb0c6", size=12))
    fig.add_annotation(x=1.5, y=5.95, text="Destino", showarrow=False, font=dict(color="#9fb0c6", size=12))
    if df is None or df.empty:
        fig.add_annotation(x=1.5,y=3,text=empty_msg,showarrow=False,font=dict(color="#f59e0b", size=14), bgcolor="rgba(7,16,24,.75)", bordercolor="#2a3b50", borderpad=10)
        return fig
    max_total = max(1, int(df["Total"].max())) if "Total" in df else 1
    for _, r in df.iterrows():
        o, d = str(r.get("origen","")), str(r.get("destino",""))
        if o not in BOTTOM_POS or d not in TOP_POS or o == "Sin zona" or d == "Sin zona":
            continue
        x0,y0 = BOTTOM_POS[o]; x1,y1 = TOP_POS[d]
        total = int(r.get("Total",1)); width = 1.5 + 5 * total / max_total
        eff = float(r.get("Eff%",0)) if r.get("Eff%",0) != "" else 0
        color = "#22c55e" if eff >= 30 else ("#ef4444" if eff < 0 else "#f59e0b")
        fig.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref="x",yref="y",axref="x",ayref="y",showarrow=True,arrowhead=3,arrowsize=1.15,arrowwidth=width,arrowcolor=color,opacity=.9,text="")
        mx,my=(x0+x1)/2,(y0+y1)/2
        fig.add_annotation(x=mx,y=my,text=str(total),showarrow=False,font=dict(color="#fff",size=11),bgcolor="rgba(0,0,0,.58)",borderpad=3)
    return fig

def lineup_html(data, set_no: int):
    lu = data.get("lineups", {}).get(set_no) or {}
    teams = [("home", data["home_team"]["name"]), ("away", data["away_team"]["name"])]
    cols = st.columns(2)
    for i,(code,name) in enumerate(teams):
        vals = lu.get(code, [])
        rot = lu.get(f"{code}_rotation", "")
        if not vals: vals = ["-","-","-","-","-","-"]
        # DataVolley suele guardar la formación como P1,P2,P3,P4,P5,P6.
        # Para dibujar la pista correctamente usamos: frontal P4-P3-P2 / fondo P5-P6-P1.
        if len(vals) >= 6:
            vals = [vals[3], vals[2], vals[1], vals[4], vals[5], vals[0]]
        with cols[i]:
            cells = "".join([f'<div class="court-cell"><div class="player-dot">{v}</div></div>' for v in vals])
            st.markdown(f"""
            <div class="lineup-card"><h3 style="text-align:center;margin:.2rem 0 .6rem;letter-spacing:.08em;font-size:1rem">{name.upper()}</h3>
            <div class="court-grid">{cells}</div><p class="muted" style="margin:.6rem 0 0"><b>{'Saque/Recepción' if not rot else 'Rotación inicial P'+str(rot)}</b></p></div>
            """, unsafe_allow_html=True)

# ----------------------------- DATA LOAD -----------------------------
def landing():
    st.markdown('<div class="hero"><h1>Volley<span>Vision</span> Hub</h1><p>Herramienta de análisis táctico para archivos DataVolley <b>.dvw</b>. Sube uno o varios partidos y obtén reportes de rendimiento, mapas de zonas, distribución, bloqueo y match plan.</p></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="three-grid">
      <div class="card"><h4>1 · Carga el partido</h4><div class="big accent">.DVW</div><div class="muted">Puedes subir un partido o varios y cambiar entre vista individual y acumulada por equipo.</div></div>
      <div class="card"><h4>2 · Explora el análisis</h4><div class="big">General · K1 · K2</div><div class="muted">Ataque, saque, recepción, bloqueo, distribución y rotaciones.</div></div>
      <div class="card"><h4>3 · Prepara el partido</h4><div class="big ok">Match Plan</div><div class="muted">Recomendaciones de saque, bloqueo y rotaciones para staff y jugadores.</div></div>
    </div>
    <div class="mini-help"><b>Cómo empezar:</b> arrastra tus archivos <b>.dvw</b>, pulsa <b>Analizar partidos</b> y usa las pestañas para revisar cada módulo. Si algún archivo no contiene zonas, colocación o rotaciones completas, la app mostrará avisos para no interpretar datos que no existen.</div>
    """, unsafe_allow_html=True)
    section("Cargar partidos")
    files = st.file_uploader("Arrastra aquí tus archivos DataVolley (.dvw)", type=["dvw"], accept_multiple_files=True)
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
    st.markdown("<div class='mini-help'>Resumen individual estilo DataVolley: puntos, saque, recepción, ataque y bloqueo. Los valores positivos aparecen en verde y los errores en rojo para lectura rápida.</div>", unsafe_allow_html=True)
    for team in team_names(data):
        df = rep[rep["Equipo"] == team].copy()
        if not df.empty:
            total = {c: df[c].sum() if pd.api.types.is_numeric_dtype(df[c]) else "" for c in df.columns}
            total["Jugador"] = "TOTAL EQUIPO"; total["#"] = ""; total["Equipo"] = team; total["Posición"] = ""
            show = pd.concat([df, pd.DataFrame([total])], ignore_index=True)
            show_cols = ["#","Jugador","Posición","PTS","W-L","SQ Tot","SQ #","SQ =","REC Tot","REC #","REC +","REC !","REC =","REC #+!%","AT Tot","AT #","AT =","AT Eff%","BLQ Tot","BLQ #","BLQ ="]
            show = show[[c for c in show_cols if c in show.columns]]
            st.markdown(f"<div class='match-report-block'><div class='match-report-title'><h3>{team}</h3><span class='muted'>Match Report</span></div>", unsafe_allow_html=True)
            pro_table(show, 460)
            st.markdown("</div>", unsafe_allow_html=True)
    section("Formaciones iniciales")
    if data.get("is_aggregate"):
        st.info("La vista acumulada no muestra formaciones iniciales. Selecciona un partido individual para revisar rotaciones y sextetos de inicio.")
    elif data.get("lineups"):
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

def _first_nonempty_rotation(data, team_name: str):
    plays = data["plays"]
    d = plays[plays["Equipo"] == team_name]
    if d.empty or "rotation" not in d:
        return "P-"
    vals = d[d["rotation"] > 0].sort_values(["set", "rally"])["rotation"].tolist()
    return f"P{int(vals[0])}" if vals else "P-"

def _top_value(df: pd.DataFrame, col: str, default="-"):
    if df is None or df.empty or col not in df.columns:
        return default
    return str(df.iloc[0].get(col, default))

def build_match_plan(data):
    plays = data["plays"]
    teams = team_names(data)
    c1,c2 = st.columns(2)
    with c1: my = st.selectbox("Mi equipo", teams, key="mp_my")
    with c2: rival = st.selectbox("Rival", [t for t in teams if t != my], key="mp_rival")
    rp = plays[plays["Equipo"] == rival].copy()
    myp = plays[plays["Equipo"] == my].copy()

    rival_start = _first_nonempty_rotation(data, rival)
    my_start = _first_nonempty_rotation(data, my)

    rival_att_zone = skill_summary(rp, "A", ["origen"]).sort_values(["Total","Eff%"], ascending=[False, False])
    rival_att_dir = skill_summary(rp, "A", ["origen","destino"]).sort_values(["Total","Eff%"], ascending=[False, False])
    rival_attackers = skill_summary(rp, "A", ["Jugador"]).sort_values(["Total","Eff%"], ascending=[False, False])
    rival_rot_attack = skill_summary(rp, "A", ["rotation_label"]).sort_values("Eff%")
    rival_rec_zone = skill_summary(rp, "R", ["destino"]).sort_values(["Eff%","Total"], ascending=[True, False])
    rival_receptors = skill_summary(rp, "R", ["Jugador"]).sort_values(["Eff%","Total"], ascending=[True, False])
    rival_serve = skill_summary(rp, "S", ["Jugador","destino"]).sort_values(["Total"], ascending=False)
    rival_setter = skill_summary(rp, "A", ["rotation_label","rec_eval","origen"]).sort_values("Total", ascending=False)
    my_serve_rot = skill_summary(myp, "S", ["rotation_label"]).sort_values(["Eff%","#"], ascending=[False, False])
    my_block_rot = skill_summary(myp, "B", ["rotation_label"]).sort_values(["#","Eff%"], ascending=[False, False])

    top_zone = _top_value(rival_att_zone, "origen")
    top_dir = "-"
    if not rival_att_dir.empty:
        top_dir = f"{rival_att_dir.iloc[0]['origen']} → {rival_att_dir.iloc[0]['destino']}"
    top_attacker = _top_value(rival_attackers, "Jugador")
    weak_rec_zone = _top_value(rival_rec_zone, "destino")
    weak_receptor = _top_value(rival_receptors, "Jugador")
    dangerous_rot = _top_value(skill_summary(rp, "A", ["rotation_label"]).sort_values(["#","Eff%"], ascending=[False, False]), "rotation_label")
    weak_rot = _top_value(rival_rot_attack, "rotation_label")
    my_best_serve_rot = _top_value(my_serve_rot, "rotation_label")
    my_best_block_rot = _top_value(my_block_rot, "rotation_label")
    rec_neg_dist = rival_setter[rival_setter["rec_eval"].isin(["-","/","="])] if not rival_setter.empty and "rec_eval" in rival_setter else pd.DataFrame()
    setter_neg_target = _top_value(rec_neg_dist, "origen") if not rec_neg_dist.empty else top_zone

    # Heurística inicial: buscar que nuestro mejor saque/bloqueo llegue pronto contra rotación vulnerable o atacante dominante.
    suggested_rotation = my_best_serve_rot if my_best_serve_rot != "-" else (my_best_block_rot if my_best_block_rot != "-" else my_start)
    if suggested_rotation == "": suggested_rotation = my_start

    insights = []
    insights.append(("Rotación inicial recomendada", f"Empezar en {suggested_rotation}", f"El rival suele empezar en {rival_start}. La idea es que nuestro saque/bloqueo fuerte aparezca pronto y presione su zona débil de recepción ({weak_rec_zone})."))
    insights.append(("Plan de saque", f"Buscar {weak_rec_zone} / {weak_receptor}", f"El rival baja rendimiento en esa zona/receptor. Repetir hasta que ajuste o cambie la línea de recepción."))
    insights.append(("Plan de bloqueo", f"Prioridad {top_zone}", f"El rival carga mucho el ataque por {top_zone}. La dirección más repetida detectada es {top_dir}."))
    insights.append(("Plan contra el colocador", f"Recepción negativa → {setter_neg_target}", "Cuando el rival no recibe cómodo, conviene preparar bloqueo-defensa sobre su salida más recurrente."))
    insights.append(("Rotación a presionar", f"{weak_rot}", "Rotación rival con menor eficiencia ofensiva detectada. Es buen momento para arriesgar más con el saque."))

    return {"my":my,"rival":rival,"rival_start":rival_start,"my_start":my_start,"suggested_rotation":suggested_rotation,
            "top_zone":top_zone,"top_dir":top_dir,"top_attacker":top_attacker,"weak_rec_zone":weak_rec_zone,
            "weak_receptor":weak_receptor,"dangerous_rot":dangerous_rot,"weak_rot":weak_rot,"setter_neg_target":setter_neg_target,
            "att_zone":rival_att_zone,"att_dir":rival_att_dir,"attackers":rival_attackers,"rec_zone":rival_rec_zone,
            "receptors":rival_receptors,"serve":rival_serve,"setter":rival_setter,"my_serve_rot":my_serve_rot,"my_block_rot":my_block_rot,
            "insights":insights}

def page_match_plan(data):
    section("Match Plan")
    if data.get("is_aggregate"):
        st.info("El Match Plan funciona mejor en partido individual o en acumulado del rival cuando subes varios partidos suyos. Si cargas varios partidos del mismo equipo, las recomendaciones se basarán en su tendencia acumulada.")
    plan = build_match_plan(data)
    st.markdown(f"<h1>Match Plan · {plan['my']} vs <span class='accent'>{plan['rival']}</span></h1>", unsafe_allow_html=True)
    st.markdown("<div class='mini-help'>Informe táctico orientado a tomar decisiones: rotación inicial, plan de saque, bloqueo-defensa y tendencias del rival. Está pensado para imprimir o usar en banquillo.</div>", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: card("Inicio rival habitual", plan["rival_start"], "Rotación inicial detectada")
    with c2: card("Nuestra rotación sugerida", plan["suggested_rotation"], "Por saque/bloqueo y emparejamiento")
    with c3: card("Atacante prioritario", plan["top_attacker"], "Mayor volumen/impacto")
    with c4: card("Zona a castigar", plan["weak_rec_zone"], f"Receptor: {plan['weak_receptor']}")

    st.markdown("### Resumen ejecutivo")
    for title, action, evidence in plan["insights"]:
        st.markdown(f"<div class='insight'><b>{title}:</b> {action}<br><span class='muted'>{evidence}</span></div>", unsafe_allow_html=True)

    tabs = st.tabs(["Rotación inicial", "Plan de saque", "Bloqueo-defensa", "Ataque rival", "Recepción rival", "Colocador rival", "Hoja imprimible"])
    with tabs[0]:
        st.markdown("### Decisión de salida")
        st.success(f"Recomendación: empezar en **{plan['suggested_rotation']}**. El rival aparece como inicio habitual en **{plan['rival_start']}**.")
        st.markdown(f"""
        <div class='mini-help'>
        <b>Lectura táctica:</b> si el rival confirma su salida en {plan['rival_start']}, buscamos que nuestro saque/bloqueo entre pronto contra su recepción más vulnerable ({plan['weak_rec_zone']}) y contra su salida ofensiva principal ({plan['top_zone']}).
        </div>
        """, unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1: pro_table(plan["my_serve_rot"], 280, "Nuestras rotaciones de saque")
        with c2: pro_table(plan["my_block_rot"], 280, "Nuestras rotaciones de bloqueo")
    with tabs[1]:
        st.markdown("### Plan de saque")
        st.markdown(f"<div class='insight'><b>Objetivo principal:</b> sacar hacia {plan['weak_rec_zone']} y cargar sobre {plan['weak_receptor']}.<br><span class='muted'>Si el rival ajusta recepción, alternar con saque a la zona adyacente para mantenerlo incómodo.</span></div>", unsafe_allow_html=True)
        pro_table(plan["rec_zone"], 300, "Recepción rival por zona")
        pro_table(plan["receptors"], 300, "Receptores rivales")
        pro_table(plan["serve"], 300, "Tendencias de saque rival")
    with tabs[2]:
        st.markdown("### Bloqueo-defensa")
        st.markdown(f"<div class='insight'><b>Prioridad:</b> preparar bloqueo sobre {plan['top_zone']} y lectura sobre {plan['top_attacker']}.<br><span class='muted'>Dirección repetida: {plan['top_dir']}. En recepción negativa rival, preparar salida a {plan['setter_neg_target']}.</span></div>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1: pro_table(plan["att_zone"], 320, "Zonas de ataque rival")
        with c2: pro_table(plan["att_dir"], 320, "Direcciones de ataque rival")
    with tabs[3]:
        pro_table(plan["attackers"], 360, "Atacantes rivales")
        pro_table(plan["att_zone"], 360, "Ataque rival por zona")
    with tabs[4]:
        pro_table(plan["receptors"], 360, "Recepción por jugador")
        pro_table(plan["rec_zone"], 360, "Recepción por zona")
    with tabs[5]:
        st.markdown(f"<div class='insight'><b>Con recepción negativa:</b> tendencia hacia {plan['setter_neg_target']}. Preparar bloqueo-defensa ahí.</div>", unsafe_allow_html=True)
        pro_table(plan["setter"], 420, "Distribución rival por rotación y calidad de recepción")
    with tabs[6]:
        st.markdown(f"""
        <div class='print-sheet'>
        <h2>Match Plan · {plan['my']} vs {plan['rival']}</h2>
        <h3>Rotación inicial</h3>
        <p><b>Empezar en:</b> {plan['suggested_rotation']} · <b>Rival suele empezar:</b> {plan['rival_start']}</p>
        <h3>Plan de saque</h3>
        <ul><li>Buscar {plan['weak_rec_zone']} / {plan['weak_receptor']}.</li><li>Repetir si baja su recepción positiva. Alternar si ajustan.</li></ul>
        <h3>Plan de bloqueo-defensa</h3>
        <ul><li>Prioridad sobre {plan['top_zone']}.</li><li>Atacante a vigilar: {plan['top_attacker']}.</li><li>Dirección repetida: {plan['top_dir']}.</li></ul>
        <h3>Plan contra el colocador</h3>
        <ul><li>Con recepción negativa rival, preparar salida a {plan['setter_neg_target']}.</li><li>En money time, no cambiar el plan por una acción aislada.</li></ul>
        <h3>Mensaje al equipo</h3>
        <p>Constancia con el saque, bloqueo disciplinado y defensa preparada detrás de la prioridad marcada.</p>
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
    data = matches[st.session_state.active_match]
    if len(matches) > 1:
        view_mode = st.radio("Vista", ["Partido individual", "Acumulado por equipo"], horizontal=True)
        if view_mode == "Partido individual":
            labels = [f"{m['home_team']['name']} vs {m['away_team']['name']} · {m['match'].get('date','')}" for m in matches]
            idx = st.selectbox("Partido", range(len(matches)), format_func=lambda i: labels[i])
            st.session_state.active_match = idx
            data = matches[st.session_state.active_match]
        else:
            counts = {}
            for m in matches:
                for t in team_names(m):
                    counts[t] = counts.get(t, 0) + 1
            items = sorted(counts.keys(), key=lambda k: (-counts[k], k))
            agg_team = st.selectbox("Equipo para acumulado", items, format_func=lambda t: f"{t} ({counts[t]} partidos)")
            data = combine_matches_for_team(matches, agg_team)
            st.markdown(f"<div class='mini-help'><b>Vista acumulada:</b> {agg_team} · {counts[agg_team]} partidos cargados. Ahora puedes estudiar tendencias acumuladas del mismo equipo en ataque, saque, recepción, bloqueo y distribución.</div>", unsafe_allow_html=True)
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
    st.markdown('<div class="footer">VolleyVision Hub · creado por Marc Riverola Castellà</div>', unsafe_allow_html=True)

if "matches" not in st.session_state:
    st.session_state.matches = []
if "active_match" not in st.session_state:
    st.session_state.active_match = 0

if not st.session_state.matches:
    landing()
else:
    top1, top2 = st.columns([5,1])
    with top1: st.markdown("# VolleyVision Hub")
    with top2:
        if st.button("Nuevo análisis"):
            st.session_state.matches=[]; st.rerun()
    dashboard()
