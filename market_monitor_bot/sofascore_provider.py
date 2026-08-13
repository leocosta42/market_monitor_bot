import time
import logging
import cloudscraper
from typing import List, Dict, Optional, Tuple
from .models import LiveMatchMetrics, TeamStats, MatchContext
from .team_stats_repository import TeamStatsRepository

logger = logging.getLogger(__name__)

# status.code == 6 -> primeiro tempo em andamento (SofaScore)
FIRST_HALF_CODE = 6


class SofaScoreProvider:
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.headers = {
            "Cache-Control": "no-cache"
        }

    # ---------------- requests ----------------
    def get_live_matches(self) -> List[Dict]:
        url = f"{self.base_url}/sport/football/events/live"
        try:
            resp = self.scraper.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json().get("events", [])
        except Exception as e:
            logger.error("Erro ao buscar jogos ao vivo: %s", e)
            return []

    def get_match_statistics(self, event_id: int) -> Dict:
        url = f"{self.base_url}/event/{event_id}/statistics"
        try:
            resp = self.scraper.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 404:
                return {}
            resp.raise_for_status()
            stats = resp.json().get("statistics", [])
            formatted: Dict[str, Dict] = {}
            if stats:
                period = stats[0]  # [0] = ALL / partida inteira
                for group in period.get("groups", []):
                    for item in group.get("statisticsItems", []):
                        formatted[item.get("name")] = {
                            "home": item.get("home"),
                            "away": item.get("away"),
                        }
            return formatted
        except Exception as e:
            logger.error("Erro ao buscar estatisticas do jogo %s: %s", event_id, e)
            return {}

    # ---------------- helpers ----------------
    @staticmethod
    def _compute_minute(event: Dict) -> Optional[int]:
        """
        Calcula o minuto de jogo a partir do timestamp de inicio do periodo.
        SofaScore NAO devolve o minuto pronto de forma confiavel.
        """
        t = event.get("time", {})
        start = t.get("currentPeriodStartTimestamp")
        if not start:
            return None
        minute = int((time.time() - start) // 60) + 1
        # sanidade: 1o tempo raramente passa de ~50' com acrescimos
        if minute < 0 or minute > 60:
            return None
        return minute

    @staticmethod
    def _score(event: Dict) -> Tuple[int, int]:
        return (
            event.get("homeScore", {}).get("current", 0),
            event.get("awayScore", {}).get("current", 0),
        )

    def is_candidate(self, event: Dict, min_minute: int, max_minute: int) -> bool:
        """
        Pre-filtro barato (SO com o payload do /live, SEM chamar /statistics).
        Evita disparar centenas de requisicoes de estatisticas por ciclo.
        """
        if event.get("status", {}).get("code") != FIRST_HALF_CODE:
            return False
        if self._score(event) != (0, 0):
            return False
        minute = self._compute_minute(event)
        if minute is None:
            return False
        # margem: comeca a puxar stats um pouco antes da janela
        return (min_minute - 3) <= minute <= max_minute

    def _parse_stat(self, stats: Dict, stat_name: str, side: str) -> int:
        if stat_name in stats:
            try:
                return int(stats[stat_name].get(side, 0) or 0)
            except (ValueError, TypeError):
                return 0
        return 0

    # ---------------- construcao de contexto ----------------
    def build_match_context(
        self, event: Dict, stats: Dict, stats_repo: TeamStatsRepository
    ) -> Optional[MatchContext]:
        if event.get("status", {}).get("code") != FIRST_HALF_CODE:
            return None

        minute = self._compute_minute(event)
        if minute is None:
            return None

        home_name = event.get("homeTeam", {}).get("name", "Home")
        away_name = event.get("awayTeam", {}).get("name", "Away")
        home_id = str(event.get("homeTeam", {}).get("id"))
        away_id = str(event.get("awayTeam", {}).get("id"))

        # DADOS REAIS (nao mock): busca historico na base. Sem base -> ignora o jogo.
        home = stats_repo.get(team_id=home_id, team_name=home_name)
        away = stats_repo.get(team_id=away_id, team_name=away_name)
        if home is None or away is None:
            logger.debug("Sem historico para %s ou %s; jogo ignorado.", home_name, away_name)
            return None

        home_score, away_score = self._score(event)

        red_cards = (
            self._parse_stat(stats, "Red cards", "home")
            + self._parse_stat(stats, "Red cards", "away")
        )

        metrics = LiveMatchMetrics(
            match_id=str(event.get("id")),
            match_time=minute,
            current_score=(home_score, away_score),
            shots_on_target=self._parse_stat(stats, "Shots on target", "home")
            + self._parse_stat(stats, "Shots on target", "away"),
            shots_off_target=self._parse_stat(stats, "Shots off target", "home")
            + self._parse_stat(stats, "Shots off target", "away"),
            dangerous_attacks=self._parse_stat(stats, "Dangerous attacks", "home")
            + self._parse_stat(stats, "Dangerous attacks", "away"),
            corners=self._parse_stat(stats, "Corner kicks", "home")
            + self._parse_stat(stats, "Corner kicks", "away"),
            fouls=self._parse_stat(stats, "Fouls", "home")
            + self._parse_stat(stats, "Fouls", "away"),
            red_cards=red_cards,
            red_card_time=None,  # SofaScore /statistics nao traz o minuto do cartao
            market_odd_over_05_ht=None,  # SofaScore nao fornece odds; preenchido no hibrido
            fair_odd_over_05_ht=None,
        )

        return MatchContext(
            match_id=str(event.get("id")),
            home_team=home,
            away_team=away,
            competition=event.get("tournament", {}).get("name", "Competição Desconhecida"),
            live_metrics=metrics,
        )
