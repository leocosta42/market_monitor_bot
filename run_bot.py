import time
import logging

from config import load_settings
from market_monitor_bot import (
    AlertOrchestrator,
    AlertManager,
    SofaScoreProvider,
    TeamStatsRepository,
    DedupStore,
    StrategyConfig,
    AlertStatus,
)
from market_monitor_bot.graphics import generate_market_card

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

POLL_SECONDS = 60


def main():
    logger.info("Iniciando Monitor OVER 0.5 HT (SofaScore)...")

    settings = load_settings()
    strategy = StrategyConfig()

    alert_manager = AlertManager(settings.to_alert_config())
    stats_repo = TeamStatsRepository(settings.team_stats_csv)
    dedup = DedupStore(settings.dedup_db)
    provider = SofaScoreProvider()
    orchestrator = AlertOrchestrator(strategy)

    if stats_repo.is_empty():
        logger.warning(
            "Base de times vazia (%s). Popule o CSV ou nenhum alerta sera gerado.",
            settings.team_stats_csv,
        )

    while True:
        try:
            events = provider.get_live_matches()
            logger.info("Encontrados %s jogos ativos.", len(events))

            # Pre-filtro: so busca estatisticas de candidatos reais (evita ban).
            candidates = [
                e for e in events
                if provider.is_candidate(e, strategy.min_minute, strategy.max_minute)
            ]
            logger.info("%s candidatos dentro da janela.", len(candidates))

            for event in candidates:
                event_id = str(event.get("id"))
                if dedup.already_alerted(event_id):
                    continue

                stats = provider.get_match_statistics(event.get("id"))
                ctx = provider.build_match_context(event, stats, stats_repo)
                if ctx is None:
                    continue

                status, _, alert_msg = orchestrator.process_match(ctx)
                logger.info(
                    "%s vs %s | %s' | %s",
                    ctx.home_team.team_name, ctx.away_team.team_name,
                    ctx.live_metrics.match_time, status.name,
                )

                if status == AlertStatus.TRIGGERED and alert_msg:
                    try:
                        photo_bytes = generate_market_card(ctx)
                        resp = alert_manager.send_alert_with_photo(photo_bytes, alert_msg)
                    except Exception as img_err:
                        logger.error("Erro gerando imagem, enviando só texto: %s", img_err)
                        resp = alert_manager.send_alert(alert_msg)

                    if resp.get("success"):
                        dedup.mark(event_id)
                        logger.info("✅ Alerta enviado para %s.", event_id)
                    else:
                        logger.error("❌ Falha ao enviar alerta para %s.", event_id)

            dedup.cleanup()
            logger.info("Ciclo completo. Aguardando %ss...\n", POLL_SECONDS)
            time.sleep(POLL_SECONDS)

        except Exception as e:
            logger.error("Erro no loop principal: %s", e)
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
