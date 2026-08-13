from market_monitor_bot import (
    AlertOrchestrator, MatchContext, TeamStats, LiveMatchMetrics, AlertStatus
)
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def create_base_context():
    home = TeamStats("home", "Time Casa", 0.75, 1.85)
    away = TeamStats("away", "Time Fora", 0.72, 1.88)
    metrics = LiveMatchMetrics(
        match_id="test",
        match_time=22,
        current_score=(0, 0),
        shots_on_target=3,
        shots_off_target=5,
        dangerous_attacks=25,
        corners=3,
        fouls=8,
        red_cards=0,
        red_card_time=None,
        current_odd_over_05_ht=1.78
    )
    return MatchContext("test", home, away, "Teste", metrics)

def run_tests():
    orchestrator = AlertOrchestrator()
    tests = [
        ("1. Cenário Ideal (Deve disparar)", lambda c: c, AlertStatus.TRIGGERED),
        ("2. Pré-jogo ruim (Deve descartar)", lambda c: setattr(c.home_team, 'over_05_ht_hit_rate', 0.60) or c, AlertStatus.DISCARDED),
        ("3. Fora da janela de tempo (Deve esperar/descartar)", lambda c: setattr(c.live_metrics, 'match_time', 10) or c, AlertStatus.WAITING),
        ("4. Placar não é 0x0 (Deve descartar)", lambda c: setattr(c.live_metrics, 'current_score', (1, 0)) or c, AlertStatus.DISCARDED),
        ("5. Poucos chutes no gol (Deve esperar)", lambda c: setattr(c.live_metrics, 'shots_on_target', 1) or c, AlertStatus.WAITING),
        ("6. Poucos ataques perigosos (Deve esperar)", lambda c: setattr(c.live_metrics, 'dangerous_attacks', 15) or c, AlertStatus.WAITING),
        ("7. Cartão vermelho precoce (Deve bloquear)", lambda c: (setattr(c.live_metrics, 'red_cards', 1), setattr(c.live_metrics, 'red_card_time', 15)) and c, AlertStatus.BLOCKED),
        ("8. Muitas faltas (Deve bloquear)", lambda c: setattr(c.live_metrics, 'fouls', 15) or c, AlertStatus.BLOCKED),
    ]

    passed = 0
    for name, modifier, expected in tests:
        context = modifier(create_base_context())
        status, _, _ = orchestrator.process_match(context)
        if status == expected:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name} (Esperado: {expected}, Recebido: {status})")

    print(f"\nResultado: {passed}/{len(tests)} testes passaram")

if __name__ == "__main__":
    run_tests()
