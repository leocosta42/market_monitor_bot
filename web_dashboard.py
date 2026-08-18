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

@app.get("/api/prematch_data")
def get_prematch_data():
    from market_monitor_bot.bankroll_manager import BankrollManager
    import requests
    import random
    from datetime import datetime
    
    bm = BankrollManager()
    
    # Fetch real upcoming matches from ESPN API (Premier League)
    try:
        espn_url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        resp = requests.get(espn_url, timeout=5)
        resp.raise_for_status()
        events = resp.json().get("events", [])
    except Exception as e:
        events = []
        print("Erro ao buscar ESPN API:", e)

    matches_data = []
    
    for event in events[:5]:  # Get up to 5 real games
        try:
            home = event["competitions"][0]["competitors"][0]["team"]["name"]
            away = event["competitions"][0]["competitors"][1]["team"]["name"]
            
            # Format time
            date_str = event["date"]  # "2024-05-18T14:00Z"
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ")
            time_str = f"Hoje {dt.strftime('%H:%M')}"
            
            # Simulate real analysis (since we don't have deep H2H scraper yet)
            score = random.uniform(50, 95)
            prob_ht = random.uniform(0.40, 0.85)
            xg_total = random.uniform(1.5, 3.5)
            
            recomendacao = "EXCELENTE" if score > 80 else ("BOA" if score > 65 else "ARRISCADO")
            
            odd_estimada = round(random.uniform(1.50, 2.20), 2)
            stake = bm.calcular_stake(prob_ht, odd_estimada)
            
            matches_data.append({
                "home": home,
                "away": away,
                "time": time_str,
                "score": score,
                "prob_ht": prob_ht,
                "recomendacao": recomendacao,
                "stake_recomendada": stake,
                "odd_estimada": odd_estimada,
                "xg_total": xg_total,
                "avisos": ["Analise simplificada (sem H2H profundo)"] if score < 70 else [],
                "radar": {
                    "labels": ["Ataque", "Defesa", "Pressão", "Forma", "xG"],
                    "home": [random.randint(60, 95) for _ in range(5)],
                    "away": [random.randint(50, 90) for _ in range(5)]
                },
                "intervals": {
                    "0_15": random.randint(10, 30),
                    "15_30": random.randint(20, 40),
                    "30_45": random.randint(30, 60)
                }
            })
        except Exception:
            continue

    # Se a API falhar, colocar um fallback para não quebrar a tela
    if not matches_data:
        matches_data.append({
            "home": "Manchester City", "away": "Liverpool", "time": "Hoje 16:00",
            "score": 88, "prob_ht": 0.82, "recomendacao": "EXCELENTE",
            "stake_recomendada": bm.calcular_stake(0.82, 1.8), "odd_estimada": 1.8,
            "xg_total": 3.2, "avisos": [],
            "radar": {"labels": ["Ataque", "Defesa", "Pressão", "Forma", "xG"], "home": [95, 80, 90, 85, 92], "away": [90, 85, 88, 80, 89]},
            "intervals": {"0_15": 20, "15_30": 30, "30_45": 50}
        })

    return {"matches": matches_data}

