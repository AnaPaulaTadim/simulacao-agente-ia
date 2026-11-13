"""Gráficos da simulação e da comparação entre estratégias."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from .ambiente import Ambiente
from .config import Config
from .formatacao import num


def _finalizar(fig, caminho) -> None:
    fig.tight_layout()
    if caminho:
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(caminho, dpi=130)
    else:
        plt.show()
    plt.close(fig)


def grafico_simulacao(ambiente: Ambiente, caminho=None) -> None:
    """Preços com os abastecimentos marcados e nível do tanque ao longo dos dias."""
    dias = range(1, len(ambiente.historico_precos) + 1)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    ax1.plot(dias, ambiente.historico_precos, "o--", color="tab:blue", label="Preço do litro")
    if ambiente.abastecimentos:
        dias_ab = [d for d, _, _ in ambiente.abastecimentos]
        precos_ab = [p for _, _, p in ambiente.abastecimentos]
        ax1.scatter(dias_ab, precos_ab, s=110, color="tab:green", zorder=3,
                    label="Abastecimento")
    ax1.set_title("Preço do combustível e abastecimentos")
    ax1.set_ylabel("Preço (R$/L)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    capacidade = ambiente.config.capacidade_l
    ax2.plot(dias, ambiente.historico_nivel, color="tab:red", label="Nível ao fim do dia")
    ax2.axhline(0.2 * capacidade, color="gray", ls=":", label="Reserva (20%)")
    ax2.set_ylim(0, capacidade * 1.05)
    ax2.set_title("Nível do tanque")
    ax2.set_xlabel("Dia")
    ax2.set_ylabel("Litros")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    _finalizar(fig, caminho)


def grafico_comparacao(medias: dict, caminho=None) -> None:
    """Barras com o custo médio por km de cada estratégia."""
    nomes = list(medias)
    custos = [medias[n]["custo_por_km"] for n in nomes]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    barras = ax.bar(range(len(nomes)), custos, color=["tab:green", "tab:gray", "tab:gray"])
    ax.set_xticks(range(len(nomes)))
    ax.set_xticklabels([n.replace(": ", ":\n") for n in nomes])
    ax.set_ylabel("Custo médio por km (R$)")
    ax.set_title("Comparação entre estratégias")
    ax.set_ylim(min(custos) * 0.9, max(custos) * 1.03)
    for barra, valor in zip(barras, custos):
        ax.text(barra.get_x() + barra.get_width() / 2, valor, f"R$ {valor:.4f}",
                ha="center", va="bottom")
    _finalizar(fig, caminho)


# --- acompanhamento dia a dia (ao vivo e GIF) ------------------------------
def _desenhar_quadro(fig, ax1, ax2, eventos: list, config: Config, dias: int) -> None:
    """Redesenha os dois gráficos com os eventos ocorridos até agora.

    É a mesma função para o gráfico ao vivo e para o GIF, então os dois ficam
    idênticos. Os eixos têm limites fixos para o gráfico não "pular" a cada dia.
    """
    ax1.clear()
    ax2.clear()
    if not eventos:
        return

    dias_x = [e.dia for e in eventos]
    ax1.plot(dias_x, [e.percepcao.preco for e in eventos], "o--",
             color="tab:blue", label="Preço do litro")
    abastecimentos = [e for e in eventos if e.litros_abastecidos > 0]
    if abastecimentos:
        ax1.scatter([e.dia for e in abastecimentos],
                    [e.percepcao.preco for e in abastecimentos],
                    s=110, color="tab:green", zorder=3, label="Abastecimento")
    preco_min, preco_max = config.preco_por_litro
    ax1.set_xlim(0.5, dias + 0.5)
    ax1.set_ylim(preco_min - 0.25, preco_max + 0.55)
    ax1.set_ylabel("Preço (R$/L)")
    ax1.set_title("Preço do combustível e abastecimentos")
    ax1.legend(loc="upper right", ncol=2)
    ax1.grid(True, alpha=0.3)

    ax2.plot(dias_x, [e.nivel_final for e in eventos], color="tab:red",
             label="Nível ao fim do dia")
    ax2.axhline(0.2 * config.capacidade_l, color="gray", ls=":", label="Reserva (20%)")
    ax2.set_ylim(0, config.capacidade_l * 1.05)
    ax2.set_xlabel("Dia")
    ax2.set_ylabel("Litros")
    ax2.set_title("Nível do tanque")
    ax2.legend(loc="lower left")
    ax2.grid(True, alpha=0.3)

    ultimo = eventos[-1]
    fig.suptitle(
        f"Dia {ultimo.dia}/{dias}  |  {ultimo.decisao.motivo}\n"
        f"Custo acumulado: R$ {num(ultimo.custo_acumulado)}",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))


def grafico_ao_vivo(eventos, config: Config, dias: int, pausa: float = 0.3):
    """Desenha os gráficos crescendo a cada dia, enquanto a simulação roda.

    ``eventos`` é o gerador ``passo_a_passo`` (ou qualquer iterável de
    ``EventoDia``). Retorna a figura; chame ``plt.show()`` para mantê-la aberta.
    """
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    ocorridos: list = []
    for ev in eventos:
        ocorridos.append(ev)
        _desenhar_quadro(fig, ax1, ax2, ocorridos, config, dias)
        fig.canvas.draw_idle()
        plt.pause(max(pausa, 0.001))
    plt.ioff()
    return fig


def salvar_gif(eventos: list, config: Config, dias: int, caminho,
               fps: int = 5, pausa_final_s: float = 2.0) -> None:
    """Grava a simulação em um GIF animado (um quadro por dia)."""
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)
    # Repete o último quadro para o GIF "respirar" antes de reiniciar
    quadros = list(range(len(eventos))) + [len(eventos) - 1] * int(fps * pausa_final_s)

    def desenhar(i: int) -> None:
        _desenhar_quadro(fig, ax1, ax2, eventos[: i + 1], config, dias)

    animacao = FuncAnimation(fig, desenhar, frames=quadros, repeat=False)
    animacao.save(str(caminho), writer=PillowWriter(fps=fps), dpi=80)
    plt.close(fig)
