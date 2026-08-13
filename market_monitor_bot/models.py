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
    current_odd_over_05_ht: float
    # Campos enriquecidos (SokkerPRO)
    xg_home: Optional[float] = None
    xg_away: Optional[float] = None
    pressure_home: Optional[float] = None
    pressure_away: Optional[float] = None
    fair_odd_over_05_ht: Optional[float] = None
    data_source: str = "sofascore"  # "sofascore", "sokkerpro", "hybrid"

@dataclass
class MatchContext:
    match_id: str
    home_team: TeamStats
    away_team: TeamStats
    competition: str
    live_metrics: LiveMatchMetrics
    alert_sent: bool = False
