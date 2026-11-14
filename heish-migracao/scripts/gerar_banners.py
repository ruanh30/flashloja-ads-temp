"""Gera as imagens de apoio da vitrine Heish Moda Praia.

Sao o banner principal e as capas das categorias da pagina inicial. Cada imagem
e descrita de forma declarativa em BANNERS e sai das fotos originais dos
produtos: o script apenas recorta, compoe e exporta, sem retocar nem gravar
texto na imagem.

Uso:
    python3 heish-migracao/scripts/gerar_banners.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FOTOS = RAIZ / "imagens"
PASTA_SAIDA = RAIZ / "banners"

COR_CALHA = (255, 255, 255)
QUALIDADE_WEBP = 90
# Capas de categoria em 4:5, a mesma proporcao das fotos da vitrine.
LARGURA_DA_CATEGORIA = 960
ALTURA_DA_CATEGORIA = 1200


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


def foto(nome: str) -> Path:
    """Foto original do produto, como veio da FacilZap."""
    return PASTA_FOTOS / f"{nome}.webp"


BANNERS: tuple[Banner, ...] = (
    Banner(
        nome="heish-banner-sirena-computador",
        largura=2400,
        altura=1200,
        calha=4,
        paineis=(
            Painel(foto("4568136_01"), (0.50, 0.28)),
            Painel(foto("4568136_02"), (0.50, 0.28)),
            Painel(foto("4568136_03"), (0.50, 0.28)),
        ),
    ),
    Banner(
        nome="heish-banner-sirena-celular",
        largura=1080,
        altura=1350,
        paineis=(Painel(foto("4568136_01"), (0.50, 0.30)),),
    ),
    Banner(
        nome="heish-categoria-biquinis",
        largura=LARGURA_DA_CATEGORIA,
        altura=ALTURA_DA_CATEGORIA,
        paineis=(Painel(foto("4568066_01"), (0.50, 0.30)),),
    ),
    Banner(
        nome="heish-categoria-maios",
        largura=LARGURA_DA_CATEGORIA,
        altura=ALTURA_DA_CATEGORIA,
        paineis=(Painel(foto("4191760_01"), (0.50, 0.60), zoom=1.15),),
    ),
    Banner(
        nome="heish-categoria-saidas-de-praia",
        largura=LARGURA_DA_CATEGORIA,
        altura=ALTURA_DA_CATEGORIA,
        paineis=(Painel(foto("4567819_02"), (0.0, 0.50), zoom=1.14),),
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
