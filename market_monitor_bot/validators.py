from typing import Dict
from .models import TeamStats, LiveMatchMetrics

class PreGameValidator:
    def validate_both_teams(self, home: TeamStats, away: TeamStats) -> bool:
        report = self.get_validation_report(home, away)
        return report["passed"]

    def get_validation_report(self, home: TeamStats, away: TeamStats) -> Dict:
        def check_team(team: TeamStats) -> bool:
            return team.over_05_ht_hit_rate > 0.70 and team.over_25_ft_pre_odd < 1.90

        home_passed = check_team(home)
        away_passed = check_team(away)
        
        return {
            "passed": home_passed and away_passed,
            "home": {
                "passed": home_passed,
                "over_05_ht": home.over_05_ht_hit_rate,
                "over_25_ft": home.over_25_ft_pre_odd
            },
            "away": {
                "passed": away_passed,
                "over_05_ht": away.over_05_ht_hit_rate,
                "over_25_ft": away.over_25_ft_pre_odd
            }
        }

class LiveGameValidator:
    def validate_time_and_score(self, metrics: LiveMatchMetrics) -> Dict:
        time_valid = 15 <= metrics.match_time <= 28
        score_valid = metrics.current_score == (0, 0)
        
        return {
            "passed": time_valid and score_valid,
            "time_valid": time_valid,
            "score_valid": score_valid,
            "time": metrics.match_time,
            "score": metrics.current_score
        }

    def validate_metrics(self, metrics: LiveMatchMetrics) -> Dict:
        shots_on_target_valid = metrics.shots_on_target >= 2
        shots_off_target_valid = metrics.shots_off_target >= 3
        
        # Ataques perigosos por minuto > 1.0
        # Ex: aos 20 minutos, precisa de > 20 ataques.
        attacks_per_min = metrics.dangerous_attacks / metrics.match_time if metrics.match_time > 0 else 0
        attacks_valid = attacks_per_min > 1.0
        
        corners_valid = metrics.corners >= 2
        odd_valid = metrics.current_odd_over_05_ht >= 1.65
        
        all_passed = (shots_on_target_valid and shots_off_target_valid and 
                      attacks_valid and corners_valid and odd_valid)
        
        return {
            "passed": all_passed,
            "shots_on_target": {"passed": shots_on_target_valid, "value": metrics.shots_on_target},
            "shots_off_target": {"passed": shots_off_target_valid, "value": metrics.shots_off_target},
            "dangerous_attacks": {"passed": attacks_valid, "value": metrics.dangerous_attacks, "per_min": round(attacks_per_min, 2)},
            "corners": {"passed": corners_valid, "value": metrics.corners},
            "odd": {"passed": odd_valid, "value": metrics.current_odd_over_05_ht}
        }

class ExceptionValidator:
    def validate_exceptions(self, metrics: LiveMatchMetrics) -> Dict:
        red_card_blocked = metrics.red_cards > 0 and metrics.red_card_time is not None and metrics.red_card_time < 20
        fouls_blocked = metrics.fouls > 12
        
        is_blocked = red_card_blocked or fouls_blocked
        
        return {
            "is_blocked": is_blocked,
            "red_card_blocked": red_card_blocked,
            "fouls_blocked": fouls_blocked
        }
