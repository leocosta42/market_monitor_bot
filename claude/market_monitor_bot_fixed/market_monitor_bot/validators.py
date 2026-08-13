from typing import Dict
from .models import TeamStats, LiveMatchMetrics
from .strategy import StrategyConfig


class PreGameValidator:
    def __init__(self, config: StrategyConfig | None = None):
        self.cfg = config or StrategyConfig()

    def _check_team(self, team: TeamStats) -> bool:
        return (
            team.over_05_ht_hit_rate > self.cfg.min_over_05_ht_hit_rate
            and team.over_25_ft_pre_odd < self.cfg.max_over_25_ft_pre_odd
        )

    def validate_both_teams(self, home: TeamStats, away: TeamStats) -> bool:
        return self.get_validation_report(home, away)["passed"]

    def get_validation_report(self, home: TeamStats, away: TeamStats) -> Dict:
        home_passed = self._check_team(home)
        away_passed = self._check_team(away)
        return {
            "passed": home_passed and away_passed,
            "home": {
                "passed": home_passed,
                "over_05_ht": home.over_05_ht_hit_rate,
                "over_25_ft": home.over_25_ft_pre_odd,
            },
            "away": {
                "passed": away_passed,
                "over_05_ht": away.over_05_ht_hit_rate,
                "over_25_ft": away.over_25_ft_pre_odd,
            },
        }


class LiveGameValidator:
    def __init__(self, config: StrategyConfig | None = None):
        self.cfg = config or StrategyConfig()

    def validate_time_and_score(self, metrics: LiveMatchMetrics) -> Dict:
        time_valid = self.cfg.min_minute <= metrics.match_time <= self.cfg.max_minute
        score_valid = metrics.current_score == (0, 0)
        return {
            "passed": time_valid and score_valid,
            "time_valid": time_valid,
            "score_valid": score_valid,
            "time": metrics.match_time,
            "score": metrics.current_score,
        }

    def validate_metrics(self, metrics: LiveMatchMetrics) -> Dict:
        cfg = self.cfg
        shots_on_target_valid = metrics.shots_on_target >= cfg.min_shots_on_target
        shots_off_target_valid = metrics.shots_off_target >= cfg.min_shots_off_target

        attacks_per_min = (
            metrics.dangerous_attacks / metrics.match_time if metrics.match_time > 0 else 0
        )
        attacks_valid = attacks_per_min > cfg.min_attacks_per_min
        corners_valid = metrics.corners >= cfg.min_corners

        # --- Verificacao de VALOR ---
        # Preferimos edge real (mercado vs justa). So cai no piso absoluto
        # quando nao temos odd justa para comparar.
        edge = metrics.value_edge
        if edge is not None:
            value_valid = edge >= cfg.min_value_edge
            value_kind = "edge"
            value_detail = round(edge, 4)
        elif metrics.market_odd_over_05_ht is not None:
            value_valid = metrics.market_odd_over_05_ht >= cfg.min_market_odd
            value_kind = "floor"
            value_detail = metrics.market_odd_over_05_ht
        else:
            # Sem qualquer odd nao da para confirmar valor.
            value_valid = False
            value_kind = "no_odd"
            value_detail = None

        all_passed = (
            shots_on_target_valid
            and shots_off_target_valid
            and attacks_valid
            and corners_valid
            and value_valid
        )

        return {
            "passed": all_passed,
            "shots_on_target": {"passed": shots_on_target_valid, "value": metrics.shots_on_target},
            "shots_off_target": {"passed": shots_off_target_valid, "value": metrics.shots_off_target},
            "dangerous_attacks": {
                "passed": attacks_valid,
                "value": metrics.dangerous_attacks,
                "per_min": round(attacks_per_min, 2),
            },
            "corners": {"passed": corners_valid, "value": metrics.corners},
            "value": {
                "passed": value_valid,
                "kind": value_kind,       # "edge" | "floor" | "no_odd"
                "detail": value_detail,
                "market_odd": metrics.market_odd_over_05_ht,
                "fair_odd": metrics.fair_odd_over_05_ht,
            },
        }


class ExceptionValidator:
    def __init__(self, config: StrategyConfig | None = None):
        self.cfg = config or StrategyConfig()

    def validate_exceptions(self, metrics: LiveMatchMetrics) -> Dict:
        red_card_blocked = (
            metrics.red_cards > 0
            and metrics.red_card_time is not None
            and metrics.red_card_time < self.cfg.red_card_before_minute
        )
        fouls_blocked = metrics.fouls > self.cfg.max_fouls
        return {
            "is_blocked": red_card_blocked or fouls_blocked,
            "red_card_blocked": red_card_blocked,
            "fouls_blocked": fouls_blocked,
        }
