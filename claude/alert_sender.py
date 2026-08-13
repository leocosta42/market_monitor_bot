"""
🚨 ALERT SENDER MODULE
Integração com Telegram e Discord para envio de alertas Over 0.5 HT
"""

import requests
import json
from typing import Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class NotificationChannel(Enum):
    """Canais de notificação suportados"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    BOTH = "both"


@dataclass
class AlertConfig:
    """Configuração de envio de alertas"""
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    channel: NotificationChannel = NotificationChannel.TELEGRAM
    retry_attempts: int = 3
    timeout: int = 10


class TelegramSender:
    """Envia alertas via Telegram Bot API"""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.send_url = f"{self.BASE_URL}{bot_token}/sendMessage"
    
    def send_alert(self, message: str, retry_attempts: int = 3) -> Tuple[bool, str]:
        """
        Envia alerta via Telegram
        
        Args:
            message: Conteúdo do alerta
            retry_attempts: Número de tentativas em caso de falha
        
        Returns:
            (sucesso: bool, resposta: str)
        """
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        for attempt in range(retry_attempts):
            try:
                response = requests.post(
                    self.send_url,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        message_id = data.get("result", {}).get("message_id")
                        return True, f"✅ Alerta enviado com sucesso (ID: {message_id})"
                
                if attempt < retry_attempts - 1:
                    print(f"⚠️ Tentativa {attempt + 1} falhou. Retentando...")
                    continue
                
                return False, f"❌ Erro Telegram (Status: {response.status_code})"
            
            except requests.exceptions.Timeout:
                if attempt < retry_attempts - 1:
                    continue
                return False, "❌ Timeout ao conectar ao Telegram"
            
            except requests.exceptions.RequestException as e:
                if attempt < retry_attempts - 1:
                    continue
                return False, f"❌ Erro de conexão: {str(e)}"
        
        return False, "❌ Falha após múltiplas tentativas"


class DiscordSender:
    """Envia alertas via Discord Webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def _format_embed(self, message: str, match_data: dict) -> dict:
        """
        Formata mensagem em Embed do Discord
        
        Args:
            message: Conteúdo da mensagem
            match_data: Dados da partida para detalhes
        
        Returns:
            Payload de Embed formatado
        """
        lines = message.strip().split('\n')
        
        # Extrai informações principais
        jogo_line = next((l for l in lines if "Jogo:" in l), "")
        competicao_line = next((l for l in lines if "Competição:" in l), "")
        tempo_line = next((l for l in lines if "Tempo:" in l), "")
        
        embed = {
            "title": "🚨 ALERTA DE VALOR: OVER 0.5 HT 🚨",
            "color": 16711680,  # Vermelho
            "fields": [
                {
                    "name": "⚽ Partida",
                    "value": jogo_line.replace("⚽ Jogo: ", ""),
                    "inline": False
                },
                {
                    "name": "🏆 Competição",
                    "value": competicao_line.replace("🏆 Competição: ", ""),
                    "inline": False
                },
                {
                    "name": "⏱ Status",
                    "value": tempo_line.replace("⏱ Tempo: ", ""),
                    "inline": True
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Over 0.5 HT Bot | Trading Esportivo"
            }
        }
        
        return embed
    
    def send_alert(self, message: str, retry_attempts: int = 3) -> Tuple[bool, str]:
        """
        Envia alerta via Discord Webhook
        
        Args:
            message: Conteúdo do alerta
            retry_attempts: Número de tentativas em caso de falha
        
        Returns:
            (sucesso: bool, resposta: str)
        """
        payload = {
            "content": "🚨 **ALERTA DE VALOR DETECTADO** 🚨",
            "embeds": [
                {
                    "title": "OVER 0.5 HT - Primeiro Tempo",
                    "description": message,
                    "color": 16711680,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        for attempt in range(retry_attempts):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code in [200, 204]:
                    return True, "✅ Alerta enviado ao Discord com sucesso"
                
                if attempt < retry_attempts - 1:
                    print(f"⚠️ Tentativa {attempt + 1} falhou. Retentando...")
                    continue
                
                return False, f"❌ Erro Discord (Status: {response.status_code})"
            
            except requests.exceptions.Timeout:
                if attempt < retry_attempts - 1:
                    continue
                return False, "❌ Timeout ao conectar ao Discord"
            
            except requests.exceptions.RequestException as e:
                if attempt < retry_attempts - 1:
                    continue
                return False, f"❌ Erro de conexão: {str(e)}"
        
        return False, "❌ Falha após múltiplas tentativas"


class AlertManager:
    """Gerenciador central de alertas"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.telegram_sender: Optional[TelegramSender] = None
        self.discord_sender: Optional[DiscordSender] = None
        
        # Inicializar senders se credenciais forem fornecidas
        if config.telegram_bot_token and config.telegram_chat_id:
            self.telegram_sender = TelegramSender(
                config.telegram_bot_token,
                config.telegram_chat_id
            )
        
        if config.discord_webhook_url:
            self.discord_sender = DiscordSender(config.discord_webhook_url)
    
    def send_alert(self, alert_message: str) -> dict:
        """
        Envia alerta pelos canais configurados
        
        Args:
            alert_message: Mensagem formatada do alerta
        
        Returns:
            Relatório de envio com status de cada canal
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "message_preview": alert_message[:100] + "...",
            "channels": {}
        }
        
        # Enviar via Telegram
        if self.config.channel in [NotificationChannel.TELEGRAM, NotificationChannel.BOTH]:
            if self.telegram_sender:
                success, response = self.telegram_sender.send_alert(
                    alert_message,
                    self.config.retry_attempts
                )
                report["channels"]["telegram"] = {
                    "sent": success,
                    "response": response
                }
            else:
                report["channels"]["telegram"] = {
                    "sent": False,
                    "response": "❌ Telegram não configurado"
                }
        
        # Enviar via Discord
        if self.config.channel in [NotificationChannel.DISCORD, NotificationChannel.BOTH]:
            if self.discord_sender:
                success, response = self.discord_sender.send_alert(
                    alert_message,
                    self.config.retry_attempts
                )
                report["channels"]["discord"] = {
                    "sent": success,
                    "response": response
                }
            else:
                report["channels"]["discord"] = {
                    "sent": False,
                    "response": "❌ Discord não configurado"
                }
        
        # Verificar sucesso geral
        report["success"] = all(
            channel.get("sent", False) 
            for channel in report["channels"].values()
        )
        
        return report
    
    def send_test_alert(self) -> dict:
        """Envia alerta de teste para validar configuração"""
        test_message = """
🚨 ALERTA DE TESTE: OVER 0.5 HT 🚨

⚽ Jogo: TESTE vs TESTE
🏆 Competição: Sistema de Testes
⏱ Tempo: 22' | Placar: 0x0

📊 Métricas da Partida:
• Odd Atual (+0.5 HT): @1.78
• Finalizações no Gol: 3
• Ataques Perigosos: 22 (1.00/min)
• Escanteios: 3

✅ Este é um alerta de teste para validar a configuração dos canais de notificação.
"""
        return self.send_alert(test_message)


# ============================================================================
# EXEMPLO DE CONFIGURAÇÃO E USO
# ============================================================================

def example_telegram_usage():
    """Exemplo: Envio via Telegram"""
    config = AlertConfig(
        telegram_bot_token="SEU_BOT_TOKEN_AQUI",
        telegram_chat_id="SEU_CHAT_ID_AQUI",
        channel=NotificationChannel.TELEGRAM
    )
    
    manager = AlertManager(config)
    
    # Testar conectividade
    print("🔍 Testando Telegram...")
    test_result = manager.send_test_alert()
    print(json.dumps(test_result, indent=2, ensure_ascii=False))


def example_discord_usage():
    """Exemplo: Envio via Discord"""
    config = AlertConfig(
        discord_webhook_url="https://discord.com/api/webhooks/SEU_WEBHOOK_URL",
        channel=NotificationChannel.DISCORD
    )
    
    manager = AlertManager(config)
    
    # Testar conectividade
    print("🔍 Testando Discord...")
    test_result = manager.send_test_alert()
    print(json.dumps(test_result, indent=2, ensure_ascii=False))


def example_both_channels():
    """Exemplo: Envio para ambos os canais"""
    config = AlertConfig(
        telegram_bot_token="SEU_BOT_TOKEN_AQUI",
        telegram_chat_id="SEU_CHAT_ID_AQUI",
        discord_webhook_url="https://discord.com/api/webhooks/SEU_WEBHOOK_URL",
        channel=NotificationChannel.BOTH
    )
    
    manager = AlertManager(config)
    
    # Testar conectividade
    print("🔍 Testando Telegram e Discord...")
    test_result = manager.send_test_alert()
    print(json.dumps(test_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("=" * 80)
    print("ALERT SENDER - Exemplos de Configuração")
    print("=" * 80)
    print("\n📌 Para usar este módulo, substitua os tokens pelas suas credenciais:")
    print("   - Telegram: Bot Token + Chat ID")
    print("   - Discord: Webhook URL")
