"""
🧪 CENÁRIOS DE TESTE - BOT OVER 0.5 HT
Exemplos reais com diferentes resultados esperados
"""

from over05_ht_bot import (
    AlertOrchestrator, MatchContext, TeamStats,
    LiveMatchMetrics, AlertStatus
)
import json


class TestScenarios:
    """Conjunto completo de cenários para validação do bot"""
    
    @staticmethod
    def scenario_1_alerta_emitido():
        """
        ✅ CENÁRIO 1: Todas as condições atendidas
        Resultado Esperado: ALERTA EMITIDO
        """
        print("\n" + "="*80)
        print("✅ CENÁRIO 1: CONDIÇÕES IDEAIS - ALERTA DEVE SER EMITIDO")
        print("="*80)
        
        home = TeamStats(
            team_id="fc_porto",
            team_name="FC Porto",
            over_05_ht_hit_rate=0.75,  # 75% > 70% ✅
            over_25_ft_pre_odd=1.85     # 1.85 < 1.90 ✅
        )
        
        away = TeamStats(
            team_id="benfica",
            team_name="SL Benfica",
            over_05_ht_hit_rate=0.72,   # 72% > 70% ✅
            over_25_ft_pre_odd=1.88     # 1.88 < 1.90 ✅
        )
        
        metrics = LiveMatchMetrics(
            match_id="scenario_1",
            match_time=22,              # 22' está entre 15-28 ✅
            current_score=(0, 0),       # Placar 0x0 ✅
            shots_on_target=3,          # 3 >= 2 ✅
            shots_off_target=5,         # 5 >= 3 ✅
            dangerous_attacks=22,       # 22/22 = 1.0/min ✅
            corners=3,                  # 3 >= 2 ✅
            fouls=8,                    # 8 <= 12 ✅
            red_cards=0,                # Sem vermelho ✅
            red_card_time=None,
            current_odd_over_05_ht=1.78 # 1.78 >= 1.65 ✅ (ideal)
        )
        
        context = MatchContext(
            match_id="scenario_1",
            home_team=home,
            away_team=away,
            competition="Primeira Liga Portugal",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: TRIGGERED | Recebido: {status.value}")
        
        if alert_msg:
            print("\n📬 ALERTA GERADO:")
            print(alert_msg)
        
        return status == AlertStatus.TRIGGERED


    @staticmethod
    def scenario_2_falha_pre_requisitos():
        """
        ❌ CENÁRIO 2: Time não atinge 70% de Over 0.5 HT
        Resultado Esperado: DESCARTADO (PRÉ-JOGO)
        """
        print("\n" + "="*80)
        print("❌ CENÁRIO 2: FALHA PRÉ-REQUISITOS - NÃO MONITORAR")
        print("="*80)
        
        home = TeamStats(
            team_id="team_a",
            team_name="Time A",
            over_05_ht_hit_rate=0.45,   # 45% < 70% ❌ FALHA
            over_25_ft_pre_odd=1.85
        )
        
        away = TeamStats(
            team_id="team_b",
            team_name="Time B",
            over_05_ht_hit_rate=0.72,
            over_25_ft_pre_odd=1.88
        )
        
        metrics = LiveMatchMetrics(
            match_id="scenario_2",
            match_time=22,
            current_score=(0, 0),
            shots_on_target=5,
            shots_off_target=6,
            dangerous_attacks=25,
            corners=4,
            fouls=6,
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.70
        )
        
        context = MatchContext(
            match_id="scenario_2",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: REJECTED | Recebido: {status.value}")
        print(f"\n📊 Motivo da Rejeição:")
        print(f"  - Time A: Over 0.5 HT = 45% (Mínimo: 70%) ❌")
        
        return status == AlertStatus.REJECTED


    @staticmethod
    def scenario_3_fora_da_janela_de_tempo():
        """
        ❌ CENÁRIO 3: Tempo fora da janela (< 15 minutos)
        Resultado Esperado: AGUARDANDO (PENDING)
        """
        print("\n" + "="*80)
        print("❌ CENÁRIO 3: FORA DA JANELA DE TEMPO - AGUARDAR")
        print("="*80)
        
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
            match_id="scenario_3",
            match_time=8,               # 8' < 15' ❌ FORA DA JANELA
            current_score=(0, 0),
            shots_on_target=2,
            shots_off_target=3,
            dangerous_attacks=10,
            corners=1,
            fouls=3,
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.70
        )
        
        context = MatchContext(
            match_id="scenario_3",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: PENDING | Recebido: {status.value}")
        print(f"\nℹ️ Tempo: {metrics.match_time}' (Janela: 15-28')")
        print(f"⏱️ Ação: Aguardar até os 15 minutos")
        
        return status == AlertStatus.PENDING


    @staticmethod
    def scenario_4_placar_nao_zerado():
        """
        ❌ CENÁRIO 4: Placar não está 0x0 (1x0)
        Resultado Esperado: AGUARDANDO (PENDING)
        """
        print("\n" + "="*80)
        print("❌ CENÁRIO 4: PLACAR NÃO É 0x0 - AGUARDAR")
        print("="*80)
        
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
            match_id="scenario_4",
            match_time=22,
            current_score=(1, 0),       # 1x0 ❌ NÃO É 0x0
            shots_on_target=4,
            shots_off_target=5,
            dangerous_attacks=22,
            corners=3,
            fouls=8,
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.70
        )
        
        context = MatchContext(
            match_id="scenario_4",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: PENDING | Recebido: {status.value}")
        print(f"\n📊 Placar Atual: {metrics.current_score[0]}x{metrics.current_score[1]}")
        print(f"⚽ Critério: Apenas 0x0 dispara alerta")
        
        return status == AlertStatus.PENDING


    @staticmethod
    def scenario_5_metricas_insuficientes():
        """
        ❌ CENÁRIO 5: Chutes no gol insuficientes
        Resultado Esperado: AGUARDANDO (PENDING)
        """
        print("\n" + "="*80)
        print("❌ CENÁRIO 5: MÉTRICAS INSUFICIENTES - AGUARDAR")
        print("="*80)
        
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
            match_id="scenario_5",
            match_time=22,
            current_score=(0, 0),
            shots_on_target=1,          # 1 < 2 ❌ INSUFICIENTE
            shots_off_target=2,         # 2 < 3 ❌ INSUFICIENTE
            dangerous_attacks=15,       # 15/22 = 0.68/min < 1.0 ❌
            corners=1,                  # 1 < 2 ❌
            fouls=8,
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.70
        )
        
        context = MatchContext(
            match_id="scenario_5",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: PENDING | Recebido: {status.value}")
        print(f"\n📊 Análise de Falhas:")
        print(f"  - Chutes no Gol: {metrics.shots_on_target}/2 ❌")
        print(f"  - Chutes para Fora: {metrics.shots_off_target}/3 ❌")
        print(f"  - Ataques/min: {metrics.dangerous_attacks/metrics.match_time:.2f}/1.0 ❌")
        print(f"  - Escanteios: {metrics.corners}/2 ❌")
        
        return status == AlertStatus.PENDING


    @staticmethod
    def scenario_6_odd_muito_baixa():
        """
        ❌ CENÁRIO 6: Odd abaixo do mínimo
        Resultado Esperado: AGUARDANDO (PENDING)
        """
        print("\n" + "="*80)
        print("❌ CENÁRIO 6: ODD ABAIXO DO MÍNIMO - AGUARDAR")
        print("="*80)
        
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
            match_id="scenario_6",
            match_time=22,
            current_score=(0, 0),
            shots_on_target=3,
            shots_off_target=5,
            dangerous_attacks=22,
            corners=3,
            fouls=8,
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.52  # 1.52 < 1.65 ❌ TOO LOW
        )
        
        context = MatchContext(
            match_id="scenario_6",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: PENDING | Recebido: {status.value}")
        print(f"\n💰 Análise de Odd:")
        print(f"  - Odd Atual: {metrics.current_odd_over_05_ht}")
        print(f"  - Mínimo Requerido: 1.65")
        print(f"  - Diferença: {metrics.current_odd_over_05_ht - 1.65:.2f}")
        print(f"  - Ação: Aguardar aumento da odd ou próxima janela")
        
        return status == AlertStatus.PENDING


    @staticmethod
    def scenario_7_cartao_vermelho():
        """
        ❌ CENÁRIO 7: Cartão vermelho antes dos 20 minutos
        Resultado Esperado: BLOQUEADO (BLOCKED)
        """
        print("\n" + "="*80)
        print("🚨 CENÁRIO 7: EXCEÇÃO - CARTÃO VERMELHO")
        print("="*80)
        
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
            match_id="scenario_7",
            match_time=22,
            current_score=(0, 0),
            shots_on_target=3,
            shots_off_target=5,
            dangerous_attacks=22,
            corners=3,
            fouls=8,
            red_cards=1,                # 1 Cartão Vermelho
            red_card_time=12,           # Aos 12 minutos < 20 ❌ BLOQUEADOR
            current_odd_over_05_ht=1.78
        )
        
        context = MatchContext(
            match_id="scenario_7",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: BLOCKED | Recebido: {status.value}")
        print(f"\n⚠️ Motivo de Bloqueio:")
        print(f"  - Cartão Vermelho: Aos {metrics.red_card_time}'")
        print(f"  - Limite: Até 20 minutos")
        print(f"  - Impacto: Jogo desequilibrado, alerta cancelado")
        
        return status == AlertStatus.BLOCKED


    @staticmethod
    def scenario_8_jogo_truncado():
        """
        ❌ CENÁRIO 8: Jogo muito truncado (> 12 faltas)
        Resultado Esperado: BLOQUEADO (BLOCKED)
        """
        print("\n" + "="*80)
        print("🚨 CENÁRIO 8: EXCEÇÃO - JOGO TRUNCADO")
        print("="*80)
        
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
            match_id="scenario_8",
            match_time=22,
            current_score=(0, 0),
            shots_on_target=3,
            shots_off_target=5,
            dangerous_attacks=22,
            corners=3,
            fouls=15,                   # 15 > 12 ❌ BLOQUEADOR
            red_cards=0,
            red_card_time=None,
            current_odd_over_05_ht=1.78
        )
        
        context = MatchContext(
            match_id="scenario_8",
            home_team=home,
            away_team=away,
            competition="Primeira Liga",
            live_metrics=metrics
        )
        
        orchestrator = AlertOrchestrator()
        status, report, alert_msg = orchestrator.process_match(context)
        
        print(f"\n🎯 Status Resultado: {status.value.upper()}")
        print(f"✅ Esperado: BLOCKED | Recebido: {status.value}")
        print(f"\n⚠️ Motivo de Bloqueio:")
        print(f"  - Total de Faltas: {metrics.fouls}")
        print(f"  - Limite Máximo: 12")
        print(f"  - Análise: Jogo muito parado, qualidade comprometida")
        print(f"  - Ação: Alerta bloqueado por excessiva interrupção")
        
        return status == AlertStatus.BLOCKED


def run_all_scenarios():
    """Executa todos os cenários de teste"""
    print("\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "TESTE COMPLETO - BOT OVER 0.5 HT".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    scenarios = [
        ("Condições Ideais", TestScenarios.scenario_1_alerta_emitido),
        ("Falha Pré-Requisitos", TestScenarios.scenario_2_falha_pre_requisitos),
        ("Fora da Janela", TestScenarios.scenario_3_fora_da_janela_de_tempo),
        ("Placar Não Zerado", TestScenarios.scenario_4_placar_nao_zerado),
        ("Métricas Insuficientes", TestScenarios.scenario_5_metricas_insuficientes),
        ("Odd Muito Baixa", TestScenarios.scenario_6_odd_muito_baixa),
        ("Cartão Vermelho", TestScenarios.scenario_7_cartao_vermelho),
        ("Jogo Truncado", TestScenarios.scenario_8_jogo_truncado),
    ]
    
    results = []
    for name, scenario_func in scenarios:
        result = scenario_func()
        results.append((name, result))
    
    # Relatório Final
    print("\n\n" + "="*80)
    print("📊 RELATÓRIO FINAL DE TESTES")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n✅ Testes Passados: {passed}/{total}")
    print(f"❌ Testes Falhados: {total-passed}/{total}\n")
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status} - {name}")
    
    print("\n" + "="*80)
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
    else:
        print(f"⚠️  {total-passed} teste(s) precisam de revisão")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_scenarios()
