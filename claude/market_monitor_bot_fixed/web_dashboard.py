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
                    if alert_manager.send_alert(alert_msg).get("success"):
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
