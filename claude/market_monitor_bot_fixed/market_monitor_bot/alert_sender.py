import time
import requests
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Callable
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
    backoff_base: float = 1.5  # segundos; cresce exponencialmente


class AlertManager:
    def __init__(self, config: AlertConfig):
        self.config = config

    # ---------- API publica ----------
    def send_alert(self, alert_message: str) -> Dict:
        result = {"success": False, "channels": {}}

        if self.config.channel in (NotificationChannel.TELEGRAM, NotificationChannel.BOTH):
            if self.config.telegram_bot_token and self.config.telegram_chat_id:
                tg = self._with_retry(lambda: self._send_telegram(alert_message))
                result["channels"]["telegram"] = tg
                result["success"] = result["success"] or tg["sent"]
            else:
                logger.warning("Configuracao do Telegram ausente.")
                result["channels"]["telegram"] = {"sent": False, "error": "Missing config"}

        if self.config.channel in (NotificationChannel.DISCORD, NotificationChannel.BOTH):
            if self.config.discord_webhook_url:
                dc = self._with_retry(lambda: self._send_discord(alert_message))
                result["channels"]["discord"] = dc
                result["success"] = result["success"] or dc["sent"]
            else:
                logger.warning("Configuracao do Discord ausente.")
                result["channels"]["discord"] = {"sent": False, "error": "Missing config"}

        return result

    def send_test_alert(self) -> Dict:
        return self.send_alert("🧪 TESTE: Bot Over 0.5 HT conectado com sucesso!")

    # ---------- infra ----------
    def _with_retry(self, fn: Callable[[], Dict]) -> Dict:
        last: Dict = {"sent": False, "error": "no attempt"}
        for attempt in range(1, self.config.retry_attempts + 1):
            last = fn()
            if last.get("sent"):
                return last
            if attempt < self.config.retry_attempts:
                delay = self.config.backoff_base ** attempt
                logger.warning(
                    "Envio falhou (tentativa %s/%s). Retentando em %.1fs...",
                    attempt, self.config.retry_attempts, delay,
                )
                time.sleep(delay)
        return last

    def _send_telegram(self, message: str) -> Dict:
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        # Texto puro (sem parse_mode) evita quebra por caracteres < > & nao escapados.
        payload = {"chat_id": self.config.telegram_chat_id, "text": message}
        try:
            resp = requests.post(url, json=payload, timeout=self.config.timeout)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Alerta Telegram enviado (msg_id=%s)", data.get("result", {}).get("message_id"))
            return {"sent": True, "response": data}
        except Exception as e:
            logger.error("Falha ao enviar Telegram: %s", e)
            return {"sent": False, "error": str(e)}

    def _send_discord(self, message: str) -> Dict:
        try:
            resp = requests.post(
                self.config.discord_webhook_url,
                json={"content": message},
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            logger.info("Alerta Discord enviado.")
            return {"sent": True, "response": "Success"}
        except Exception as e:
            logger.error("Falha ao enviar Discord: %s", e)
            return {"sent": False, "error": str(e)}
