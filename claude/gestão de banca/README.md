# 🏆 SISTEMA PROFISSIONAL DE GESTÃO DE BANCA + ANÁLISE DE APOSTAS

Sistema completo para gerenciar apostas esportivas com análise profissional, cálculo de stakes usando Kelly Criterion, monitoramento de risco e integração com Antigravity.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Uso Rápido](#uso-rápido)
- [API REST](#api-rest)
- [Módulos](#módulos)
- [Integração Antigravity](#integração-antigravity)

---

## 🎯 Visão Geral

### O que faz?

Este sistema implementa **gestão profissional de banca** para apostas esportivas:

```
PRÉ-JOGO (Análise)
    ↓
RECOMENDAÇÃO (Stake calculado com Kelly)
    ↓
REGISTRO (Aposta realizada)
    ↓
AO VIVO (Bot emite alertas)
    ↓
RESULTADO (Registra ganho/perda)
    ↓
DASHBOARD (Análise de desempenho)
```

### Componentes

| Módulo | Função |
|--------|--------|
| **BankrollManager** | Controle de capital, cálculo de stakes, ROI |
| **RiskManager** | Limites de risco, probabilidade de ruína, alertas |
| **AnalyticsDashboard** | Gráficos, tabelas, estatísticas |
| **IntegracaoAnalisePreJogo** | Conecta análise com gestão de banca |
| **AlertManager** | Notificações (Telegram, Discord, Email) |
| **DataPersistence** | Salva/carrega dados (JSON, Firebase) |

---

## 🏗️ Arquitetura

```
antigravity-betting-system/
├── models/
│   └── betting_models.py          # Dataclasses (Aposta, Recomendacao, etc)
├── core/
│   ├── bankroll_manager.py        # Gestão de banca (Kelly, stakes)
│   ├── risk_manager.py            # Verificação de limites e risco
│   └── analytics_dashboard.py     # Gráficos e análises
├── services/
│   ├── pre_game_integration.py    # Conecta análise com banca
│   ├── alert_manager.py           # Alertas (Telegram, Discord)
│   ├── data_persistence.py        # Persistência (JSON, Firebase)
│   └── api_antigravity.py         # API REST para Antigravity
├── main.py                        # Exemplo de uso completo
├── requirements.txt               # Dependências
└── README.md                      # Este arquivo
```

---

## 📦 Instalação

### 1. Clonar/Baixar projeto

```bash
cd antigravity-betting-system
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Testar instalação

```bash
python main.py
```

---

## 🚀 Uso Rápido

### Exemplo 1: Análise Pré-Jogo

```python
from main import SistemaGestiaoBanca

# Inicializa
sistema = SistemaGestiaoBanca(banca_inicial=1000.0)

# Análise pré-jogo
recomendacao = sistema.analisar_pre_jogo(
    time_home="Porto",
    time_away="Benfica",
    prob_over_25=0.65,
    prob_over_05_ht=0.70,
    score=68,
    mercado="over_0.5_ht",
    odds_esperada=1.75
)

print(recomendacao)
# {
#   'partida': 'Porto vs Benfica',
#   'pode_apostar': True,
#   'stake_recomendado': 95.50,
#   'odds': 1.75,
#   'ev': '+6.3%',
#   'confianca': 'ALTO'
# }
```

### Exemplo 2: Registrar Aposta

```python
# Registra aposta que foi realizada
aposta_id = sistema.registrar_aposta_realizada(
    partida="Porto vs Benfica",
    mercado="over_0.5_ht",
    odds_realizada=1.75,
    stake=95.50
)

# Registra resultado (depois do jogo)
sistema.registrar_resultado(
    aposta_id=aposta_id['aposta_id'],
    resultado="vencida",
    lucro_prejuizo=82.75
)
```

### Exemplo 3: Dashboard

```python
# Retorna dashboard completo
dashboard = sistema.get_dashboard_completo()

print(dashboard['resumo'])
# {
#   'banca_atual': 1082.75,
#   'lucro_total': 82.75,
#   'roi_percentual': 8.3,
#   'win_rate': '100%',
#   'total_apostas': 1
# }
```

---

## 🌐 API REST

### Iniciar Servidor

```bash
python -c "from services.api_antigravity import BettingSystemAPI; api = BettingSystemAPI(1000.0); api.run()"
```

Servidor rodando em: `http://localhost:5000`

### Endpoints Principais

#### GET `/api/v1/banca`
Retorna informações da banca atual

```bash
curl http://localhost:5000/api/v1/banca
```

#### POST `/api/v1/aposta`
Registra nova aposta

```bash
curl -X POST http://localhost:5000/api/v1/aposta \
  -H "Content-Type: application/json" \
  -d '{
    "time_home": "Porto",
    "time_away": "Benfica",
    "mercado": "over_0.5_ht",
    "odds": 1.75,
    "stake": 100,
    "probabilidade_sua": 0.70,
    "expected_value": 0.06
  }'
```

#### GET `/api/v1/dashboard`
Retorna dashboard completo

```bash
curl http://localhost:5000/api/v1/dashboard
```

#### GET `/api/v1/risco`
Retorna análise de risco

```bash
curl http://localhost:5000/api/v1/risco
```

---

## 📊 Módulos

### BankrollManager

Gerencia capital e cálculo de stakes.

```python
from core.bankroll_manager import BankrollManager
from models.betting_models import ConfiguracaoBanca

config = ConfiguracaoBanca(banca_inicial=1000)
manager = BankrollManager(config)

# Kelly Criterion
kelly_puro = manager.kelly_criterion(odds=1.75, probabilidade=0.70)
# 0.433 (43.3%)

# Stake recomendado (Kelly 1/4 + ajuste confiança)
stake = manager.calcular_stake_recomendado(
    odds=1.75,
    probabilidade=0.70,
    confianca=NivelConfianca.ALTO
)
# R$ 108.25

# Estatísticas
stats = manager.calcular_estatisticas()
print(f"Win Rate: {stats.win_rate*100:.1f}%")
print(f"ROI: {stats.roi*100:.1f}%")
```

### RiskManager

Verifica limites e emite alertas.

```python
from core.risk_manager import RiskManager

risk = RiskManager(config, manager)

# Verificar limites
limite_diario = risk.verificar_limite_diario()
print(f"Pode apostar hoje? {limite_diario.pode_apostar}")

# Análise completa de risco
analise = risk.analisar_risco_completo()
print(f"Nível de risco: {analise.risco_nivel}")
print(f"Prob. de ruína: {analise.probabilidade_ruina*100:.1f}%")
```

### AnalyticsDashboard

Gera dados para visualização.

```python
from core.analytics_dashboard import AnalyticsDashboard

dashboard = AnalyticsDashboard(manager, risk)

# Gráfico de evolução
evolucao = dashboard.gerar_evolucao_banca(dias=30)

# Tabela de apostas
apostas = dashboard.gerar_tabela_apostas(quantidade=10)

# Desempenho por mercado
por_mercado = dashboard.gerar_desempenho_por_mercado()
```

### AlertManager

Emite notificações.

```python
from services.alert_manager import AlertManager

config_telegram = {
    'token': 'seu_token_aqui',
    'chat_id': 'seu_chat_id_aqui'
}

alertas = AlertManager(config_telegram=config_telegram)

# Alerta de recomendação
alertas.alerta_recomendacao(recomendacao)

# Alerta de limite
alertas.alerta_limite_atingido('stop_loss', {'percentual': -10})

# Alerta de resultado
alertas.alerta_resultado(aposta, 'WIN')
```

---

## 🔗 Integração Antigravity

### 1. Criar Componente em Antigravity

No seu projeto Antigravity, crie um componente Python que chama a API:

```python
import requests

# URL da API (rodando localmente ou em servidor)
API_URL = "http://localhost:5000/api/v1"

def analisar_partida(time_home, time_away, prob, score):
    response = requests.post(
        f"{API_URL}/analise/recomendacao",
        json={
            "time_home": time_home,
            "time_away": time_away,
            "prob_over_05_ht": prob,
            "score": score,
            "odds_estimada": 1.75
        }
    )
    return response.json()

# Usar no componente
resultado = analisar_partida("Porto", "Benfica", 0.70, 68)
```

### 2. Conectar ao Dashboard

No Antigravity, adicione gráficos e tabelas usando dados da API:

```javascript
// Exemplo em JavaScript/React
import React from 'react';

export function Dashboard() {
  const [dados, setDados] = React.useState(null);
  
  React.useEffect(() => {
    fetch('http://localhost:5000/api/v1/dashboard')
      .then(r => r.json())
      .then(data => setDados(data));
  }, []);
  
  if (!dados) return <p>Carregando...</p>;
  
  return (
    <div>
      <h1>Gestão de Banca</h1>
      <p>Banca: R$ {dados.data.resumo.banca_atual}</p>
      <p>ROI: {dados.data.resumo.roi_percentual}%</p>
      {/* Adicionar gráficos, tabelas, etc */}
    </div>
  );
}
```

### 3. Deploy

Para usar em produção:

1. **Local**: Manter API rodando em máquina local
2. **Google Cloud**: Deploy em Cloud Run/Functions
3. **Vercel**: Deploy como API serverless
4. **Firebase**: Usar Firestore para persistência

---

## 🔧 Configuração

Edite `ConfiguracaoBanca` para ajustar risco:

```python
config = ConfiguracaoBanca(
    banca_inicial=1000.0,
    risco_maximo_aposta=0.02,       # 2% por aposta
    risco_maximo_dia=0.05,          # 5% por dia
    stop_loss_percentual=0.10,      # -10% stop loss
    profit_target_percentual=0.20,  # +20% profit target
    max_perdas_consecutivas=5,      # Pausa após 5 perdas
    max_apostas_dia=10,             # Máximo 10 apostas/dia
    usar_kelly_fraction=0.25        # Kelly 1/4 (conservador)
)
```

---

## 📈 Métricas Rastreadas

- **Win Rate**: % de apostas ganhas
- **ROI**: Retorno sobre investimento
- **EV (Expected Value)**: Valor esperado de cada aposta
- **Drawdown**: Maior perda desde o pico
- **Streak**: Sequências de ganhos/perdas
- **Probabilidade de Ruína**: Chance matemática de quebra
- **Kelly Criterion**: Dimensionamento ótimo de stakes

---

## 🚨 Alertas Automáticos

Sistema emite alertas para:

- ✅ Recomendação de aposta boa
- ⚠️ Limite diário atingido
- 🔴 Stop loss (-10%)
- 🟢 Profit target (+20%)
- 🟡 Muitas perdas consecutivas
- 📊 Análise de risco alta

---

## 💾 Persistência

Dados salvos automaticamente em:

- `dados/configuracao.json` - Configurações
- `dados/apostas.json` - Histórico de apostas
- `dados/snapshots.json` - Snapshots da banca
- `dados/backup_TIMESTAMP.json` - Backup completo

Ou em Firebase/Firestore (se configurado).

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### API não responde

Certifique-se de que está rodando:

```bash
python -c "from services.api_antigravity import BettingSystemAPI; api = BettingSystemAPI(); api.run(debug=True)"
```

### Telegram não funciona

Verifique token e chat_id:

```python
config = {
    'token': 'seu_token_do_botfather',
    'chat_id': 'seu_chat_id_do_userinfobot'
}
```

---

## 📚 Referências

- **Kelly Criterion**: Fórmula para dimensionamento ótimo
- **Expected Value**: EV = (P × Odds) - 1
- **Gambler's Ruin**: Probabilidade matemática de quebra
- **Drawdown**: Maior perda percentual desde pico

---

## 📝 Licença

MIT License - Use livremente!

---

## ✉️ Suporte

Para dúvidas ou sugestões, abra uma issue ou entre em contato.

---

**Desenvolvido para traders que querem ser profissionais!** 🏆
