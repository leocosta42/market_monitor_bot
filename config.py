"""
Carregamento centralizado de configuracao a partir do .env.
Importe `load_settings()` em qualquer runner (bot / dashboard).
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

from market_monitor_bot import AlertConfig, NotificationChannel


@dataclass
class Settings:
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    discord_webhook_url: str | None
    channel: NotificationChannel
    team_stats_csv: str
    dedup_db: str

    def to_alert_config(self) -> AlertConfig:
        return AlertConfig(
            telegram_bot_token=self.telegram_bot_token,
            telegram_chat_id=self.telegram_chat_id,
            discord_webhook_url=self.discord_webhook_url,
            channel=self.channel,
        )


def _parse_channel(raw: str | None) -> NotificationChannel:
    mapping = {
        "telegram": NotificationChannel.TELEGRAM,
        "discord": NotificationChannel.DISCORD,
        "both": NotificationChannel.BOTH,
    }
    return mapping.get((raw or "both").strip().lower(), NotificationChannel.BOTH)


def load_settings() -> Settings:
    load_dotenv()  # le o arquivo .env se existir
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        channel=_parse_channel(os.getenv("NOTIFICATION_CHANNEL")),
        team_stats_csv=os.getenv("TEAM_STATS_CSV", "data/team_stats.csv"),
        dedup_db=os.getenv("DEDUP_DB", "data/alerts.db"),
    )
