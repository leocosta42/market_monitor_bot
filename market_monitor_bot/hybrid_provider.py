"""
Hybrid Data Provider
Combina SofaScore (scanner rápido) + SokkerPRO (enriquecimento com xG, Pressão, Odds).
"""
import logging
from typing import List, Optional
from .models import MatchContext
from .sofascore_provider import SofaScoreProvider
from .sokkerpro_provider import SokkerProProvider

logger = logging.getLogger(__name__)

class HybridProvider:
    """
    Provedor Híbrido de Dados:
    1. SofaScore varre TODOS os jogos ao vivo (rápido, leve).
    2. SokkerPRO enriquece jogos promissores (xG, Pressão, Odd Justa).
    """
    def __init__(self):
        self.sofascore = SofaScoreProvider()
        self.sokkerpro = SokkerProProvider()
        self._sokkerpro_live_cache = []
        self._cache_cycle = 0
    
    def get_enriched_matches(self) -> List[MatchContext]:
        """
        Fluxo principal:
        1. Busca todos os jogos ao vivo via SofaScore.
        2. Filtra os que estão no 1º tempo.
        3. Tenta enriquecer cada um com dados do SokkerPRO.
        """
        enriched_contexts = []
        
        # PASSO 1: SofaScore - Scanner rápido de todos os jogos
        events = self.sofascore.get_live_matches()
        logger.info(f"[SofaScore] {len(events)} jogos ao vivo detectados.")
        
        # PASSO 2: SokkerPRO - Atualiza cache de jogos a cada 3 ciclos (~90s)
        self._cache_cycle += 1
        if self._cache_cycle >= 3 or not self._sokkerpro_live_cache:
            self._sokkerpro_live_cache = self.sokkerpro.get_live_fixtures()
            self._cache_cycle = 0
        
        # PASSO 3: Para cada jogo do SofaScore, montar contexto e enriquecer
        for event in events:
            event_id = str(event.get("id"))
            stats = self.sofascore.get_match_statistics(event.get("id"))
            match_context = self.sofascore.build_match_context(event, stats)
            
            if match_context is None:
                continue  # Não está no 1º tempo
            
            # PASSO 4: Tentar enriquecer com SokkerPRO
            home_name = match_context.home_team.team_name
            away_name = match_context.away_team.team_name
            
            fixture_id = self.sokkerpro.find_fixture_by_teams(
                home_name, away_name, self._sokkerpro_live_cache
            )
            
            if fixture_id:
                enriched_data = self.sokkerpro.enrich_match_data(fixture_id)
                
                if enriched_data.get("enriched"):
                    metrics = match_context.live_metrics
                    
                    # Aplicar dados enriquecidos
                    if enriched_data.get("xg_home") is not None:
                        metrics.xg_home = enriched_data["xg_home"]
                    if enriched_data.get("xg_away") is not None:
                        metrics.xg_away = enriched_data["xg_away"]
                    if enriched_data.get("pressure_home") is not None:
                        metrics.pressure_home = enriched_data["pressure_home"]
                    if enriched_data.get("pressure_away") is not None:
                        metrics.pressure_away = enriched_data["pressure_away"]
                    if enriched_data.get("fair_odd_over_05_ht") is not None:
                        metrics.fair_odd_over_05_ht = enriched_data["fair_odd_over_05_ht"]
                        # Se temos a odd real, usamos ela no lugar do mock!
                        metrics.current_odd_over_05_ht = enriched_data["fair_odd_over_05_ht"]
                    
                    metrics.data_source = "hybrid"
                    logger.info(f"[Hybrid] ✅ {home_name} vs {away_name} enriquecido com SokkerPRO (xG, Pressão)")
                else:
                    logger.debug(f"[Hybrid] SokkerPRO não retornou dados extras para {home_name} vs {away_name}")
            
            enriched_contexts.append(match_context)
        
        return enriched_contexts
