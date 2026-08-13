from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum


class AlertStatus(Enum):
    TRIGGERED = "TRIGGERED"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    DISCARDED = "DISCARDED"


@dataclass
class TeamStats:
    team_id: str
    team_name: str
    over_05_ht_hit_rate: float
    over_25_ft_pre_odd: float


@dataclass
class LiveMatchMetrics:
    match_id: str
    match_time: int
    current_score: Tuple[int, int]
    shots_on_target: int
    shots_off_target: int
    dangerous_attacks: int
    corners: int
    fouls: int
    red_cards: int
    red_card_time: Optional[int]

    # Odd praticada no mercado (bookmaker). None quando ainda nao temos fonte de odds.
    market_odd_over_05_ht: Optional[float] = None
    # Odd justa estimada por modelo (SokkerPRO / xG). None quando indisponivel.
    fair_odd_over_05_ht: Optional[float] = None

    # Campos enriquecidos (SokkerPRO)
    xg_home: Optional[float] = None
    xg_away: Optional[float] = None
    pressure_home: Optional[float] = None
    pressure_away: Optional[float] = None

    data_source: str = "sofascore"  # "sofascore", "sokkerpro", "hybrid"

    @property
    def value_edge(self) -> Optional[float]:
        """
        Edge de valor = (odd_mercado / odd_justa) - 1.
        > 0 significa que o mercado paga mais do que o modelo considera justo.
        Retorna None se faltar qualquer uma das odds.
        """
        if (
            self.market_odd_over_05_ht
            and self.fair_odd_over_05_ht
            and self.fair_odd_over_05_ht > 0
        ):
            return (self.market_odd_over_05_ht / self.fair_odd_over_05_ht) - 1.0
        return None


@dataclass
class MatchContext:
    match_id: str
    home_team: TeamStats
    away_team: TeamStats
    competition: str
    live_metrics: LiveMatchMetrics
    alert_sent: bool = False
