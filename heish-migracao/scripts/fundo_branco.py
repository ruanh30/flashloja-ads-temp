"""Troca o fundo das fotos de produto por branco puro, no padrao de catalogo.

Etapas por foto:
  1. Um modelo de segmentacao (BiRefNet, licenca MIT) estima a mascara do primeiro plano.
  2. As cores das bordas sao descontaminadas do fundo antigo, para nao deixar halo.
  3. O recorte e composto sobre branco e enquadrado em 3:4, sem ampliar nem retocar a foto.

O modelo nao fica no repositorio. Baixe o arquivo .onnx uma vez:
    https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx

Uso:
    python3 heish-migracao/scripts/fundo_branco.py --modelo CAMINHO.onnx            # todas as fotos
    python3 heish-migracao/scripts/fundo_branco.py --modelo CAMINHO.onnx 4568136    # um produto
    python3 heish-migracao/scripts/fundo_branco.py --modelo CAMINHO.onnx 4568136_01 # uma foto

Com --conferencia PASTA, grava uma folha por foto com original, mascara e resultado
lado a lado, para revisao visual do recorte.
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FOTOS = RAIZ / "imagens"
PASTA_SAIDA_PADRAO = RAIZ / "imagens-fundo-branco"

LADO_DO_MODELO = 1024
MEDIA_IMAGENET = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DESVIO_IMAGENET = np.array([0.229, 0.224, 0.225], dtype=np.float32)

PROPORCAO_DA_VITRINE = 3 / 4
TOLERANCIA_DE_PROPORCAO = 0.01
OPACIDADE_QUE_CONTA_COMO_PRODUTO = 0.5
MARGEM_DE_BORDA = 3

RAIO_DE_FUSAO_AMPLO = 90
RAIO_DE_FUSAO_FINO = 6
QUALIDADE_WEBP = 92
# O sufixo acompanha o arquivo ate a loja, onde distingue a versao recortada da foto original.
SUFIXO_DE_SAIDA = "-fundo-branco"
ALTURA_DA_FOLHA_DE_CONFERENCIA = 900


@dataclass(frozen=True)
class Resultado:
    arquivo: str
    largura: int
    altura: int
    cobertura: float
    segundos: float


class Segmentador:
    """Estima, para cada pixel, o quanto ele pertence ao primeiro plano (0 a 1)."""

    def __init__(self, caminho_do_modelo: Path, threads: int) -> None:
        opcoes = ort.SessionOptions()
        opcoes.intra_op_num_threads = threads
        # Sem a arena o pico de memoria cai quase pela metade, ao custo de alguns segundos por foto.
        opcoes.enable_cpu_mem_arena = False
        opcoes.enable_mem_pattern = False
        self._sessao = ort.InferenceSession(
            str(caminho_do_modelo), sess_options=opcoes, providers=["CPUExecutionProvider"]
        )
        self._nome_da_entrada = self._sessao.get_inputs()[0].name

    def mascara(self, foto: Image.Image) -> np.ndarray:
        reduzida = foto.resize((LADO_DO_MODELO, LADO_DO_MODELO), Image.Resampling.LANCZOS)
        pixels = np.asarray(reduzida, dtype=np.float32)
        pixels = pixels / max(float(pixels.max()), 1e-6)
        tensor = ((pixels - MEDIA_IMAGENET) / DESVIO_IMAGENET).transpose(2, 0, 1)[np.newaxis]
        saida = self._sessao.run(None, {self._nome_da_entrada: tensor.astype(np.float32)})[0]
        probabilidade = 1.0 / (1.0 + np.exp(-saida[0, 0]))
        minimo, maximo = float(probabilidade.min()), float(probabilidade.max())
        normalizada = (probabilidade - minimo) / max(maximo - minimo, 1e-6)
        em_8_bits = Image.fromarray((normalizada * 255).astype(np.uint8), mode="L")
        ampliada = em_8_bits.resize(foto.size, Image.Resampling.LANCZOS)
        return np.asarray(ampliada, dtype=np.float32) / 255.0


def _fundir(
    imagem: np.ndarray, primeiro_plano: np.ndarray, fundo: np.ndarray, alfa: np.ndarray, raio: int
) -> tuple[np.ndarray, np.ndarray]:
    """Um passo da estimativa de cor por fusao de desfoques (Forte e Pitie, 2021)."""
    janela = (raio, raio)
    alfa_desfocado = cv2.blur(alfa, janela)[:, :, np.newaxis]
    plano_desfocado = cv2.blur(primeiro_plano * alfa, janela) / (alfa_desfocado + 1e-5)
    fundo_desfocado = cv2.blur(fundo * (1 - alfa), janela) / ((1 - alfa_desfocado) + 1e-5)
    estimado = plano_desfocado + alfa * (imagem - alfa * plano_desfocado - (1 - alfa) * fundo_desfocado)
    return np.clip(estimado, 0.0, 1.0), fundo_desfocado


def descontaminar_bordas(imagem: np.ndarray, alfa: np.ndarray) -> np.ndarray:
    """Estima a cor real do primeiro plano nos pixels de borda, sem a tinta do fundo antigo."""
    alfa_3d = alfa[:, :, np.newaxis]
    amplo, fundo = _fundir(imagem, imagem, imagem, alfa_3d, RAIO_DE_FUSAO_AMPLO)
    fino, _ = _fundir(imagem, amplo, fundo, alfa_3d, RAIO_DE_FUSAO_FINO)
    return fino


def compor_sobre_branco(foto: Image.Image, alfa: np.ndarray) -> Image.Image:
    imagem = np.asarray(foto, dtype=np.float32) / 255.0
    primeiro_plano = descontaminar_bordas(imagem, alfa)
    alfa_3d = alfa[:, :, np.newaxis]
    composicao = primeiro_plano * alfa_3d + (1.0 - alfa_3d)
    return Image.fromarray((np.clip(composicao, 0.0, 1.0) * 255).round().astype(np.uint8), mode="RGB")


def faixa_horizontal_do_produto(alfa: np.ndarray) -> tuple[int, int] | None:
    """Primeira e ultima coluna ocupadas pelo produto, ou None se a mascara estiver vazia."""
    colunas = np.flatnonzero((alfa > OPACIDADE_QUE_CONTA_COMO_PRODUTO).any(axis=0))
    if colunas.size == 0:
        return None
    return int(colunas[0]), int(colunas[-1])


def enquadrar_para_vitrine(composicao: Image.Image, alfa: np.ndarray) -> Image.Image:
    """Leva a foto a 3:4 completando ou cortando apenas area branca nas laterais.

    Nunca amplia a foto nem corta o produto. Quando o produto encosta numa lateral
    da foto original, essa lateral continua encostada na borda, para o corte nao
    ficar solto no meio do branco. Se nao houver enquadramento seguro, devolve a
    foto como esta.
    """
    largura, altura = composicao.size
    largura_alvo = round(altura * PROPORCAO_DA_VITRINE)
    if abs(largura - largura_alvo) <= largura * TOLERANCIA_DE_PROPORCAO:
        return composicao
    faixa = faixa_horizontal_do_produto(alfa)
    if faixa is None:
        return composicao
    inicio, fim = faixa
    encosta_na_esquerda = inicio <= MARGEM_DE_BORDA
    encosta_na_direita = fim >= largura - 1 - MARGEM_DE_BORDA
    centro_do_produto = (inicio + fim) / 2

    if largura < largura_alvo:
        if encosta_na_esquerda and encosta_na_direita:
            return composicao
        if encosta_na_esquerda:
            deslocamento = 0
        elif encosta_na_direita:
            deslocamento = largura_alvo - largura
        else:
            deslocamento = round(largura_alvo / 2 - centro_do_produto)
            deslocamento = min(max(deslocamento, -inicio), largura_alvo - 1 - fim)
        tela = Image.new("RGB", (largura_alvo, altura), (255, 255, 255))
        tela.paste(composicao, (deslocamento, 0))
        return tela

    if fim - inicio + 1 > largura_alvo:
        return composicao
    esquerda = round(centro_do_produto - largura_alvo / 2)
    esquerda = min(max(esquerda, 0), largura - largura_alvo)
    return composicao.crop((esquerda, 0, esquerda + largura_alvo, altura))


def folha_de_conferencia(foto: Image.Image, alfa: np.ndarray, resultado: Image.Image) -> Image.Image:
    """Original, mascara e resultado lado a lado, na mesma altura."""
    mascara = Image.fromarray((alfa * 255).astype(np.uint8), mode="L").convert("RGB")
    paineis = []
    for painel in (foto, mascara, resultado):
        escala = ALTURA_DA_FOLHA_DE_CONFERENCIA / painel.height
        paineis.append(painel.resize((round(painel.width * escala), ALTURA_DA_FOLHA_DE_CONFERENCIA)))
    espaco = 12
    largura_total = sum(painel.width for painel in paineis) + espaco * (len(paineis) - 1)
    folha = Image.new("RGB", (largura_total, ALTURA_DA_FOLHA_DE_CONFERENCIA), (255, 0, 255))
    posicao_x = 0
    for painel in paineis:
        folha.paste(painel, (posicao_x, 0))
        posicao_x += painel.width + espaco
    return folha


def processar(
    caminho: Path, segmentador: Segmentador, pasta_saida: Path, pasta_conferencia: Path | None
) -> Resultado:
    inicio = time.monotonic()
    with Image.open(caminho) as original:
        foto = original.convert("RGB")
    alfa = segmentador.mascara(foto)
    resultado = enquadrar_para_vitrine(compor_sobre_branco(foto, alfa), alfa)
    destino = pasta_saida / f"{caminho.stem}{SUFIXO_DE_SAIDA}.webp"
    resultado.save(destino, "WEBP", quality=QUALIDADE_WEBP, method=6)
    if pasta_conferencia is not None:
        folha_de_conferencia(foto, alfa, resultado).save(
            pasta_conferencia / f"{caminho.stem}.jpg", "JPEG", quality=85
        )
    return Resultado(
        arquivo=destino.name,
        largura=resultado.width,
        altura=resultado.height,
        cobertura=float((alfa > OPACIDADE_QUE_CONTA_COMO_PRODUTO).mean()),
        segundos=time.monotonic() - inicio,
    )


def selecionar_fotos(filtros: list[str]) -> list[Path]:
    """Fotos cujo nome comeca por algum dos filtros. Sem filtros, todas."""
    todas = sorted(PASTA_FOTOS.glob("*.webp"))
    if not filtros:
        return todas
    return [foto for foto in todas if any(foto.stem.startswith(filtro) for filtro in filtros)]


def ler_argumentos() -> argparse.Namespace:
    analisador = argparse.ArgumentParser(description="Troca o fundo das fotos de produto por branco.")
    analisador.add_argument("--modelo", type=Path, required=True, help="Arquivo .onnx do BiRefNet.")
    analisador.add_argument("--saida", type=Path, default=PASTA_SAIDA_PADRAO, help="Pasta das fotos geradas.")
    analisador.add_argument("--conferencia", type=Path, default=None, help="Pasta das folhas de revisao.")
    analisador.add_argument("--threads", type=int, default=os.cpu_count() or 1, help="Threads do modelo.")
    analisador.add_argument("filtros", nargs="*", help="Id de produto ou nome de foto, sem extensao.")
    return analisador.parse_args()


def main() -> None:
    argumentos = ler_argumentos()
    fotos = selecionar_fotos(argumentos.filtros)
    if not fotos:
        raise SystemExit("Nenhuma foto corresponde aos filtros informados.")
    argumentos.saida.mkdir(parents=True, exist_ok=True)
    if argumentos.conferencia is not None:
        argumentos.conferencia.mkdir(parents=True, exist_ok=True)
    segmentador = Segmentador(argumentos.modelo, argumentos.threads)
    for caminho in fotos:
        resultado = processar(caminho, segmentador, argumentos.saida, argumentos.conferencia)
        print(
            f"{resultado.arquivo}  {resultado.largura}x{resultado.altura}  "
            f"produto {resultado.cobertura:.0%} da foto  {resultado.segundos:.1f}s",
            flush=True,
        )


if __name__ == "__main__":
    main()
