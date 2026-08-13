"""
🚨 OVER 0.5 HT LIVE ALERT BOT
Sistema de Alertas Estatísticos para Trading Esportivo
Especialista: Análise de Futebol em Tempo Real
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
import json

# ============================================================================
# 1. DEFINIÇÃO DE ESTRUTURAS DE DADOS
# ============================================================================

class AlertStatus(Enum):
    """Status do alerta"""
    PENDING = "pending"          # Aguardando condições
    TRIGGERED = "triggered"      # Condições atendidas
    SENT = "sent"               # Enviado com sucesso
    REJECTED = "rejected"       # Descartado por critérios
    BLOCKED = "blocked"         # Bloqueado por exceção


@dataclass
class TeamStats:
    """Estatísticas históricas do time"""
    team_id: str
    team_name: str
    over_05_ht_hit_rate: float  # Porcentagem de Over 0.5 HT (últimos 10 jogos)
    over_25_ft_pre_odd: float   # Odd pré-jogo Over 2.5 FT


@dataclass
class LiveMatchMetrics:
    """Métricas ao vivo durante o jogo"""
    match_id: str
    match_time: int                    # Minuto atual (0-90+)
    current_score: tuple              # (gols_casa, gols_fora)
    shots_on_target: int              # Chutes no gol
    shots_off_target: int             # Chutes para fora
    dangerous_attacks: int            # Total de ataques perigosos
    corners: int                      # Total de escanteios
    fouls: int                        # Total de faltas
    red_cards: int                    # Cartões vermelhos
    red_card_time: Optional[int]      # Minuto do cartão vermelho
    current_odd_over_05_ht: float     # Odd atual Over 0.5 HT


@dataclass
class MatchContext:
    """Contexto completo da partida"""
    match_id: str
    home_team: TeamStats
    away_team: TeamStats
    competition: str
    live_metrics: LiveMatchMetrics
    triggered_at_time: Optional[int] = None
    alert_sent: bool = False


# ============================================================================
# 2. SISTEMA DE VALIDAÇÃO (PRÉ-REQUISITOS)
# ============================================================================

class PreGameValidator:
    """Valida critérios pré-jogo antes de monitorar"""
    
    MIN_OVER_05_HT_HIT_RATE = 0.70    # 70%
    MAX_OVER_25_FT_PRE_ODD = 1.90     # Odds < 1.90
    
    @staticmethod
    def validate_both_teams(home: TeamStats, away: TeamStats) -> bool:
        """
        Verifica se AMBAS as equipes atendem aos critérios pré-jogo
        
        Critérios:
        1. Média histórica Over 0.5 HT > 70% (últimos 10 jogos)
        2. Odd pré-jogo Over 2.5 FT < 1.90 (jogo movimentado esperado)
        """
        home_passes = (
            home.over_05_ht_hit_rate >= PreGameValidator.MIN_OVER_05_HT_HIT_RATE
            and home.over_25_ft_pre_odd < PreGameValidator.MAX_OVER_25_FT_PRE_ODD
        )
        
        away_passes = (
            away.over_05_ht_hit_rate >= PreGameValidator.MIN_OVER_05_HT_HIT_RATE
            and away.over_25_ft_pre_odd < PreGameValidator.MAX_OVER_25_FT_PRE_ODD
        )
        
        return home_passes and away_passes
    
    @staticmethod
    def get_validation_report(home: TeamStats, away: TeamStats) -> Dict:
        """Relatório detalhado da validação pré-jogo"""
        return {
            "home": {
                "team": home.team_name,
                "over_05_ht_rate": f"{home.over_05_ht_hit_rate*100:.1f}%",
                "over_05_ht_valid": home.over_05_ht_hit_rate >= PreGameValidator.MIN_OVER_05_HT_HIT_RATE,
                "over_25_ft_odd": home.over_25_ft_pre_odd,
                "over_25_ft_valid": home.over_25_ft_pre_odd < PreGameValidator.MAX_OVER_25_FT_PRE_ODD,
            },
            "away": {
                "team": away.team_name,
                "over_05_ht_rate": f"{away.over_05_ht_hit_rate*100:.1f}%",
                "over_05_ht_valid": away.over_05_ht_hit_rate >= PreGameValidator.MIN_OVER_05_HT_HIT_RATE,
                "over_25_ft_odd": away.over_25_ft_pre_odd,
                "over_25_ft_valid": away.over_25_ft_pre_odd < PreGameValidator.MAX_OVER_25_FT_PRE_ODD,
            },
            "both_pass": PreGameValidator.validate_both_teams(home, away)
        }


# ============================================================================
# 3. VALIDADOR AO VIVO (LIVE DATA CHECKER)
# ============================================================================

class LiveGameValidator:
    """Valida condições ao vivo durante o primeiro tempo"""
    
    # Janela de tempo (minutos)
    MIN_TIME = 15
    MAX_TIME = 28
    
    # Métricas mínimas
    MIN_SHOTS_ON_TARGET = 2
    MIN_SHOTS_OFF_TARGET = 3
    MIN_CORNERS = 2
    MIN_DANGEROUS_ATTACKS_PER_MINUTE = 1.0
    
    # Odd
    MIN_ODD_OVER_05_HT = 1.65
    IDEAL_ODD_RANGE = (1.70, 1.85)
    
    @staticmethod
    def validate_time_and_score(metrics: LiveMatchMetrics) -> Dict:
        """Verifica janela de tempo e placar 0x0"""
        time_valid = LiveGameValidator.MIN_TIME <= metrics.match_time <= LiveGameValidator.MAX_TIME
        score_valid = metrics.current_score == (0, 0)
        
        return {
            "time_valid": time_valid,
            "current_time": f"{metrics.match_time}'",
            "min_time": LiveGameValidator.MIN_TIME,
            "max_time": LiveGameValidator.MAX_TIME,
            "score_valid": score_valid,
            "current_score": f"{metrics.current_score[0]}x{metrics.current_score[1]}"
        }
    
    @staticmethod
    def validate_metrics(metrics: LiveMatchMetrics) -> Dict:
        """Valida todas as métricas de jogo"""
        shots_on_target_valid = metrics.shots_on_target >= LiveGameValidator.MIN_SHOTS_ON_TARGET
        shots_off_target_valid = metrics.shots_off_target >= LiveGameValidator.MIN_SHOTS_OFF_TARGET
        corners_valid = metrics.corners >= LiveGameValidator.MIN_CORNERS
        
        # Ataques perigosos: média por minuto
        attacks_per_minute = metrics.dangerous_attacks / max(metrics.match_time, 1)
        attacks_valid = attacks_per_minute >= LiveGameValidator.MIN_DANGEROUS_ATTACKS_PER_MINUTE
        
        # Odd
        odd_valid = metrics.current_odd_over_05_ht >= LiveGameValidator.MIN_ODD_OVER_05_HT
        odd_ideal = LiveGameValidator.IDEAL_ODD_RANGE[0] <= metrics.current_odd_over_05_ht <= LiveGameValidator.IDEAL_ODD_RANGE[1]
        
        all_metrics_pass = all([
            shots_on_target_valid,
            shots_off_target_valid,
            corners_valid,
            attacks_valid,
            odd_valid
        ])
        
        return {
            "shots_on_target": {
                "current": metrics.shots_on_target,
                "minimum": LiveGameValidator.MIN_SHOTS_ON_TARGET,
                "valid": shots_on_target_valid
            },
            "shots_off_target": {
                "current": metrics.shots_off_target,
                "minimum": LiveGameValidator.MIN_SHOTS_OFF_TARGET,
                "valid": shots_off_target_valid
            },
            "corners": {
                "current": metrics.corners,
                "minimum": LiveGameValidator.MIN_CORNERS,
                "valid": corners_valid
            },
            "dangerous_attacks": {
                "current": metrics.dangerous_attacks,
                "per_minute": f"{attacks_per_minute:.2f}",
                "minimum_per_minute": LiveGameValidator.MIN_DANGEROUS_ATTACKS_PER_MINUTE,
                "valid": attacks_valid
            },
            "odd_over_05_ht": {
                "current": metrics.current_odd_over_05_ht,
                "minimum": LiveGameValidator.MIN_ODD_OVER_05_HT,
                "ideal_range": LiveGameValidator.IDEAL_ODD_RANGE,
                "valid": odd_valid,
                "in_ideal_range": odd_ideal
            },
            "all_metrics_pass": all_metrics_pass
        }


# ============================================================================
# 4. VALIDADOR DE EXCEÇÕES (EXCEPTION HANDLER)
# ============================================================================

class ExceptionValidator:
    """Valida condições que BLOQUEIAM o alerta"""
    
    MAX_RED_CARD_TIME = 20     # Cartão vermelho antes de 20 min
    MAX_FOULS = 12             # Máximo de faltas antes de bloqueio
    
    @staticmethod
    def validate_exceptions(metrics: LiveMatchMetrics) -> Dict:
        """
        Verifica exceções que descartam o alerta:
        1. Cartão vermelho antes dos 20 minutos
        2. Número de faltas > 12 (jogo truncado)
        """
        red_card_blocked = False
        red_card_reason = None
        
        if metrics.red_cards > 0 and metrics.red_card_time is not None:
            if metrics.red_card_time < ExceptionValidator.MAX_RED_CARD_TIME:
                red_card_blocked = True
                red_card_reason = f"Cartão vermelho aos {metrics.red_card_time}'"
        
        fouls_blocked = metrics.fouls > ExceptionValidator.MAX_FOULS
        fouls_reason = f"Jogo muito truncado ({metrics.fouls} faltas)" if fouls_blocked else None
        
        is_blocked = red_card_blocked or fouls_blocked
        
        return {
            "is_blocked": is_blocked,
            "red_card_blocked": {
                "blocked": red_card_blocked,
                "reason": red_card_reason,
                "red_cards": metrics.red_cards,
                "max_time_threshold": ExceptionValidator.MAX_RED_CARD_TIME
            },
            "fouls_blocked": {
                "blocked": fouls_blocked,
                "reason": fouls_reason,
                "current_fouls": metrics.fouls,
                "max_threshold": ExceptionValidator.MAX_FOULS
            }
        }


# ============================================================================
# 5. ORQUESTRADOR CENTRAL (ALERT ORCHESTRATOR)
# ============================================================================

class AlertOrchestrator:
    """
    Orquestra toda a lógica de validação e emissão de alertas
    Ponto central para monitoramento de partidas
    """
    
    def __init__(self):
        self.pre_game_validator = PreGameValidator()
        self.live_validator = LiveGameValidator()
        self.exception_validator = ExceptionValidator()
        self.alerts_history: List[Dict] = []
    
    def should_monitor_match(self, home: TeamStats, away: TeamStats) -> tuple[bool, Dict]:
        """
        Determina se a partida deve ser monitorada
        
        Returns:
            (should_monitor: bool, validation_report: Dict)
        """
        validation_report = self.pre_game_validator.get_validation_report(home, away)
        should_monitor = validation_report["both_pass"]
        
        return should_monitor, validation_report
    
    def evaluate_live_conditions(self, metrics: LiveMatchMetrics) -> tuple[AlertStatus, Dict]:
        """
        Avalia condições ao vivo em tempo real
        
        Returns:
            (status: AlertStatus, evaluation_report: Dict)
        """
        time_score_check = self.live_validator.validate_time_and_score(metrics)
        metrics_check = self.live_validator.validate_metrics(metrics)
        exception_check = self.exception_validator.validate_exceptions(metrics)
        
        # Lógica de decisão
        time_score_pass = time_score_check["time_valid"] and time_score_check["score_valid"]
        metrics_pass = metrics_check["all_metrics_pass"]
        
        if not time_score_pass:
            status = AlertStatus.PENDING
        elif exception_check["is_blocked"]:
            status = AlertStatus.BLOCKED
        elif metrics_pass:
            status = AlertStatus.TRIGGERED
        else:
            status = AlertStatus.PENDING
        
        evaluation_report = {
            "time_and_score": time_score_check,
            "metrics": metrics_check,
            "exceptions": exception_check,
            "status": status.value,
            "timestamp": datetime.now().isoformat()
        }
        
        return status, evaluation_report
    
    def generate_alert_message(self, context: MatchContext) -> str:
        """
        Gera mensagem formatada para envio via Telegram/Discord
        
        Formato:
        🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨
        ⚽ Jogo: [Times]
        🏆 Competição: [Campeonato]
        ...
        """
        metrics = context.live_metrics
        
        # Cálculo de ataques perigosos por minuto
        attacks_per_minute = metrics.dangerous_attacks / max(metrics.match_time, 1)
        
        # Média histórica dos times
        avg_ht_rate = (
            (context.home_team.over_05_ht_hit_rate + context.away_team.over_05_ht_hit_rate) / 2
        ) * 100
        
        message = f"""
🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨

⚽ Jogo: {context.home_team.team_name} vs {context.away_team.team_name}
🏆 Competição: {context.competition}
⏱ Tempo: {metrics.match_time}' | Placar: {metrics.current_score[0]}x{metrics.current_score[1]}

📊 Métricas da Partida:
• Odd Atual (+0.5 HT): @{metrics.current_odd_over_05_ht:.2f}
• Finalizações no Gol: {metrics.shots_on_target}
• Ataques Perigosos: {metrics.dangerous_attacks} ({attacks_per_minute:.2f}/min)
• Escanteios: {metrics.corners}
• Chutes para Fora: {metrics.shots_off_target}

💡 Histórico Pré-Jogo:
• Média HT dos times: {avg_ht_rate:.1f}%
• {context.home_team.team_name}: {context.home_team.over_05_ht_hit_rate*100:.1f}%
• {context.away_team.team_name}: {context.away_team.over_05_ht_hit_rate*100:.1f}%

⚠️ Gestão recomendada: 1 Unidade / Stake Padrão.

📈 Valor detectado aos {metrics.match_time}'
✅ Todos os critérios atendidos
"""
        return message.strip()
    
    def process_match(self, context: MatchContext) -> tuple[AlertStatus, Dict, Optional[str]]:
        """
        Processa uma partida completa, retornando status e alerta
        
        Returns:
            (status: AlertStatus, report: Dict, alert_message: Optional[str])
        """
        # 1. Valida pré-requisitos
        should_monitor, pre_game_report = self.should_monitor_match(
            context.home_team, context.away_team
        )
        
        if not should_monitor:
            return AlertStatus.REJECTED, {"pre_game": pre_game_report}, None
        
        # 2. Avalia condições ao vivo
        status, live_report = self.evaluate_live_conditions(context.live_metrics)
        
        # 3. Gera alerta se condições forem atendidas
        alert_message = None
        if status == AlertStatus.TRIGGERED:
            alert_message = self.generate_alert_message(context)
            context.alert_sent = True
            context.triggered_at_time = context.live_metrics.match_time
            self.alerts_history.append({
                "match_id": context.match_id,
                "sent_at": datetime.now().isoformat(),
                "match_time": context.triggered_at_time
            })
        
        full_report = {
            "pre_game": pre_game_report,
            "live": live_report,
            "status": status.value,
            "alert_generated": alert_message is not None
        }
        
        return status, full_report, alert_message


# ============================================================================
# 6. EXEMPLO DE UTILIZAÇÃO
# ============================================================================

def example_usage():
    """Demonstração de uso do sistema"""
    
    # Criar dados de exemplo
    home = TeamStats(
        team_id="fc_porto",
        team_name="FC Porto",
        over_05_ht_hit_rate=0.75,
        over_25_ft_pre_odd=1.85
    )
    
    away = TeamStats(
        team_id="benfica",
        team_name="SL Benfica",
        over_05_ht_hit_rate=0.72,
        over_25_ft_pre_odd=1.88
    )
    
    metrics = LiveMatchMetrics(
        match_id="porto_vs_benfica_20240815",
        match_time=22,
        current_score=(0, 0),
        shots_on_target=3,
        shots_off_target=5,
        dangerous_attacks=22,
        corners=3,
        fouls=8,
        red_cards=0,
        red_card_time=None,
        current_odd_over_05_ht=1.78
    )
    
    context = MatchContext(
        match_id="porto_vs_benfica_20240815",
        home_team=home,
        away_team=away,
        competition="Primeira Liga Portugal",
        live_metrics=metrics
    )
    
    # Processar partida
    orchestrator = AlertOrchestrator()
    status, report, alert_message = orchestrator.process_match(context)
    
    # Exibir resultados
    print("=" * 80)
    print("RESULTADO DO PROCESSAMENTO")
    print("=" * 80)
    print(f"\nStatus: {status.value.upper()}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    if alert_message:
        print("\n" + "=" * 80)
        print("ALERTA GERADO")
        print("=" * 80)
        print(alert_message)
    else:
        print("\n❌ Nenhum alerta foi gerado nesta partida.")


if __name__ == "__main__":
    example_usage()
