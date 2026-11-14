"""Gera os banners da vitrine Heish Moda Praia a partir das fotos dos produtos.

Cada banner e descrito de forma declarativa em BANNERS. O script apenas recorta,
compoe e exporta: nenhuma foto e retocada, para preservar a fidelidade do produto.

Os banners de destaque reservam uma faixa de cor lisa para o texto que o tema
sobrepoe a imagem. Assim o texto nunca cobre o produto: no computador a faixa
fica a esquerda das fotos e, no celular, abaixo delas.

Uso:
    python3 heish-migracao/scripts/gerar_banners.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FOTOS = RAIZ / "imagens"
PASTA_CRIATIVOS = RAIZ / "criativos"
PASTA_SAIDA = RAIZ / "banners"

COR_CALHA = (250, 246, 241)
COR_FAIXA_DE_TEXTO = (241, 228, 216)
QUALIDADE_WEBP = 88

# Largura da faixa de texto no computador, como fracao do banner. O CSS do tema
# limita o texto do carrossel a essa mesma fracao (ver css_code nas configuracoes).
LARGURA_DESTAQUE = 2400
ALTURA_DESTAQUE = 1000
FRACAO_FAIXA_LATERAL = 0.30


class LadoDaFaixa(Enum):
    ESQUERDA = "esquerda"
    BASE = "base"


@dataclass(frozen=True)
class Painel:
    """Uma foto dentro do banner.

    foco indica, de 0 a 1 em cada eixo, para onde o recorte se desloca.
    zoom maior que 1 aproxima o recorte e descarta as bordas opostas ao foco.
    """

    fonte: Path
    foco: tuple[float, float] = (0.5, 0.5)
    zoom: float = 1.0


@dataclass(frozen=True)
class FaixaDeTexto:
    """Area de cor lisa reservada ao texto.

    tamanho e a largura (faixa a esquerda) ou a altura (faixa na base), em pixels.
    transicao e quantos pixels da borda das fotos se dissolvem na cor da faixa.
    """

    lado: LadoDaFaixa
    tamanho: int
    transicao: int = 0


@dataclass(frozen=True)
class Banner:
    nome: str
    largura: int
    altura: int
    paineis: tuple[Painel, ...]
    calha: int = 0
    faixa: FaixaDeTexto | None = None


def foto(nome: str) -> Path:
    return PASTA_FOTOS / f"{nome}.webp"


FAIXA_LATERAL = FaixaDeTexto(LadoDaFaixa.ESQUERDA, round(LARGURA_DESTAQUE * FRACAO_FAIXA_LATERAL))
FAIXA_NA_BASE = FaixaDeTexto(LadoDaFaixa.BASE, tamanho=440, transicao=110)

BANNERS: tuple[Banner, ...] = (
    Banner(
        nome="hero-sirena-desktop",
        largura=LARGURA_DESTAQUE,
        altura=ALTURA_DESTAQUE,
        calha=6,
        faixa=FAIXA_LATERAL,
        paineis=(
            Painel(foto("4568136_01"), (0.5, 0.30)),
            Painel(foto("4568136_02"), (0.5, 0.30)),
            Painel(foto("4568136_03"), (0.5, 0.30)),
        ),
    ),
    Banner(
        nome="hero-sirena-mobile",
        largura=1080,
        altura=1660,
        faixa=FAIXA_NA_BASE,
        paineis=(Painel(foto("4568136_01"), (0.5, 0.32)),),
    ),
    Banner(
        nome="hero-capri-desktop",
        largura=LARGURA_DESTAQUE,
        altura=ALTURA_DESTAQUE,
        calha=6,
        faixa=FAIXA_LATERAL,
        paineis=(
            Painel(foto("4468164_01"), (0.5, 0.35)),
            Painel(foto("4611471_01"), (0.5, 0.30)),
        ),
    ),
    Banner(
        nome="hero-capri-mobile",
        largura=1080,
        altura=1660,
        faixa=FAIXA_NA_BASE,
        paineis=(Painel(foto("4611471_01"), (0.5, 0.25)),),
    ),
    Banner(
        nome="categoria-biquinis",
        largura=900,
        altura=1200,
        paineis=(Painel(foto("4487891_02")),),
    ),
    Banner(
        nome="categoria-maios",
        largura=900,
        altura=1200,
        paineis=(Painel(foto("4191760_01"), (0.5, 0.60), zoom=1.15),),
    ),
    Banner(
        nome="categoria-saidas-de-praia",
        largura=900,
        altura=1200,
        paineis=(Painel(foto("4567819_02"), (0.0, 0.50), zoom=1.14),),
    ),
    Banner(
        nome="editorial-sirena",
        largura=1120,
        altura=1400,
        paineis=(Painel(PASTA_CRIATIVOS / "sirena-poa-nude-4x5.png"),),
    ),
    Banner(
        nome="editorial-capri",
        largura=1012,
        altura=1265,
        paineis=(Painel(foto("4468163_02"), (0.5, 0.5)),),
    ),
)


def area_das_fotos(banner: Banner) -> tuple[int, int, int, int]:
    """Retorna (x, y, largura, altura) da regiao ocupada pelas fotos."""
    if banner.faixa is None:
        return 0, 0, banner.largura, banner.altura
    if banner.faixa.lado is LadoDaFaixa.ESQUERDA:
        return banner.faixa.tamanho, 0, banner.largura - banner.faixa.tamanho, banner.altura
    return 0, 0, banner.largura, banner.altura - banner.faixa.tamanho


def larguras_dos_paineis(largura_total: int, quantidade: int, calha: int) -> list[int]:
    """Divide a largura util entre os paineis, entregando a sobra aos primeiros."""
    util = largura_total - calha * (quantidade - 1)
    base, sobra = divmod(util, quantidade)
    return [base + (1 if indice < sobra else 0) for indice in range(quantidade)]


def recortar(original: Image.Image, largura: int, altura: int, painel: Painel) -> Image.Image:
    """Recorta a foto na proporcao do painel, respeitando foco e zoom, e redimensiona."""
    proporcao = largura / altura
    largura_original, altura_original = original.size
    if largura_original / altura_original > proporcao:
        altura_recorte = altura_original / painel.zoom
        largura_recorte = altura_recorte * proporcao
    else:
        largura_recorte = largura_original / painel.zoom
        altura_recorte = largura_recorte / proporcao
    esquerda = (largura_original - largura_recorte) * painel.foco[0]
    topo = (altura_original - altura_recorte) * painel.foco[1]
    caixa = (esquerda, topo, esquerda + largura_recorte, topo + altura_recorte)
    return original.resize((largura, altura), Image.Resampling.LANCZOS, box=caixa)


def dissolver_na_faixa(tela: Image.Image, banner: Banner) -> Image.Image:
    """Dissolve a borda inferior das fotos na cor da faixa, com curva suave."""
    faixa = banner.faixa
    if faixa is None or faixa.transicao == 0 or faixa.lado is not LadoDaFaixa.BASE:
        return tela
    _, _, _, altura_fotos = area_das_fotos(banner)
    inicio = altura_fotos - faixa.transicao
    coluna = Image.new("L", (1, banner.altura), 0)
    for y in range(inicio, banner.altura):
        progresso = min((y - inicio) / faixa.transicao, 1.0)
        suave = progresso * progresso * (3 - 2 * progresso)
        coluna.putpixel((0, y), round(255 * suave))
    mascara = coluna.resize(tela.size)
    camada = Image.new("RGB", tela.size, COR_FAIXA_DE_TEXTO)
    return Image.composite(camada, tela, mascara)


def montar(banner: Banner) -> Image.Image:
    cor_de_fundo = COR_CALHA if banner.faixa is None else COR_FAIXA_DE_TEXTO
    tela = Image.new("RGB", (banner.largura, banner.altura), cor_de_fundo)
    origem_x, origem_y, largura_fotos, altura_fotos = area_das_fotos(banner)
    larguras = larguras_dos_paineis(largura_fotos, len(banner.paineis), banner.calha)
    posicao_x = origem_x
    for painel, largura in zip(banner.paineis, larguras):
        with Image.open(painel.fonte) as original:
            recorte = recortar(original.convert("RGB"), largura, altura_fotos, painel)
        tela.paste(recorte, (posicao_x, origem_y))
        posicao_x += largura + banner.calha
    return dissolver_na_faixa(tela, banner)


def main() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    for banner in BANNERS:
        destino = PASTA_SAIDA / f"{banner.nome}.webp"
        montar(banner).save(destino, "WEBP", quality=QUALIDADE_WEBP, method=6)
        print(f"{destino.relative_to(RAIZ)}  {banner.largura}x{banner.altura}  {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
