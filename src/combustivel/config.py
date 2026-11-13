"""Parâmetros da simulação, reunidos em um único lugar."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Configuração do ambiente simulado.

    Todos os intervalos são sorteados de forma uniforme a cada dia.
    Use a mesma ``semente`` para obter resultados reproduzíveis.
    """

    capacidade_l: float = 50.0           # capacidade máxima do tanque (litros)
    km_por_dia: tuple = (20.0, 80.0)     # distância rodada por dia (km)
    km_por_litro: tuple = (10.0, 15.0)   # eficiência do veículo (km/L)
    preco_por_litro: tuple = (5.0, 6.5)  # preço da gasolina (R$/L)
    semente: int = 42                    # semente do gerador aleatório
