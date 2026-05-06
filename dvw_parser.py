"""
dvw_parser.py — VolleyVision Hub
Parser profesional de archivos DataVolley (.dvw)
Compatible con DataVolley 4, VolleyStation Pro, Click & Scout
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple

# ─── Mapeos ───────────────────────────────────────────────────

SKILL_MAP = {"S": "Saque", "R": "Recepcion", "E": "Colocacion",
             "A": "Ataque", "B": "Bloqueo", "D": "Defensa", "F": "Freeball"}

EVAL_MAP = {"#": "Punto", "+": "Positivo", "!": "Exclamacion",
            "-": "Negativo", "/": "Slash", "=": "Error"}

EVAL_SCORE = {"#": 4, "+": 3, "!": 2, "/": 1, "-": 0, "=": -1}

SKILL_TYPE_MAP = {
    "Q": "Rapido", "T": "Tenso", "H": "Alto", "M": "Medio",
    "U": "Shoot set", "N": "Slide", "O": "Otros",
}

POSITION_MAP = {"1": "Libero", "2": "Opuesto", "3": "Central",
                "4": "Receptor", "5": "Colocador", "6": "Universal"}


class DVWParser:
    """Parser completo de archivos .dvw"""

    def __init__(self, content: str):
        self.raw = content.replace("\r\n", "\n").replace("\r", "\n")
        self.lines = self.raw.split("\n")
        self.sections: Dict[str, List[str]] = {}
        self._split_sections()

    def parse(self) -> dict:
        match_info = self._parse_match()
        sets_info = self._parse_sets()
        home_team, away_team = self._parse_teams()
        home_players = self._parse_players("3PLAYERS-H")
        away_players = self._parse_players("3PLAYERS-V")
        attack_combos = self._parse_attack_combinations()
        plays = self._parse_scout(home_players, away_players)

        return {
            "match": match_info,
            "sets": sets_info,
            "home_team": home_team,
            "away_team": away_team,
            "home_players": pd.DataFrame(home_players) if home_players else pd.DataFrame(),
            "away_players": pd.DataFrame(away_players) if away_players else pd.DataFrame(),
            "attack_combos": attack_combos,
            "plays": pd.DataFrame(plays) if plays else pd.DataFrame(),
        }

    # ─── Secciones ────────────────────────────────────────────

    def _split_sections(self):
        current = None
        for line in self.lines:
            line = line.strip()
            if line.startswith("[3") and line.endswith("]"):
                current = line[1:-1]
                self.sections[current] = []
            elif current is not None:
                self.sections.setdefault(current, []).append(line)

    def _get_section(self, key: str) -> List[str]:
        return self.sections.get(key, [])

    # ─── Match ────────────────────────────────────────────────

    def _parse_match(self) -> dict:
        lines = self._get_section("3MATCH")
        info = {"date": "", "time": "", "season": "", "league": "", "phase": "", "match_number": ""}
        for line in lines:
            parts = line.split(";")
            if len(parts) >= 5 and parts[0].strip():
                info["date"] = parts[0].strip()
                info["time"] = parts[1].strip() if len(parts) > 1 else ""
                info["season"] = parts[2].strip() if len(parts) > 2 else ""
                info["league"] = parts[3].strip() if len(parts) > 3 else ""
                info["match_number"] = parts[8].strip() if len(parts) > 8 else ""
                break
        return info

    # ─── Sets ─────────────────────────────────────────────────

    def _parse_sets(self) -> List[dict]:
        lines = self._get_section("3SET")
        sets = []
        for line in lines:
            if not line.strip() or not line.startswith("True") and not line.startswith("False"):
                continue
            parts = line.split(";")
            if len(parts) < 5:
                continue
            played = parts[0].strip() == "True"
            if not played:
                continue
            # Scores are in format "25-23" or " 8- 7" with spaces
            scores_raw = [p.strip() for p in parts[1:5]]
            # Find the final score (last non-empty score pair that looks like a score)
            partial_scores = []
            for s in scores_raw:
                match = re.match(r'(\d+)\s*-\s*(\d+)', s)
                if match:
                    partial_scores.append((int(match.group(1)), int(match.group(2))))

            if partial_scores:
                final = partial_scores[-1]
                duration = parts[5].strip() if len(parts) > 5 else ""
                sets.append({
                    "set": len(sets) + 1,
                    "home_score": final[0],
                    "away_score": final[1],
                    "duration": duration,
                    "partial_scores": partial_scores,
                })
        return sets

    # ─── Teams ────────────────────────────────────────────────

    def _parse_teams(self) -> Tuple[dict, dict]:
        lines = self._get_section("3TEAMS")
        home = {"id": "", "name": "Local", "coach": "", "assistant": ""}
        away = {"id": "", "name": "Visitante", "coach": "", "assistant": ""}
        team_lines = [l for l in lines if ";" in l and l.strip()]
        if len(team_lines) >= 1:
            p = team_lines[0].split(";")
            home["id"] = p[0].strip()
            home["name"] = p[1].strip() if len(p) > 1 else "Local"
            home["coach"] = p[3].strip() if len(p) > 3 else ""
            home["assistant"] = p[4].strip() if len(p) > 4 else ""
        if len(team_lines) >= 2:
            p = team_lines[1].split(";")
            away["id"] = p[0].strip()
            away["name"] = p[1].strip() if len(p) > 1 else "Visitante"
            away["coach"] = p[3].strip() if len(p) > 3 else ""
            away["assistant"] = p[4].strip() if len(p) > 4 else ""
        return home, away

    # ─── Players ──────────────────────────────────────────────

    def _parse_players(self, section_key: str) -> List[dict]:
        lines = self._get_section(section_key)
        players = []
        for line in lines:
            if not line.strip() or ";" not in line:
                continue
            parts = line.split(";")
            if len(parts) < 11:
                continue
            try:
                shirt = int(parts[1].strip())
            except (ValueError, IndexError):
                continue

            player_idx = parts[2].strip()
            fed_id = parts[8].strip() if len(parts) > 8 else ""
            surname = parts[9].strip() if len(parts) > 9 else ""
            firstname = parts[10].strip() if len(parts) > 10 else ""

            # Detectar libero y posicion
            is_libero = False
            position = ""
            for i in range(11, min(len(parts), 16)):
                val = parts[i].strip()
                if val == "L":
                    is_libero = True
                if val in POSITION_MAP:
                    position = POSITION_MAP[val]
                if val in ("True", "False"):
                    break

            # Rotaciones (campos 3-6)
            rotations = []
            for i in range(3, min(7, len(parts))):
                r = parts[i].strip()
                if r and r != "*" and r.isdigit():
                    rotations.append(int(r))

            full_name = f"{surname}, {firstname}" if firstname else surname

            players.append({
                "dorsal": shirt,
                "indice": player_idx,
                "fed_id": fed_id,
                "apellido": surname,
                "nombre": firstname,
                "nombre_completo": full_name,
                "nombre_corto": f"{surname} {firstname[0]}." if firstname else surname,
                "posicion": position,
                "es_libero": is_libero,
                "titular": len(rotations) > 0,
                "rotaciones": rotations,
            })

        return players

    # ─── Attack Combinations ──────────────────────────────────

    def _parse_attack_combinations(self) -> dict:
        lines = self._get_section("3ATTACKCOMBINATION")
        combos = {}
        for line in lines:
            if ";" not in line:
                continue
            parts = line.split(";")
            if len(parts) >= 5:
                code = parts[0].strip()
                description = parts[4].strip() if len(parts) > 4 else parts[3].strip()
                combos[code] = {
                    "code": code,
                    "target_zone": parts[1].strip(),
                    "description": description,
                }
        return combos

    # ─── Scout (Play-by-Play) ─────────────────────────────────

    def _parse_scout(self, home_players: List[dict], away_players: List[dict]) -> List[dict]:
        lines = self._get_section("3SCOUT")

        # Crear lookups por dorsal
        home_lookup = {p["dorsal"]: p for p in home_players}
        away_lookup = {p["dorsal"]: p for p in away_players}

        plays = []
        current_set = 1
        home_score = 0
        away_score = 0
        rally = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # DataVolley guarda el set real también en las columnas posteriores al código.
            # Las líneas **1set, **2set... marcan el cierre del set anterior; por eso no deben
            # usarse como inicio del mismo set, sino como cambio al siguiente si no hay metadatos.
            meta_parts = line.split(";")
            line_set = None
            if len(meta_parts) > 8 and str(meta_parts[8]).strip().isdigit():
                line_set = int(meta_parts[8].strip())

            # Detectar cambio/cierre de set
            set_match = re.match(r'\*\*(\d+)set', line)
            if set_match:
                current_set = line_set if line_set is not None else int(set_match.group(1)) + 1
                home_score = 0
                away_score = 0
                rally = 0
                continue

            if line_set is not None:
                if line_set != current_set:
                    rally = 0
                    home_score = 0
                    away_score = 0
                current_set = line_set

            # Detectar marcador
            score_match = re.match(r'[*a]p(\d+):(\d+)', line)
            if score_match:
                home_score = int(score_match.group(1))
                away_score = int(score_match.group(2))
                rally += 1
                continue

            # Parsear jugada
            play = self._parse_play(line, current_set, rally, home_score, away_score,
                                     home_lookup, away_lookup)
            if play:
                plays.append(play)

        return plays

    def _parse_play(self, line: str, set_num: int, rally: int,
                     h_score: int, a_score: int,
                     home_lookup: dict, away_lookup: dict) -> Optional[dict]:
        """Parsea una linea de scout DVW."""

        if len(line) < 6:
            return None

        parts = line.split(";")
        code_field = parts[0].strip()

        # Metadatos DataVolley posteriores al código: tiempo, set, rotaciones y sextetos.
        meta_set = int(parts[8]) if len(parts) > 8 and parts[8].strip().isdigit() else set_num
        rot_home = int(parts[9]) if len(parts) > 9 and parts[9].strip().isdigit() else None
        rot_away = int(parts[10]) if len(parts) > 10 and parts[10].strip().isdigit() else None
        lineup_home = [int(x) for x in parts[14:20] if str(x).strip().isdigit()] if len(parts) >= 20 else []
        lineup_away = [int(x) for x in parts[20:26] if str(x).strip().isdigit()] if len(parts) >= 26 else []

        # Equipo
        if code_field.startswith("*"):
            team_code = "home"
            code = code_field[1:]
        elif code_field.startswith("a"):
            team_code = "away"
            code = code_field[1:]
        else:
            return None

        rotation = rot_home if team_code == "home" else rot_away
        lineup = lineup_home if team_code == "home" else lineup_away

        # Ignorar lineas especiales (sustituciones, rotaciones, timeouts, lineups, etc)
        if code.startswith("P") or code.startswith("z") or code.startswith("c"):
            return None
        if code.startswith("T") or code.startswith("$"):
            # Punto de equipo ($$&H# o $$&H=)
            if code.startswith("$$"):
                eval_char = ""
                for ch in code:
                    if ch in EVAL_MAP:
                        eval_char = ch
                        break
                if eval_char:
                    return {
                        "set": meta_set, "rally": rally,
                        "home_score": h_score, "away_score": a_score,
                        "equipo": team_code,
                        "dorsal": 0, "jugador": "Equipo",
                        "skill": "Punto equipo", "skill_code": "$",
                        "tipo": "", "tipo_code": "",
                        "evaluacion": EVAL_MAP.get(eval_char, ""),
                        "eval_code": eval_char,
                        "eval_score": EVAL_SCORE.get(eval_char, 0),
                        "combo": "", "combo_desc": "",
                        "zona_inicio": "", "zona_fin": "",
                        "es_punto": eval_char == "#",
                        "es_error": eval_char == "=",
                        "num_bloqueadores": "",
                        "posicion": "",
                        "rot_home": rot_home, "rot_away": rot_away, "rotation": rotation,
                        "lineup_home": lineup_home, "lineup_away": lineup_away, "lineup": lineup,
                        "raw": line,
                    }
            return None

        # Dorsal (2 digitos)
        try:
            dorsal = int(code[:2])
        except ValueError:
            return None

        # Buscar jugador
        lookup = home_lookup if team_code == "home" else away_lookup
        player = lookup.get(dorsal, {})
        jugador = player.get("nombre_corto", f"#{dorsal}")
        posicion = player.get("posicion", "")

        # Skill + tipo (posiciones 2 y 3)
        skill_code = code[2] if len(code) > 2 else ""
        tipo_code = code[3] if len(code) > 3 else ""

        if skill_code not in SKILL_MAP:
            return None

        skill = SKILL_MAP.get(skill_code, skill_code)
        tipo = SKILL_TYPE_MAP.get(tipo_code, tipo_code)

        # Evaluacion (posicion 4)
        eval_char = code[4] if len(code) > 4 else ""
        evaluacion = EVAL_MAP.get(eval_char, eval_char)
        eval_score = EVAL_SCORE.get(eval_char, 0)

        # Combinacion de ataque (posiciones 5-6)
        combo = code[5:7].strip("~") if len(code) > 6 else ""

        # Zonas (buscar en el resto del codigo)
        zona_inicio = ""
        zona_fin = ""
        rest = code[5:] if len(code) > 5 else ""
        # Las zonas estan despues de ~ tipicamente en formato ~ZiZf
        zone_match = re.search(r'~(\d)(\d)', rest)
        if zone_match:
            zona_inicio = zone_match.group(1)
            zona_fin = zone_match.group(2)

        # Numero de bloqueadores (buscar patron como H2, T1, etc despues de las zonas)
        num_bloq = ""
        bloq_match = re.search(r'[A-Z](\d)[A-Z]?$', code.split(";")[0] if ";" in code else code)
        if bloq_match:
            num_bloq = bloq_match.group(1)

        return {
            "set": meta_set,
            "rally": rally,
            "home_score": h_score,
            "away_score": a_score,
            "equipo": team_code,
            "dorsal": dorsal,
            "jugador": jugador,
            "skill": skill,
            "skill_code": skill_code,
            "tipo": tipo,
            "tipo_code": tipo_code,
            "evaluacion": evaluacion,
            "eval_code": eval_char,
            "eval_score": eval_score,
            "combo": combo,
            "combo_desc": "",
            "zona_inicio": zona_inicio,
            "zona_fin": zona_fin,
            "es_punto": eval_char == "#",
            "es_error": eval_char == "=",
            "num_bloqueadores": num_bloq,
            "posicion": posicion,
            "rot_home": rot_home, "rot_away": rot_away, "rotation": rotation,
            "lineup_home": lineup_home, "lineup_away": lineup_away, "lineup": lineup,
            "raw": line,
        }


# ═══════════════════════════════════════════════════════════════
# FUNCIONES DE ANALISIS
# ═══════════════════════════════════════════════════════════════

def stats_por_jugador(data: dict) -> pd.DataFrame:
    """Estadisticas completas por jugador."""
    plays = data["plays"]
    if plays.empty:
        return pd.DataFrame()

    rows = []
    for team_code in ["home", "away"]:
        team_plays = plays[plays["equipo"] == team_code]
        team_name = data["home_team"]["name"] if team_code == "home" else data["away_team"]["name"]
        players_df = data["home_players"] if team_code == "home" else data["away_players"]

        for dorsal in team_plays["dorsal"].unique():
            if dorsal == 0:
                continue
            pp = team_plays[team_plays["dorsal"] == dorsal]

            # Info del jugador
            pinfo = players_df[players_df["dorsal"] == dorsal] if not players_df.empty else pd.DataFrame()
            nombre = pinfo.iloc[0]["nombre_completo"] if not pinfo.empty else f"#{dorsal}"
            posicion = pinfo.iloc[0]["posicion"] if not pinfo.empty and "posicion" in pinfo.columns else ""

            # Ataque
            att = pp[pp["skill_code"] == "A"]
            att_total = len(att)
            att_kill = len(att[att["eval_code"] == "#"])
            att_err = len(att[att["eval_code"] == "="])
            att_blk = len(att[att["eval_code"].isin(["/", "-"])])
            att_eff = round((att_kill - att_err) / att_total * 100, 1) if att_total > 0 else 0.0
            att_kill_pct = round(att_kill / att_total * 100, 1) if att_total > 0 else 0.0

            # Saque
            srv = pp[pp["skill_code"] == "S"]
            srv_total = len(srv)
            srv_ace = len(srv[srv["eval_code"] == "#"])
            srv_err = len(srv[srv["eval_code"] == "="])
            srv_eff = round((srv_ace - srv_err) / srv_total * 100, 1) if srv_total > 0 else 0.0

            # Recepcion
            rec = pp[pp["skill_code"] == "R"]
            rec_total = len(rec)
            rec_pos = len(rec[rec["eval_code"].isin(["#", "+", "!"])])
            rec_perf = len(rec[rec["eval_code"] == "#"])
            rec_err = len(rec[rec["eval_code"] == "="])
            rec_pct = round(rec_pos / rec_total * 100, 1) if rec_total > 0 else 0.0
            rec_perf_pct = round(rec_perf / rec_total * 100, 1) if rec_total > 0 else 0.0

            # Bloqueo
            blk = pp[pp["skill_code"] == "B"]
            blk_kill = len(blk[blk["eval_code"] == "#"])
            blk_err = len(blk[blk["eval_code"] == "="])

            # Defensa
            dig = pp[pp["skill_code"] == "D"]
            dig_total = len(dig)
            dig_pos = len(dig[dig["eval_code"].isin(["#", "+", "!"])])
            dig_err = len(dig[dig["eval_code"] == "="])

            # Totales
            pts_total = att_kill + srv_ace + blk_kill
            err_total = att_err + srv_err + rec_err + blk_err

            rows.append({
                "Equipo": team_name, "Dorsal": dorsal, "Jugador": nombre,
                "Posicion": posicion,
                "Pts": pts_total, "Err": err_total, "Balance": pts_total - err_total,
                # Ataque
                "AT K": att_kill, "AT Err": att_err, "AT Tot": att_total,
                "AT Eff%": att_eff, "AT Kill%": att_kill_pct,
                # Saque
                "SQ Ace": srv_ace, "SQ Err": srv_err, "SQ Tot": srv_total,
                "SQ Eff%": srv_eff,
                # Recepcion
                "REC Pos": rec_pos, "REC Perf": rec_perf, "REC Err": rec_err,
                "REC Tot": rec_total, "REC%": rec_pct, "REC Perf%": rec_perf_pct,
                # Bloqueo
                "BLQ K": blk_kill, "BLQ Err": blk_err,
                # Defensa
                "DEF Pos": dig_pos, "DEF Err": dig_err, "DEF Tot": dig_total,
            })

    return pd.DataFrame(rows).sort_values("Pts", ascending=False)


def resumen_equipo(data: dict) -> dict:
    """KPIs de resumen por equipo."""
    plays = data["plays"]
    if plays.empty:
        return {"home": {}, "away": {}}

    result = {}
    for team_code in ["home", "away"]:
        tp = plays[(plays["equipo"] == team_code) & (plays["dorsal"] != 0)]

        att = tp[tp["skill_code"] == "A"]
        srv = tp[tp["skill_code"] == "S"]
        rec = tp[tp["skill_code"] == "R"]
        blk = tp[tp["skill_code"] == "B"]

        att_k = len(att[att["eval_code"] == "#"])
        att_e = len(att[att["eval_code"] == "="])
        att_t = len(att)
        srv_a = len(srv[srv["eval_code"] == "#"])
        srv_e = len(srv[srv["eval_code"] == "="])
        rec_t = len(rec)
        rec_p = len(rec[rec["eval_code"].isin(["#", "+", "!"])])
        rec_pf = len(rec[rec["eval_code"] == "#"])
        blk_k = len(blk[blk["eval_code"] == "#"])

        result[team_code] = {
            "puntos": att_k + srv_a + blk_k,
            "att_kills": att_k, "att_errors": att_e, "att_total": att_t,
            "att_eff": round((att_k - att_e) / max(att_t, 1) * 100, 1),
            "att_kill_pct": round(att_k / max(att_t, 1) * 100, 1),
            "srv_aces": srv_a, "srv_errors": srv_e, "srv_total": len(srv),
            "rec_pos_pct": round(rec_p / max(rec_t, 1) * 100, 1),
            "rec_perf_pct": round(rec_pf / max(rec_t, 1) * 100, 1),
            "rec_errors": len(rec[rec["eval_code"] == "="]),
            "blk_kills": blk_k,
        }

    return result


def distribucion_ataque(data: dict) -> pd.DataFrame:
    """Distribucion de ataques por zona de inicio."""
    plays = data["plays"]
    if plays.empty:
        return pd.DataFrame()
    att = plays[(plays["skill_code"] == "A") & (plays["zona_inicio"] != "")].copy()
    if att.empty:
        return pd.DataFrame()
    att["zona"] = "Z" + att["zona_inicio"]
    grouped = att.groupby(["equipo", "zona"]).agg(
        total=("skill_code", "count"),
        kills=("es_punto", "sum"),
        errores=("es_error", "sum"),
    ).reset_index()
    grouped["eff"] = round((grouped["kills"] - grouped["errores"]) / grouped["total"].replace(0, 1) * 100, 1)
    grouped["kill_pct"] = round(grouped["kills"] / grouped["total"].replace(0, 1) * 100, 1)
    return grouped


def mapa_ataque_destino(data: dict) -> pd.DataFrame:
    """Mapa de ataques: zona inicio -> zona destino."""
    plays = data["plays"]
    if plays.empty:
        return pd.DataFrame()
    att = plays[(plays["skill_code"] == "A") &
                (plays["zona_inicio"] != "") &
                (plays["zona_fin"] != "")].copy()
    if att.empty:
        return pd.DataFrame()
    att["desde"] = "Z" + att["zona_inicio"]
    att["hacia"] = "Z" + att["zona_fin"]
    grouped = att.groupby(["equipo", "desde", "hacia"]).agg(
        total=("skill_code", "count"),
        kills=("es_punto", "sum"),
        errores=("es_error", "sum"),
    ).reset_index()
    return grouped
