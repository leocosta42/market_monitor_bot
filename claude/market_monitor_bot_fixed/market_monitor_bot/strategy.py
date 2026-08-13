from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """
    Todos os parametros da estrategia Over 0.5 HT em um unico lugar,
    para facilitar ajuste/backtest sem cacar numeros magicos pelo codigo.
    """
    # Pre-jogo
    min_over_05_ht_hit_rate: float = 0.70
    max_over_25_ft_pre_odd: float = 1.90

    # Janela de tempo (minutos)
    min_minute: int = 15
    max_minute: int = 28

    # Metricas ao vivo (soma casa + fora)
    min_shots_on_target: int = 2
    min_shots_off_target: int = 3
    min_attacks_per_min: float = 1.0
    min_corners: int = 2

    # Valor: edge minimo exigido (odd_mercado / odd_justa - 1)
    min_value_edge: float = 0.05  # 5%
    # Piso absoluto de odd de mercado (evita gatilhos em odds baixas demais)
    min_market_odd: float = 1.65

    # Excecoes que bloqueiam o alerta
    red_card_before_minute: int = 20
    max_fouls: int = 12
