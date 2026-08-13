import requests
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    BOTH = "both"

@dataclass
class AlertConfig:
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    channel: NotificationChannel = NotificationChannel.BOTH
    retry_attempts: int = 3
    timeout: int = 10

class AlertManager:
    def __init__(self, config: AlertConfig):
        self.config = config

    def send_alert(self, alert_message: str) -> Dict:
        result = {"success": False, "channels": {}}
        
        if self.config.channel in [NotificationChannel.TELEGRAM, NotificationChannel.BOTH]:
            if self.config.telegram_bot_token and self.config.telegram_chat_id:
                tg_result = self._send_telegram(alert_message)
                result["channels"]["telegram"] = tg_result
                if tg_result["sent"]:
                    result["success"] = True
            else:
                logger.warning("Telegram configuration missing.")
                result["channels"]["telegram"] = {"sent": False, "error": "Missing config"}

        if self.config.channel in [NotificationChannel.DISCORD, NotificationChannel.BOTH]:
            if self.config.discord_webhook_url:
                dc_result = self._send_discord(alert_message)
                result["channels"]["discord"] = dc_result
                if dc_result["sent"]:
                    result["success"] = True
            else:
                logger.warning("Discord configuration missing.")
                result["channels"]["discord"] = {"sent": False, "error": "Missing config"}

        return result

    def send_test_alert(self) -> Dict:
        test_message = "🧪 TESTE: Bot Over 0.5 HT conectado com sucesso!"
        return self.send_alert(test_message)

    def _send_telegram(self, message: str) -> Dict:
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.config.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Telegram alert sent: ID {data.get('result', {}).get('message_id')}")
            return {"sent": True, "response": data}
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return {"sent": False, "error": str(e)}

    def _send_discord(self, message: str) -> Dict:
        payload = {
            "content": message
        }
        
        try:
            response = requests.post(self.config.discord_webhook_url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            logger.info("Discord alert sent successfully.")
            return {"sent": True, "response": "Success"}
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return {"sent": False, "error": str(e)}
