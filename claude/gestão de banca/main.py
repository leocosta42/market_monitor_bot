"""
🏆 SISTEMA COMPLETO DE GESTÃO DE BANCA + ANÁLISE
Exemplo de uso integrado para Antigravity
"""

from models.betting_models import (
    ConfiguracaoBanca, AnalisePreJogo, Aposta, Recomendacao,
    TipoMercado, ResultadoAposta, NivelConfianca
)
from core.bankroll_manager import BankrollManager
from core.risk_manager import RiskManager
from core.analytics_dashboard import AnalyticsDashboard
from services.pre_game_integration import IntegracaoAnalisePreJogo
from services.alert_manager import AlertManager
from services.data_persistence import DataPersistence
from datetime import datetime
import json


class SistemaGestiaoBanca:
    """
    Sistema completo de gestão de banca + análise de apostas
    Pronto para integração com Antigravity
    """
    
    def __init__(self, banca_inicial: float = 1000.0):
        """
        Inicializa o sistema
        
        Args:
            banca_inicial: Valor inicial da banca em R$
        """
        print(f"🎯 Inicializando Sistema de Gestão de Banca...")
        print(f"   Banca Inicial: R$ {banca_inicial:.2f}\n")
        
        # Configuração
        self.config = ConfiguracaoBanca(
            banca_inicial=banca_inicial,
            risco_maximo_aposta=0.02,      # 2% por aposta
            risco_maximo_dia=0.05,         # 5% por dia
            stop_loss_percentual=0.10,     # -10% stop loss
            profit_target_percentual=0.20, # +20% profit target
            max_perdas_consecutivas=5,
            max_apostas_dia=10,
            usar_kelly_fraction=0.25       # Kelly 1/4 (seguro)
        )
        
        # Componentes
        self.bankroll = BankrollManager(self.config)
        self.risk = RiskManager(self.config, self.bankroll)
        self.dashboard = AnalyticsDashboard(self.bankroll, self.risk)
        self.integracao = IntegracaoAnalisePreJogo(self.bankroll, self.risk)
        self.alertas = AlertManager()
        self.persistence = DataPersistence()
        
        print("✅ Sistema inicializado com sucesso!\n")
    
    # ========================================================================
    # FLUXO PRINCIPAL: PRÉ-JOGO
    # ========================================================================
    
    def analisar_pre_jogo(
        self,
        time_home: str,
        time_away: str,
        prob_over_25: float,
        prob_over_05_ht: float,
        score: float,
        mercado: str = "over_0.5_ht",
        odds_esperada: float = 1.75
    ) -> dict:
        """
        Executa fluxo pré-jogo:
        1. Recebe análise pré-jogo
        2. Gera recomendação com stake calculado
        3. Emite alerta
        4. Retorna para interface Antigravity
        
        Args:
            time_home: Time da casa
            time_away: Time visitante
            prob_over_25: Probabilidade Over 2.5
            prob_over_05_ht: Probabilidade Over 0.5 HT
            score: Score da análise (0-100)
            mercado: Tipo de mercado
            odds_esperada: Odds esperada
        
        Returns:
            Dict com recomendação completa
        """
        print(f"\n📊 ANÁLISE PRÉ-JOGO: {time_home} vs {time_away}")
        print("="*60)
        
        # Simula análise pré-jogo
        analise = AnalisePreJogo(
            partida_id=f"{time_home}_{time_away}_{datetime.now().timestamp()}",
            time_home=time_home,
            time_away=time_away,
            competicao="Campeonato",
            probabilidade_over_25=prob_over_25,
            probabilidade_over_15=(prob_over_25 + 0.15),
            probabilidade_over_05_ht=prob_over_05_ht,
            score_final=score,
            nivel_confianca=NivelConfianca.ALTO,
            recomendacao="Análise completa realizada"
        )
        
        print(f"Odds: @{odds_esperada}")
        print(f"Sua Probabilidade: {prob_over_05_ht*100:.1f}%")
        print(f"Score Análise: {score:.1f}/100")
        
        # Gera recomendação
        recomendacao = self.integracao.gerar_recomendacao(
            analise,
            TipoMercado(mercado),
            odds_esperada
        )
        
        # Emite alerta
        if recomendacao.pode_apostar:
            self.alertas.alerta_recomendacao(recomendacao)
        
        # Retorna dados para Antigravity
        return {
            'partida': f"{time_home} vs {time_away}",
            'pode_apostar': recomendacao.pode_apostar,
            'stake_recomendado': recomendacao.stake_recomendado,
            'odds': odds_esperada,
            'ev': f"{recomendacao.expected_value*100:.1f}%",
            'confianca': recomendacao.confianca.name,
            'motivo': recomendacao.motivo_recomendacao,
            'alertas': recomendacao.alertas
        }
    
    # ========================================================================
    # FLUXO: REGISTRAR APOSTA
    # ========================================================================
    
    def registrar_aposta_realizada(
        self,
        partida: str,
        mercado: str,
        odds_realizada: float,
        stake: float
    ) -> dict:
        """
        Registra aposta que foi realizada
        
        Args:
            partida: Nome da partida
            mercado: Tipo de mercado
            odds_realizada: Odds final
            stake: Valor apostado
        
        Returns:
            Dict com confirmação
        """
        print(f"\n💰 APOSTA REGISTRADA")
        print("="*60)
        print(f"Partida: {partida}")
        print(f"Mercado: {mercado}")
        print(f"Odds: @{odds_realizada}")
        print(f"Stake: R$ {stake:.2f}")
        
        # Criar aposta
        aposta = Aposta(
            aposta_id=f"aposta_{datetime.now().timestamp()}",
            usuario_id="usuario_antigravity",
            data_aposta=datetime.now(),
            partida_id=partida,
            time_home=partida.split(" vs ")[0],
            time_away=partida.split(" vs ")[1] if " vs " in partida else "",
            competicao="Campeonato",
            mercado=TipoMercado(mercado),
            odds=odds_realizada,
            stake=stake,
            probabilidade_sua=0.70,
            expected_value=0.06,
            confianca=NivelConfianca.ALTO,
            recomendacao_sistema="Registrada via Antigravity"
        )
        
        # Registra
        self.bankroll.registrar_aposta(aposta)
        
        print(f"✅ Aposta ID: {aposta.aposta_id}")
        
        return {
            'aposta_id': aposta.aposta_id,
            'status': 'registrada',
            'banca_atual': self.bankroll.banca_atual
        }
    
    # ========================================================================
    # FLUXO: REGISTRAR RESULTADO
    # ========================================================================
    
    def registrar_resultado(
        self,
        aposta_id: str,
        resultado: str,
        lucro_prejuizo: float
    ) -> dict:
        """
        Registra resultado de aposta
        
        Args:
            aposta_id: ID da aposta
            resultado: 'vencida' ou 'perdida'
            lucro_prejuizo: Valor ganho/perdido
        
        Returns:
            Dict com resultado
        """
        print(f"\n🏁 RESULTADO DA APOSTA")
        print("="*60)
        print(f"Aposta ID: {aposta_id}")
        print(f"Resultado: {resultado.upper()}")
        print(f"Lucro/Perda: R$ {lucro_prejuizo:+.2f}")
        
        # Registra resultado
        res = ResultadoAposta(resultado)
        self.bankroll.registrar_resultado(aposta_id, res, lucro_prejuizo)
        
        # Verifica limites
        limites = self.risk.verificar_todos_limites()
        
        if limites['stop_loss']:
            self.alertas.alerta_limite_atingido('stop_loss', {'percentual': -10})
        
        if limites['profit_target']:
            self.alertas.alerta_limite_atingido('profit_target', {'percentual': 20})
        
        # Emite alerta do resultado
        aposta = [a for a in self.bankroll.historico_apostas if a.aposta_id == aposta_id][0]
        self.alertas.alerta_resultado(aposta, resultado.upper())
        
        stats = self.bankroll.calcular_estatisticas()
        
        return {
            'status': 'resultado_registrado',
            'banca_atual': self.bankroll.banca_atual,
            'lucro_total': self.bankroll.get_lucro_total(),
            'win_rate': f"{stats.win_rate*100:.1f}%",
            'roi': f"{stats.roi*100:.1f}%"
        }
    
    # ========================================================================
    # PAINEL: RESUMO
    # ========================================================================
    
    def get_painel_resumo(self) -> dict:
        """
        Retorna dados para painel resumido do dashboard
        
        Returns:
            Dict com resumo executivo
        """
        resumo = self.dashboard.gerar_resumo_executivo()
        stats = self.bankroll.calcular_estatisticas()
        
        return {
            'resumo': resumo,
            'alertas': self.alertas.get_historico_alertas(quantidade=5),
            'ultimas_apostas': self.dashboard.gerar_tabela_apostas(5)
        }
    
    # ========================================================================
    # PAINEL: ANÁLISE DE RISCO
    # ========================================================================
    
    def get_painel_risco(self) -> dict:
        """
        Retorna dados para painel de análise de risco
        
        Returns:
            Dict com análise completa de risco
        """
        return self.dashboard.gerar_card_risco()
    
    # ========================================================================
    # PAINEL: GRÁFICOS
    # ========================================================================
    
    def get_graficos(self) -> dict:
        """
        Retorna dados para renderizar gráficos
        
        Returns:
            Dict com dados de gráficos
        """
        return {
            'evolucao_banca': self.dashboard.gerar_evolucao_banca(30),
            'distribuicao_win_loss': self.dashboard.gerar_distribuicao_win_loss(),
            'desempenho_por_dia': self.dashboard.gerar_desempenho_por_dia(30)
        }
    
    # ========================================================================
    # PAINEL: COMPLETO
    # ========================================================================
    
    def get_dashboard_completo(self) -> dict:
        """
        Retorna TODOS os dados do dashboard
        
        Returns:
            Dict com dashboard completo pronto para Antigravity
        """
        return self.dashboard.gerar_dashboard_completo()
    
    # ========================================================================
    # PERSISTÊNCIA
    # ========================================================================
    
    def salvar_dados(self) -> bool:
        """Salva todos os dados"""
        config_dict = {
            'banca_inicial': self.config.banca_inicial,
            'risco_maximo_aposta': self.config.risco_maximo_aposta,
            'risco_maximo_dia': self.config.risco_maximo_dia,
            'stop_loss_percentual': self.config.stop_loss_percentual,
            'profit_target_percentual': self.config.profit_target_percentual,
            'max_perdas_consecutivas': self.config.max_perdas_consecutivas,
            'max_apostas_dia': self.config.max_apostas_dia,
            'usar_kelly_fraction': self.config.usar_kelly_fraction,
            'moeda': self.config.moeda
        }
        
        self.persistence.salvar_configuracao(self.config)
        self.persistence.salvar_apostas(self.bankroll.historico_apostas)
        self.persistence.salvar_snapshots(self.bankroll.snapshots_banca)
        
        print("✅ Dados salvos com sucesso!")
        return True
    
    def exportar_backup(self) -> str:
        """Exporta backup completo"""
        self.persistence.exportar_tudo()
        return "Backup criado com sucesso!"


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def exemplo_uso_completo():
    """Demonstra fluxo completo do sistema"""
    
    # Inicializa sistema
    sistema = SistemaGestiaoBanca(banca_inicial=1000.0)
    
    # Simula análise pré-jogo
    print("\n" + "="*80)
    print("PASSO 1: ANÁLISE PRÉ-JOGO")
    print("="*80)
    
    recom1 = sistema.analisar_pre_jogo(
        time_home="Porto",
        time_away="Benfica",
        prob_over_25=0.65,
        prob_over_05_ht=0.70,
        score=68,
        mercado="over_0.5_ht",
        odds_esperada=1.75
    )
    
    print(f"\n📋 Recomendação:")
    print(json.dumps(recom1, indent=2, ensure_ascii=False))
    
    # Registra aposta (se recomendação for boa)
    if recom1['pode_apostar']:
        print("\n" + "="*80)
        print("PASSO 2: REGISTRAR APOSTA")
        print("="*80)
        
        aposta_result = sistema.registrar_aposta_realizada(
            partida="Porto vs Benfica",
            mercado="over_0.5_ht",
            odds_realizada=1.75,
            stake=100.0
        )
        
        aposta_id = aposta_result['aposta_id']
        
        # Registra resultado
        print("\n" + "="*80)
        print("PASSO 3: REGISTRAR RESULTADO")
        print("="*80)
        
        resultado = sistema.registrar_resultado(
            aposta_id=aposta_id,
            resultado="vencida",
            lucro_prejuizo=87.50
        )
        
        print(f"\n✅ Resultado:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Mostra dashboard
    print("\n" + "="*80)
    print("DASHBOARD RESUMIDO")
    print("="*80)
    
    painel = sistema.get_painel_resumo()
    print(json.dumps(painel['resumo'], indent=2, ensure_ascii=False))
    
    # Salva dados
    print("\n" + "="*80)
    print("SALVANDO DADOS")
    print("="*80)
    
    sistema.salvar_dados()


if __name__ == "__main__":
    exemplo_uso_completo()
