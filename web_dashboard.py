import time
import threading
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import load_settings
from market_monitor_bot import (
    AlertOrchestrator,
    AlertManager,
    HybridProvider,
    TeamStatsRepository,
    DedupStore,
    StrategyConfig,
    AlertStatus,
)
from market_monitor_bot.graphics import generate_market_card

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

POLL_SECONDS = 30

# Estado global protegido por lock (thread do bot escreve, endpoint le).
_state_lock = threading.Lock()
global_state: Dict[str, Any] = {
    "live_matches": [],
    "total_alerts": 0,
    "last_update": "Aguardando...",
}


def bot_loop():
    logger.info("Iniciando Monitoramento Hibrido (SofaScore + SokkerPRO)...")

    settings = load_settings()
    strategy = StrategyConfig()

    alert_manager = AlertManager(settings.to_alert_config())
    stats_repo = TeamStatsRepository(settings.team_stats_csv)
    dedup = DedupStore(settings.dedup_db)
    provider = HybridProvider(stats_repo, strategy.min_minute, strategy.max_minute)
    orchestrator = AlertOrchestrator(strategy)

    while True:
        try:
            matches = provider.get_enriched_matches()
            current = []
            new_alerts = 0

            for ctx in matches:
                event_id = ctx.match_id
                status, _, alert_msg = orchestrator.process_match(ctx)

                if status == AlertStatus.TRIGGERED and not dedup.already_alerted(event_id):
                    try:
                        photo_bytes = generate_market_card(ctx)
                        resp = alert_manager.send_alert_with_photo(photo_bytes, alert_msg)
                    except Exception as img_err:
                        logger.error("Erro gerando imagem, enviando só texto: %s", img_err)
                        resp = alert_manager.send_alert(alert_msg)
                        
                    if resp.get("success"):
                        dedup.mark(event_id)
                        new_alerts += 1

                m = ctx.live_metrics
                apm = m.dangerous_attacks / max(m.match_time, 1)
                xg_total = (
                    round(m.xg_home + m.xg_away, 2)
                    if m.xg_home is not None and m.xg_away is not None
                    else None
                )
                current.append({
                    "id": event_id,
                    "home": ctx.home_team.team_name,
                    "away": ctx.away_team.team_name,
                    "competition": ctx.competition,
                    "time": m.match_time,
                    "score": f"{m.current_score[0]} - {m.current_score[1]}",
                    "attacks": m.dangerous_attacks,
                    "apm": round(apm, 2),
                    "shots_on_target": m.shots_on_target,
                    "corners": m.corners,
                    "xg_home": m.xg_home,
                    "xg_away": m.xg_away,
                    "xg_total": xg_total,
                    "pressure_home": m.pressure_home,
                    "pressure_away": m.pressure_away,
                    "market_odd": m.market_odd_over_05_ht,
                    "fair_odd": m.fair_odd_over_05_ht,
                    "edge": round(m.value_edge, 4) if m.value_edge is not None else None,
                    "data_source": m.data_source,
                    "status": status.name,
                    "triggered": dedup.already_alerted(event_id),
                })

            with _state_lock:
                global_state["live_matches"] = current
                global_state["total_alerts"] += new_alerts
                global_state["last_update"] = time.strftime("%H:%M:%S")

            dedup.cleanup()
            time.sleep(POLL_SECONDS)

        except Exception as e:
            logger.error("Erro no loop principal: %s", e)
            time.sleep(POLL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()
    yield


app = FastAPI(title="Market Monitor Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/state")
def get_state():
    with _state_lock:
        return dict(global_state)

@app.get("/pre-jogo", response_class=HTMLResponse)
def read_prematch(request: Request):
    return templates.TemplateResponse(request=request, name="prematch.html")

@app.get("/api/prematch_data")
def get_prematch_data():
    from market_monitor_bot.prematch import (
        AnalisadorPreJogo, HistoricoTime, ConfrontoDirecto, ContextoJogo
    )
    # Exemplo Mock 1: Porto vs Benfica (Do script original)
    porto = HistoricoTime("FC Porto", 2.3, 1.1, 0.70, 0.85, 0.75, 1.6, 1.2, 0.60, 1.2, 1.1, 8, 7.5, [], [], 62, 4.2, 2, "alta", True, 1.72, 1.2)
    benfica = HistoricoTime("SL Benfica", 1.8, 1.4, 0.60, 0.75, 0.65, 1.2, 1.5, 0.50, 0.7, 1.1, 3, 6.0, ["Lateral Direito"], [], 48, 3.0, 12, "média", False, 0.98, 1.4)
    h2h_1 = ConfrontoDirecto("Porto", "Benfica", [(2, 1), (1, 0), (3, 2), (2, 0), (1, 1)])
    ctx_1 = ContextoJogo("Porto", "Benfica", "Primeira Liga", 25, "nublado", "molhado", 50, 19, "João Silva", 3.2, True, True, 2, 1)
    
    # Exemplo Mock 2: Arsenal vs Chelsea (Mais focado em gols)
    arsenal = HistoricoTime("Arsenal", 2.8, 0.9, 0.80, 0.90, 0.85, 3.0, 1.0, 0.80, 1.5, 1.3, 12, 8.5, [], [], 65, 6.5, 1, "alta", True, 2.1, 0.8)
    chelsea = HistoricoTime("Chelsea", 2.1, 1.5, 0.70, 0.80, 0.60, 2.5, 2.0, 0.80, 1.0, 1.1, 7, 5.5, ["Zagueiro Titular"], [], 55, 4.5, 6, "alta", False, 1.8, 1.6)
    h2h_2 = ConfrontoDirecto("Arsenal", "Chelsea", [(3, 1), (2, 2), (1, 1), (4, 2), (0, 0)])
    ctx_2 = ContextoJogo("Arsenal", "Chelsea", "Premier League", 30, "chuva", "perfeito", 10, 16, "Michael Oliver", 2.5, True, False, 5, 4)

    analisador = AnalisadorPreJogo()
    res1 = analisador.analise_final(porto, benfica, h2h_1, ctx_1)
    res2 = analisador.analise_final(arsenal, chelsea, h2h_2, ctx_2)

    return {
        "matches": [
            {
                "home": "FC Porto", "away": "SL Benfica", "time": "Hoje 19:00",
                "score": res1["score_final"],
                "prob_ht": res1["probabilidade_over_05_ht"],
                "recomendacao": res1["recomendacao"],
                "xg_total": res1["analises_detalhadas"]["expected_goals"]["xg_total"],
                "avisos": res1["avisos"],
                "radar": {
                    "labels": ["Ataque", "Defesa", "Pressão Média", "Forma Recente", "xG Criado"],
                    "home": [85, 75, 80, 60, 82],
                    "away": [70, 60, 65, 50, 68]
                },
                "intervals": {
                    "0_15": 15, "15_30": 25, "30_45": 60
                }
            },
            {
                "home": "Arsenal", "away": "Chelsea", "time": "Hoje 16:00",
                "score": res2["score_final"],
                "prob_ht": res2["probabilidade_over_05_ht"],
                "recomendacao": res2["recomendacao"],
                "xg_total": res2["analises_detalhadas"]["expected_goals"]["xg_total"],
                "avisos": res2["avisos"],
                "radar": {
                    "labels": ["Ataque", "Defesa", "Pressão Média", "Forma Recente", "xG Criado"],
                    "home": [90, 85, 88, 95, 92],
                    "away": [75, 55, 60, 70, 72]
                },
                "intervals": {
                    "0_15": 30, "15_30": 35, "30_45": 35
                }
            }
        ]
    }

