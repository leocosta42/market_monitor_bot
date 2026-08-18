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

@app.get("/banca", response_class=HTMLResponse)
def read_banca(request: Request):
    return templates.TemplateResponse(request=request, name="banca.html")

from pydantic import BaseModel
class ResolveApostaRequest(BaseModel):
    id: int
    status: str

@app.get("/api/banca")
def api_get_banca():
    from market_monitor_bot.bankroll_manager import BankrollManager
    bm = BankrollManager()
    return bm.get_stats()

@app.post("/api/banca/resolver")
def api_resolve_banca(req: ResolveApostaRequest):
    from market_monitor_bot.bankroll_manager import BankrollManager
    bm = BankrollManager()
    success = bm.resolver_aposta(req.id, req.status)
    return {"success": success}

class NovaApostaRequest(BaseModel):
    partida: str
    mercado: str
    odd: float
    stake: float

@app.post("/api/banca/apostar")
def api_nova_aposta(req: NovaApostaRequest):
    from market_monitor_bot.bankroll_manager import BankrollManager
    bm = BankrollManager()
    aposta = bm.registrar_aposta(req.partida, req.mercado, req.odd, req.stake)
    return {"success": True, "aposta": aposta}

# --- Cache para não rodar a analise a cada request (leva ~30s) ---
import threading as _threading
_prematch_cache = {"data": [], "updated_at": None}
_prematch_lock = _threading.Lock()

def _refresh_prematch_cache():
    """Roda em background: busca jogos reais e analisa."""
    try:
        from market_monitor_bot.prematch_fetcher import PrematchFetcher
        from market_monitor_bot.bankroll_manager import BankrollManager
        bm = BankrollManager()
        fetcher = PrematchFetcher()
        matches = fetcher.analyze_todays_matches(max_matches=15)

        for m in matches:
            m["stake_recomendada"] = bm.calcular_stake(m["prob_ht"], 1.75)
            m["odd_estimada"] = 1.75

        with _prematch_lock:
            from datetime import datetime
            _prematch_cache["data"] = matches
            _prematch_cache["updated_at"] = datetime.now().strftime("%H:%M")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Erro ao atualizar cache prematch: %s", e)

@app.get("/api/prematch_data")
def get_prematch_data():
    with _prematch_lock:
        cached = list(_prematch_cache["data"])
        updated = _prematch_cache["updated_at"]

    # Se cache vazio, tenta popular agora (primeira chamada)
    if not cached:
        t = _threading.Thread(target=_refresh_prematch_cache, daemon=True)
        t.start()
        return {"matches": [], "updated_at": None, "loading": True}

    return {"matches": cached, "updated_at": updated, "loading": False}

@app.get("/api/prematch_refresh")
def refresh_prematch():
    """Dispara atualizacao manual do cache (pode levar 30-60s)."""
    t = _threading.Thread(target=_refresh_prematch_cache, daemon=True)
    t.start()
    return {"status": "refreshing"}
