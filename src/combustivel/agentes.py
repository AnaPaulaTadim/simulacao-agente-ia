"""Agentes: estratégias para decidir quando e quanto abastecer."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass

from .ambiente import Percepcao
from .config import Config
from .formatacao import num

# Tipos de decisão (usados para colorir a saída e contar os abastecimentos)
URGENCIA = "urgencia"
OPORTUNIDADE = "oportunidade"
PROGRAMADO = "programado"
NENHUMA = "nenhuma"


@dataclass(frozen=True)
class Decisao:
    """Decisão do agente: quanto abastecer e *por quê*."""

    litros: float  # 0 = não abastecer
    motivo: str    # explicação legível da decisão
    tipo: str      # URGENCIA, OPORTUNIDADE, PROGRAMADO ou NENHUMA

    @property
    def abastece(self) -> bool:
        return self.litros > 0


class Agente(ABC):
    """Interface comum: recebe uma percepção e devolve uma decisão explicada."""

    nome: str = "Agente"

    @abstractmethod
    def decidir(self, percepcao: Percepcao) -> Decisao:
        """Decide quantos litros abastecer hoje e explica o motivo."""


class AgenteReativo(Agente):
    """Agente reativo baseado em nível do tanque e em oportunidade de preço.

    Regras, na ordem:
      1. **Urgência:** se o nível está abaixo de ``nivel_minimo`` (fração da
         capacidade), enche o tanque, não importa o preço.
      2. **Oportunidade:** se o preço de hoje está abaixo de ``desconto`` vezes a
         média móvel dos últimos ``janela`` dias *e* há espaço suficiente no
         tanque, aproveita e enche.
      3. Caso contrário, não abastece.
    """

    nome = "Reativo (nível + preço)"

    def __init__(
        self,
        config: Config,
        nivel_minimo: float = 0.20,
        desconto: float = 0.95,
        janela: int = 7,
        espaco_minimo: float = 0.30,
    ) -> None:
        self.config = config
        self.nivel_minimo = nivel_minimo
        self.desconto = desconto
        self.espaco_minimo = espaco_minimo
        self._precos_recentes: deque = deque(maxlen=janela)

    def decidir(self, percepcao: Percepcao) -> Decisao:
        # A média usa apenas dias anteriores, sem incluir o preço de hoje
        n_dias = len(self._precos_recentes)
        media = sum(self._precos_recentes) / n_dias if n_dias else percepcao.preco
        self._precos_recentes.append(percepcao.preco)

        reserva = self.nivel_minimo * percepcao.capacidade
        if percepcao.nivel < reserva:
            return Decisao(
                percepcao.espaco,
                f"Urgência: nível de {num(percepcao.nivel, 1)} L abaixo da reserva "
                f"de {num(reserva, 1)} L",
                URGENCIA,
            )

        preco_bom = percepcao.preco < self.desconto * media
        espaco_ok = percepcao.espaco > self.espaco_minimo * percepcao.capacidade
        if preco_bom and espaco_ok:
            abaixo = (1 - percepcao.preco / media) * 100
            return Decisao(
                percepcao.espaco,
                f"Oportunidade: preço {num(abaixo, 0)}% abaixo da média de {n_dias} dias",
                OPORTUNIDADE,
            )
        if preco_bom:
            motivo = (f"Preço bom, mas só cabem {num(percepcao.espaco, 1)} L "
                      f"no tanque")
        elif n_dias == 0:
            motivo = "Nível confortável e ainda sem histórico de preços"
        else:
            motivo = (f"Nível confortável ({num(percepcao.nivel, 1)} L) "
                      f"e preço sem vantagem")
        return Decisao(0.0, motivo, NENHUMA)


class AgenteNivelMinimo(Agente):
    """Linha de base 1: enche o tanque sempre que o nível cai abaixo do mínimo."""

    nome = "Linha de base: nível mínimo"

    def __init__(self, config: Config, nivel_minimo: float = 0.20) -> None:
        self.config = config
        self.nivel_minimo = nivel_minimo

    def decidir(self, percepcao: Percepcao) -> Decisao:
        reserva = self.nivel_minimo * percepcao.capacidade
        if percepcao.nivel < reserva:
            return Decisao(
                percepcao.espaco,
                f"Nível de {num(percepcao.nivel, 1)} L abaixo da reserva "
                f"de {num(reserva, 1)} L",
                URGENCIA,
            )
        return Decisao(0.0, f"Nível acima da reserva ({num(reserva, 1)} L)", NENHUMA)


class AgenteDiaFixo(Agente):
    """Linha de base 2: enche o tanque a cada ``intervalo`` dias."""

    nome = "Linha de base: dia fixo"

    def __init__(self, config: Config, intervalo: int = 7) -> None:
        self.config = config
        self.intervalo = intervalo

    def decidir(self, percepcao: Percepcao) -> Decisao:
        if percepcao.dia % self.intervalo == 0:
            return Decisao(
                percepcao.espaco,
                f"Dia de abastecer (a cada {self.intervalo} dias)",
                PROGRAMADO,
            )
        faltam = self.intervalo - percepcao.dia % self.intervalo
        return Decisao(0.0, f"Próximo abastecimento programado em {faltam} dia(s)", NENHUMA)
