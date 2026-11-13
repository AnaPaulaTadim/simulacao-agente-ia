"""Saída em texto: uma linha por dia (modo verboso) e o resumo final."""

import os
import sys

from .agentes import NENHUMA, OPORTUNIDADE, PROGRAMADO, URGENCIA
from .formatacao import num
from .simulacao import EventoDia, Resultado

_RESET = "\033[0m"
_CORES = {
    URGENCIA: "\033[33m",       # amarelo
    OPORTUNIDADE: "\033[32m",   # verde
    PROGRAMADO: "\033[36m",     # ciano
    NENHUMA: "\033[2m",         # cinza (esmaecido)
}
_ROTULOS = {URGENCIA: "por urgência", OPORTUNIDADE: "por oportunidade",
            PROGRAMADO: "programados"}


def usar_cor(sem_cor: bool = False) -> bool:
    """Cores só quando a saída é um terminal e o usuário não as desativou."""
    return not sem_cor and sys.stdout.isatty() and "NO_COLOR" not in os.environ


def formatar_evento(ev: EventoDia, dias: int, cor: bool = False) -> str:
    """Uma linha descrevendo o dia: dados, decisão e motivo."""
    largura = len(str(dias))
    nivel = ev.percepcao.nivel
    pct = nivel / ev.percepcao.capacidade * 100
    if ev.litros_abastecidos > 0:
        acao = f"ABASTECE {num(ev.litros_abastecidos, 1)} L (R$ {num(ev.custo_dia)})"
    else:
        acao = "sem abastecer"

    linha = (
        f"Dia {ev.dia:>{largura}}/{dias} | R$ {num(ev.percepcao.preco)}/L | "
        f"tanque {num(nivel, 1):>5} L ({pct:>3.0f}%) | {acao:<29} | {ev.decisao.motivo}"
    )
    if ev.tanque_seco:
        linha += f"  !! TANQUE SECO (rodou só {num(ev.km, 1)} km)"
    if cor:
        linha = f"{_CORES.get(ev.decisao.tipo, '')}{linha}{_RESET}"
    return linha


def formatar_resumo(resultado: Resultado, dias: int, eventos=None) -> str:
    """Resumo final da simulação. Com ``eventos``, detalha os motivos."""
    detalhe = ""
    if eventos:
        contagem: dict = {}
        for ev in eventos:
            if ev.litros_abastecidos > 0:
                contagem[ev.decisao.tipo] = contagem.get(ev.decisao.tipo, 0) + 1
        partes = [f"{n} {_ROTULOS.get(tipo, tipo)}" for tipo, n in contagem.items()]
        if partes:
            detalhe = f" ({', '.join(partes)})"

    linhas = [
        "=" * 60,
        f"Resumo: {resultado.nome} | {dias} dias",
        "=" * 60,
        f"Abastecimentos .......... {resultado.n_abastecimentos}{detalhe}",
        f"Litros comprados ........ {num(resultado.litros, 1)} L",
        f"Custo total ............. R$ {num(resultado.custo_total)}",
        f"Preço médio pago ........ R$ {num(resultado.preco_medio_pago)}/L",
        f"Custo por km ............ R$ {num(resultado.custo_por_km, 4)}",
        f"Dias com tanque seco .... {resultado.dias_tanque_seco}",
    ]
    return "\n".join(linhas)
