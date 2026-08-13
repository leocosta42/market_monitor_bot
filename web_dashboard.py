import time
import threading
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from market_monitor_bot import (
    AlertOrchestrator, 
    AlertManager, 
    AlertConfig, 
    HybridProvider,
    AlertStatus
)

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Monitor Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Estado Global
global_state: Dict[str, Any] = {
    "live_matches": [],
    "total_alerts": 0,
    "last_update": "Aguardando...",
}

alerts_sent = {}

def bot_loop():
    logger.info("Iniciando Monitoramento Híbrido (SofaScore + SokkerPRO)...")
    
    config = AlertConfig() # Coloque seus tokens aqui se quiser alertas reais
    alert_manager = AlertManager(config)
    provider = HybridProvider()
    orchestrator = AlertOrchestrator()
    
    while True:
        try:
            logger.info("Buscando partidas ao vivo (Hybrid)...")
            matches = provider.get_enriched_matches()
            
            current_matches_data = []
            
            for match_context in matches:
                event_id = match_context.match_id
                
                status, report, alert_msg = orchestrator.process_match(match_context)
                
                if status == AlertStatus.TRIGGERED and event_id not in alerts_sent:
                    alert_manager.send_alert(alert_msg)
                    alerts_sent[event_id] = True
                    global_state["total_alerts"] += 1
                    
                # Prepara dados visuais pro dashboard
                metrics = match_context.live_metrics
                attacks_per_min = metrics.dangerous_attacks / max(metrics.match_time, 1)
                
                # xG total
                xg_total = None
                if metrics.xg_home is not None and metrics.xg_away is not None:
                    xg_total = round(metrics.xg_home + metrics.xg_away, 2)
                
                current_matches_data.append({
                    "id": event_id,
                    "home": match_context.home_team.team_name,
                    "away": match_context.away_team.team_name,
                    "competition": match_context.competition,
                    "time": metrics.match_time,
                    "score": f"{metrics.current_score[0]} - {metrics.current_score[1]}",
                    "attacks": metrics.dangerous_attacks,
                    "apm": round(attacks_per_min, 2),
                    "shots_on_target": metrics.shots_on_target,
                    "corners": metrics.corners,
                    "xg_home": metrics.xg_home,
                    "xg_away": metrics.xg_away,
                    "xg_total": xg_total,
                    "pressure_home": metrics.pressure_home,
                    "pressure_away": metrics.pressure_away,
                    "fair_odd": metrics.fair_odd_over_05_ht,
                    "odd": metrics.current_odd_over_05_ht,
                    "data_source": metrics.data_source,
                    "status": status.name,
                    "triggered": event_id in alerts_sent
                })
            
            # Atualiza o estado global para a API ler
            global_state["live_matches"] = current_matches_data
            global_state["last_update"] = time.strftime("%H:%M:%S")
            
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(30)

@app.on_event("startup")
def startup_event():
    # Inicia o loop em uma thread separada para não travar a web
    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/state")
def get_state():
    return global_state
