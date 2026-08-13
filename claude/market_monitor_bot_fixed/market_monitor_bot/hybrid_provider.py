"""
Hybrid Data Provider.
SofaScore = scanner rapido de todos os jogos.
SokkerPRO = enriquecimento (xG, pressao, odd de mercado e odd justa).
"""
import logging
from typing import List
from .models import MatchContext
from .sofascore_provider import SofaScoreProvider
from .sokkerpro_provider import SokkerProProvider
from .team_stats_repository import TeamStatsRepository

logger = logging.getLogger(__name__)


class HybridProvider:
    def __init__(self, stats_repo: TeamStatsRepository, min_minute: int = 15, max_minute: int = 28):
        self.sofascore = SofaScoreProvider()
        self.sokkerpro = SokkerProProvider()
        self.stats_repo = stats_repo
        self.min_minute = min_minute
        self.max_minute = max_minute
        self._sokkerpro_cache: List = []
        self._cache_cycle = 0

    def get_enriched_matches(self) -> List[MatchContext]:
        contexts: List[MatchContext] = []

        events = self.sofascore.get_live_matches()
        logger.info("[SofaScore] %s jogos ao vivo detectados.", len(events))

        # Pre-filtro barato ANTES de puxar estatisticas (protege contra ban por volume).
        candidates = [
            e for e in events
            if self.sofascore.is_candidate(e, self.min_minute, self.max_minute)
        ]
        logger.info("[Filtro] %s candidatos dentro da janela/placar 0x0.", len(candidates))
        if not candidates:
            return contexts

        # Atualiza cache do SokkerPRO a cada ~3 ciclos.
        self._cache_cycle += 1
        if self._cache_cycle >= 3 or not self._sokkerpro_cache:
            self._sokkerpro_cache = self.sokkerpro.get_live_fixtures()
            self._cache_cycle = 0

        for event in candidates:
            stats = self.sofascore.get_match_statistics(event.get("id"))
            ctx = self.sofascore.build_match_context(event, stats, self.stats_repo)
            if ctx is None:
                continue

            fixture_id = self.sokkerpro.find_fixture_by_teams(
                ctx.home_team.team_name, ctx.away_team.team_name, self._sokkerpro_cache
            )
            if fixture_id:
                data = self.sokkerpro.enrich_match_data(fixture_id)
                if data.get("enriched"):
                    m = ctx.live_metrics
                    m.xg_home = data.get("xg_home", m.xg_home)
                    m.xg_away = data.get("xg_away", m.xg_away)
                    m.pressure_home = data.get("pressure_home", m.pressure_home)
                    m.pressure_away = data.get("pressure_away", m.pressure_away)
                    # market e fair permanecem SEPARADOS (nunca sobrescreve um com o outro)
                    if data.get("market_odd_over_05_ht") is not None:
                        m.market_odd_over_05_ht = data["market_odd_over_05_ht"]
                    if data.get("fair_odd_over_05_ht") is not None:
                        m.fair_odd_over_05_ht = data["fair_odd_over_05_ht"]
                    m.data_source = "hybrid"
                    logger.info("[Hybrid] ✅ %s vs %s enriquecido.",
                                ctx.home_team.team_name, ctx.away_team.team_name)

            contexts.append(ctx)

        return contexts
