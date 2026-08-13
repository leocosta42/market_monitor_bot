# Market Monitor Bot — Over 0.5 HT

Bot que varre jogos ao vivo (SofaScore), enriquece com xG/pressão/odds (SokkerPRO)
e dispara alertas de valor via Telegram/Discord.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edite com seus tokens
# popule data/team_stats.csv com o histórico real dos times
```

## Rodar

```bash
python run_bot.py               # modo CLI (SofaScore)
uvicorn web_dashboard:app --reload   # dashboard + modo híbrido
```

## Testes

```bash
python tests/test_scenarios.py
```

## O que mudou nesta versão

- `requirements.txt` completo (cloudscraper, fastapi, uvicorn, jinja2).
- Configuração real via `.env` (`config.py`) — nada de tokens hardcoded.
- Fim dos dados mock: histórico dos times vem de `data/team_stats.csv`
  (`TeamStatsRepository`). Time sem histórico é ignorado, não forçado a passar.
- Minuto do jogo calculado a partir do timestamp do período.
- Odd de mercado e odd justa separadas + cálculo de **edge** de valor.
- Deduplicação persistente em SQLite (`DedupStore`), sobrevive a reinício.
- Pré-filtro antes de buscar estatísticas (reduz risco de ban por volume).
- Retry com backoff no envio de alertas.
- Thresholds centralizados em `StrategyConfig`.
- FastAPI com `lifespan` e estado global protegido por lock.

## Avisos

- Os endpoints de SofaScore/SokkerPRO não são oficiais; podem mudar ou bloquear
  acesso e o uso pode violar os termos desses serviços. Avalie o risco.
- Aposte com responsabilidade. Este projeto é para fins de estudo/monitoramento.
