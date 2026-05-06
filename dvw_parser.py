"""VolleyVision Hub · DataVolley parser and analysis helpers.
Robust enough for standard DVW 4 files: teams, rosters, lineups, rotations, skills, zones and phases.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

SKILL_MAP = {"S":"Saque", "R":"Recepción", "E":"Colocación", "A":"Ataque", "B":"Bloqueo", "D":"Defensa", "F":"Freeball"}
EVALS = ["#", "+", "!", "-", "/", "="]
EVAL_SCORE = {"#":4,"+":3,"!":2,"-":1,"/":0,"=":-1}
SERVE_TYPE = {"Q":"Salto potencia", "T":"Salto flotante", "N":"Saque suelo", "H":"Flotante", "M":"Mixto", "U":"Otros", "O":"Otros"}
ATTACK_TYPE = {"Q":"Rápida", "T":"Tensa", "H":"Alta", "M":"Media", "U":"Shoot", "N":"Slide", "O":"Otros"}
POSITION_MAP = {"1":"Líbero", "2":"Opuesto", "3":"Central", "4":"Receptor", "5":"Colocador", "6":"Universal"}


def _clean(v: Any) -> str:
    return str(v or "").strip().replace("\\x", "")


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        s = str(x).strip()
        if s in ("", "*", "None"):
            return default
        return int(float(s))
    except Exception:
        return default


def pct(num: float, den: float) -> float:
    return round(float(num) / float(den) * 100, 1) if den else 0.0


class DVWParser:
    def __init__(self, content: str):
        self.raw = content.replace("\r\n", "\n").replace("\r", "\n")
        self.lines = self.raw.split("\n")
        self.sections: Dict[str, List[str]] = {}
        self._split_sections()

    def _split_sections(self):
        cur = None
        for line in self.lines:
            line = line.strip()
            if line.startswith("[3") and line.endswith("]"):
                cur = line[1:-1]
                self.sections[cur] = []
            elif cur is not None:
                self.sections[cur].append(line)

    def sec(self, name: str) -> List[str]:
        return self.sections.get(name, [])

    def parse(self) -> dict:
        home_team, away_team = self._parse_teams()
        home_players = self._parse_players("3PLAYERS-H", home_team["name"], "home")
        away_players = self._parse_players("3PLAYERS-V", away_team["name"], "away")
        players = pd.DataFrame(home_players + away_players)
        combos = self._parse_attack_combinations()
        plays, lineups = self._parse_scout(home_players, away_players, combos)
        sets = self._parse_sets(plays)
        return {
            "match": self._parse_match(),
            "sets": sets,
            "home_team": home_team,
            "away_team": away_team,
            "home_players": pd.DataFrame(home_players),
            "away_players": pd.DataFrame(away_players),
            "players": players,
            "attack_combos": combos,
            "lineups": lineups,
            "plays": plays,
            "validation": self._validate(plays, lineups, sets),
        }

    def _parse_match(self) -> dict:
        info = {"date":"", "time":"", "season":"", "league":"", "phase":"", "match_number":""}
        for line in self.sec("3MATCH"):
            parts = line.split(";")
            if len(parts) > 8 and parts[0].strip():
                info.update({
                    "date": parts[0].strip(), "time": parts[1].strip(), "season": parts[2].strip(),
                    "league": parts[3].strip(), "phase": parts[4].strip(), "match_number": parts[7].strip() if len(parts)>7 else "",
                })
                break
        return info

    def _parse_teams(self) -> Tuple[dict, dict]:
        teams = []
        for line in self.sec("3TEAMS"):
            if ";" not in line: continue
            p = line.split(";")
            if len(p) >= 2 and p[1].strip():
                teams.append({"id":p[0].strip(), "name":p[1].strip(), "coach":p[3].strip() if len(p)>3 else ""})
        while len(teams) < 2:
            teams.append({"id":"", "name":"Local" if not teams else "Visitante", "coach":""})
        return teams[0], teams[1]

    def _parse_players(self, section: str, team_name: str, team_code: str) -> List[dict]:
        out = []
        for line in self.sec(section):
            if ";" not in line: continue
            p = line.split(";")
            if len(p) < 11: continue
            dorsal = _safe_int(p[1], -1)
            if dorsal < 0: continue
            surname = p[9].strip() if len(p)>9 else ""
            firstname = p[10].strip() if len(p)>10 else ""
            full = f"{surname}, {firstname}" if firstname else surname or f"#{dorsal}"
            short = f"{surname} {firstname[:1]}." if firstname else surname or f"#{dorsal}"
            is_libero = False; position = ""
            for val in p[11:18]:
                val = val.strip()
                if val == "L": is_libero = True
                if val in POSITION_MAP: position = POSITION_MAP[val]
            rotations = []
            for val in p[3:7]:
                if val.strip().isdigit(): rotations.append(int(val.strip()))
            out.append({
                "team_code": team_code, "Equipo": team_name, "dorsal": dorsal, "Dorsal": dorsal,
                "Jugador": full, "jugador_corto": short, "Posición": position or ("Líbero" if is_libero else ""),
                "es_libero": is_libero, "rotaciones_base": rotations
            })
        return out

    def _parse_attack_combinations(self) -> dict:
        combos = {}
        for line in self.sec("3ATTACKCOMBINATION"):
            p = line.split(";")
            if len(p) >= 5 and p[0].strip():
                combos[p[0].strip()] = {"code":p[0].strip(), "target_zone":p[1].strip(), "type":p[3].strip(), "description":p[4].strip()}
        return combos

    def _score_sets_from_3set(self):
        sets = []
        for line in self.sec("3SET"):
            p = line.split(";")
            if not p or p[0].strip() != "True": continue
            scores = []
            for token in p[1:5]:
                m = re.search(r"(\d+)\s*-\s*(\d+)", token)
                if m: scores.append((int(m.group(1)), int(m.group(2))))
            if scores:
                h,a = scores[-1]
                sets.append({"set": len(sets)+1, "home_score":h, "away_score":a, "duration":p[5].strip() if len(p)>5 else ""})
        return sets

    def _parse_sets(self, plays: pd.DataFrame) -> List[dict]:
        sets = self._score_sets_from_3set()
        if sets:
            return sets
        if plays.empty: return []
        out = []
        for s, g in plays.groupby("set"):
            out.append({"set": int(s), "home_score": int(g["home_score"].max()), "away_score": int(g["away_score"].max()), "duration":""})
        return out

    def _players_lookup(self, home_players, away_players):
        look = {"home":{}, "away":{}}
        for p in home_players: look["home"][p["dorsal"]] = p
        for p in away_players: look["away"][p["dorsal"]] = p
        return look

    def _extract_lineup(self, parts: List[str]) -> Tuple[List[int], List[int]]:
        vals = [_safe_int(x, -999) for x in parts[14:]]
        vals = [v for v in vals if v != -999]
        if len(vals) >= 12:
            return vals[:6], vals[6:12]
        return [], []

    def _parse_scout(self, home_players, away_players, combos) -> Tuple[pd.DataFrame, Dict[int, Dict[str, List[int]]]]:
        lookup = self._players_lookup(home_players, away_players)
        rows = []
        current_set = 1; rally = 0; home_score = 0; away_score = 0; serve_team = ""
        lineups: Dict[int, Dict[str, List[int]]] = {}
        last_rec: Dict[str, Any] = {}
        last_set: Dict[str, Any] = {}

        for raw in self.sec("3SCOUT"):
            raw = raw.strip()
            if not raw: continue
            if raw.startswith("**"):
                m = re.search(r"\*\*(\d+)set", raw)
                if m:
                    current_set = int(m.group(1)); rally = 0; home_score = 0; away_score = 0; serve_team = ""
                continue
            if not (raw.startswith("*") or raw.startswith("a")):
                continue
            parts = raw.split(";")
            code_full = parts[0]
            prefix = code_full[0]
            team = "home" if prefix == "*" else "away"
            code = code_full[1:]

            # Set/rotation/lineup metadata from DVW columns when present
            meta_set = _safe_int(parts[8], current_set) if len(parts)>8 else current_set
            if meta_set > 0: current_set = meta_set
            home_rot = _safe_int(parts[9], 0) if len(parts)>9 else 0
            away_rot = _safe_int(parts[10], 0) if len(parts)>10 else 0
            home_lu, away_lu = self._extract_lineup(parts)
            if home_lu and away_lu and current_set not in lineups:
                lineups[current_set] = {"home": home_lu, "away": away_lu, "home_rotation": home_rot, "away_rotation": away_rot}

            # Score lines
            sm = re.match(r"p(\d+):(\d+)", code)
            if sm:
                home_score = int(sm.group(1)); away_score = int(sm.group(2)); rally += 1; serve_team = ""
                continue
            if code.startswith(("P", "z", "T")) or code.startswith("$$"):
                continue
            if len(code) < 5: continue
            try: dorsal = int(code[:2])
            except Exception: continue
            skill_code = code[2]
            if skill_code not in SKILL_MAP: continue
            type_code = code[3] if len(code)>3 else ""
            eval_code = code[4] if len(code)>4 else ""
            if eval_code not in EVALS: eval_code = ""
            skill = SKILL_MAP[skill_code]
            if skill_code == "S": serve_team = team; rally += 1 if rally == 0 else 0
            phase = "K1" if serve_team and team != serve_team else "K2"
            if skill_code == "R": phase = "K1"
            if skill_code == "S": phase = "K2"
            player = lookup.get(team, {}).get(dorsal, {})
            jugador = player.get("Jugador", f"#{dorsal}")
            pos = player.get("Posición", "")
            combo = ""; combo_desc = ""
            if skill_code in ("A", "E"):
                after = code[5:]
                cm = re.match(r"([A-Z0-9]{2})", after)
                if cm:
                    c = cm.group(1)
                    if c in combos:
                        combo = c; combo_desc = combos[c].get("description", "")
            zm = re.search(r"~(\d)(\d)", code)
            zstart = zm.group(1) if zm else ""
            zend = zm.group(2) if zm else ""
            bm = re.search(r"[HTA-Z](\d)(?:[A-Z])?$", code.replace("~", ""))
            blockers = bm.group(1) if bm else ""
            row = {
                "raw": raw, "set": current_set, "rally": rally, "home_score": home_score, "away_score": away_score,
                "team_code": team, "equipo": team, "Equipo": "", "dorsal": dorsal, "Dorsal": dorsal, "Jugador": jugador, "Posición": pos,
                "skill_code": skill_code, "skill": skill, "tipo_code": type_code,
                "tipo": SERVE_TYPE.get(type_code, ATTACK_TYPE.get(type_code, type_code)),
                "eval_code": eval_code, "eval_score": EVAL_SCORE.get(eval_code, 0), "phase": phase,
                "home_rotation": home_rot, "away_rotation": away_rot, "rotation": home_rot if team == "home" else away_rot,
                "rotation_label": f"P{home_rot if team == 'home' else away_rot}" if (home_rot if team == 'home' else away_rot) else "",
                "serve_team": serve_team, "zona_inicio": zstart, "zona_fin": zend,
                "origen": f"Z{zstart}" if zstart else "Sin zona", "destino": f"Z{zend}" if zend else "Sin zona",
                "combo": combo, "combo_desc": combo_desc, "num_bloqueadores": blockers,
                "es_punto": eval_code == "#", "es_error": eval_code == "=",
                "team_score": home_score if team == "home" else away_score,
                "opp_score": away_score if team == "home" else home_score,
            }
            if skill_code == "R":
                last_rec[team] = row
            if skill_code == "E":
                last_set[team] = row
                # reception context
                rec = last_rec.get(team, {})
                row["rec_eval"] = rec.get("eval_code", "")
                row["rec_zone"] = rec.get("destino", "")
            if skill_code == "A":
                rec = last_rec.get(team, {})
                setr = last_set.get(team, {})
                row["rec_eval"] = rec.get("eval_code", "")
                row["rec_zone"] = rec.get("destino", "")
                row["setter"] = setr.get("Jugador", "")
                row["set_combo"] = setr.get("combo", "")
            rows.append(row)

        df = pd.DataFrame(rows)
        if not df.empty:
            for c in ["home_rotation", "away_rotation", "rotation", "home_score", "away_score", "team_score", "opp_score", "set", "rally"]:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        return df, lineups

    def _validate(self, plays: pd.DataFrame, lineups: dict, sets: list) -> dict:
        if plays.empty:
            return {"ok": False, "issues": ["No se han detectado acciones de scouting."]}
        issues = []
        for c, label in [("zona_inicio", "zonas de origen"), ("zona_fin", "zonas de destino")]:
            if c in plays and (plays[c].astype(str) != "").sum() == 0: issues.append(f"No hay {label} codificadas.")
        if not lineups: issues.append("No se han detectado formaciones/lineups.")
        if not sets: issues.append("No se han detectado sets.")
        return {"ok": len(issues)==0, "issues": issues, "actions": int(len(plays)), "sets": len(sets), "lineup_sets": len(lineups)}


def attach_team_names(data: dict) -> dict:
    plays = data["plays"].copy()
    if not plays.empty:
        h = data["home_team"]["name"]; a = data["away_team"]["name"]
        plays["Equipo"] = plays["team_code"].map({"home": h, "away": a})
        plays["Rival"] = plays["team_code"].map({"home": a, "away": h})
    data["plays"] = plays
    return data


def filter_plays(plays: pd.DataFrame, team_name: str="Todos", phase: str="Total", rotation: str="Todas", desde_punto: int=0, player: str="Todos", skill: Optional[str]=None) -> pd.DataFrame:
    df = plays.copy()
    if skill: df = df[df["skill_code"] == skill]
    if team_name != "Todos": df = df[df["Equipo"] == team_name]
    if phase != "Total": df = df[df["phase"] == phase]
    if rotation != "Todas":
        r = int(str(rotation).replace("P", ""))
        df = df[df["rotation"] == r]
    if desde_punto:
        df = df[df["team_score"] >= int(desde_punto)]
    if player != "Todos": df = df[df["Jugador"] == player]
    return df


def skill_summary(df: pd.DataFrame, skill_code: str, group_cols: List[str]) -> pd.DataFrame:
    d = df[df["skill_code"] == skill_code].copy()
    for gc in group_cols:
        if gc not in d.columns:
            d[gc] = ""
    if d.empty:
        return pd.DataFrame(columns=group_cols + ["Total", "#", "+", "!", "-", "/", "=", "#+!%", "#%", "Eff%"])
    for ev in EVALS:
        d[ev] = (d["eval_code"] == ev).astype(int)
    g = d.groupby(group_cols, dropna=False).agg(Total=("skill_code", "count"), **{ev:(ev,"sum") for ev in EVALS}).reset_index()
    g["#+!%"] = ((g["#"] + g["+"] + g["!"]) / g["Total"].replace(0, pd.NA) * 100).fillna(0).round(1)
    g["#%"] = (g["#"] / g["Total"].replace(0, pd.NA) * 100).fillna(0).round(1)
    g["Eff%"] = ((g["#"] - g["="]) / g["Total"].replace(0, pd.NA) * 100).fillna(0).round(1)
    return g


def player_report(data: dict) -> pd.DataFrame:
    plays = data["plays"]
    if plays.empty: return pd.DataFrame()
    rows = []
    rosters = pd.concat([data["home_players"], data["away_players"]], ignore_index=True)
    for _, p in rosters.iterrows():
        pp = plays[(plays["Equipo"] == p["Equipo"]) & (plays["dorsal"] == p["dorsal"])]
        def cnt(sk, ev=None):
            x = pp[pp["skill_code"] == sk]
            return int((x["eval_code"] == ev).sum()) if ev else int(len(x))
        at_t=cnt("A"); at_k=cnt("A","#"); at_e=cnt("A","="); at_b=int((pp[(pp.skill_code=="A")]["eval_code"].isin(["/","-"])).sum()) if not pp.empty else 0
        sq_t=cnt("S"); sq_a=cnt("S","#"); sq_e=cnt("S","=")
        rec_t=cnt("R"); rec_h=cnt("R","#"); rec_p=cnt("R","+"); rec_m=cnt("R","!"); rec_e=cnt("R","=")
        blq_t=cnt("B"); blq_k=cnt("B","#"); blq_e=cnt("B","=")
        pts=at_k+sq_a+blq_k; err=at_e+sq_e+rec_e+blq_e
        rows.append({"Equipo":p["Equipo"], "#":p["Dorsal"], "Jugador":p["Jugador"], "Posición":p.get("Posición",""),
                     "PTS":pts, "W-L":pts-err, "SQ Tot":sq_t, "SQ #":sq_a, "SQ =":sq_e,
                     "REC Tot":rec_t, "REC #":rec_h, "REC +":rec_p, "REC !":rec_m, "REC =":rec_e, "REC #+!%":pct(rec_h+rec_p+rec_m, rec_t), "REC #%":pct(rec_h, rec_t),
                     "AT Tot":at_t, "AT #":at_k, "AT =":at_e, "AT /-":at_b, "AT Eff%":pct(at_k-at_e, at_t), "AT #%":pct(at_k, at_t),
                     "BLQ Tot":blq_t, "BLQ #":blq_k, "BLQ =":blq_e})
    return pd.DataFrame(rows)


def team_names(data: dict) -> List[str]:
    return [data["home_team"]["name"], data["away_team"]["name"]]
