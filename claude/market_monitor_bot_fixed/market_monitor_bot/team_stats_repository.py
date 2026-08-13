"""
Fonte REAL de estatisticas historicas dos times.

Substitui os valores mockados que antes ficavam chumbados no provider.
Carrega um CSV com colunas:

    team_id,team_name,over_05_ht_hit_rate,over_25_ft_pre_odd

A busca aceita team_id OU nome (normalizado). Se o time nao existir na base,
retorna None -> o jogo e ignorado (nao entra no funil com dado inventado).
"""
import csv
import logging
from typing import Dict, Optional
from .models import TeamStats

logger = logging.getLogger(__name__)


def _norm(name: str) -> str:
    return "".join(ch for ch in (name or "").lower().strip() if ch.isalnum() or ch == " ")


class TeamStatsRepository:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._by_id: Dict[str, TeamStats] = {}
        self._by_name: Dict[str, TeamStats] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    try:
                        ts = TeamStats(
                            team_id=str(row["team_id"]).strip(),
                            team_name=row["team_name"].strip(),
                            over_05_ht_hit_rate=float(row["over_05_ht_hit_rate"]),
                            over_25_ft_pre_odd=float(row["over_25_ft_pre_odd"]),
                        )
                    except (KeyError, ValueError) as e:
                        logger.warning("Linha invalida no CSV de times ignorada: %s (%s)", row, e)
                        continue
                    self._by_id[ts.team_id] = ts
                    self._by_name[_norm(ts.team_name)] = ts
            logger.info("TeamStatsRepository: %s times carregados de %s", len(self._by_id), self.csv_path)
        except FileNotFoundError:
            logger.error(
                "CSV de estatisticas nao encontrado em '%s'. Nenhum jogo passara no filtro "
                "pre-jogo ate voce popular essa base.", self.csv_path,
            )

    def get(self, team_id: Optional[str] = None, team_name: Optional[str] = None) -> Optional[TeamStats]:
        if team_id and team_id in self._by_id:
            return self._by_id[team_id]
        if team_name:
            return self._by_name.get(_norm(team_name))
        return None

    def is_empty(self) -> bool:
        return not self._by_id
