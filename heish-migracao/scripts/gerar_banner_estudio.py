"""Gera o banner principal da Heish no padrao de estudio da Insider.

Referencia fiel: o banner da pagina inicial da insiderstore.com.br.
  - Fonte: Manrope (licenca aberta OFL), a mesma do site de referencia. Titulo em
    ExtraBold com letras apertadas e traco levemente engrossado; apoio em ExtraBold
    e Medium.
  - Fundo: degrade de estudio azul acinzentado, escuro no topo e claro na base,
    com a faixa azul no rodape. As cores foram medidas no banner de referencia e
    estao descritas em tabelas neste arquivo; nenhuma imagem de terceiros e usada.

A modelo vem da foto original do produto, recortada com transparencia pelo mesmo
segmentador de scripts/fundo_branco.py. O recorte fica salvo em banner-estudio/,
entao o modelo de segmentacao so e necessario na primeira vez. A unica correcao
na foto e um ajuste leve de cor, para aproximar a luz da praia da luz do estudio.

O botao de compra nao faz parte da imagem: e um bloco do tema, posicionado sobre
a faixa azul, que por isso fica livre de texto.

As medidas de cada banner estao em pixels do banner de referencia (1920x920 no
computador e 750x1026 no celular). A imagem final sai ampliada por ESCALA_DE_SAIDA.

As fontes usadas (Manrope-500.ttf e Manrope-800.ttf) ficam em fontes/, junto com a
licenca. A loja nao usa esses arquivos: la a Manrope vem da biblioteca da Shopify.

Uso:
    python3 heish-migracao/scripts/gerar_banner_estudio.py
    python3 heish-migracao/scripts/gerar_banner_estudio.py --modelo CAMINHO.onnx
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FOTOS = RAIZ / "imagens"
PASTA_SAIDA = RAIZ / "banner-estudio"
PASTA_FONTES = RAIZ / "fontes"

ESCALA_DE_SAIDA = 1.5
QUALIDADE_WEBP = 88
BRANCO = (255, 255, 255)
PESO_DO_TITULO = 800
PESO_DE_APOIO = 500
# Medidos por comparacao de pixels com o titulo do banner de referencia.
TRACKING_DO_TITULO = -0.055
TRACO_DO_TITULO = 0.006
TRACKING_DO_SUBTITULO = -0.035
# As letras apertadas do titulo fecham tambem o espaco entre palavras; este valor o devolve.
ESPACO_ENTRE_PALAVRAS_DO_TITULO = 0.17
RUIDO_DO_FUNDO = 1.2
# Ajuste leve de cor da modelo: um pouco menos de saturacao e de vermelho.
SATURACAO_DA_MODELO = 0.93
GANHOS_DA_MODELO = (0.97, 0.985, 1.0)

Cor = tuple[int, int, int]
Alinhamento = Literal["esquerda", "centro", "direita"]


@dataclass(frozen=True)
class Fundo:
    """Degrade do estudio.

    linhas traz, para cada altura (0 no topo, 1 na base), a cor na borda esquerda e
    na borda direita. forma diz como a cor caminha de uma borda a outra: 0 e a cor da
    esquerda, 1 a da direita, e valores negativos escurecem alem da borda esquerda.
    """

    linhas: tuple[tuple[float, Cor, Cor], ...]
    forma: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Faixa:
    """Faixa azul do rodape: multiplica cada canal da imagem que esta por baixo.

    Fica livre de texto porque e a area do botao, que e um bloco do tema e nao da imagem.
    """

    topo: int
    fatores: tuple[float, float, float]


@dataclass(frozen=True)
class Modelo:
    foto: str
    escala: float
    topo_da_cabeca: int
    centro_x: int


@dataclass(frozen=True)
class Bloco:
    """Linhas de texto em caixa alta. topo e o topo das maiusculas da primeira linha."""

    linhas: tuple[str, ...]
    tamanho: int
    x: int
    topo: int
    alinhamento: Alinhamento
    entrelinha: float = 1.0
    tracking: float = TRACKING_DO_SUBTITULO
    traco: float = 0.0
    espaco_entre_palavras: float = 0.0
    atras_da_modelo: bool = False


@dataclass(frozen=True)
class Pilula:
    texto: str
    tamanho: int
    x: int
    topo: int
    altura: int
    alinhamento: Alinhamento
    folga_lateral: int = 24


@dataclass(frozen=True)
class Banner:
    nome: str
    largura: int
    altura: int
    fundo: Fundo
    faixa: Faixa
    modelo: Modelo
    blocos: tuple[Bloco, ...]
    pilula: Pilula


FUNDO_COMPUTADOR = Fundo(
    linhas=(
        (0.0000, (18, 38, 44), (37, 53, 62)),
        (0.0778, (23, 40, 47), (42, 58, 67)),
        (0.1555, (31, 46, 55), (49, 66, 75)),
        (0.2333, (39, 53, 65), (58, 75, 84)),
        (0.3111, (49, 64, 75), (73, 91, 101)),
        (0.3888, (63, 78, 90), (89, 106, 117)),
        (0.4666, (83, 98, 110), (103, 119, 130)),
        (0.5444, (98, 114, 125), (117, 133, 143)),
        (0.6221, (114, 130, 139), (131, 147, 155)),
        (0.6999, (136, 151, 159), (150, 164, 171)),
        (0.7777, (154, 167, 174), (165, 180, 184)),
        (0.8554, (165, 180, 183), (180, 194, 195)),
        (1.0000, (186, 204, 200), (208, 220, 216)),
    ),
    forma=(
        (0.00, 0.00), (0.06, -0.04), (0.125, -0.11), (0.19, -0.16), (0.245, -0.20),
        (0.57, 0.37), (0.70, 0.42), (0.78, 0.48), (0.86, 0.60), (0.93, 0.80), (1.00, 1.00),
    ),
)

FUNDO_CELULAR = Fundo(
    linhas=(
        (0.0000, (16, 37, 44), (34, 51, 59)),
        (0.0786, (17, 38, 43), (37, 53, 61)),
        (0.1572, (20, 39, 46), (40, 56, 65)),
        (0.2358, (27, 43, 52), (46, 62, 71)),
        (0.3144, (37, 50, 61), (53, 71, 79)),
        (0.3930, (44, 58, 70), (66, 83, 93)),
        (0.4716, (54, 69, 81), (83, 101, 112)),
        (0.5502, (68, 84, 95), (97, 113, 123)),
        (0.6287, (86, 103, 115), (109, 125, 136)),
        (0.7073, (102, 118, 130), (120, 137, 146)),
        (0.7859, (117, 132, 141), (140, 153, 161)),
        (0.8645, (132, 146, 154), (152, 166, 173)),
        (1.0000, (158, 170, 176), (173, 188, 194)),
    ),
    forma=((0.00, 0.00), (0.08, 0.00), (0.30, 0.45), (0.60, 0.62), (0.72, 0.88), (0.91, 0.95), (1.00, 1.00)),
)

FAIXA_COMPUTADOR = Faixa(topo=795, fatores=(0.0, 0.70, 1.10))
FAIXA_CELULAR = Faixa(topo=852, fatores=(0.0, 0.62, 0.99))
AVISO_DE_ENVIO = "ENVIAMOS PARA TODO O BRASIL"


def titulo(linhas: tuple[str, ...], tamanho: int, x: int, topo: int, alinhamento: Alinhamento, **opcoes: bool | float) -> Bloco:
    """Bloco no estilo do titulo da referencia: letras apertadas e traco engrossado."""
    return Bloco(
        linhas, tamanho, x, topo, alinhamento, tracking=TRACKING_DO_TITULO, traco=TRACO_DO_TITULO,
        espaco_entre_palavras=ESPACO_ENTRE_PALAVRAS_DO_TITULO, **opcoes,
    )


BANNERS: tuple[Banner, ...] = (
    Banner(
        nome="heish-banner-sirena-estudio-computador",
        largura=1920,
        altura=920,
        fundo=FUNDO_COMPUTADOR,
        faixa=FAIXA_COMPUTADOR,
        modelo=Modelo(foto="4568136_02", escala=0.905, topo_da_cabeca=58, centro_x=991),
        blocos=(
            titulo(("BIQUÍNI",), 190, 155, 322, "esquerda", atras_da_modelo=True),
            titulo(("SIRENA",), 190, 1829, 322, "direita", atras_da_modelo=True),
            Bloco(("4 CORES", "POR R$ 60"), 53, 1782, 512, "direita", entrelinha=1.02),
        ),
        pilula=Pilula(AVISO_DE_ENVIO, 22, 1782, 624, 47, "direita"),
    ),
    Banner(
        nome="heish-banner-sirena-estudio-celular",
        largura=750,
        altura=1026,
        fundo=FUNDO_CELULAR,
        faixa=FAIXA_CELULAR,
        modelo=Modelo(foto="4568136_02", escala=0.96, topo_da_cabeca=28, centro_x=188),
        blocos=(
            titulo(("BIQUÍNI", "SIRENA"), 118, 690, 72, "direita", entrelinha=0.86),
            Bloco(("4 CORES", "POR R$ 60"), 42, 690, 296, "direita", entrelinha=1.02),
        ),
        pilula=Pilula(AVISO_DE_ENVIO, 16, 690, 388, 38, "direita", folga_lateral=18),
    ),
    Banner(
        nome="heish-banner-kit-capri-estudio-computador",
        largura=1920,
        altura=920,
        fundo=FUNDO_COMPUTADOR,
        faixa=FAIXA_COMPUTADOR,
        modelo=Modelo(foto="4611471_01", escala=0.72, topo_da_cabeca=58, centro_x=808),
        blocos=(
            titulo(("KIT",), 212, 588, 316, "direita", atras_da_modelo=True),
            titulo(("CAPRI",), 212, 1046, 316, "esquerda", atras_da_modelo=True),
            Bloco(("BIQUÍNI + CALÇA", "POR R$ 159,90"), 53, 1594, 512, "direita", entrelinha=1.02),
        ),
        pilula=Pilula(AVISO_DE_ENVIO, 22, 1594, 624, 47, "direita"),
    ),
    Banner(
        nome="heish-banner-kit-capri-estudio-celular",
        largura=750,
        altura=1026,
        fundo=FUNDO_CELULAR,
        faixa=FAIXA_CELULAR,
        modelo=Modelo(foto="4611471_01", escala=0.64, topo_da_cabeca=322, centro_x=375),
        blocos=(
            titulo(("KIT CAPRI",), 118, 375, 64, "centro"),
            Bloco(("BIQUÍNI + CALÇA", "POR R$ 159,90"), 40, 375, 180, "centro", entrelinha=1.02),
        ),
        pilula=Pilula(AVISO_DE_ENVIO, 16, 375, 272, 38, "centro", folga_lateral=18),
    ),
)


def em_saida(valor: float) -> int:
    return round(valor * ESCALA_DE_SAIDA)


def construir_fundo(banner: Banner) -> np.ndarray:
    largura, altura = em_saida(banner.largura), em_saida(banner.altura)
    alturas = np.array([linha[0] for linha in banner.fundo.linhas])
    esquerda = np.array([linha[1] for linha in banner.fundo.linhas], dtype=np.float32)
    direita = np.array([linha[2] for linha in banner.fundo.linhas], dtype=np.float32)
    v = np.linspace(0.0, 1.0, altura)
    u = np.linspace(0.0, 1.0, largura)
    cor_esquerda = np.stack([np.interp(v, alturas, esquerda[:, canal]) for canal in range(3)], axis=1)
    cor_direita = np.stack([np.interp(v, alturas, direita[:, canal]) for canal in range(3)], axis=1)
    forma = np.interp(u, [p[0] for p in banner.fundo.forma], [p[1] for p in banner.fundo.forma])
    fundo = cor_esquerda[:, np.newaxis, :] + (cor_direita - cor_esquerda)[:, np.newaxis, :] * forma[np.newaxis, :, np.newaxis]
    # O desfoque tira as quinas da interpolacao e o ruido fino evita degraus no degrade.
    janela = em_saida(120) | 1
    fundo = cv2.GaussianBlur(fundo.astype(np.float32), (janela, janela), 0, borderType=cv2.BORDER_REPLICATE)
    ruido = np.random.default_rng(7).normal(0.0, RUIDO_DO_FUNDO, fundo.shape[:2])[:, :, np.newaxis]
    return np.clip(fundo + ruido, 0, 255)


def caminho_do_recorte(foto: str) -> Path:
    return PASTA_SAIDA / f"recorte-{foto}.png"


def criar_recorte(foto: str, caminho_do_modelo: Path) -> None:
    """Recorta a modelo com transparencia usando o segmentador de fundo_branco.py."""
    from fundo_branco import Segmentador, descontaminar_bordas

    original = Image.open(PASTA_FOTOS / f"{foto}.webp").convert("RGB")
    alfa = Segmentador(caminho_do_modelo, threads=4).mascara(original)
    cor = descontaminar_bordas(np.asarray(original, dtype=np.float32) / 255.0, alfa)
    rgba = np.clip(np.dstack([cor, alfa]), 0.0, 1.0)
    Image.fromarray((rgba * 255).round().astype(np.uint8), mode="RGBA").save(caminho_do_recorte(foto))


def eixo_do_corpo(alfa: np.ndarray) -> float:
    """Coluna central do tronco, medida na faixa entre os ombros e a cintura."""
    linhas = np.flatnonzero((alfa > 128).any(axis=1))
    topo, base = int(linhas[0]), int(linhas[-1])
    tronco = alfa[topo + (base - topo) * 22 // 100 : topo + (base - topo) * 45 // 100] > 128
    colunas = np.flatnonzero(tronco.sum(axis=0) > tronco.shape[0] * 0.8)
    return float(colunas[0] + colunas[-1]) / 2


def integrar_ao_estudio(recorte: Image.Image) -> Image.Image:
    """Aproxima a foto de praia da luz fria do estudio, sem alterar a cor do produto de forma visivel."""
    pixels = np.asarray(recorte, dtype=np.float32)
    cor, alfa = pixels[:, :, :3], pixels[:, :, 3:]
    cinza = cor.mean(axis=2, keepdims=True)
    cor = (cinza + (cor - cinza) * SATURACAO_DA_MODELO) * np.array(GANHOS_DA_MODELO, dtype=np.float32)
    return Image.fromarray(np.dstack([np.clip(cor, 0, 255), alfa]).round().astype(np.uint8), mode="RGBA")


def camada_da_modelo(banner: Banner) -> Image.Image:
    recorte = integrar_ao_estudio(Image.open(caminho_do_recorte(banner.modelo.foto)).convert("RGBA"))
    alfa = np.asarray(recorte)[:, :, 3]
    topo_da_cabeca = int(np.flatnonzero((alfa > 128).any(axis=1))[0])
    escala = banner.modelo.escala * ESCALA_DE_SAIDA
    ampliada = recorte.resize((round(recorte.width * escala), round(recorte.height * escala)), Image.Resampling.LANCZOS)
    camada = Image.new("RGBA", (em_saida(banner.largura), em_saida(banner.altura)), (0, 0, 0, 0))
    origem_x = em_saida(banner.modelo.centro_x) - round(eixo_do_corpo(alfa) * escala)
    origem_y = em_saida(banner.modelo.topo_da_cabeca) - round(topo_da_cabeca * escala)
    # A camada esta vazia, entao colar copia cor e transparencia; o que passa da tela e cortado.
    camada.paste(ampliada, (origem_x, origem_y))
    return camada


class Fontes:
    def __init__(self, pasta: Path) -> None:
        self._pasta = pasta
        self._cache: dict[tuple[int, int], ImageFont.FreeTypeFont] = {}

    def obter(self, peso: int, tamanho: int) -> ImageFont.FreeTypeFont:
        chave = (peso, tamanho)
        if chave not in self._cache:
            self._cache[chave] = ImageFont.truetype(str(self._pasta / f"Manrope-{peso}.ttf"), tamanho)
        return self._cache[chave]


def posicoes_das_letras(
    fonte: ImageFont.FreeTypeFont, texto: str, tracking: float, espaco_extra: float = 0.0
) -> tuple[list[float], float]:
    """Posicao de cada letra, com o kerning da fonte e o tracking pedido, e a largura total.

    espaco_extra e somado a cada espaco entre palavras.
    """
    posicoes: list[float] = []
    cursor = 0.0
    for indice, letra in enumerate(texto):
        posicoes.append(cursor)
        proxima = texto[indice + 1 : indice + 2]
        avanco = fonte.getlength(letra + proxima) - fonte.getlength(proxima) if proxima else fonte.getlength(letra)
        cursor += avanco + tracking + (espaco_extra if letra == " " else 0.0)
    return posicoes, cursor - tracking


def escrever_linha(
    desenho: ImageDraw.ImageDraw,
    fonte: ImageFont.FreeTypeFont,
    texto: str,
    x: float,
    linha_de_base: float,
    alinhamento: Alinhamento,
    tracking: float,
    traco: int,
    cor: tuple[int, int, int, int],
    espaco_extra: float = 0.0,
) -> None:
    posicoes, largura = posicoes_das_letras(fonte, texto, tracking, espaco_extra)
    inicio = {"esquerda": x, "centro": x - largura / 2, "direita": x - largura}[alinhamento]
    for letra, posicao in zip(texto, posicoes):
        desenho.text((inicio + posicao, linha_de_base), letra, font=fonte, fill=cor, anchor="ls", stroke_width=traco, stroke_fill=cor)


def altura_das_maiusculas(fonte: ImageFont.FreeTypeFont) -> int:
    return -fonte.getbbox("H", anchor="ls")[1]


def desenhar_bloco(camada: Image.Image, bloco: Bloco, fontes: Fontes) -> None:
    tamanho = em_saida(bloco.tamanho)
    fonte = fontes.obter(PESO_DO_TITULO, tamanho)
    desenho = ImageDraw.Draw(camada)
    linha_de_base = em_saida(bloco.topo) + altura_das_maiusculas(fonte)
    for linha in bloco.linhas:
        escrever_linha(
            desenho, fonte, linha, em_saida(bloco.x), linha_de_base, bloco.alinhamento,
            bloco.tracking * tamanho, round(bloco.traco * tamanho), (*BRANCO, 255),
            bloco.espaco_entre_palavras * tamanho,
        )
        linha_de_base += round(tamanho * bloco.entrelinha)


def desenhar_pilula(camada: Image.Image, pilula: Pilula, fontes: Fontes) -> None:
    fonte = fontes.obter(PESO_DE_APOIO, em_saida(pilula.tamanho))
    tracking = 0.02 * em_saida(pilula.tamanho)
    _, largura_do_texto = posicoes_das_letras(fonte, pilula.texto, tracking)
    largura = largura_do_texto + 2 * em_saida(pilula.folga_lateral)
    altura = em_saida(pilula.altura)
    x = em_saida(pilula.x)
    esquerda = {"esquerda": x, "centro": x - largura / 2, "direita": x - largura}[pilula.alinhamento]
    topo = em_saida(pilula.topo)
    desenho = ImageDraw.Draw(camada)
    desenho.rounded_rectangle(
        (esquerda, topo, esquerda + largura, topo + altura), radius=altura / 2,
        fill=(*BRANCO, 26), outline=(*BRANCO, 200), width=max(1, em_saida(1.2)),
    )
    linha_de_base = topo + (altura + altura_das_maiusculas(fonte)) / 2
    escrever_linha(
        desenho, fonte, pilula.texto, esquerda + em_saida(pilula.folga_lateral), linha_de_base,
        "esquerda", tracking, 0, (*BRANCO, 255),
    )


def aplicar_faixa(imagem: np.ndarray, faixa: Faixa) -> np.ndarray:
    topo = em_saida(faixa.topo)
    imagem[topo:] = np.clip(imagem[topo:] * np.array(faixa.fatores, dtype=np.float32), 0, 255)
    return imagem


def compor(tela: Image.Image, camada: Image.Image) -> Image.Image:
    return Image.alpha_composite(tela, camada)


def montar(banner: Banner, fontes: Fontes) -> Image.Image:
    tamanho = (em_saida(banner.largura), em_saida(banner.altura))
    tela = Image.fromarray(construir_fundo(banner).round().astype(np.uint8), mode="RGB").convert("RGBA")

    atras = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    frente = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    for bloco in banner.blocos:
        desenhar_bloco(atras if bloco.atras_da_modelo else frente, bloco, fontes)
    desenhar_pilula(frente, banner.pilula, fontes)

    tela = compor(tela, atras)
    tela = compor(tela, camada_da_modelo(banner))
    tela = compor(tela, frente)

    com_faixa = aplicar_faixa(np.asarray(tela.convert("RGB"), dtype=np.float32).copy(), banner.faixa)
    return Image.fromarray(com_faixa.round().astype(np.uint8), mode="RGB")


def ler_argumentos() -> argparse.Namespace:
    leitor = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    leitor.add_argument("--fontes", type=Path, default=PASTA_FONTES, help="pasta com Manrope-500.ttf e Manrope-800.ttf")
    leitor.add_argument("--modelo", type=Path, help="arquivo .onnx do BiRefNet, so para criar um recorte que ainda nao existe")
    return leitor.parse_args()


def main() -> None:
    argumentos = ler_argumentos()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    fontes = Fontes(argumentos.fontes)
    for foto in sorted({banner.modelo.foto for banner in BANNERS}):
        if caminho_do_recorte(foto).exists():
            continue
        if argumentos.modelo is None:
            raise SystemExit(f"Falta o recorte de {foto}. Rode de novo com --modelo CAMINHO.onnx.")
        criar_recorte(foto, argumentos.modelo)
    for banner in BANNERS:
        destino = PASTA_SAIDA / f"{banner.nome}.webp"
        imagem = montar(banner, fontes)
        imagem.save(destino, "WEBP", quality=QUALIDADE_WEBP, method=6)
        print(f"{destino.relative_to(RAIZ)}  {imagem.width}x{imagem.height}  {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
