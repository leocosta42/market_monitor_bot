from typing import Tuple, Dict, Optional
from .models import TeamStats, LiveMatchMetrics, MatchContext, AlertStatus
from .validators import PreGameValidator, LiveGameValidator, ExceptionValidator
from .strategy import StrategyConfig


class AlertOrchestrator:
    def __init__(self, config: StrategyConfig | None = None):
        self.cfg = config or StrategyConfig()
        self.pre_game_validator = PreGameValidator(self.cfg)
        self.live_game_validator = LiveGameValidator(self.cfg)
        self.exception_validator = ExceptionValidator(self.cfg)

    def should_monitor_match(self, home: TeamStats, away: TeamStats) -> Tuple[bool, Dict]:
        report = self.pre_game_validator.get_validation_report(home, away)
        return report["passed"], report

    def evaluate_live_conditions(self, metrics: LiveMatchMetrics) -> Tuple[AlertStatus, Dict]:
        time_score_report = self.live_game_validator.validate_time_and_score(metrics)

        if not time_score_report["passed"]:
            # Placar deixou de ser 0x0 ou ja passou da janela -> descarta de vez.
            if metrics.current_score != (0, 0) or metrics.match_time > self.cfg.max_minute:
                return AlertStatus.DISCARDED, {"time_score": time_score_report}
            # Ainda cedo demais -> segue observando.
            return AlertStatus.WAITING, {"time_score": time_score_report}

        metrics_report = self.live_game_validator.validate_metrics(metrics)
        if not metrics_report["passed"]:
            return AlertStatus.WAITING, {"time_score": time_score_report, "metrics": metrics_report}

        exceptions_report = self.exception_validator.validate_exceptions(metrics)
        base = {
            "time_score": time_score_report,
            "metrics": metrics_report,
            "exceptions": exceptions_report,
        }
        if exceptions_report["is_blocked"]:
            return AlertStatus.BLOCKED, base
        return AlertStatus.TRIGGERED, base

    def process_match(self, context: MatchContext) -> Tuple[AlertStatus, Dict, Optional[str]]:
        should_monitor, pre_game_report = self.should_monitor_match(
            context.home_team, context.away_team
        )
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
        m = context.live_metrics
        avg_ht = (context.home_team.over_05_ht_hit_rate + context.away_team.over_05_ht_hit_rate) / 2
        attacks_per_min = m.dangerous_attacks / m.match_time if m.match_time > 0 else 0

        lines = [
            "🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨",
            "",
            f"⚽ Jogo: {context.home_team.team_name} vs {context.away_team.team_name}",
            f"🏆 Competição: {context.competition}",
            f"⏱ Tempo: {m.match_time}' | Placar: {m.current_score[0]}x{m.current_score[1]}",
            "",
            "📊 Métricas da Partida:",
            f"• Finalizações no gol: {m.shots_on_target}",
            f"• Ataques perigosos: {m.dangerous_attacks} ({attacks_per_min:.2f}/min)",
            f"• Escanteios: {m.corners}",
        ]

        if m.market_odd_over_05_ht is not None:
            lines.append(f"• Odd de mercado (+0.5 HT): @{m.market_odd_over_05_ht:.2f}")
        if m.fair_odd_over_05_ht is not None:
            lines.append(f"• Odd justa (modelo): @{m.fair_odd_over_05_ht:.2f}")
        if m.value_edge is not None:
            lines.append(f"• Edge de valor: {m.value_edge * 100:+.1f}%")

        lines += [
            "",
            "💡 Histórico pré-jogo:",
            f"• Média HT dos times: {avg_ht * 100:.1f}%",
            "",
            "⚠️ Gestão recomendada: 1 unidade / stake padrão. Aposte com responsabilidade.",
        ]
        return "\n".join(lines)
