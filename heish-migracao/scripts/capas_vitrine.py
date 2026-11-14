"""Monta a capa de vitrine de cada produto a partir da foto com fundo branco.

A capa segue o padrao de catalogo: proporcao 3:4, fundo branco puro e a modelo
ocupando quase toda a altura, com a mesma folga em todos os produtos. O script
so reposiciona a foto dentro de uma tela branca: nao amplia, nao reduz e nao
retoca. Quando o corpo ja estava cortado pela borda da foto original, essa borda
continua encostada na borda da capa.

A foto escolhida para cada produto veio da revisao visual dos recortes.

Uso:
    python3 heish-migracao/scripts/capas_vitrine.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FUNDO_BRANCO = RAIZ / "imagens-fundo-branco"
PASTA_CAPAS = RAIZ / "capas-vitrine"

PROPORCAO = 3 / 4
FOLGA_VERTICAL = 0.04
FOLGA_LATERAL = 0.04
TOM_QUE_CONTA_COMO_BRANCO = 245
MARGEM_DE_BORDA = 3
QUALIDADE_WEBP = 92


@dataclass(frozen=True)
class Capa:
    """Foto escolhida para a capa de um produto.

    corte_na_base, quando informado, e a fracao da altura da modelo mantida a
    partir do topo. Serve para fotos em que as pernas estao em sombra dura: a
    capa termina na coxa, como nas demais fotos cortadas pela borda.
    """

    produto: int
    foto: str
    corte_na_base: float | None = None


CAPAS: tuple[Capa, ...] = (
    Capa(4110578, "4110578_01"),
    Capa(4110584, "4110584_01"),
    Capa(4110596, "4110596_01"),
    Capa(4110610, "4110610_02"),
    Capa(4171636, "4171636_01", corte_na_base=0.565),
    Capa(4171651, "4171651_01"),
    Capa(4175122, "4175122_02", corte_na_base=0.58),
    Capa(4191760, "4191760_01"),
    Capa(4191780, "4191780_01"),
    Capa(4233271, "4233271_03"),
    Capa(4468163, "4468163_01"),
    Capa(4468164, "4468164_04"),
    Capa(4487891, "4487891_01"),
    Capa(4567819, "4567819_01"),
    Capa(4568066, "4568066_01"),
    Capa(4568136, "4568136_01"),
    Capa(4611471, "4611471_01"),
)


@dataclass(frozen=True)
class Ocupacao:
    """Retangulo ocupado pela modelo e em quais bordas da foto ela encosta."""

    esquerda: int
    topo: int
    direita: int
    base: int
    encosta_na_esquerda: bool
    encosta_no_topo: bool
    encosta_na_direita: bool
    encosta_na_base: bool

    @property
    def largura(self) -> int:
        return self.direita - self.esquerda

    @property
    def altura(self) -> int:
        return self.base - self.topo


def medir_ocupacao(foto: Image.Image, corte_na_base: float | None) -> Ocupacao:
    pixels = np.asarray(foto.convert("RGB"))
    ocupado = (pixels < TOM_QUE_CONTA_COMO_BRANCO).any(axis=2)
    colunas = np.flatnonzero(ocupado.any(axis=0))
    linhas = np.flatnonzero(ocupado.any(axis=1))
    if colunas.size == 0 or linhas.size == 0:
        raise ValueError("A foto esta toda branca: nao ha o que enquadrar.")
    esquerda, direita = int(colunas[0]), int(colunas[-1]) + 1
    topo, base = int(linhas[0]), int(linhas[-1]) + 1
    encosta_na_base = base >= foto.height - MARGEM_DE_BORDA
    if corte_na_base is not None:
        base = topo + round((base - topo) * corte_na_base)
        encosta_na_base = True
        colunas = np.flatnonzero(ocupado[topo:base].any(axis=0))
        esquerda, direita = int(colunas[0]), int(colunas[-1]) + 1
    return Ocupacao(
        esquerda=esquerda,
        topo=topo,
        direita=direita,
        base=base,
        encosta_na_esquerda=esquerda <= MARGEM_DE_BORDA,
        encosta_no_topo=topo <= MARGEM_DE_BORDA,
        encosta_na_direita=direita >= foto.width - MARGEM_DE_BORDA,
        encosta_na_base=encosta_na_base,
    )


def tamanho_da_tela(ocupacao: Ocupacao) -> tuple[float, float]:
    """Largura e altura da capa para a modelo caber com as folgas padrao."""
    folgas_verticais = (0 if ocupacao.encosta_no_topo else 1) + (0 if ocupacao.encosta_na_base else 1)
    folgas_laterais = (0 if ocupacao.encosta_na_esquerda else 1) + (0 if ocupacao.encosta_na_direita else 1)
    altura = ocupacao.altura / (1 - FOLGA_VERTICAL * folgas_verticais)
    largura_minima = ocupacao.largura / (1 - FOLGA_LATERAL * folgas_laterais)
    largura = max(altura * PROPORCAO, largura_minima)
    return largura, largura / PROPORCAO


def posicionar(inicio: int, fim: int, encosta_no_inicio: bool, encosta_no_fim: bool, tamanho: float) -> float:
    """Coordenada inicial da tela num eixo, respeitando as bordas em que a modelo encosta."""
    if encosta_no_inicio and not encosta_no_fim:
        return float(inicio)
    if encosta_no_fim and not encosta_no_inicio:
        return fim - tamanho
    return (inicio + fim) / 2 - tamanho / 2


def enquadrar(foto: Image.Image, corte_na_base: float | None = None) -> Image.Image:
    ocupacao = medir_ocupacao(foto, corte_na_base)
    largura, altura = tamanho_da_tela(ocupacao)
    origem_x = posicionar(
        ocupacao.esquerda, ocupacao.direita, ocupacao.encosta_na_esquerda, ocupacao.encosta_na_direita, largura
    )
    origem_y = posicionar(
        ocupacao.topo, ocupacao.base, ocupacao.encosta_no_topo, ocupacao.encosta_na_base, altura
    )
    tela = Image.new("RGB", (round(largura), round(altura)), (255, 255, 255))
    tela.paste(foto.convert("RGB"), (-round(origem_x), -round(origem_y)))
    return tela


def main() -> None:
    PASTA_CAPAS.mkdir(parents=True, exist_ok=True)
    for capa in CAPAS:
        with Image.open(PASTA_FUNDO_BRANCO / f"{capa.foto}-fundo-branco.webp") as foto:
            resultado = enquadrar(foto, capa.corte_na_base)
        destino = PASTA_CAPAS / f"{capa.produto}-capa-fundo-branco.webp"
        resultado.save(destino, "WEBP", quality=QUALIDADE_WEBP, method=6)
        print(f"{destino.name}  {resultado.width}x{resultado.height}  a partir de {capa.foto}")


if __name__ == "__main__":
    main()
