"""Execução das simulações, acompanhamento dia a dia e métricas."""

from dataclasses import dataclass, replace
from typing import Iterator

from .agentes import Agente, AgenteDiaFixo, AgenteNivelMinimo, AgenteReativo, Decisao
from .ambiente import Ambiente, Percepcao
from .config import Config

ESTRATEGIAS: dict = {
    AgenteReativo.nome: AgenteReativo,
    AgenteNivelMinimo.nome: AgenteNivelMinimo,
    AgenteDiaFixo.nome: AgenteDiaFixo,
}


@dataclass(frozen=True)
class EventoDia:
    """Tudo o que aconteceu em um dia da simulação."""

    dia: int
    percepcao: Percepcao      # situação *antes* da decisão
    decisao: Decisao          # o que o agente decidiu e por quê
    litros_abastecidos: float # litros efetivamente abastecidos
    custo_dia: float          # litros abastecidos x preço do dia
    custo_acumulado: float    # custo total até este dia
    km: float                 # km realmente percorridos
    nivel_final: float        # litros no tanque ao fim do dia
    tanque_seco: bool         # True se o combustível acabou no caminho


@dataclass
class Resultado:
    """Métricas de uma simulação."""

    nome: str
    custo_total: float
    litros: float
    n_abastecimentos: int
    dias_tanque_seco: int
    km_total: float

    @property
    def preco_medio_pago(self) -> float:
        return self.custo_total / self.litros if self.litros else 0.0

    @property
    def custo_por_km(self) -> float:
        return self.custo_total / self.km_total if self.km_total else 0.0


def passo_a_passo(agente: Agente, ambiente: Ambiente, dias: int) -> Iterator[EventoDia]:
    """Gerador que roda a simulação e entrega um ``EventoDia`` por dia.

    Permite acompanhar a simulação enquanto ela acontece (terminal, gráfico ao
    vivo, GIF...). Ao final, use ``resumir`` para obter as métricas.
    """
    custo_acumulado = 0.0
    for _ in range(dias):
        ambiente.novo_dia()
        percepcao = ambiente.perceber()
        decisao = agente.decidir(percepcao)
        resultado_dia = ambiente.agir(decisao.litros)

        custo_dia = resultado_dia.litros_abastecidos * percepcao.preco
        custo_acumulado += custo_dia
        yield EventoDia(
            dia=percepcao.dia,
            percepcao=percepcao,
            decisao=decisao,
            litros_abastecidos=resultado_dia.litros_abastecidos,
            custo_dia=custo_dia,
            custo_acumulado=custo_acumulado,
            km=resultado_dia.km,
            nivel_final=ambiente.nivel,
            tanque_seco=resultado_dia.tanque_seco,
        )


def resumir(nome: str, ambiente: Ambiente) -> Resultado:
    """Calcula as métricas finais a partir do estado do ambiente."""
    return Resultado(
        nome=nome,
        custo_total=ambiente.custo_total,
        litros=ambiente.litros_comprados,
        n_abastecimentos=len(ambiente.abastecimentos),
        dias_tanque_seco=len(ambiente.dias_tanque_seco),
        km_total=ambiente.km_total,
    )


def simular(agente: Agente, config: Config, dias: int = 60):
    """Roda a simulação inteira de uma vez.

    Retorna uma tupla ``(Resultado, Ambiente)``.
    """
    ambiente = Ambiente(config)
    for _ in passo_a_passo(agente, ambiente, dias):
        pass
    return resumir(agente.nome, ambiente), ambiente


def comparar(config: Config, dias: int = 60, simulacoes: int = 200) -> dict:
    """Compara as estratégias em várias simulações (sementes diferentes).

    Todas as estratégias enfrentam exatamente as mesmas sementes, o que torna a
    comparação justa. Retorna a média de cada métrica por estratégia.
    """
    somas = {
        nome: {"custo_por_km": 0.0, "preco_medio_pago": 0.0,
               "n_abastecimentos": 0.0, "dias_tanque_seco": 0.0}
        for nome in ESTRATEGIAS
    }
    for i in range(simulacoes):
        cfg = replace(config, semente=config.semente + i)
        for nome, fabrica in ESTRATEGIAS.items():
            resultado, _ = simular(fabrica(cfg), cfg, dias)
            for metrica in somas[nome]:
                somas[nome][metrica] += getattr(resultado, metrica)

    return {
        nome: {metrica: valor / simulacoes for metrica, valor in metricas.items()}
        for nome, metricas in somas.items()
    }
