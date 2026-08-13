import requests
import cloudscraper
import logging
from typing import List, Dict, Optional
from .models import LiveMatchMetrics, TeamStats, MatchContext

logger = logging.getLogger(__name__)

class SofaScoreProvider:
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.scraper = cloudscraper.create_scraper() # Instancia o bypasser
        self.headers = {
            "Accept": "*/*",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com"
        }

    def get_live_matches(self) -> List[Dict]:
        """Busca todas as partidas de futebol acontecendo ao vivo no momento."""
        url = f"{self.base_url}/sport/football/events/live"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("events", [])
        except Exception as e:
            logger.error(f"Erro ao buscar jogos ao vivo: {e}")
            return []

    def get_match_statistics(self, event_id: int) -> Dict:
        """Busca as estatísticas detalhadas de uma partida específica."""
        url = f"{self.base_url}/event/{event_id}/statistics"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            if response.status_code == 404:
                return {} # Partida pode não ter estatísticas detalhadas
            response.raise_for_status()
            data = response.json()
            stats = data.get("statistics", [])
            
            # Formatar estatísticas para um dicionário mais fácil de ler
            formatted_stats = {}
            if stats:
                # Geralmente a API retorna [0] como "ALL" (partida inteira) e [1] como "1ST" (primeiro tempo)
                # Vamos pegar os dados do tempo atual
                period = stats[0] 
                groups = period.get("groups", [])
                for group in groups:
                    for item in group.get("statisticsItems", []):
                        formatted_stats[item.get("name")] = {
                            "home": item.get("home"),
                            "away": item.get("away")
                        }
            return formatted_stats
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas do jogo {event_id}: {e}")
            return {}
            
    def _parse_stat(self, stats: Dict, stat_name: str, team_side: str) -> int:
        """Extrai um número da estatística, retornando 0 se não encontrar."""
        if stat_name in stats:
            try:
                val = stats[stat_name].get(team_side, "0")
                return int(val)
            except (ValueError, TypeError):
                return 0
        return 0

    def build_match_context(self, event: Dict, stats: Dict) -> Optional[MatchContext]:
        """Constrói o objeto MatchContext a partir dos dados do SofaScore."""
        
        # Filtros básicos: Precisamos do tempo e do placar
        status_code = event.get("status", {}).get("code")
        
        # 6 = First half in progress (no SofaScore)
        # Se não for primeiro tempo, ignoramos na construção base (ou retornamos None)
        if status_code != 6:
            return None
            
        home_team_name = event.get("homeTeam", {}).get("name", "Home")
        away_team_name = event.get("awayTeam", {}).get("name", "Away")
        
        # O tempo no SofaScore fica em time -> currentPeriodStartTimestamp
        # Para simplificar, o "status -> description" as vezes traz o minuto "22'"
        # Mas vamos pegar de "time" -> "played" (se disponível) ou inferir.
        time_info = event.get("time", {})
        match_time = time_info.get("played")
        if match_time is None:
             match_time = time_info.get("initial", 0) # Fallback

        home_score = event.get("homeScore", {}).get("current", 0)
        away_score = event.get("awayScore", {}).get("current", 0)
        
        # Extrair estatísticas somadas (Casa + Fora)
        shots_on_target = self._parse_stat(stats, "Shots on target", "home") + self._parse_stat(stats, "Shots on target", "away")
        shots_off_target = self._parse_stat(stats, "Shots off target", "home") + self._parse_stat(stats, "Shots off target", "away")
        corners = self._parse_stat(stats, "Corner kicks", "home") + self._parse_stat(stats, "Corner kicks", "away")
        fouls = self._parse_stat(stats, "Fouls", "home") + self._parse_stat(stats, "Fouls", "away")
        dangerous_attacks = self._parse_stat(stats, "Dangerous attacks", "home") + self._parse_stat(stats, "Dangerous attacks", "away")
        
        # No SofaScore "Red cards"
        red_cards = self._parse_stat(stats, "Red cards", "home") + self._parse_stat(stats, "Red cards", "away")
        
        # Criamos times falsos/mock para o histórico (já que não temos histórico grátis aqui facilmente)
        # Na vida real, você preencheria isso cruzando com seu DB de médias.
        home = TeamStats(
            team_id=str(event.get("homeTeam", {}).get("id")),
            team_name=home_team_name,
            over_05_ht_hit_rate=0.75, # Mock: assume que passou no filtro pré-jogo
            over_25_ft_pre_odd=1.85   # Mock
        )

        away = TeamStats(
            team_id=str(event.get("awayTeam", {}).get("id")),
            team_name=away_team_name,
            over_05_ht_hit_rate=0.75, # Mock
            over_25_ft_pre_odd=1.85   # Mock
        )
        
        metrics = LiveMatchMetrics(
            match_id=str(event.get("id")),
            match_time=match_time,
            current_score=(home_score, away_score),
            shots_on_target=shots_on_target,
            shots_off_target=shots_off_target,
            dangerous_attacks=dangerous_attacks,
            corners=corners,
            fouls=fouls,
            red_cards=red_cards,
            red_card_time=10 if red_cards > 0 else None, # Mock time se houver
            current_odd_over_05_ht=1.70 # Contorno: assumimos Odd ideal se chegou até aqui
        )
        
        tournament = event.get("tournament", {}).get("name", "Competição Desconhecida")
        
        return MatchContext(
            match_id=str(event.get("id")),
            home_team=home,
            away_team=away,
            competition=tournament,
            live_metrics=metrics
        )
