from typing import Tuple, Dict, Optional
from .models import TeamStats, LiveMatchMetrics, MatchContext, AlertStatus
from .validators import PreGameValidator, LiveGameValidator, ExceptionValidator

class AlertOrchestrator:
    def __init__(self):
        self.pre_game_validator = PreGameValidator()
        self.live_game_validator = LiveGameValidator()
        self.exception_validator = ExceptionValidator()

    def should_monitor_match(self, home: TeamStats, away: TeamStats) -> Tuple[bool, Dict]:
        report = self.pre_game_validator.get_validation_report(home, away)
        return report["passed"], report

    def evaluate_live_conditions(self, metrics: LiveMatchMetrics) -> Tuple[AlertStatus, Dict]:
        time_score_report = self.live_game_validator.validate_time_and_score(metrics)
        
        if not time_score_report["passed"]:
            # If not in time window or score is not 0x0
            if metrics.current_score != (0, 0) or metrics.match_time > 28:
                return AlertStatus.DISCARDED, {"time_score": time_score_report}
            return AlertStatus.WAITING, {"time_score": time_score_report}
            
        metrics_report = self.live_game_validator.validate_metrics(metrics)
        
        if not metrics_report["passed"]:
            return AlertStatus.WAITING, {"time_score": time_score_report, "metrics": metrics_report}
            
        exceptions_report = self.exception_validator.validate_exceptions(metrics)
        
        if exceptions_report["is_blocked"]:
            return AlertStatus.BLOCKED, {
                "time_score": time_score_report, 
                "metrics": metrics_report, 
                "exceptions": exceptions_report
            }
            
        return AlertStatus.TRIGGERED, {
            "time_score": time_score_report, 
            "metrics": metrics_report, 
            "exceptions": exceptions_report
        }

    def process_match(self, context: MatchContext) -> Tuple[AlertStatus, Dict, Optional[str]]:
        should_monitor, pre_game_report = self.should_monitor_match(context.home_team, context.away_team)
        
        report = {"pre_game": pre_game_report, "live": {}}
        
        if not should_monitor:
            return AlertStatus.DISCARDED, report, None
            
        status, live_report = self.evaluate_live_conditions(context.live_metrics)
        report["live"] = live_report
        
        alert_message = None
        if status == AlertStatus.TRIGGERED and not context.alert_sent:
            alert_message = self._generate_alert_message(context)
            
        return status, report, alert_message

    def _generate_alert_message(self, context: MatchContext) -> str:
        metrics = context.live_metrics
        avg_ht = (context.home_team.over_05_ht_hit_rate + context.away_team.over_05_ht_hit_rate) / 2
        
        attacks_per_min = metrics.dangerous_attacks / metrics.match_time if metrics.match_time > 0 else 0
        
        msg = f"🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨\n\n"
        msg += f"⚽ Jogo: {context.home_team.team_name} vs {context.away_team.team_name}\n"
        msg += f"🏆 Competição: {context.competition}\n"
        msg += f"⏱ Tempo: {metrics.match_time}' | Placar: {metrics.current_score[0]}x{metrics.current_score[1]}\n\n"
        msg += f"📊 Métricas da Partida:\n"
        msg += f"• Odd Atual (+0.5 HT): @{metrics.current_odd_over_05_ht:.2f}\n"
        msg += f"• Finalizações no Gol: {metrics.shots_on_target}\n"
        msg += f"• Ataques Perigosos: {metrics.dangerous_attacks} ({attacks_per_min:.2f}/min)\n"
        msg += f"• Escanteios: {metrics.corners}\n\n"
        msg += f"💡 Histórico Pré-Jogo:\n"
        msg += f"• Média HT dos times: {avg_ht * 100:.1f}%\n\n"
        msg += f"⚠️ Gestão recomendada: 1 Unidade / Stake Padrão."
        
        return msg
