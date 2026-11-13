"""Formatação de números no padrão brasileiro (1.234,56)."""


def num(valor: float, casas: int = 2) -> str:
    """Formata ``valor`` com separador de milhar ponto e decimal vírgula."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
