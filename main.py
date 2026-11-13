"""Linha de comando do projeto.

Exemplos:
    python main.py simular --dias 60 --semente 42 --verboso
    python main.py simular --dias 60 --ao-vivo --pausa 0.3
    python main.py simular --dias 60 --gif docs/img/simulacao.gif
    python main.py comparar --dias 60 --simulacoes 500 --saida docs/img
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib  # noqa: E402

from combustivel import (  # noqa: E402
    Ambiente, AgenteReativo, Config, comparar, passo_a_passo, resumir,
)
from combustivel.formatacao import num  # noqa: E402
from combustivel.terminal import formatar_evento, formatar_resumo, usar_cor  # noqa: E402


def _criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agente de controle de combustível")
    sub = parser.add_subparsers(dest="comando", required=True)

    sim = sub.add_parser("simular", help="roda uma simulação com o agente reativo")
    sim.add_argument("--dias", type=int, default=60)
    sim.add_argument("--semente", type=int, default=42)
    sim.add_argument("--verboso", action="store_true",
                     help="mostra uma linha por dia com a decisão e o motivo")
    sim.add_argument("--ao-vivo", action="store_true",
                     help="abre o gráfico e o atualiza a cada dia")
    sim.add_argument("--pausa", type=float, default=0.3,
                     help="segundos entre os dias no modo verboso/ao vivo (padrão: 0.3)")
    sim.add_argument("--gif", metavar="ARQUIVO",
                     help="grava a simulação em um GIF animado (ex.: docs/img/simulacao.gif)")
    sim.add_argument("--sem-cor", action="store_true", help="desativa as cores no terminal")
    sim.add_argument("--saida", help="pasta para salvar o gráfico final (PNG)")

    cmp_ = sub.add_parser("comparar", help="compara as estratégias em várias simulações")
    cmp_.add_argument("--dias", type=int, default=60)
    cmp_.add_argument("--simulacoes", type=int, default=200)
    cmp_.add_argument("--semente", type=int, default=42)
    cmp_.add_argument("--saida", help="pasta para salvar o gráfico (se omitido, exibe na tela)")
    return parser


def _acompanhar(eventos, dias: int, verboso: bool, pausa: float, cor: bool, registro: list):
    """Repassa os eventos, guardando-os e imprimindo uma linha por dia se verboso."""
    for ev in eventos:
        registro.append(ev)
        if verboso:
            print(formatar_evento(ev, dias, cor), flush=True)
            if pausa > 0 and not _acompanhar.sem_espera:
                time.sleep(pausa)
        yield ev


_acompanhar.sem_espera = False


def _simular(args, config: Config) -> None:
    from combustivel import visualizacao as vis

    ambiente = Ambiente(config)
    agente = AgenteReativo(config)
    registro: list = []
    cor = usar_cor(args.sem_cor)

    # No modo ao vivo, o gráfico já provoca a pausa entre os dias
    _acompanhar.sem_espera = args.ao_vivo or bool(args.gif)
    eventos = _acompanhar(passo_a_passo(agente, ambiente, args.dias),
                          args.dias, args.verboso, args.pausa, cor, registro)

    figura_ao_vivo = None
    if args.ao_vivo:
        figura_ao_vivo = vis.grafico_ao_vivo(eventos, config, args.dias, args.pausa)
    else:
        for _ in eventos:  # consome o gerador (imprime se verboso)
            pass

    resultado = resumir(agente.nome, ambiente)
    if args.verboso:
        print()
    print(formatar_resumo(resultado, args.dias, registro))

    if args.gif:
        vis.salvar_gif(registro, config, args.dias, args.gif)
        print(f"\nGIF salvo em {args.gif}")
    if args.saida:
        vis.grafico_simulacao(ambiente, Path(args.saida) / "simulacao.png")
        print(f"Gráfico salvo em {Path(args.saida) / 'simulacao.png'}")
    elif not args.ao_vivo and not args.gif:
        vis.grafico_simulacao(ambiente, None)  # exibe o gráfico final na tela

    if figura_ao_vivo is not None:
        import matplotlib.pyplot as plt
        plt.show()  # mantém a janela aberta até o usuário fechar


def _comparar(args, config: Config) -> None:
    from combustivel.visualizacao import grafico_comparacao

    medias = comparar(config, args.dias, args.simulacoes)
    print(f"Média de {args.simulacoes} simulações de {args.dias} dias\n")
    print(f"{'Estratégia':<32}{'R$/km':>9}{'R$/L pago':>11}{'Abast.':>8}{'Tanque seco':>13}")
    for nome, m in medias.items():
        print(f"{nome:<32}{num(m['custo_por_km'], 4):>9}{num(m['preco_medio_pago'], 3):>11}"
              f"{num(m['n_abastecimentos'], 1):>8}{num(m['dias_tanque_seco'], 2):>13}")
    grafico_comparacao(medias, Path(args.saida) / "comparacao.png" if args.saida else None)


def main() -> None:
    args = _criar_parser().parse_args()
    if getattr(args, "ao_vivo", False) is False and (args.saida or getattr(args, "gif", None)):
        matplotlib.use("Agg")  # sem janela: apenas grava arquivos

    config = Config(semente=args.semente)
    if args.comando == "simular":
        _simular(args, config)
    else:
        _comparar(args, config)


if __name__ == "__main__":
    main()
