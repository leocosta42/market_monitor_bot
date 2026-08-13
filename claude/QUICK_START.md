# 🚀 QUICK START - BOT OVER 0.5 HT
## Guia de Início Rápido (5 minutos)

---

## ⚡ 30 Segundos: O Que Faz Este Bot?

```
📍 ENTRADA: Partida de futebol ao vivo
         (Minuto 15-28, Placar 0x0, Odds good)

🔍 ANALISA: 7 critérios + 2 exceções

🚨 SAÍDA: Alerta automático via Telegram/Discord
         "Over 0.5 Gols no 1º Tempo = @1.78"
```

---

## 📦 Instalação (2 minutos)

### 1. Clonar Repositório
```bash
git clone <repo-url>
cd over05_ht_bot
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
# Apenas 1 dependência: requests
```

### 3. Configurar Credenciais

#### Opção A: Variáveis de Ambiente (.env)
```bash
# Criar arquivo .env
TELEGRAM_BOT_TOKEN=sua_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
DISCORD_WEBHOOK_URL=seu_webhook_aqui
```

#### Opção B: Hardcode (rápido para teste)
```python
from alert_sender import AlertManager, AlertConfig

config = AlertConfig(
    telegram_bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    telegram_chat_id="-1001234567890"
)
```

---

## 🎯 Uso Básico (3 minutos)

### Teste Rápido
```python
# Executar teste com exemplo pré-configurado
python over05_ht_bot.py
# Output: Alerta formatado + JSON com análise completa
```

### Testar com Seus Dados
```python
from over05_ht_bot import (
    AlertOrchestrator, MatchContext, TeamStats, LiveMatchMetrics
)

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
if alert_msg:
    print(alert_msg)  # 🚨 ALERTA EMITIDO!
```

---

## 📱 Enviar Alerta (Exemplo Completo)

### Telegram
```python
from alert_sender import AlertManager, AlertConfig, NotificationChannel

# Configurar
config = AlertConfig(
    telegram_bot_token="YOUR_BOT_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID",
    channel=NotificationChannel.TELEGRAM
)

# Criar gerenciador
manager = AlertManager(config)

# Testar (envia alerta de teste)
result = manager.send_test_alert()
print(result)
# Output: {"success": true, "channels": {"telegram": {"sent": true, ...}}}

# Enviar alerta real
alert_msg = """
🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨

⚽ Jogo: FC Porto vs SL Benfica
🏆 Competição: Primeira Liga Portugal
⏱ Tempo: 22' | Placar: 0x0

📊 Métricas da Partida:
• Odd Atual (+0.5 HT): @1.78
• Finalizações no Gol: 3
• Ataques Perigosos: 22 (1.00/min)
• Escanteios: 3

💡 Histórico Pré-Jogo:
• Média HT dos times: 73.5%

⚠️ Gestão recomendada: 1 Unidade / Stake Padrão.
"""

result = manager.send_alert(alert_msg)
print(result)
```

### Discord
```python
config = AlertConfig(
    discord_webhook_url="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    channel=NotificationChannel.DISCORD
)

manager = AlertManager(config)
result = manager.send_alert(alert_msg)
```

---

## 🔍 Testar Todos os Cenários

```bash
# Executa 8 cenários de teste (2 minutos)
python test_scenarios.py
```

**Resultado esperado:** ✅ 8/8 testes passam

---

## 🐛 Troubleshooting Rápido

### Problema: "Telegram não configurado"
```bash
# 1. Obter Bot Token
# Fale com @BotFather no Telegram
# Digite: /newbot
# Copie o token

# 2. Obter Chat ID
# Envie mensagem para seu bot
# Acesse: https://api.telegram.org/bot[TOKEN]/getUpdates
# Copie o valor de "chat": {"id": [CHAT_ID]}
```

### Problema: "ImportError: No module named 'requests'"
```bash
pip install requests
```

### Problema: "Timeout ao conectar"
```python
# Aumentar timeout
config = AlertConfig(
    telegram_bot_token="...",
    telegram_chat_id="...",
    timeout=20  # Aumentado de 10
)
```

---

## 📊 Critérios em 30 segundos

### ✅ Será Emitido Alerta SE:

```
PRÉ-JOGO (Antes do Jogo)
├─ Over 0.5 HT ambos times > 70% ✅
└─ Over 2.5 FT pré-jogo < 1.90 ✅

AO VIVO (15-28 minutos, Placar 0x0)
├─ Chutes no Gol ≥ 2 ✅
├─ Chutes para Fora ≥ 3 ✅
├─ Ataques Perigosos > 1.0/min ✅
├─ Escanteios ≥ 2 ✅
└─ Odd ≥ 1.65 ✅

EXCEÇÕES (Bloqueadores)
├─ Sem cartão vermelho < 20 min ✅
└─ Faltas ≤ 12 ✅
```

### ❌ NÃO Será Emitido Se:

```
🚫 Qualquer pré-requisito falhar
🚫 Fora da janela 15-28 minutos
🚫 Placar ≠ 0x0
🚫 Qualquer métrica insuficiente
🚫 Odd < 1.65
🚫 Cartão vermelho < 20 min
🚫 Faltas > 12
```

---

## 📈 Fluxo de Decisão Visual

```
┌─────────────────────┐
│ Partida Iniciada    │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Pré-Requisitos OK?   │
    │ (70%, Odd < 1.90)    │
    └──────┬───────────────┘
           │
    ┌──NO──┴──SIM──┐
    │             │
    ▼             ▼
  ❌           Aguardar
 Descartar    1º Tempo
              (15-28 min)
              │
              ▼
         ┌────────────────────┐
         │ Todas Métricas OK? │
         │ (Chutes, Ataques)  │
         └────────┬───────────┘
                  │
         ┌────NO──┴──SIM──┐
         │                │
         ▼                ▼
       ❌            ┌─────────────┐
    Aguardar      │ Exceções?   │
                   │ (Vermelho>20)│
                   └─────┬───────┘
                         │
                  ┌─SIM──┴──NÃO──┐
                  │              │
                  ▼              ▼
                 ❌            🚨
              BLOQUEADO      ALERTA!
```

---

## 💡 Dicas Práticas

### 1. Começar Pequeno
```python
# Teste com 1 partida primeiro
# Depois expanda para múltiplas
```

### 2. Usar Logs
```python
import logging
logging.basicConfig(level=logging.INFO)
# Verá cada decisão do bot em tempo real
```

### 3. Monitorar Multisala
```bash
# Rode múltiplas instâncias para múltiplas partidas:
python bot_instance_1.py &  # Porto vs Benfica
python bot_instance_2.py &  # Braga vs Guimaraes
python bot_instance_3.py &  # Sporting vs Estoril
```

### 4. Integrar com Scraper
```python
# Seu código de scraping → LiveMatchMetrics
# bot.process_match(context) → Alerta automático
```

---

## 📞 Próximos Passos

1. **Configurar Credenciais** → 2 min
2. **Rodar Testes** → python test_scenarios.py
3. **Testar com Sua API** → Integrar seu data source
4. **Monitorar Partidas** → Go Live!

---

## 🎓 Documentação Completa

Para detalhes técnicos, arquitetura completa e exemplos avançados:

👉 Leia: `DOCUMENTACAO_BOT_OVER05HT.md`

---

## ⚙️ Stack Técnico

```
Python 3.8+
├─ requests (HTTP)
├─ Telegram Bot API
├─ Discord Webhooks
└─ Estruturas de dados customizadas
```

---

## ✅ Checklist de Setup

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install requests`)
- [ ] Bot Token do Telegram ou Webhook do Discord configurado
- [ ] Arquivo .env ou config.json criado
- [ ] Test Scenarios passando (`python test_scenarios.py`)
- [ ] Pronto para monitorar partidas!

---

## 🚀 Iniciar Monitoramento

```bash
# Terminal 1: Monitor de Partida
python bot_monitor.py

# Terminal 2: Logs em Tempo Real
tail -f bot_alerts.log
```

---

**Criado com ❤️ para Traders Esportivos**  
**Over 0.5 HT Alert Bot v1.0**
