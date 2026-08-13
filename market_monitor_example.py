import json
from market_monitor_bot import (
    AlertOrchestrator, MatchContext, TeamStats, LiveMatchMetrics
)

def run_example():
    # 1. Dados dos times
    home = TeamStats(
        team_id="fc_porto",
        team_name="FC Porto",
        over_05_ht_hit_rate=0.75,      # 75% de Over 0.5 HT
        over_25_ft_pre_odd=1.85        # Odd Over 2.5 FT
    )

    away = TeamStats(
        team_id="benfica",
        team_name="SL Benfica",
        over_05_ht_hit_rate=0.72,
        over_25_ft_pre_odd=1.88
    )

    # 2. Métricas ao vivo (30+ minutos de jogo)
    metrics = LiveMatchMetrics(
        match_id="porto_benfica_123",
        match_time=22,               # Minuto atual
        current_score=(0, 0),        # Placar
        shots_on_target=3,           # Chutes no gol
        shots_off_target=5,          # Chutes para fora
        dangerous_attacks=22,        # Ataques perigosos
        corners=3,                   # Escanteios
        fouls=8,                     # Faltas
        red_cards=0,                 # Cartões vermelhos
        red_card_time=None,          # Minuto do vermelho
        current_odd_over_05_ht=1.78  # Odd atual
    )

    # 3. Processar
    orchestrator = AlertOrchestrator()
    status, report, alert_msg = orchestrator.process_match(
        MatchContext(
            match_id="porto_benfica_123",
            home_team=home,
            away_team=away,
            competition="Primeira Liga Portugal",
            live_metrics=metrics
        )
    )

    # 4. Resultado
    print(f"Status: {status.name}\n")
    if alert_msg:
        print(alert_msg)
    else:
        print("Nenhum alerta emitido.")
        
    print("\n--- Relatório Detalhado ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_example()
