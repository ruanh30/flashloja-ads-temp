"""Gera as imagens de apoio da vitrine Heish Moda Praia.

Hoje sao os atalhos de categoria exibidos em circulos na pagina inicial. Cada
imagem e descrita de forma declarativa em BANNERS e sai de uma capa de produto
ja em fundo branco: o script apenas recorta e exporta, sem retocar nem gravar
texto na imagem.

Uso:
    python3 heish-migracao/scripts/gerar_banners.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CAPAS = RAIZ / "capas-vitrine"
PASTA_SAIDA = RAIZ / "banners"

COR_CALHA = (255, 255, 255)
QUALIDADE_WEBP = 90
# As categorias aparecem em circulos de ate 96 px. 480 px cobre telas de alta densidade.
LADO_DA_BOLINHA = 480


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
class Banner:
    nome: str
    largura: int
    altura: int
    paineis: tuple[Painel, ...]
    calha: int = 0


def capa(produto: int) -> Path:
    """Capa de vitrine do produto, ja em fundo branco (ver capas_vitrine.py)."""
    return PASTA_CAPAS / f"{produto}-capa-fundo-branco.webp"


BANNERS: tuple[Banner, ...] = (
    Banner(
        nome="bolinha-biquinis",
        largura=LADO_DA_BOLINHA,
        altura=LADO_DA_BOLINHA,
        paineis=(Painel(capa(4568136), (0.50, 0.50), zoom=1.40),),
    ),
    Banner(
        nome="bolinha-maios",
        largura=LADO_DA_BOLINHA,
        altura=LADO_DA_BOLINHA,
        paineis=(Painel(capa(4191760), (0.50, 0.27), zoom=1.50),),
    ),
    Banner(
        nome="bolinha-saidas-de-praia",
        largura=LADO_DA_BOLINHA,
        altura=LADO_DA_BOLINHA,
        paineis=(Painel(capa(4567819), (0.50, 0.85), zoom=1.35),),
    ),
)


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


def montar(banner: Banner) -> Image.Image:
    tela = Image.new("RGB", (banner.largura, banner.altura), COR_CALHA)
    larguras = larguras_dos_paineis(banner.largura, len(banner.paineis), banner.calha)
    posicao_x = 0
    for painel, largura in zip(banner.paineis, larguras):
        with Image.open(painel.fonte) as original:
            recorte = recortar(original.convert("RGB"), largura, banner.altura, painel)
        tela.paste(recorte, (posicao_x, 0))
        posicao_x += largura + banner.calha
    return tela


def main() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    nomes_atuais = {f"{banner.nome}.webp" for banner in BANNERS}
    for antigo in PASTA_SAIDA.glob("*.webp"):
        if antigo.name not in nomes_atuais:
            antigo.unlink()
    for banner in BANNERS:
        destino = PASTA_SAIDA / f"{banner.nome}.webp"
        montar(banner).save(destino, "WEBP", quality=QUALIDADE_WEBP, method=6)
        print(f"{destino.relative_to(RAIZ)}  {banner.largura}x{banner.altura}  {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
