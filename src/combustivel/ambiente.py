"""Ambiente: o veículo, o tanque e o mercado de combustível."""

import random
from dataclasses import dataclass, field

from .config import Config


@dataclass(frozen=True)
class Percepcao:
    """O que o agente consegue observar do ambiente em um dia."""

    dia: int
    preco: float       # preço do litro hoje (R$/L)
    nivel: float       # litros atualmente no tanque
    capacidade: float  # capacidade máxima do tanque (litros)

    @property
    def espaco(self) -> float:
        """Litros que ainda cabem no tanque."""
        return self.capacidade - self.nivel


@dataclass(frozen=True)
class ResultadoDia:
    """O que aconteceu no ambiente depois da ação do agente."""

    litros_abastecidos: float  # litros efetivamente colocados no tanque
    km: float                  # distância realmente percorrida no dia
    tanque_seco: bool          # True se o combustível acabou no caminho


@dataclass
class Ambiente:
    """Simula o dia a dia de um veículo.

    A cada dia o ambiente sorteia o preço do combustível (``novo_dia``), o agente
    percebe a situação (``perceber``) e decide quantos litros abastecer, e o
    ambiente aplica a ação e simula o uso do veículo (``agir``).
    """

    config: Config = field(default_factory=Config)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.config.semente)
        self.nivel: float = self.config.capacidade_l
        self.dia: int = 0
        self.preco_hoje: float = 0.0

        # Históricos usados nos gráficos e nas métricas
        self.historico_precos: list[float] = []
        self.historico_nivel: list[float] = []    # nível ao fim de cada dia
        self.historico_consumo: list[float] = []  # km/L de cada dia
        self.abastecimentos: list[tuple[int, float, float]] = []  # (dia, litros, preço)
        self.dias_tanque_seco: list[int] = []
        self.km_total: float = 0.0

    # --- ciclo de um dia -------------------------------------------------
    def novo_dia(self) -> None:
        """Avança para o próximo dia e sorteia o preço do combustível."""
        self.dia += 1
        self.preco_hoje = self._rng.uniform(*self.config.preco_por_litro)
        self.historico_precos.append(self.preco_hoje)

    def perceber(self) -> Percepcao:
        """Retorna o que o agente pode observar hoje."""
        return Percepcao(
            dia=self.dia,
            preco=self.preco_hoje,
            nivel=self.nivel,
            capacidade=self.config.capacidade_l,
        )

    def agir(self, litros: float = 0.0) -> ResultadoDia:
        """Aplica a ação do agente e simula o uso do veículo no dia.

        Args:
            litros: quantidade que o agente deseja abastecer hoje.

        Returns:
            Um ``ResultadoDia`` com os litros efetivamente abastecidos (limitados
            ao espaço no tanque), os km rodados e se o tanque secou.
        """
        litros = max(0.0, min(litros, self.config.capacidade_l - self.nivel))
        if litros > 0:
            self.nivel += litros
            self.abastecimentos.append((self.dia, litros, self.preco_hoje))

        km_planejado = self._rng.uniform(*self.config.km_por_dia)
        km_por_litro = self._rng.uniform(*self.config.km_por_litro)
        litros_necessarios = km_planejado / km_por_litro

        tanque_seco = litros_necessarios > self.nivel
        if tanque_seco:  # ficou sem combustível no caminho
            km_planejado = self.nivel * km_por_litro
            litros_necessarios = self.nivel
            self.dias_tanque_seco.append(self.dia)

        self.nivel -= litros_necessarios
        self.km_total += km_planejado
        self.historico_consumo.append(km_por_litro)
        self.historico_nivel.append(self.nivel)
        return ResultadoDia(litros_abastecidos=litros, km=km_planejado, tanque_seco=tanque_seco)

    # --- métricas --------------------------------------------------------
    @property
    def custo_total(self) -> float:
        return sum(litros * preco for _, litros, preco in self.abastecimentos)

    @property
    def litros_comprados(self) -> float:
        return sum(litros for _, litros, _ in self.abastecimentos)
