"""Agente inteligente para controle de combustível de um veículo."""

from .config import Config
from .ambiente import Ambiente, Percepcao
from .agentes import Agente, AgenteReativo, AgenteNivelMinimo, AgenteDiaFixo, Decisao
from .simulacao import (
    EventoDia, Resultado, simular, passo_a_passo, resumir, comparar, ESTRATEGIAS,
)

__all__ = [
    "Config",
    "Ambiente",
    "Percepcao",
    "Decisao",
    "EventoDia",
    "Agente",
    "AgenteReativo",
    "AgenteNivelMinimo",
    "AgenteDiaFixo",
    "Resultado",
    "simular",
    "passo_a_passo",
    "resumir",
    "comparar",
    "ESTRATEGIAS",
]
