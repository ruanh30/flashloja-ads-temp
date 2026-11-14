"""Exporta o catalogo da Heish para o formato de importacao de produtos da Shopify.

Entradas, todas extraidas da FacilZap:
  --catalogo   catalogo normalizado (produtos, variantes, estoque, peso e medidas)
  --facilzap   resposta bruta da API de produtos, de onde saem os precos por catalogo
  --manifesto  relacao entre cada produto e os arquivos das fotos originais

Saidas, gravadas em --saida:
  heish-produtos-shopify.csv        arquivo para Produtos > Importar, no painel da Shopify
  heish-dados-complementares.csv    o que a Shopify nao tem campo proprio para guardar:
                                    preco do segundo catalogo e medidas da embalagem

As fotos sao referenciadas por URL publica. Ao importar, a Shopify copia cada
foto para o proprio servidor, entao a loja nao depende dessas URLs depois.

Uso:
    python3 heish-migracao/scripts/exportar_shopify.py \\
        --catalogo CATALOGO.json --facilzap PRODUTOS.json --manifesto MANIFESTO.json \\
        --base-imagens https://.../heish-migracao/imagens --saida PASTA
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MARCA = "Heish Moda Praia"
CATALOGO_DE_VAREJO = 0
OPCAO_COR = "Cor"
OPCAO_TAMANHO = "Tamanho"

# Nome da categoria na FacilZap -> tipo de produto na Shopify.
TIPO_POR_CATEGORIA: dict[str, str] = {
    "BIQUÍNIS": "Biquínis",
    "Maiô": "Maiôs",
    "SAÍDAS": "Saídas de Praia",
}

COLUNAS_SHOPIFY: tuple[str, ...] = (
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Type",
    "Tags",
    "Published",
    "Option1 Name",
    "Option1 Value",
    "Option2 Name",
    "Option2 Value",
    "Variant SKU",
    "Variant Grams",
    "Variant Inventory Tracker",
    "Variant Inventory Qty",
    "Variant Inventory Policy",
    "Variant Fulfillment Service",
    "Variant Price",
    "Variant Compare At Price",
    "Variant Requires Shipping",
    "Variant Taxable",
    "Image Src",
    "Image Position",
    "Image Alt Text",
    "Gift Card",
    "Variant Weight Unit",
    "Status",
)

COLUNAS_COMPLEMENTARES: tuple[str, ...] = (
    "Handle",
    "Produto",
    "Preco de varejo",
    "Preco promocional",
    "Preco do segundo catalogo",
    "Peso (g)",
    "Comprimento (cm)",
    "Largura (cm)",
    "Altura (cm)",
)


@dataclass(frozen=True)
class Precos:
    """Precos de um produto nos catalogos da FacilZap."""

    varejo: float
    promocional: float | None
    segundo_catalogo: float | None

    @property
    def de_venda(self) -> float:
        return self.promocional if self.promocional is not None else self.varejo

    @property
    def de_comparacao(self) -> float | None:
        return self.varejo if self.promocional is not None else None


@dataclass(frozen=True)
class Resumo:
    produtos: int
    variantes: int
    unidades: int
    fotos: int
    em_promocao: int


def ler_json(caminho: Path) -> Any:
    return json.loads(caminho.read_text(encoding="utf-8"))


def criar_handle(nome: str) -> str:
    """Identificador de URL: minusculas, sem acentos, palavras separadas por hifen."""
    sem_acentos = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", sem_acentos.lower()).strip("-")


def formatar_preco(valor: float | None) -> str:
    return "" if valor is None else f"{valor:.2f}"


def produtos_brutos(resposta: Any) -> list[dict[str, Any]]:
    """A API devolve a lista direta ou dentro de 'data'. Aceita os dois formatos."""
    if isinstance(resposta, list):
        return resposta
    return list(resposta.get("data") or resposta.get("produtos") or [])


def ler_precos(resposta: Any) -> dict[int, Precos]:
    """Precos de cada produto: varejo, promocional ativo e segundo catalogo, se houver."""
    precos: dict[int, Precos] = {}
    for produto in produtos_brutos(resposta):
        varejo: float | None = None
        promocional: float | None = None
        segundo: float | None = None
        for catalogo in produto.get("catalogos", []):
            if not catalogo.get("ativado"):
                continue
            tabela = catalogo.get("precos") or {}
            if catalogo.get("id") == CATALOGO_DE_VAREJO:
                varejo = float(tabela["preco"])
                promocao = tabela.get("promocional") or {}
                if promocao.get("ativado") and promocao.get("preco"):
                    promocional = float(promocao["preco"])
            elif segundo is None and tabela.get("preco") is not None:
                segundo = float(tabela["preco"])
        if varejo is None:
            raise ValueError(f"Produto {produto.get('id')} sem preco no catalogo de varejo.")
        precos[int(produto["id"])] = Precos(varejo, promocional, segundo)
    return precos


def fotos_por_produto(manifesto: list[dict[str, Any]]) -> dict[int, list[str]]:
    """Arquivos de foto de cada produto, na ordem em que aparecem na FacilZap."""
    fotos: dict[int, list[tuple[int, str]]] = {}
    for item in manifesto:
        if item.get("ok"):
            fotos.setdefault(int(item["facilzap_id"]), []).append((int(item["posicao"]), item["arquivo"]))
    return {produto: [arquivo for _, arquivo in sorted(lista)] for produto, lista in fotos.items()}


def etiquetas(produto: dict[str, Any], tipos: list[str]) -> str:
    palavras = produto.get("keywords") or []
    if isinstance(palavras, str):
        palavras = [parte.strip() for parte in palavras.split(",")]
    unicas = list(dict.fromkeys([*tipos, *(palavra for palavra in palavras if palavra)]))
    return ", ".join(unicas)


def opcoes_do_produto(variantes: list[dict[str, Any]]) -> tuple[str, ...]:
    """Nomes das opcoes do produto. Todas as variantes precisam usar as mesmas."""
    tem_cor = [bool(variante.get("cor")) for variante in variantes]
    tem_tamanho = [bool(variante.get("tamanho")) for variante in variantes]
    if any(tem_cor) != all(tem_cor) or any(tem_tamanho) != all(tem_tamanho):
        raise ValueError("Variantes do mesmo produto com opcoes diferentes.")
    nomes = ([OPCAO_COR] if all(tem_cor) else []) + ([OPCAO_TAMANHO] if all(tem_tamanho) else [])
    if not nomes:
        raise ValueError("Produto com variantes sem cor e sem tamanho.")
    return tuple(nomes)


def valores_das_opcoes(variante: dict[str, Any], opcoes: tuple[str, ...]) -> list[str]:
    valor_por_opcao = {OPCAO_COR: variante.get("cor"), OPCAO_TAMANHO: variante.get("tamanho")}
    return [str(valor_por_opcao[opcao]) for opcao in opcoes]


def linhas_do_produto(
    produto: dict[str, Any], precos: Precos, fotos: list[str], base_imagens: str
) -> list[dict[str, str]]:
    """Linhas do CSV: a primeira leva os dados do produto, as demais variantes e fotos."""
    handle = criar_handle(produto["nome"])
    variantes = [variante for variante in produto["variantes"] if variante.get("ativa")]
    opcoes = opcoes_do_produto(variantes)
    tipos = [TIPO_POR_CATEGORIA[categoria] for categoria in produto["categorias"]]
    linhas: list[dict[str, str]] = []
    for indice in range(max(len(variantes), len(fotos))):
        linha = {coluna: "" for coluna in COLUNAS_SHOPIFY}
        linha["Handle"] = handle
        if indice == 0:
            linha.update(
                {
                    "Title": produto["nome"],
                    "Body (HTML)": produto.get("descricao_html") or "",
                    "Vendor": MARCA,
                    "Type": tipos[0],
                    "Tags": etiquetas(produto, tipos),
                    "Published": "TRUE",
                    "Gift Card": "FALSE",
                    "Status": "active",
                }
            )
        if indice < len(variantes):
            variante = variantes[indice]
            valores = valores_das_opcoes(variante, opcoes)
            linha["Option1 Value"] = valores[0]
            if indice == 0:
                linha["Option1 Name"] = opcoes[0]
            if len(opcoes) > 1:
                linha["Option2 Value"] = valores[1]
                if indice == 0:
                    linha["Option2 Name"] = opcoes[1]
            linha.update(
                {
                    "Variant SKU": variante.get("sku") or "",
                    "Variant Grams": str(int(produto["peso_g"])),
                    "Variant Inventory Tracker": "shopify",
                    "Variant Inventory Qty": str(int(variante.get("estoque") or 0)),
                    "Variant Inventory Policy": "deny",
                    "Variant Fulfillment Service": "manual",
                    "Variant Price": formatar_preco(precos.de_venda),
                    "Variant Compare At Price": formatar_preco(precos.de_comparacao),
                    "Variant Requires Shipping": "TRUE",
                    "Variant Taxable": "TRUE",
                    "Variant Weight Unit": "g",
                }
            )
        if indice < len(fotos):
            linha.update(
                {
                    "Image Src": f"{base_imagens.rstrip('/')}/{fotos[indice]}",
                    "Image Position": str(indice + 1),
                    "Image Alt Text": produto["nome"],
                }
            )
        linhas.append(linha)
    return linhas


def linha_complementar(produto: dict[str, Any], precos: Precos) -> dict[str, str]:
    return {
        "Handle": criar_handle(produto["nome"]),
        "Produto": produto["nome"],
        "Preco de varejo": formatar_preco(precos.varejo),
        "Preco promocional": formatar_preco(precos.promocional),
        "Preco do segundo catalogo": formatar_preco(precos.segundo_catalogo),
        "Peso (g)": str(int(produto["peso_g"])),
        "Comprimento (cm)": str(produto.get("comprimento_cm") or ""),
        "Largura (cm)": str(produto.get("largura_cm") or ""),
        "Altura (cm)": str(produto.get("altura_cm") or ""),
    }


def gravar_csv(caminho: Path, colunas: tuple[str, ...], linhas: list[dict[str, str]]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def exportar(
    catalogo: list[dict[str, Any]],
    precos: dict[int, Precos],
    fotos: dict[int, list[str]],
    base_imagens: str,
    pasta_saida: Path,
) -> Resumo:
    linhas_shopify: list[dict[str, str]] = []
    linhas_complementares: list[dict[str, str]] = []
    handles: set[str] = set()
    for produto in catalogo:
        if not produto.get("ativo"):
            continue
        identificador = int(produto["id"])
        handle = criar_handle(produto["nome"])
        if handle in handles:
            raise ValueError(f"Dois produtos geram o mesmo handle: {handle}.")
        handles.add(handle)
        linhas_shopify += linhas_do_produto(
            produto, precos[identificador], fotos.get(identificador, []), base_imagens
        )
        linhas_complementares.append(linha_complementar(produto, precos[identificador]))
    pasta_saida.mkdir(parents=True, exist_ok=True)
    gravar_csv(pasta_saida / "heish-produtos-shopify.csv", COLUNAS_SHOPIFY, linhas_shopify)
    gravar_csv(pasta_saida / "heish-dados-complementares.csv", COLUNAS_COMPLEMENTARES, linhas_complementares)
    return Resumo(
        produtos=len(handles),
        variantes=sum(1 for linha in linhas_shopify if linha["Variant Price"]),
        unidades=sum(int(linha["Variant Inventory Qty"] or 0) for linha in linhas_shopify),
        fotos=sum(1 for linha in linhas_shopify if linha["Image Src"]),
        em_promocao=sum(1 for linha in linhas_complementares if linha["Preco promocional"]),
    )


def ler_argumentos() -> argparse.Namespace:
    analisador = argparse.ArgumentParser(description="Exporta o catalogo da Heish para a Shopify.")
    analisador.add_argument("--catalogo", type=Path, required=True)
    analisador.add_argument("--facilzap", type=Path, required=True)
    analisador.add_argument("--manifesto", type=Path, required=True)
    analisador.add_argument("--base-imagens", required=True, help="URL publica da pasta das fotos.")
    analisador.add_argument("--saida", type=Path, required=True)
    return analisador.parse_args()


def main() -> None:
    argumentos = ler_argumentos()
    resumo = exportar(
        catalogo=ler_json(argumentos.catalogo),
        precos=ler_precos(ler_json(argumentos.facilzap)),
        fotos=fotos_por_produto(ler_json(argumentos.manifesto)),
        base_imagens=argumentos.base_imagens,
        pasta_saida=argumentos.saida,
    )
    print(
        f"{resumo.produtos} produtos, {resumo.variantes} variantes, {resumo.unidades} unidades em estoque, "
        f"{resumo.fotos} fotos, {resumo.em_promocao} produtos em promocao"
    )


if __name__ == "__main__":
    main()
