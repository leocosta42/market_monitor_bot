"""
🏆 ANÁLISE PRÉ-JOGO: SISTEMA EXPERT DE AVALIAÇÃO DE OVER
Como os profissionais avaliam Over antes do jogo começar
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Nível de confiança na previsão"""
    MUITO_BAIXO = 0  # < 45%
    BAIXO = 1        # 45-55%
    MÉDIO = 2        # 55-65%
    ALTO = 3         # 65-75%
    MUITO_ALTO = 4   # > 75%


@dataclass
class HistoricoTime:
    """Histórico estatístico de um time"""
    nome: str
    
    # Últimos 10 jogos
    gols_marcados_10: float          # Média
    gols_sofridos_10: float          # Média
    over_25_historico_10: float      # Porcentagem (0-1)
    over_15_historico_10: float
    over_05_ht_historico_10: float
    
    # Últimos 5 jogos (forma atual)
    gols_marcados_5: float
    gols_sofridos_5: float
    over_25_historico_5: float
    
    # Padrão de gols
    gols_1tempo_media: float         # Média de gols no 1º tempo
    gols_2tempo_media: float
    
    # Qualidade
    atacante_principal_gols_10: int  # Gols do melhor atacante
    defesa_force: float              # 0-10 (10 = excelente)
    
    # Xis
    lesionados: List[str]            # Lista de lesionados
    suspensos: List[str]
    posse_media: float               # Porcentagem
    escanteios_media: float
    
    # Contexto
    posicao_tabela: int              # 1º, 2º, 3º, etc
    motivacao: str                   # "alta", "média", "baixa"
    joga_em_casa: bool
    xg_media_ataque: float           # Expected Goals ofensivo
    xg_media_defesa: float           # Expected Goals sofrido


@dataclass
class ConfrontoDirecto:
    """Histórico de confrontos H2H"""
    time_a: str
    time_b: str
    ultimos_5_placar: List[Tuple[int, int]]  # [(2,1), (1,0), ...]
    
    def calcular_media_gols(self) -> float:
        """Calcula média de gols nos confrontos"""
        total_gols = sum(g1 + g2 for g1, g2 in self.ultimos_5_placar)
        return total_gols / len(self.ultimos_5_placar) if self.ultimos_5_placar else 0
    
    def calcular_over_25_taxa(self) -> float:
        """Calcula porcentagem de Over 2.5 nos H2H"""
        over = sum(1 for g1, g2 in self.ultimos_5_placar if g1 + g2 >= 3)
        return over / len(self.ultimos_5_placar) if self.ultimos_5_placar else 0


@dataclass
class ContextoJogo:
    """Contexto do jogo específico"""
    time_casa: str
    time_fora: str
    competicao: str
    rodada: int
    
    # Condições
    clima: str                       # "chuva", "nublado", "sol"
    campo: str                       # "perfeito", "molhado", "seco"
    altitude: int                    # em metros
    hora_jogo: int                   # 14:00, 19:00, etc
    
    # Arbitro
    nome_arbitro: str
    cartoes_amarelos_media: float
    
    # Contexto emocional
    time_casa_em_pressao: bool       # Precisa vencer
    time_fora_em_pressao: bool
    descanso_casa_dias: int          # Dias desde último jogo
    descanso_fora_dias: int


class AnalisadorPreJogo:
    """Sistema completo de análise pré-jogo como um expert"""
    
    def __init__(self):
        self.scores = {}  # Armazena scores de cada análise
        self.avisos = []  # Alertas importantes
    
    # ========================================================================
    # 1. ANÁLISE DE HISTÓRICO
    # ========================================================================
    
    def analisar_historico_10(self, time_home: HistoricoTime, time_away: HistoricoTime) -> Dict:
        """Analisa o histórico dos últimos 10 jogos"""
        
        # Gols esperados
        gols_home = time_home.gols_marcados_10
        gols_away = time_away.gols_marcados_10
        total_gols_esperado = gols_home + gols_away
        
        # Over 2.5 combinado
        probabilidade_over_25 = (time_home.over_25_historico_10 + time_away.over_25_historico_10) / 2
        
        # Over 0.5 HT (crítico para nosso bot!)
        probabilidade_over_05_ht = (time_home.over_05_ht_historico_10 + time_away.over_05_ht_historico_10) / 2
        
        # Score
        score_historico = probabilidade_over_25 * 100
        self.scores['historico_10'] = score_historico
        
        return {
            "gols_esperado_home": gols_home,
            "gols_esperado_away": gols_away,
            "total_gols_esperado": total_gols_esperado,
            "probabilidade_over_25": probabilidade_over_25,
            "probabilidade_over_05_ht": probabilidade_over_05_ht,
            "score": score_historico,
            "nivel_confianca": self._get_nivel_confianca(probabilidade_over_25)
        }
    
    # ========================================================================
    # 2. ANÁLISE DE FORMA ATUAL
    # ========================================================================
    
    def analisar_forma_atual(self, time_home: HistoricoTime, time_away: HistoricoTime) -> Dict:
        """Analisa forma dos últimos 5 jogos (MUITO IMPORTANTE)"""
        
        gols_home_5 = time_home.gols_marcados_5
        gols_away_5 = time_away.gols_marcados_5
        total_esperado_5 = gols_home_5 + gols_away_5
        
        # Comparar com média de 10
        tendencia_home = "📈" if gols_home_5 > time_home.gols_marcados_10 else "📉"
        tendencia_away = "📈" if gols_away_5 > time_away.gols_marcados_10 else "📉"
        
        # Probabilidade Over baseada em forma
        prob_over_forma = min(0.85, total_esperado_5 / 2.5)  # Se marcam 2.5+/jogo = high over
        
        score_forma = prob_over_forma * 100
        self.scores['forma_atual'] = score_forma
        
        return {
            "gols_home_5": gols_home_5,
            "gols_away_5": gols_away_5,
            "total_esperado": total_esperado_5,
            "tendencia_home": tendencia_home,
            "tendencia_away": tendencia_away,
            "probabilidade_over_forma": prob_over_forma,
            "score": score_forma,
            "aviso": "FORMA PIOR QUE NORMAL" if prob_over_forma < 0.55 else None
        }
    
    # ========================================================================
    # 3. ANÁLISE H2H
    # ========================================================================
    
    def analisar_h2h(self, h2h: ConfrontoDirecto) -> Dict:
        """Analisa confrontos diretos"""
        
        media_gols_h2h = h2h.calcular_media_gols()
        taxa_over_25_h2h = h2h.calcular_over_25_taxa()
        
        placar_str = " vs ".join([f"{g1}-{g2}" for g1, g2 in h2h.ultimos_5_placar])
        
        # Score H2H (pode ser diferente do geral!)
        score_h2h = taxa_over_25_h2h * 100
        self.scores['h2h'] = score_h2h
        
        # Aviso se H2H é muito diferente do padrão geral
        if taxa_over_25_h2h < 0.40:
            self.avisos.append("⚠️ AVISO: H2H mostra Over 2.5 em apenas 40% - esses times jogam defensivo um contra o outro!")
        
        return {
            "ultimos_5_placares": placar_str,
            "media_gols_h2h": media_gols_h2h,
            "taxa_over_25_h2h": taxa_over_25_h2h,
            "score": score_h2h,
            "diferenca_vs_historico": "TIMES JOGAM MAIS DEFENSIVO MUTUAMENTE"
        }
    
    # ========================================================================
    # 4. ANÁLISE DE XG (EXPECTED GOALS)
    # ========================================================================
    
    def analisar_xg(self, time_home: HistoricoTime, time_away: HistoricoTime) -> Dict:
        """Analisa Expected Goals (métrica avançada)"""
        
        xg_total_esperado = time_home.xg_media_ataque + time_away.xg_media_ataque
        
        # XG alto = mais chances = mais provável Over
        # Cada 1.0 xG = ~0.75 gols reais (em média)
        gols_reais_esperados = xg_total_esperado * 0.75
        
        score_xg = min(100, (gols_reais_esperados / 2.5) * 100)
        self.scores['xg'] = score_xg
        
        return {
            "xg_home_ataque": time_home.xg_media_ataque,
            "xg_away_ataque": time_away.xg_media_ataque,
            "xg_total": xg_total_esperado,
            "gols_reais_esperados": gols_reais_esperados,
            "score": score_xg,
            "confianca": "MUITO ALTA" if xg_total_esperado > 2.5 else "ALTA" if xg_total_esperado > 2.0 else "MÉDIA"
        }
    
    # ========================================================================
    # 5. ANÁLISE DE LESÕES
    # ========================================================================
    
    def analisar_lesoes(self, time_home: HistoricoTime, time_away: HistoricoTime) -> Dict:
        """Impacto de lesões e suspensões"""
        
        impacto_home = 0  # -1 a +1 (negativo = pior)
        impacto_away = 0
        
        # Cada lesionado importante = -5% na capacidade ofensiva
        if len(time_home.lesionados) > 0:
            impacto_home -= len(time_home.lesionados) * 0.05
            self.avisos.append(f"⚠️ {time_home.nome} tem {len(time_home.lesionados)} lesionado(s): {', '.join(time_home.lesionados)}")
        
        if len(time_away.lesionados) > 0:
            impacto_away -= len(time_away.lesionados) * 0.05
            self.avisos.append(f"⚠️ {time_away.nome} tem {len(time_away.lesionados)} lesionado(s): {', '.join(time_away.lesionados)}")
        
        # Suspensões (mais impacto que lesões no curto prazo)
        if len(time_home.suspensos) > 0:
            impacto_home -= len(time_home.suspensos) * 0.08
        
        if len(time_away.suspensos) > 0:
            impacto_away -= len(time_away.suspensos) * 0.08
        
        score_lesoes = max(0, (1 + impacto_home + impacto_away) / 2 * 100)
        self.scores['lesoes'] = score_lesoes
        
        return {
            "lesionados_home": time_home.lesionados,
            "lesionados_away": time_away.lesionados,
            "impacto_combinado": impacto_home + impacto_away,
            "score": score_lesoes,
            "fator": "PREJUDICIAL" if (impacto_home + impacto_away) < -0.1 else "NEUTRO"
        }
    
    # ========================================================================
    # 6. ANÁLISE DE CONTEXTO
    # ========================================================================
    
    def analisar_contexto(self, contexto: ContextoJogo, time_home: HistoricoTime, time_away: HistoricoTime) -> Dict:
        """Analisa fatores contextuais"""
        
        fatores = []
        impacto_total = 0
        
        # Vantagem de casa
        if contexto.time_casa_em_pressao:
            fatores.append("🔴 Time casa em pressão (pode jogar aberto = Over)")
            impacto_total += 0.05
        
        # Campo
        if contexto.campo == "molhado":
            fatores.append("🌧️ Campo molhado (bola corre mais = mais chances)")
            impacto_total += 0.03
        
        # Clima
        if contexto.clima == "chuva":
            fatores.append("⛈️ Chuva (dificulta defesa = mais gols)")
            impacto_total += 0.02
        
        # Hora do jogo
        if contexto.hora_jogo == 19:  # Noite
            fatores.append("🌙 Noite (times mais criativos)")
            impacto_total += 0.02
        
        # Árbitro rigoroso
        if contexto.cartoes_amarelos_media > 3.0:
            fatores.append("🟨 Árbitro rigoroso (jogo truncado = menos gols)")
            impacto_total -= 0.05
        
        score_contexto = (0.55 + impacto_total) * 100  # Base 55%
        self.scores['contexto'] = score_contexto
        
        return {
            "fatores": fatores,
            "impacto_total": impacto_total,
            "score": score_contexto
        }
    
    # ========================================================================
    # 7. ANÁLISE COMBINADA FINAL
    # ========================================================================
    
    def analise_final(self, 
                     time_home: HistoricoTime,
                     time_away: HistoricoTime,
                     h2h: ConfrontoDirecto,
                     contexto: ContextoJogo) -> Dict:
        """Análise completa como um expert profissional"""
        
        # Rodar todas as análises
        hist_10 = self.analisar_historico_10(time_home, time_away)
        forma = self.analisar_forma_atual(time_home, time_away)
        confronto = self.analisar_h2h(h2h)
        xg_analise = self.analisar_xg(time_home, time_away)
        lesoes_analise = self.analisar_lesoes(time_home, time_away)
        contexto_analise = self.analisar_contexto(contexto, time_home, time_away)
        
        # Combinar scores com pesos
        score_final = (
            hist_10['score'] * 0.25 +          # Histórico = 25%
            forma['score'] * 0.25 +            # Forma atual = 25%
            confronto['score'] * 0.15 +        # H2H = 15%
            xg_analise['score'] * 0.20 +       # XG = 20%
            lesoes_analise['score'] * 0.10 +   # Lesões = 10%
            contexto_analise['score'] * 0.05   # Contexto = 5%
        )
        
        # Over 0.5 HT é mais fácil que Over 2.5
        # Se Over 2.5 tem 65% de chance, Over 0.5 HT tem ~78% de chance
        prob_over_05_ht_estimada = hist_10['probabilidade_over_05_ht']
        
        # Recomendação de aposta
        recomendacao = self._gerar_recomendacao(score_final, prob_over_05_ht_estimada)
        
        return {
            "analises_detalhadas": {
                "historico_10": hist_10,
                "forma_atual": forma,
                "confronto_direto": confronto,
                "expected_goals": xg_analise,
                "lesoes": lesoes_analise,
                "contexto": contexto_analise
            },
            "score_final": score_final,
            "probabilidade_over_25": score_final / 100,
            "probabilidade_over_05_ht": prob_over_05_ht_estimada,
            "nivel_confianca": self._get_nivel_confianca(score_final / 100),
            "recomendacao": recomendacao,
            "avisos": self.avisos
        }
    
    # ========================================================================
    # FUNÇÕES AUXILIARES
    # ========================================================================
    
    def _get_nivel_confianca(self, probabilidade: float) -> ConfidenceLevel:
        """Converte probabilidade em nível de confiança"""
        if probabilidade < 0.45:
            return ConfidenceLevel.MUITO_BAIXO
        elif probabilidade < 0.55:
            return ConfidenceLevel.BAIXO
        elif probabilidade < 0.65:
            return ConfidenceLevel.MÉDIO
        elif probabilidade < 0.75:
            return ConfidenceLevel.ALTO
        else:
            return ConfidenceLevel.MUITO_ALTO
    
    def _gerar_recomendacao(self, score: float, prob_ht: float) -> str:
        """Gera recomendação final"""
        if score < 45:
            return "❌ NÃO APOSTAR - Muito arriscado"
        elif score < 55:
            return "⚠️ EVITAR - Oportunidade fraca"
        elif score < 65:
            return "✅ CONSIDERAR - Aposta aceitável"
        elif score < 75:
            return "✅✅ BOA OPORTUNIDADE - Vale a pena"
        else:
            return "✅✅✅ EXCELENTE - Aposta de alto valor"


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def exemplo_analise_completa():
    """Demonstração de análise completa como um expert"""
    
    print("="*80)
    print("🏆 ANÁLISE PRÉ-JOGO: Porto vs Benfica")
    print("="*80)
    
    # DADOS DO PORTO
    porto = HistoricoTime(
        nome="FC Porto",
        gols_marcados_10=2.3,
        gols_sofridos_10=1.1,
        over_25_historico_10=0.70,
        over_15_historico_10=0.85,
        over_05_ht_historico_10=0.75,
        gols_marcados_5=1.6,  # Queda de forma
        gols_sofridos_5=1.2,
        over_25_historico_5=0.60,
        gols_1tempo_media=1.2,
        gols_2tempo_media=1.1,
        atacante_principal_gols_10=8,
        defesa_force=7.5,
        lesionados=[],
        suspensos=[],
        posse_media=62,
        escanteios_media=4.2,
        posicao_tabela=2,
        motivacao="alta",
        joga_em_casa=True,
        xg_media_ataque=1.72,
        xg_media_defesa=1.2
    )
    
    # DADOS DO BENFICA
    benfica = HistoricoTime(
        nome="SL Benfica",
        gols_marcados_10=1.8,
        gols_sofridos_10=1.4,
        over_25_historico_10=0.60,
        over_15_historico_10=0.75,
        over_05_ht_historico_10=0.65,
        gols_marcados_5=1.2,
        gols_sofridos_5=1.5,
        over_25_historico_5=0.50,
        gols_1tempo_media=0.7,
        gols_2tempo_media=1.1,
        atacante_principal_gols_10=3,
        defesa_force=6.0,
        lesionados=["Lateral Direito"],
        suspensos=[],
        posse_media=48,
        escanteios_media=3.0,
        posicao_tabela=12,
        motivacao="média",
        joga_em_casa=False,
        xg_media_ataque=0.98,
        xg_media_defesa=1.4
    )
    
    # H2H
    h2h = ConfrontoDirecto(
        time_a="Porto",
        time_b="Benfica",
        ultimos_5_placar=[(2, 1), (1, 0), (3, 2), (2, 0), (1, 1)]
    )
    
    # CONTEXTO
    contexto = ContextoJogo(
        time_casa="Porto",
        time_fora="Benfica",
        competicao="Primeira Liga",
        rodada=25,
        clima="nublado",
        campo="molhado",
        altitude=50,
        hora_jogo=19,
        nome_arbitro="João Silva",
        cartoes_amarelos_media=3.2,
        time_casa_em_pressao=True,
        time_fora_em_pressao=True,
        descanso_casa_dias=2,
        descanso_fora_dias=1
    )
    
    # ANÁLISE
    analisador = AnalisadorPreJogo()
    resultado = analisador.analise_final(porto, benfica, h2h, contexto)
    
    # EXIBIR RESULTADO
    print("\n📊 ANÁLISE DETALHADA:\n")
    
    print(f"▶ Histórico (Últimos 10):")
    print(f"  • Over 2.5: {resultado['analises_detalhadas']['historico_10']['probabilidade_over_25']:.0%}")
    print(f"  • Over 0.5 HT: {resultado['analises_detalhadas']['historico_10']['probabilidade_over_05_ht']:.0%}")
    
    print(f"\n▶ Forma Atual (Últimos 5):")
    print(f"  • Porto: {resultado['analises_detalhadas']['forma_atual']['gols_home_5']:.1f} gols/jogo {resultado['analises_detalhadas']['forma_atual']['tendencia_home']}")
    print(f"  • Benfica: {resultado['analises_detalhadas']['forma_atual']['gols_away_5']:.1f} gols/jogo {resultado['analises_detalhadas']['forma_atual']['tendencia_away']}")
    
    print(f"\n▶ Confrontos Diretos (H2H):")
    print(f"  • Média de gols: {resultado['analises_detalhadas']['confronto_direto']['media_gols_h2h']:.1f}")
    print(f"  • Over 2.5 em H2H: {resultado['analises_detalhadas']['confronto_direto']['taxa_over_25_h2h']:.0%}")
    
    print(f"\n▶ Expected Goals (XG):")
    print(f"  • XG Total: {resultado['analises_detalhadas']['expected_goals']['xg_total']:.2f}")
    print(f"  • Gols Reais Esperados: {resultado['analises_detalhadas']['expected_goals']['gols_reais_esperados']:.2f}")
    
    print(f"\n▶ Lesões:")
    print(f"  • Benfica: {', '.join(resultado['analises_detalhadas']['lesoes']['lesionados_away'])}")
    
    print("\n" + "="*80)
    print("🎯 RESULTADO FINAL")
    print("="*80)
    
    print(f"\nScore Over 2.5: {resultado['score_final']:.1f}/100")
    print(f"Probabilidade Over 2.5: {resultado['probabilidade_over_25']:.0%}")
    print(f"Probabilidade Over 0.5 HT: {resultado['probabilidade_over_05_ht']:.0%}")
    print(f"Nível de Confiança: {resultado['nivel_confianca'].name}")
    print(f"\n{resultado['recomendacao']}")
    
    if resultado['avisos']:
        print(f"\n⚠️ AVISOS IMPORTANTES:")
        for aviso in resultado['avisos']:
            print(f"  {aviso}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    exemplo_analise_completa()
