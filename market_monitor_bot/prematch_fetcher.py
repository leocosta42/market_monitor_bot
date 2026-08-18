"""
Pre-Match Data Fetcher
- Agenda de jogos: ESPN API (multi-liga, sem bloqueio)
- Histórico / Forma dos times: SofaScore API
- Produz um score de Over 0.5 HT para cada jogo do dia
"""
import logging
import time
import cloudscraper
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Ligas suportadas (ESPN slug -> nome legível)
LEAGUES = {
    "eng.1": "Premier League",
    "esp.1": "La Liga",
    "ger.1": "Bundesliga",
    "ita.1": "Serie A",
    "fra.1": "Ligue 1",
    "bra.1": "Brasileirão",
    "por.1": "Primeira Liga",
    "ned.1": "Eredivisie",
}


class PrematchFetcher:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        self._sf_id_cache: Dict[str, Optional[int]] = {}

    # ------------------------------------------------------------------
    # 1. Agenda de jogos via ESPN
    # ------------------------------------------------------------------
    def get_todays_matches(self) -> List[Dict]:
        """Retorna todos os jogos do dia em todas as ligas configuradas."""
        all_matches = []
        for slug, league_name in LEAGUES.items():
            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard"
                resp = requests.get(url, timeout=8)
                if resp.status_code != 200:
                    continue
                events = resp.json().get("events", [])
                for evt in events:
                    match = self._parse_espn_event(evt, league_name, slug)
                    if match:
                        all_matches.append(match)
            except Exception as e:
                logger.warning("Erro ao buscar ESPN %s: %s", slug, e)
        return all_matches

    def _parse_espn_event(self, evt: Dict, league_name: str, slug: str) -> Optional[Dict]:
        try:
            comp = evt["competitions"][0]
            home_info = comp["competitors"][0]["team"]
            away_info = comp["competitors"][1]["team"]
            date_str = evt["date"]  # "2024-08-18T14:00Z"
            # Parse time (UTC → show as-is)
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
                time_str = dt.strftime("%H:%M UTC")
            except Exception:
                time_str = "Hoje"

            return {
                "home": home_info["name"],
                "away": away_info["name"],
                "home_espn_id": home_info["id"],
                "away_espn_id": away_info["id"],
                "home_logo": home_info.get("logo", ""),
                "away_logo": away_info.get("logo", ""),
                "time": time_str,
                "league": league_name,
                "league_slug": slug,
                "status": comp.get("status", {}).get("type", {}).get("name", ""),
            }
        except Exception as e:
            logger.debug("Erro ao parsear evento ESPN: %s", e)
            return None

    # ------------------------------------------------------------------
    # 2. Encontrar ID do time no SofaScore via busca
    # ------------------------------------------------------------------
    def _get_sofascore_id(self, team_name: str) -> Optional[int]:
        if team_name in self._sf_id_cache:
            return self._sf_id_cache[team_name]
        try:
            query = team_name.replace(" ", "%20")
            r = self.scraper.get(
                f"https://api.sofascore.com/api/v1/search/all?q={query}", timeout=8
            )
            if r.status_code != 200:
                self._sf_id_cache[team_name] = None
                return None
            results = r.json().get("results", [])
            teams = [x for x in results if x.get("type") == "team"]
            if not teams:
                self._sf_id_cache[team_name] = None
                return None
            sf_id = teams[0]["entity"]["id"]
            self._sf_id_cache[team_name] = sf_id
            return sf_id
        except Exception as e:
            logger.warning("Sofascore search falhou para %s: %s", team_name, e)
            self._sf_id_cache[team_name] = None
            return None

    # ------------------------------------------------------------------
    # 3. Últimos N jogos de um time no SofaScore
    # ------------------------------------------------------------------
    def _get_last_matches(self, sf_team_id: int, n: int = 5) -> List[Dict]:
        try:
            r = self.scraper.get(
                f"https://api.sofascore.com/api/v1/team/{sf_team_id}/events/last/0",
                timeout=10,
            )
            if r.status_code != 200:
                return []
            events = r.json().get("events", [])
            return events[-n:] if len(events) >= n else events
        except Exception as e:
            logger.warning("Sofascore last events falhou (team %s): %s", sf_team_id, e)
            return []

    # ------------------------------------------------------------------
    # 4. Calcular métricas de forma a partir dos últimos N jogos
    # ------------------------------------------------------------------
    def _calc_form(self, sf_team_id: int, last_matches: List[Dict]) -> Dict:
        goals_scored = []
        goals_conceded = []
        ht_goals = []
        wins = 0

        for ev in last_matches:
            is_home = ev.get("homeTeam", {}).get("id") == sf_team_id
            home_score = ev.get("homeScore", {}).get("current", 0) or 0
            away_score = ev.get("awayScore", {}).get("current", 0) or 0
            home_ht = ev.get("homeScore", {}).get("period1", 0) or 0
            away_ht = ev.get("awayScore", {}).get("period1", 0) or 0

            if is_home:
                scored, conceded = home_score, away_score
                ht_scored = home_ht
                wins += 1 if home_score > away_score else 0
            else:
                scored, conceded = away_score, home_score
                ht_scored = away_ht
                wins += 1 if away_score > home_score else 0

            goals_scored.append(scored)
            goals_conceded.append(conceded)
            ht_goals.append(ht_scored + (away_ht if is_home else home_ht))

        n = len(last_matches) or 1
        avg_scored = sum(goals_scored) / n
        avg_conceded = sum(goals_conceded) / n
        avg_ht_goals = sum(ht_goals) / n
        over_05_ht_rate = sum(1 for g in ht_goals if g > 0) / n
        win_rate = wins / n

        return {
            "avg_scored": round(avg_scored, 2),
            "avg_conceded": round(avg_conceded, 2),
            "avg_ht_goals": round(avg_ht_goals, 2),
            "over_05_ht_rate": round(over_05_ht_rate, 2),
            "win_rate": round(win_rate, 2),
            "n_matches": n,
        }

    # ------------------------------------------------------------------
    # 5. Calcular Score de Over 0.5 HT baseado nos dados reais
    # ------------------------------------------------------------------
    def _calc_score(self, home_form: Dict, away_form: Dict) -> Dict:
        # Probabilidade combinada baseada em taxa histórica de Over 0.5 HT
        home_rate = home_form["over_05_ht_rate"]
        away_rate = away_form["over_05_ht_rate"]
        # P(gol no HT) = 1 - P(sem gol home) * P(sem gol away)
        prob_ht = 1 - (1 - home_rate) * (1 - away_rate)

        # Score 0-100 baseado em média de gols + taxa HT
        avg_goals = (home_form["avg_scored"] + away_form["avg_scored"]) / 2
        avg_ht = (home_form["avg_ht_goals"] + away_form["avg_ht_goals"]) / 2

        score = (
            prob_ht * 40          # peso maior: taxa histórica real
            + min(avg_goals / 3, 1) * 30  # média de gols normalizada
            + min(avg_ht / 1.5, 1) * 30   # média HT normalizada
        ) * 100

        score = min(max(score, 0), 100)

        if score >= 78:
            recomendacao = "⭐ EXCELENTE OPORTUNIDADE"
        elif score >= 62:
            recomendacao = "✅ BOA OPORTUNIDADE"
        elif score >= 48:
            recomendacao = "⚠️ CONSIDERAR"
        else:
            recomendacao = "❌ ARRISCADO"

        # Intervalos estimados (baseado em taxa HT dos últimos jogos)
        i0_15 = round(prob_ht * 0.20 * 100)
        i15_30 = round(prob_ht * 0.35 * 100)
        i30_45 = round(prob_ht * 0.45 * 100)

        return {
            "score": round(score, 1),
            "prob_ht": round(prob_ht, 3),
            "recomendacao": recomendacao,
            "xg_estimado": round(avg_goals, 2),
            "intervals": {
                "0_15": i0_15,
                "15_30": i15_30,
                "30_45": i30_45,
            },
            "radar": {
                "labels": ["Ataque", "Defesa", "Taxa Over HT", "Gols Marcados", "Win Rate"],
                "home": [
                    int(min(home_form["avg_scored"] / 3 * 100, 100)),
                    int(max(100 - home_form["avg_conceded"] / 3 * 100, 10)),
                    int(home_form["over_05_ht_rate"] * 100),
                    int(min(home_form["avg_scored"] / 3 * 100, 100)),
                    int(home_form["win_rate"] * 100),
                ],
                "away": [
                    int(min(away_form["avg_scored"] / 3 * 100, 100)),
                    int(max(100 - away_form["avg_conceded"] / 3 * 100, 10)),
                    int(away_form["over_05_ht_rate"] * 100),
                    int(min(away_form["avg_scored"] / 3 * 100, 100)),
                    int(away_form["win_rate"] * 100),
                ],
            },
        }

    # ------------------------------------------------------------------
    # 6. Pipeline completo
    # ------------------------------------------------------------------
    def analyze_todays_matches(self, max_matches: int = 10) -> List[Dict]:
        """
        Busca jogos reais do dia + analisa forma de cada time.
        Retorna lista ordenada por Score (maior = maior oportunidade).
        """
        matches = self.get_todays_matches()
        if not matches:
            return []

        results = []
        for match in matches[:max_matches]:
            home_name = match["home"]
            away_name = match["away"]

            # Busca IDs no SofaScore
            home_sf_id = self._get_sofascore_id(home_name)
            time.sleep(0.4)  # respeita rate limit
            away_sf_id = self._get_sofascore_id(away_name)
            time.sleep(0.4)

            if not home_sf_id or not away_sf_id:
                logger.info("IDs SF não encontrados para %s vs %s", home_name, away_name)
                continue

            # Últimos 5 jogos de cada time
            home_last = self._get_last_matches(home_sf_id, 5)
            time.sleep(0.4)
            away_last = self._get_last_matches(away_sf_id, 5)
            time.sleep(0.4)

            if not home_last or not away_last:
                continue

            home_form = self._calc_form(home_sf_id, home_last)
            away_form = self._calc_form(away_sf_id, away_last)
            analysis = self._calc_score(home_form, away_form)

            results.append({
                "home": home_name,
                "away": away_name,
                "home_logo": match.get("home_logo", ""),
                "away_logo": match.get("away_logo", ""),
                "time": match["time"],
                "league": match["league"],
                "score": analysis["score"],
                "prob_ht": analysis["prob_ht"],
                "recomendacao": analysis["recomendacao"],
                "xg_total": analysis["xg_estimado"],
                "intervals": analysis["intervals"],
                "radar": analysis["radar"],
                "avisos": [],
                "home_form": home_form,
                "away_form": away_form,
            })

        # Ordena por score decrescente
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
