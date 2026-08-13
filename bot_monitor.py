import time
import logging
from market_monitor_bot import (
    AlertOrchestrator, 
    AlertManager, 
    AlertConfig, 
    SofaScoreProvider,
    AlertStatus
)

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Iniciando Monitor do OVER 0.5 HT Bot...")
    
    # 1. Configurar Alertas
    # Idealmente, puxe isso do .env usando python-dotenv
    config = AlertConfig(
        telegram_bot_token="TEST_TOKEN", # Substitua pelo real
        telegram_chat_id="TEST_ID",
    )
    alert_manager = AlertManager(config)
    
    # 2. Iniciar Provedor e Orquestrador
    provider = SofaScoreProvider()
    orchestrator = AlertOrchestrator()
    
    # Dicionário para guardar jogos que já enviaram alerta
    # Estrutura: { "match_id": True }
    alerts_sent = {}
    
    while True:
        try:
            logger.info("Buscando partidas ao vivo...")
            events = provider.get_live_matches()
            logger.info(f"Encontrados {len(events)} jogos ativos.")
            
            for event in events:
                event_id = str(event.get("id"))
                
                # Se já enviou alerta para esse jogo, pula
                if event_id in alerts_sent:
                    continue
                
                # 3. Buscar Estatísticas apenas se for necessário
                stats = provider.get_match_statistics(event.get("id"))
                
                # 4. Construir o Contexto (Retorna None se não for 1º tempo)
                match_context = provider.build_match_context(event, stats)
                
                if match_context:
                    # 5. Processar a Partida
                    status, report, alert_msg = orchestrator.process_match(match_context)
                    
                    logger.info(f"Jogo: {match_context.home_team.team_name} vs {match_context.away_team.team_name} | Tempo: {match_context.live_metrics.match_time}' | Status: {status.name}")
                    
                    if status == AlertStatus.TRIGGERED:
                        logger.info(f"🚨 ALERTA DISPARADO para {event_id}!")
                        
                        # Tentar enviar via Telegram/Discord
                        send_result = alert_manager.send_alert(alert_msg)
                        
                        if send_result.get("success"):
                            alerts_sent[event_id] = True
                            logger.info("✅ Alerta enviado com sucesso.")
                        else:
                            logger.error("❌ Falha ao enviar alerta.")
                            
            logger.info("Ciclo completo. Aguardando 60 segundos...\n")
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(60) # Aguarda antes de tentar novamente para não bugar

if __name__ == "__main__":
    main()
