"""
Testes de cenario para a estrategia Over 0.5 HT.
Rodar:  python -m pytest tests/ -v   (ou)   python tests/test_scenarios.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from market_monitor_bot import (  # noqa: E402
    AlertOrchestrator, MatchContext, TeamStats, LiveMatchMetrics, AlertStatus, StrategyConfig,
)


def _teams():
    home = TeamStats("fc_porto", "FC Porto", 0.75, 1.85)
    away = TeamStats("benfica", "SL Benfica", 0.72, 1.88)
    return home, away


def _metrics(**kw):
    base = dict(
        match_id="m1", match_time=22, current_score=(0, 0),
        shots_on_target=3, shots_off_target=5, dangerous_attacks=25,
        corners=3, fouls=8, red_cards=0, red_card_time=None,
        market_odd_over_05_ht=1.80, fair_odd_over_05_ht=1.65,
    )
    base.update(kw)
    return LiveMatchMetrics(**base)


def _ctx(metrics):
    home, away = _teams()
    return MatchContext("m1", home, away, "Primeira Liga", metrics)


def run_case(name, ctx, expected):
    orch = AlertOrchestrator(StrategyConfig())
    status, _, msg = orch.process_match(ctx)
    ok = status == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {status.name} (esperado {expected.name})")
    assert ok, f"{name}: {status.name} != {expected.name}"
    return msg


def main():
    # 1. Cenario ideal com edge positivo -> dispara
    run_case("edge positivo", _ctx(_metrics()), AlertStatus.TRIGGERED)

    # 2. Sem odd nenhuma -> nao confirma valor -> espera
    run_case("sem odds", _ctx(_metrics(market_odd_over_05_ht=None, fair_odd_over_05_ht=None)),
             AlertStatus.WAITING)

    # 3. Odd de mercado abaixo da justa (edge negativo) -> espera
    run_case("edge negativo", _ctx(_metrics(market_odd_over_05_ht=1.60, fair_odd_over_05_ht=1.80)),
             AlertStatus.WAITING)

    # 4. Placar 1x0 dentro da janela -> descarta
    run_case("gol saiu", _ctx(_metrics(current_score=(1, 0))), AlertStatus.DISCARDED)

    # 5. Cartao vermelho cedo -> bloqueia
    run_case("vermelho cedo", _ctx(_metrics(red_cards=1, red_card_time=12)), AlertStatus.BLOCKED)

    # 6. Muitas faltas -> bloqueia
    run_case("faltas demais", _ctx(_metrics(fouls=15)), AlertStatus.BLOCKED)

    # 7. Cedo demais (min 8) e 0x0 -> espera
    run_case("cedo demais", _ctx(_metrics(match_time=8)), AlertStatus.WAITING)

    print("\nTodos os cenarios passaram.")


if __name__ == "__main__":
    main()
