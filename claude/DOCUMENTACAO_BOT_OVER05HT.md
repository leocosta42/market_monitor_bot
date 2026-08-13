# 📊 SISTEMA AUTOMATIZADO DE ALERTAS: OVER 0.5 HT
## Documentação Técnica Completa

**Data:** Agosto 2026  
**Especialidade:** Análise Estatística de Futebol | Trading Esportivo  
**Versão:** 1.0

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Critérios de Validação](#critérios-de-validação)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Exemplos de Uso](#exemplos-de-uso)
6. [Integração com APIs](#integração-com-apis)
7. [Monitoramento e Logs](#monitoramento-e-logs)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### Objetivo
Sistema automatizado para monitorar partidas de futebol em tempo real e emitir alertas de **OVER 0.5 Gols no Primeiro Tempo** quando as seguintes condições forem simultaneamente atendidas:

- ✅ Tempo de jogo entre 15:00 e 28:00 minutos
- ✅ Placar rigorosamente 0x0
- ✅ Odd atual ≥ 1.65 (ideal 1.70-1.85)
- ✅ Todas as métricas operacionais de jogo atendidas
- ✅ Nenhuma exceção bloqueadora ativa

### Fluxo Principal
```
Partida Iniciada
    ↓
Valida Pré-Requisitos Pré-Jogo
    ↓ (Passa)
Aguarda Primeiro Tempo (15-28 min)
    ↓
Valida Métricas Ao Vivo
    ↓ (Todas passam)
Valida Exceções
    ↓ (Nenhuma bloqueadora)
🚨 EMITE ALERTA
    ↓
Envia via Telegram/Discord
```

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

#### 1. **PreGameValidator**
Valida os pré-requisitos históricos das equipes antes da partida.

```python
class PreGameValidator:
    - validate_both_teams(home, away) → bool
    - get_validation_report(home, away) → Dict
```

**Critérios:**
- Média histórica de Over 0.5 HT > 70% (últimos 10 jogos)
- Odd pré-jogo Over 2.5 FT < 1.90

#### 2. **LiveGameValidator**
Monitora e valida métricas em tempo real durante o primeiro tempo.

```python
class LiveGameValidator:
    - validate_time_and_score(metrics) → Dict
    - validate_metrics(metrics) → Dict
```

**Critérios ao Vivo:**
- Tempo: 15:00 - 28:00 minutos
- Placar: 0x0
- Chutes no Gol: ≥ 2
- Chutes Para Fora: ≥ 3
- Ataques Perigosos: > 1.0 por minuto
- Escanteios: ≥ 2
- Odd Over 0.5 HT: ≥ 1.65

#### 3. **ExceptionValidator**
Bloqueia alertas em situações excecionais.

```python
class ExceptionValidator:
    - validate_exceptions(metrics) → Dict
```

**Bloqueadores:**
- Cartão vermelho antes dos 20 minutos
- Total de faltas > 12 (jogo muito truncado)

#### 4. **AlertOrchestrator**
Orquestra toda a lógica de decisão e geração de alertas.

```python
class AlertOrchestrator:
    - should_monitor_match(home, away) → (bool, Dict)
    - evaluate_live_conditions(metrics) → (AlertStatus, Dict)
    - process_match(context) → (AlertStatus, Dict, Optional[str])
```

#### 5. **AlertManager**
Gerencia envio de notificações via múltiplos canais.

```python
class AlertManager:
    - send_alert(alert_message) → Dict
    - send_test_alert() → Dict
```

---

## 📊 Critérios de Validação Detalhados

### FASE 1: Pré-Jogo (Antes da Partida)

#### Critério 1.1: Histórico Over 0.5 HT
```
Ambas as equipes DEVEM ter:
├─ Over 0.5 HT nos últimos 10 jogos ≥ 70%
└─ Over 2.5 FT (odd pré-jogo) < 1.90
```

**Exemplo de Validação:**
```
Time A:
├─ Over 0.5 HT: 75% ✅ (> 70%)
└─ Over 2.5 FT: 1.85 ✅ (< 1.90)

Time B:
├─ Over 0.5 HT: 72% ✅ (> 70%)
└─ Over 2.5 FT: 1.88 ✅ (< 1.90)

Resultado: AMBOS PASSAM ✅ → Monitorar partida
```

---

### FASE 2: Ao Vivo - Janela de Tempo

#### Critério 2.1: Janela Temporal
```
Minuto atual DEVE estar entre 15:00 e 28:00
├─ Antes de 15 minutos: Aguardar
├─ Entre 15-28 minutos: Ativo para alerta
└─ Após 28 minutos: Janela fechada (sem novo alerta no HT)
```

#### Critério 2.2: Placar
```
Placar DEVE ser rigorosamente 0x0
├─ Se houver qualquer gol: Descartar alerta
└─ Placar deve estar exatamente (0, 0)
```

---

### FASE 3: Ao Vivo - Métricas de Jogo

#### Critério 3.1: Finalizações (Shots)
```
Chutes no Gol (On Target):
├─ Mínimo: 2 chutes
└─ Avalia capacidade ofensiva

Chutes Para Fora (Off Target):
├─ Mínimo: 3 chutes
└─ Indica volume de ataques reais
```

#### Critério 3.2: Ataques Perigosos
```
Média de Ataques Perigosos por Minuto:
├─ Mínimo: > 1.0 ataque por minuto
├─ Cálculo: (Total Ataques) / (Minuto Atual)
└─ Exemplo: 22 ataques aos 20 min = 1.1/min ✅
```

**Tabela de Referência:**
```
Minuto | Ataques Mín | Exemplo
-------|-------------|----------
15 min | > 15        | 16 ataques ✅
20 min | > 20        | 22 ataques ✅
25 min | > 25        | 26 ataques ✅
```

#### Critério 3.3: Escanteios
```
Total de Escanteios:
├─ Mínimo: 2 escanteios
└─ Indica pressão tática
```

#### Critério 3.4: Odd (Preço de Mercado)
```
Odd Atual Over 0.5 HT:
├─ Mínimo: 1.65
├─ Ideal: 1.70 - 1.85
└─ Acima de 1.85: Avaliar se mantém outras métricas
```

---

### FASE 4: Validação de Exceções (Bloqueadores)

#### Exceção 4.1: Cartão Vermelho Precoce
```
SE: Cartão Vermelho antes de 20 minutos
ENTÃO: BLOQUEAR ALERTA (jogo desequilibrado)
```

#### Exceção 4.2: Jogo Muito Truncado
```
SE: Total de Faltas > 12
ENTÃO: BLOQUEAR ALERTA (jogo parado, sem fluidez)
```

---

## 💻 Instalação e Configuração

### Pré-requisitos
```bash
Python 3.8+
pip install requests
pip install python-dotenv  # Opcional, para gerenciar credenciais
```

### Instalação Básica
```bash
# Clone ou baixe os arquivos
git clone <repo-url>
cd over05_ht_bot

# Instale dependências
pip install -r requirements.txt
```

### Arquivo requirements.txt
```
requests>=2.28.0
python-dotenv>=0.21.0
```

### Configuração de Credenciais

#### Opção 1: Variáveis de Ambiente (.env)
```bash
# .env
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
DISCORD_WEBHOOK_URL=sua_webhook_url_aqui
```

#### Opção 2: Arquivo de Configuração (config.json)
```json
{
  "telegram": {
    "bot_token": "SEU_BOT_TOKEN",
    "chat_id": "SEU_CHAT_ID"
  },
  "discord": {
    "webhook_url": "https://discord.com/api/webhooks/..."
  },
  "alert_settings": {
    "channel": "both",
    "retry_attempts": 3,
    "timeout": 10
  }
}
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Processar Única Partida
```python
from over05_ht_bot import (
    AlertOrchestrator, MatchContext, TeamStats,
    LiveMatchMetrics, AlertStatus
)

# Dados das equipes
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

# Métricas ao vivo
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

# Contexto completo
context = MatchContext(
    match_id="porto_vs_benfica_20240815",
    home_team=home,
    away_team=away,
    competition="Primeira Liga Portugal",
    live_metrics=metrics
)

# Processar
orchestrator = AlertOrchestrator()
status, report, alert_message = orchestrator.process_match(context)

if status == AlertStatus.TRIGGERED:
    print("✅ ALERTA EMITIDO!")
    print(alert_message)
else:
    print(f"❌ Status: {status.value}")
```

### Exemplo 2: Monitoramento Contínuo
```python
import time
from alert_sender import AlertManager, AlertConfig, NotificationChannel

# Configurar canais
config = AlertConfig(
    telegram_bot_token="SEU_TOKEN",
    telegram_chat_id="SEU_CHAT_ID",
    channel=NotificationChannel.TELEGRAM,
    retry_attempts=3
)

manager = AlertManager(config)
orchestrator = AlertOrchestrator()

# Simulação de monitoramento
def monitor_match(match_context):
    """Monitora uma partida continuamente"""
    while match_context.live_metrics.match_time <= 45:
        # Atualizar métricas do API/Scraper
        status, report, alert_msg = orchestrator.process_match(match_context)
        
        if status == AlertStatus.TRIGGERED and not match_context.alert_sent:
            # Enviar alerta
            send_result = manager.send_alert(alert_msg)
            print(f"Alerta enviado: {send_result}")
            match_context.alert_sent = True
        
        # Atualizar métricas a cada 30 segundos
        time.sleep(30)
        # Buscar dados atualizados do API...

# Usar
monitor_match(context)
```

### Exemplo 3: Enviar Alerta via Telegram
```python
from alert_sender import AlertManager, AlertConfig, NotificationChannel

config = AlertConfig(
    telegram_bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    telegram_chat_id="-1001234567890",
    channel=NotificationChannel.TELEGRAM
)

manager = AlertManager(config)

# Testar conexão
test = manager.send_test_alert()
print(test)
# Output:
# {
#   "success": true,
#   "channels": {
#     "telegram": {
#       "sent": true,
#       "response": "✅ Alerta enviado com sucesso (ID: 12345)"
#     }
#   }
# }
```

### Exemplo 4: Enviar Alerta via Discord
```python
from alert_sender import AlertManager, AlertConfig, NotificationChannel

config = AlertConfig(
    discord_webhook_url="https://discord.com/api/webhooks/...",
    channel=NotificationChannel.DISCORD
)

manager = AlertManager(config)
result = manager.send_test_alert()
print(result)
```

---

## 🔗 Integração com APIs

### Integração com Bet365/Betfair (Scraping)
```python
# Pseudocódigo para integração com provedores de dados
class BetDataProvider:
    def get_live_metrics(self, match_id: str) -> LiveMatchMetrics:
        """Busca métricas ao vivo de um provedor"""
        # Implementar scraping ou API call
        # Retornar LiveMatchMetrics atualizado
        pass

# Usar
provider = BetDataProvider()
metrics = provider.get_live_metrics("match_123")
```

### Integração com Binance API (Odd de Criptomoedas)
```python
# Se usar trading de criptomoedas também
import requests

def get_binance_odds():
    """Busca odds de moedas (integração futura)"""
    url = "https://api.binance.com/api/v3/ticker/price"
    # Implementar
    pass
```

---

## 📊 Monitoramento e Logs

### Estrutura de Logs
```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_alerts.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usar
logger.info(f"Partida monitorada: {match_id}")
logger.warning(f"Alerta bloqueado por exceção: {reason}")
logger.error(f"Erro ao enviar alerta: {error}")
```

### Exemplo de Log Output
```
2024-08-15 22:10:05 - over05_ht_bot - INFO - Partida iniciada: fc_porto_vs_benfica
2024-08-15 22:10:05 - over05_ht_bot - INFO - Validação pré-jogo: PASSOU
2024-08-15 22:32:10 - over05_ht_bot - INFO - Minuto 22' | Métricas ao vivo verificadas
2024-08-15 22:32:10 - over05_ht_bot - INFO - Status: TRIGGERED
2024-08-15 22:32:11 - alert_sender - INFO - Alerta enviado via Telegram (ID: 12345)
```

---

## 🔧 Troubleshooting

### Problema 1: "Telegram não configurado"
**Causa:** Token ou Chat ID faltando
**Solução:**
```bash
# Obter Bot Token
1. Fale com @BotFather no Telegram
2. Crie um novo bot: /newbot
3. Copie o token fornecido

# Obter Chat ID
1. Envie uma mensagem para seu bot
2. Acesse: https://api.telegram.org/botSEU_TOKEN/getUpdates
3. Procure por "chat": {"id": SEU_CHAT_ID}
```

### Problema 2: "Timeout ao conectar ao Telegram"
**Causa:** Conexão lenta ou firewall bloqueando
**Solução:**
```python
# Aumentar timeout
config = AlertConfig(
    telegram_bot_token="...",
    telegram_chat_id="...",
    timeout=20  # Aumentar de 10 para 20 segundos
)
```

### Problema 3: "Alerta não disparando mesmo com métricas corretas"
**Causa Comum:** Exceção está bloqueando
**Debug:**
```python
status, report, alert_msg = orchestrator.process_match(context)

# Verificar exceções
print(report["live"]["exceptions"])
# Se "is_blocked": true, verificar:
# - red_card_blocked
# - fouls_blocked
```

### Problema 4: Discord mostrando erro 401
**Causa:** Webhook URL inválido ou expirado
**Solução:**
1. Gerar novo webhook URL no Discord
2. Verificar permissões do bot na channel
3. Validar URL com teste

---

## 📈 Métricas de Performance

### Taxa de Alerta Esperada
```
Partidas monitoradas: 100
Partidas que passam pré-jogo: 40 (40%)
Partidas com alerta acionado: 8-12 (20-30% das 40)
Taxa de conversão esperada: 70-80%
```

### Valor Esperado (ROI)
```
Odd média: 1.75
Win rate esperada: 75%
ROI: 1.75 × 0.75 = 1.3125 (31.25% de retorno)
```

---

## 📞 Suporte e Contato

Para dúvidas sobre implementação, abra uma issue no repositório.

**Especialista:** Análise Estatística de Futebol | Trading Esportivo  
**Versão:** 1.0  
**Última atualização:** Agosto 2026

---

## ⚖️ Disclaimer

Este sistema é fornecido para fins educacionais e de análise. Trading em apostas esportivas envolve risco. Não há garantias de lucro. Use responsavelmente.

---

**© 2026 Over 0.5 HT Alert Bot | Todos os direitos reservados**
