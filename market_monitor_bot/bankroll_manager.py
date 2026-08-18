import json
import os
from datetime import datetime
from pymongo import MongoClient

BANKROLL_FILE = "data/bankroll.json"
MONGO_URI = os.getenv("MONGODB_URI")

class BankrollManager:
    def __init__(self):
        self.is_cloud = bool(MONGO_URI)
        if self.is_cloud:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client.market_monitor
            self.collection = self.db.bankroll
            self.ensure_cloud_db()
        else:
            self.ensure_local_db()
        
    def ensure_cloud_db(self):
        doc = self.collection.find_one({"_id": "main_bankroll"})
        if not doc:
            default_data = {
                "_id": "main_bankroll",
                "banca_inicial": 1000.0,
                "banca_atual": 1000.0,
                "risco_por_aposta_max": 0.02,
                "apostas": []
            }
            self.collection.insert_one(default_data)

    def ensure_local_db(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(BANKROLL_FILE):
            default_data = {
                "banca_inicial": 1000.0,
                "banca_atual": 1000.0,
                "risco_por_aposta_max": 0.02,
                "apostas": []
            }
            with open(BANKROLL_FILE, 'w') as f:
                json.dump(default_data, f, indent=4)
                
    def load_data(self):
        if self.is_cloud:
            return self.collection.find_one({"_id": "main_bankroll"})
        else:
            with open(BANKROLL_FILE, 'r') as f:
                return json.load(f)
            
    def save_data(self, data):
        if self.is_cloud:
            self.collection.replace_one({"_id": "main_bankroll"}, data)
        else:
            with open(BANKROLL_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            
    def get_stats(self):
        data = self.load_data()
        apostas = data.get("apostas", [])
        
        wins = len([a for a in apostas if a.get("status") == "vencida"])
        losses = len([a for a in apostas if a.get("status") == "perdida"])
        total_finalizadas = wins + losses
        
        win_rate = (wins / total_finalizadas * 100) if total_finalizadas > 0 else 0
        lucro_total = data["banca_atual"] - data["banca_inicial"]
        roi = (lucro_total / data["banca_inicial"] * 100) if data["banca_inicial"] > 0 else 0
        
        return {
            "banca_inicial": data["banca_inicial"],
            "banca_atual": data["banca_atual"],
            "lucro_total": lucro_total,
            "win_rate": win_rate,
            "roi": roi,
            "total_apostas": len(apostas),
            "apostas": list(reversed(apostas[-20:])) # last 20
        }

    def calcular_stake(self, probabilidade_vitoria, odd_esperada):
        """
        Kelly Criterion: f = (bp - q) / b
        f = fracao da banca a apostar
        b = decimal odd - 1
        p = probabilidade de ganhar
        q = probabilidade de perder (1 - p)
        """
        data = self.load_data()
        banca = data["banca_atual"]
        
        if odd_esperada <= 1:
            return 0
            
        b = odd_esperada - 1
        p = probabilidade_vitoria
        q = 1 - p
        
        f = (b * p - q) / b
        
        # Kelly Fracionado (usamos 1/4 para seguranca)
        f_seguro = f * 0.25
        
        # Limit to max risk (ex: 2%)
        max_f = data.get("risco_por_aposta_max", 0.02)
        f_final = max(0, min(f_seguro, max_f))
        
        stake = banca * f_final
        return round(stake, 2)
        
    def registrar_aposta(self, partida, mercado, odd, stake):
        data = self.load_data()
        aposta = {
            "id": int(datetime.now().timestamp()),
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "partida": partida,
            "mercado": mercado,
            "odd": odd,
            "stake": stake,
            "status": "pendente",
            "lucro": 0
        }
        data["apostas"].append(aposta)
        # Deduct stake from bankroll
        data["banca_atual"] -= stake
        self.save_data(data)
        return aposta
        
    def resolver_aposta(self, aposta_id, status):
        # status: 'vencida', 'perdida', 'reembolso'
        data = self.load_data()
        for aposta in data["apostas"]:
            if aposta["id"] == aposta_id and aposta["status"] == "pendente":
                aposta["status"] = status
                if status == "vencida":
                    retorno = aposta["stake"] * aposta["odd"]
                    aposta["lucro"] = retorno - aposta["stake"]
                    data["banca_atual"] += retorno
                elif status == "perdida":
                    aposta["lucro"] = -aposta["stake"]
                elif status == "reembolso":
                    aposta["lucro"] = 0
                    data["banca_atual"] += aposta["stake"]
                
                self.save_data(data)
                return True
        return False
