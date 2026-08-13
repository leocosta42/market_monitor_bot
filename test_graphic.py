from market_monitor_bot.models import MatchContext, TeamStats, LiveMatchMetrics
from market_monitor_bot.graphics import generate_market_card
import os

def test_card():
    # Cria dados falsos de uma partida com muuuita pressao para testarmos o visual
    metrics = LiveMatchMetrics(
        match_id="test1234",
        match_time=25,
        current_score=(0, 0),
        shots_on_target=4,
        shots_off_target=5,
        dangerous_attacks=35,
        corners=3,
        fouls=2,
        red_cards=0,
        red_card_time=None,
        market_odd_over_05_ht=1.85,
        xg_home=1.12,
        xg_away=0.30,
        pressure_home=75.0,
        pressure_away=25.0,
        fair_odd_over_05_ht=1.50,
        data_source="hybrid"
    )
    
    home = TeamStats(team_id="t1", team_name="Real Madrid", over_05_ht_hit_rate=80.0, over_25_ft_pre_odd=1.5)
    away = TeamStats(team_id="t2", team_name="Barcelona", over_05_ht_hit_rate=75.0, over_25_ft_pre_odd=1.6)
    
    ctx = MatchContext(
        match_id="test1234",
        home_team=home,
        away_team=away,
        competition="Champions League - Semifinal",
        live_metrics=metrics
    )
    
    # Gera a imagem
    photo_bytes = generate_market_card(ctx)
    
    # Salva no disco para vermos
    with open("test_card.png", "wb") as f:
        f.write(photo_bytes)
        
    print("Sucesso! O arquivo test_card.png foi criado na sua pasta.")

if __name__ == "__main__":
    test_card()
