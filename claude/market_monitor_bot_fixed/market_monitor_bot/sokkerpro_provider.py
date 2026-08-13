"""
SokkerPRO Data Provider (enriquecimento: xG, pressao, odds).

ATENCAO: os endpoints internos do SokkerPRO nao sao publicos/documentados.
O mapeamento de chaves abaixo e uma tentativa e provavelmente precisa de ajuste.
Use `dump_raw()` para salvar uma resposta real e mapear os campos corretos
antes de confiar nos dados enriquecidos.
"""
import json
import logging
import cloudscraper
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class SokkerProProvider:
    def __init__(self):
        self.base_url = "https://m2.sokkerpro.com"
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "Accept": "application/json",
            "Referer": "https://sokkerpro.com/",
            "Origin": "https://sokkerpro.com",
        }
        self._fixture_cache: Dict[str, int] = {}

    def _get(self, path: str) -> Optional[Dict]:
        try:
            resp = self.scraper.get(f"{self.base_url}{path}", headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning("SokkerPRO %s falhou: %s", path, e)
            return None

    def dump_raw(self, fixture_id: int, out_path: str = "sokkerpro_raw.json") -> None:
        """Salva as respostas cruas para voce inspecionar e mapear as chaves reais."""
        payload = {
            "dados": self._get(f"/fixture/{fixture_id}/dados"),
            "fixture": self._get(f"/fixture/{fixture_id}"),
            "preodds": self._get(f"/fixture/{fixture_id}/preodds"),
        }
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        logger.info("Resposta crua do SokkerPRO salva em %s", out_path)

    def get_live_fixtures(self) -> List[Dict]:
        data = self._get("/livescores")
        if data is None:
            return []
        fixtures: List[Dict] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    events = item.get("events", item.get("fixtures", []))
                    fixtures.extend(events if isinstance(events, list) else [item])
        elif isinstance(data, dict):
            events = data.get("events", data.get("fixtures", [data]))
            fixtures.extend(events)
        logger.info("SokkerPRO: %s jogos ao vivo.", len(fixtures))
        return fixtures

    def find_fixture_by_teams(
        self, home_name: str, away_name: str, live_fixtures: List[Dict]
    ) -> Optional[int]:
        cache_key = f"{home_name}_{away_name}"
        if cache_key in self._fixture_cache:
            return self._fixture_cache[cache_key]

        h, a = home_name.lower(), away_name.lower()
        for fx in live_fixtures:
            sp_home = sp_away = ""
            if isinstance(fx.get("homeTeam"), dict):
                sp_home = fx["homeTeam"].get("name", "").lower()
                sp_away = fx.get("awayTeam", {}).get("name", "").lower()
            elif "home" in fx:
                sp_home = (fx["home"].get("name", "") if isinstance(fx["home"], dict) else str(fx["home"])).lower()
                sp_away = (fx.get("away", {}).get("name", "") if isinstance(fx.get("away"), dict) else str(fx.get("away", ""))).lower()

            if (h in sp_home or sp_home in h) and (a in sp_away or sp_away in a):
                fixture_id = fx.get("id") or fx.get("fixture_id")
                if fixture_id:
                    self._fixture_cache[cache_key] = fixture_id
                    return fixture_id
        return None

    def enrich_match_data(self, fixture_id: int) -> Dict:
        """
        Retorna xG, pressao, ODD DE MERCADO e ODD JUSTA separadamente.
        Mantemos as duas odds distintas para que o calculo de valor funcione.
        """
        enriched = {
            "xg_home": None, "xg_away": None,
            "pressure_home": None, "pressure_away": None,
            "market_odd_over_05_ht": None,
            "fair_odd_over_05_ht": None,
            "enriched": False,
        }

        stats = self._get(f"/fixture/{fixture_id}/dados")
        if isinstance(stats, dict) and stats:
            enriched["enriched"] = True
            xg = stats.get("xg", stats.get("expectedGoals", {}))
            if isinstance(xg, dict):
                enriched["xg_home"] = xg.get("home", xg.get("h"))
                enriched["xg_away"] = xg.get("away", xg.get("a"))
            elif isinstance(xg, list) and len(xg) >= 2:
                enriched["xg_home"], enriched["xg_away"] = xg[0], xg[1]

            pressure = stats.get("pressure", stats.get("momentum", {}))
            if isinstance(pressure, dict):
                enriched["pressure_home"] = pressure.get("home", pressure.get("h"))
                enriched["pressure_away"] = pressure.get("away", pressure.get("a"))

        details = self._get(f"/fixture/{fixture_id}")
        if isinstance(details, dict):
            odds = details.get("odds", {})
            block = odds.get("over_05_ht", odds.get("overUnder", {}).get("0.5", {}))
            if isinstance(block, dict):
                # odd praticada pela casa
                enriched["market_odd_over_05_ht"] = block.get("over", block.get("o"))
                # odd justa/modelo, se o SokkerPRO expuser
                enriched["fair_odd_over_05_ht"] = block.get("fair", block.get("justa"))
            elif isinstance(block, (int, float)):
                enriched["market_odd_over_05_ht"] = float(block)

        return enriched
