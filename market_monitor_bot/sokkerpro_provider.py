"""
SokkerPRO Data Provider
Usa os endpoints internos do SokkerPRO (m2.sokkerpro.com) para enriquecer
os dados das partidas com xG, Pressão e Odd Justa.
"""
import cloudscraper
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class SokkerProProvider:
    def __init__(self):
        self.base_url = "https://m2.sokkerpro.com"
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "Accept": "application/json",
            "Referer": "https://sokkerpro.com/",
            "Origin": "https://sokkerpro.com"
        }
        # Cache de fixture_ids para não buscar repetidamente
        self._fixture_cache: Dict[str, int] = {}

    def get_live_fixtures(self) -> List[Dict]:
        """Busca todos os jogos ao vivo no SokkerPRO."""
        url = f"{self.base_url}/livescores"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            fixtures = []
            # O retorno do livescores pode ser uma lista de ligas com jogos
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        events = item.get("events", item.get("fixtures", []))
                        if isinstance(events, list):
                            fixtures.extend(events)
                        else:
                            fixtures.append(item)
            elif isinstance(data, dict):
                events = data.get("events", data.get("fixtures", [data]))
                fixtures.extend(events)
            
            logger.info(f"SokkerPRO: {len(fixtures)} jogos ao vivo encontrados.")
            return fixtures
        except Exception as e:
            logger.warning(f"SokkerPRO livescores falhou: {e}")
            return []

    def get_fixture_stats(self, fixture_id: int) -> Dict:
        """Busca as estatísticas detalhadas de uma partida (xG, pressão, etc)."""
        url = f"{self.base_url}/fixture/{fixture_id}/dados"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"SokkerPRO stats falhou para fixture {fixture_id}: {e}")
            return {}

    def get_fixture_details(self, fixture_id: int) -> Dict:
        """Busca informações detalhadas da partida (odds, times, etc)."""
        url = f"{self.base_url}/fixture/{fixture_id}"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"SokkerPRO fixture details falhou para {fixture_id}: {e}")
            return {}

    def get_fixture_preodds(self, fixture_id: int) -> Dict:
        """Busca odds pré-jogo de uma partida."""
        url = f"{self.base_url}/fixture/{fixture_id}/preodds"
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"SokkerPRO preodds falhou para {fixture_id}: {e}")
            return {}

    def find_fixture_by_teams(self, home_name: str, away_name: str, live_fixtures: List[Dict]) -> Optional[int]:
        """
        Tenta encontrar o fixture_id correspondente no SokkerPRO
        comparando nomes dos times com os jogos ao vivo.
        """
        cache_key = f"{home_name}_{away_name}"
        if cache_key in self._fixture_cache:
            return self._fixture_cache[cache_key]
        
        home_lower = home_name.lower()
        away_lower = away_name.lower()
        
        for fixture in live_fixtures:
            # Tenta diferentes formatos de nome do SokkerPRO
            sp_home = ""
            sp_away = ""
            
            if "homeTeam" in fixture:
                sp_home = fixture.get("homeTeam", {}).get("name", "").lower()
                sp_away = fixture.get("awayTeam", {}).get("name", "").lower()
            elif "home" in fixture:
                sp_home = fixture.get("home", {}).get("name", "").lower() if isinstance(fixture.get("home"), dict) else str(fixture.get("home", "")).lower()
                sp_away = fixture.get("away", {}).get("name", "").lower() if isinstance(fixture.get("away"), dict) else str(fixture.get("away", "")).lower()
            
            # Verifica se há correspondência parcial nos nomes dos times
            if (home_lower in sp_home or sp_home in home_lower) and \
               (away_lower in sp_away or sp_away in away_lower):
                fixture_id = fixture.get("id") or fixture.get("fixture_id")
                if fixture_id:
                    self._fixture_cache[cache_key] = fixture_id
                    return fixture_id
        
        return None

    def enrich_match_data(self, fixture_id: int) -> Dict:
        """
        Busca dados enriquecidos do SokkerPRO para uma partida específica.
        Retorna um dicionário com xG, pressão, e odds justa.
        """
        enriched = {
            "xg_home": None,
            "xg_away": None,
            "pressure_home": None,
            "pressure_away": None,
            "fair_odd_over_05_ht": None,
            "enriched": False
        }
        
        try:
            # Buscar estatísticas ao vivo (xG, pressão, etc)
            stats = self.get_fixture_stats(fixture_id)
            if stats:
                enriched["enriched"] = True
                
                # Extrair xG (o formato depende da resposta da API)
                if isinstance(stats, dict):
                    # Tenta extrair xG
                    xg = stats.get("xg", stats.get("expectedGoals", {}))
                    if isinstance(xg, dict):
                        enriched["xg_home"] = xg.get("home", xg.get("h"))
                        enriched["xg_away"] = xg.get("away", xg.get("a"))
                    elif isinstance(xg, list) and len(xg) >= 2:
                        enriched["xg_home"] = xg[0]
                        enriched["xg_away"] = xg[1]
                    
                    # Extrair pressão
                    pressure = stats.get("pressure", stats.get("momentum", {}))
                    if isinstance(pressure, dict):
                        enriched["pressure_home"] = pressure.get("home", pressure.get("h"))
                        enriched["pressure_away"] = pressure.get("away", pressure.get("a"))
                    
                    # Tentar ler chutes e ataques caso disponível
                    for key in ["attacks", "dangerousAttacks", "dangerous_attacks"]:
                        if key in stats:
                            val = stats[key]
                            if isinstance(val, dict):
                                total = (val.get("home", 0) or 0) + (val.get("away", 0) or 0)
                                if total > 0:
                                    enriched["dangerous_attacks"] = total

            # Buscar detalhes da partida para odds
            details = self.get_fixture_details(fixture_id)
            if details and isinstance(details, dict):
                odds = details.get("odds", {})
                # Procurar odd de Over 0.5 HT
                over_05 = odds.get("over_05_ht", odds.get("overUnder", {}).get("0.5", {}))
                if isinstance(over_05, dict):
                    enriched["fair_odd_over_05_ht"] = over_05.get("over", over_05.get("o"))
                elif isinstance(over_05, (int, float)):
                    enriched["fair_odd_over_05_ht"] = float(over_05)
                    
        except Exception as e:
            logger.warning(f"Erro ao enriquecer dados do SokkerPRO (fixture {fixture_id}): {e}")
        
        return enriched
