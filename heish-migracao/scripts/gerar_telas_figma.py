"""Gera a replica estatica da pagina inicial da Heish para levar ao Figma.

O documento e autossuficiente: fontes e imagens vao embutidas em base64. Ele
repete, em HTML e CSS simples, o que esta salvo no tema Horizon da Shopify, em
duas telas lado a lado: computador (1440px) e celular (390px).

Uso:
    npm pack @fontsource/poppins@5.1.0 && tar -xzf fontsource-poppins-5.1.0.tgz
    python3 heish-migracao/scripts/gerar_telas_figma.py heish-migracao package/files heish-home.html
"""

from __future__ import annotations

import base64
import io
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path

from PIL import Image

QUALIDADE_JPEG = 84


@dataclass(frozen=True)
class Produto:
    foto: str
    nome: str
    preco: str
    preco_de: str | None = None


@dataclass(frozen=True)
class Categoria:
    arquivo: str
    nome: str


@dataclass(frozen=True)
class Tela:
    """Medidas que mudam entre computador e celular."""

    variante: str
    largura: int
    banner: str
    banner_tamanho: tuple[int, int]
    largura_cartao_categoria: int
    largura_cartao_produto: int


PRODUTOS: tuple[Produto, ...] = (
    Produto("4110610_01", "Biquíni Sirena Suplex", "R$ 39,90"),
    Produto("4171636_01", "Maiô Santorini", "R$ 50,00"),
    Produto("4568136_01", "Biquíni Sirena - Poliamida", "R$ 60,00"),
    Produto("4191760_01", "Maiô Ibiza", "R$ 50,00"),
    Produto("4110596_01", "Biquíni Malibu", "R$ 50,00"),
    Produto("4233271_01", "Kit Lua - Kimono + Pareo", "R$ 120,00"),
    Produto("4567819_01", "Calça flora", "R$ 79,00", "R$ 120,00"),
    Produto("4110584_01", "Biquíni Jade Suplex", "R$ 50,00"),
    Produto("4171651_01", "Biquíni Ipanema", "R$ 60,00"),
    Produto("4468163_01", "Calça Capri", "R$ 110,00", "R$ 130,00"),
    Produto("4110578_01", "Biquini Fita", "R$ 35,00"),
    Produto("4568066_01", "Biquini de Poá", "R$ 75,00"),
    Produto("4487891_01", "Biquini Jade - POLIAMIDA", "R$ 65,00"),
    Produto("4468164_01", "Biquíni Capri", "R$ 90,00"),
    Produto("4611471_01", "Biquíni + Calça Saída de Praia", "R$ 159,90"),
    Produto("4175122_01", "Maiô Riviera", "R$ 70,00"),
)

CATEGORIAS: tuple[Categoria, ...] = (
    Categoria("heish-categoria-biquinis", "Biquínis"),
    Categoria("heish-categoria-maios", "Maiôs"),
    Categoria("heish-categoria-saidas-de-praia", "Saídas de Praia"),
)

MENU: tuple[str, ...] = ("Biquínis", "Maiôs", "Saídas de Praia", "Todos os produtos", "Contato")
ATENDIMENTO: tuple[str, ...] = ("WhatsApp", "Minha conta", "Busca")

COMPUTADOR = Tela("computador", 1440, "heish-banner-sirena-computador", (1440, 720), 441, 329)
CELULAR = Tela("celular", 390, "heish-banner-sirena-celular", (390, 488), 281, 175)

ICONE_BUSCA = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="8.6" cy="8.6" r="5.1" stroke="#1A1A1A" stroke-width="1.4"/><path d="M12.5 12.5 16.5 16.5" stroke="#1A1A1A" stroke-width="1.4" stroke-linecap="round"/></svg>'
ICONE_CONTA = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="6.6" r="3.1" stroke="#1A1A1A" stroke-width="1.4"/><path d="M3.8 16.6c.5-3 3-4.6 6.2-4.6s5.7 1.6 6.2 4.6z" stroke="#1A1A1A" stroke-width="1.4" stroke-linejoin="round"/></svg>'
ICONE_SACOLA = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3.4" y="6.4" width="13.2" height="10.2" rx="2" stroke="#1A1A1A" stroke-width="1.4"/><path d="M7 6.4V5.6a3 3 0 0 1 6 0v.8" stroke="#1A1A1A" stroke-width="1.4"/></svg>'
ICONE_MENU = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3.5 7.5h13M3.5 12.5h13" stroke="#1A1A1A" stroke-width="1.4" stroke-linecap="round"/></svg>'
SETA_ESQUERDA = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M7.5 2.5 4 6l3.5 3.5" stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
SETA_DIREITA = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4.5 2.5 8 6 4.5 9.5" stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def em_base64(dados: bytes, tipo: str) -> str:
    return f"data:{tipo};base64,{base64.b64encode(dados).decode('ascii')}"


def imagem_embutida(caminho: Path, largura: int, altura: int, foco_vertical: float = 0.0) -> str:
    """Recorta a imagem na proporcao pedida, no dobro da resolucao, e devolve em base64."""
    with Image.open(caminho) as original:
        imagem = original.convert("RGB")
    proporcao = largura / altura
    if imagem.width / imagem.height > proporcao:
        nova_largura = round(imagem.height * proporcao)
        esquerda = (imagem.width - nova_largura) // 2
        imagem = imagem.crop((esquerda, 0, esquerda + nova_largura, imagem.height))
    else:
        nova_altura = round(imagem.width / proporcao)
        topo = round((imagem.height - nova_altura) * foco_vertical)
        imagem = imagem.crop((0, topo, imagem.width, topo + nova_altura))
    destino = (min(largura * 2, imagem.width), min(altura * 2, imagem.height))
    imagem = imagem.resize(destino, Image.Resampling.LANCZOS)
    memoria = io.BytesIO()
    imagem.save(memoria, "JPEG", quality=QUALIDADE_JPEG, optimize=True)
    return em_base64(memoria.getvalue(), "image/jpeg")


def fontes_embutidas(pasta: Path) -> str:
    regras = []
    for peso in (400, 500, 600):
        dados = (pasta / f"poppins-latin-{peso}-normal.woff2").read_bytes()
        regras.append(
            "@font-face{font-family:'Poppins';font-style:normal;"
            f"font-weight:{peso};src:url({em_base64(dados, 'font/woff2')}) format('woff2');}}"
        )
    return "\n".join(regras)


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#E5E5E5;font-family:'Poppins',sans-serif;color:#1A1A1A;-webkit-font-smoothing:antialiased}
.prancha{display:flex;align-items:flex-start;gap:120px;padding:80px;width:max-content}
.tela{background:#FFFFFF;overflow:hidden;--margem:50px}
.tela--computador{width:1440px}
.tela--celular{width:390px;--margem:16px}
img{display:block}
.aviso{height:40px;background:#000000;color:#FFFFFF;display:flex;align-items:center;justify-content:space-between;padding:0 var(--margem);font-size:13px;letter-spacing:.06em}
.cabecalho{height:79px;display:flex;align-items:center;justify-content:space-between;padding:0 var(--margem);border-bottom:1px solid #F0F0F0}
.tela--celular .cabecalho{height:60px}
.cabecalho__lado{display:flex;align-items:center;gap:24px;width:160px}
.cabecalho__lado--fim{justify-content:flex-end}
.tela--celular .cabecalho__lado{width:80px;gap:20px}
.logo{width:56px;height:56px;border-radius:50%}
.tela--celular .logo{width:44px;height:44px}
.menu{display:flex;gap:22px;font-size:14px;text-transform:uppercase;color:#333333}
.banner{width:100%}
.legenda{display:flex;flex-direction:column;align-items:center;gap:12px;padding:32px var(--margem) 24px;text-align:center}
.sobretitulo{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#757575}
.titulo-banner{font-size:40px;line-height:1.2;font-weight:500;padding-bottom:12px}
.tela--celular .titulo-banner{font-size:28px}
.botao{display:inline-flex;align-items:center;justify-content:center;height:56px;padding:0 32px;background:#1A1A1A;color:#FFFFFF;font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:.02em}
.botao--contorno{background:#FFFFFF;color:#1A1A1A;border:2px solid #1A1A1A}
.secao{padding:24px var(--margem)}
.titulo-secao{font-size:24px;line-height:1.3;font-weight:500;text-transform:uppercase;letter-spacing:.04em;text-align:center;margin-bottom:24px}
.tela--celular .titulo-secao{font-size:22px}
.categorias{display:flex;gap:8px}
.tela--celular .categorias{width:max-content}
.categoria{display:flex;flex-direction:column;align-items:center;gap:12px}
.categoria__nome{font-size:16px;font-weight:500;text-transform:uppercase;letter-spacing:.04em}
.categoria__link{font-size:12px;text-transform:uppercase;letter-spacing:.04em;text-decoration:underline;text-underline-offset:3px;padding-bottom:6px}
.vitrine{display:flex;flex-wrap:wrap;gap:24px 8px}
.produto{position:relative;display:flex;flex-direction:column;gap:8px}
.produto__nome{font-size:14px;line-height:1.5;letter-spacing:.06em;color:#757575;padding-top:4px}
.tela--celular .produto__nome{font-size:12px}
.produto__precos{display:flex;align-items:baseline;gap:6px}
.produto__preco{font-size:15px;font-weight:500}
.produto__preco-de{font-size:12px;color:#757575;text-decoration:line-through}
.selo{position:absolute;top:8px;left:8px;background:#1A1A1A;color:#FFFFFF;font-size:12px;letter-spacing:.04em;text-transform:uppercase;padding:4px 10px}
.ver-todos{display:flex;justify-content:center;padding:16px var(--margem) 64px}
.novidades{background:#F0F0F0;padding:40px var(--margem);display:flex;align-items:center;justify-content:space-between;gap:24px}
.tela--celular .novidades{flex-direction:column;align-items:stretch;padding:32px var(--margem)}
.novidades__titulo{font-size:24px;line-height:1.25;font-weight:500}
.novidades__form{display:flex;gap:8px}
.tela--celular .novidades__form{flex-direction:column}
.campo{width:498px;height:56px;background:#FFFFFF;border:1px solid #1A1A1A;display:flex;align-items:center;padding:0 28px;font-size:14px;color:#757575}
.tela--celular .campo{width:100%}
.rodape{display:flex;gap:24px;padding:48px var(--margem) 40px}
.tela--celular .rodape{flex-direction:column;gap:32px;padding:32px var(--margem)}
.rodape__coluna{flex:1;display:flex;flex-direction:column;gap:14px;font-size:14px}
.rodape__titulo{font-size:14px;font-weight:500;text-transform:uppercase;letter-spacing:.06em}
.rodape__texto{max-width:300px;line-height:1.6}
.rodape__direitos{max-width:200px;font-size:12px;line-height:1.6;color:#757575}
.politicas{margin:0 var(--margem);border-top:1px solid #DBDBDB;padding:20px 0 28px;font-size:12px;color:#757575}
.tela--celular .politicas{text-align:center}
"""


def cabecalho(tela: Tela, logo: str) -> str:
    imagem_logo = f'<img class="logo" src="{logo}" alt="Heish Moda Praia">'
    if tela is CELULAR:
        return (
            '<header class="cabecalho">'
            f'<div class="cabecalho__lado">{ICONE_MENU}</div>{imagem_logo}'
            f'<div class="cabecalho__lado cabecalho__lado--fim">{ICONE_BUSCA}{ICONE_SACOLA}</div>'
            "</header>"
        )
    itens = "".join(f"<span>{escape(item)}</span>" for item in MENU)
    return (
        '<header class="cabecalho">'
        f'<div class="cabecalho__lado">{imagem_logo}</div><nav class="menu">{itens}</nav>'
        f'<div class="cabecalho__lado cabecalho__lado--fim">{ICONE_BUSCA}{ICONE_CONTA}{ICONE_SACOLA}</div>'
        "</header>"
    )


def cartao_categoria(tela: Tela, categoria: Categoria, pasta: Path) -> str:
    largura = tela.largura_cartao_categoria
    altura = round(largura * 5 / 4)
    foto = imagem_embutida(pasta / "banners" / f"{categoria.arquivo}.webp", largura, altura)
    return (
        '<div class="categoria">'
        f'<img src="{foto}" width="{largura}" height="{altura}" alt="">'
        f'<span class="categoria__nome">{escape(categoria.nome)}</span>'
        '<span class="categoria__link">Conferir</span></div>'
    )


def cartao_produto(tela: Tela, produto: Produto, pasta: Path) -> str:
    largura = tela.largura_cartao_produto
    altura = round(largura * 5 / 4)
    foto = imagem_embutida(pasta / "imagens" / f"{produto.foto}.webp", largura, altura)
    selo = '<span class="selo">Promoção</span>' if produto.preco_de else ""
    preco_de = f'<span class="produto__preco-de">{produto.preco_de}</span>' if produto.preco_de else ""
    return (
        f'<div class="produto" style="width:{largura}px">'
        f'<img src="{foto}" width="{largura}" height="{altura}" alt="">{selo}'
        f'<span class="produto__nome">{escape(produto.nome)}</span>'
        f'<div class="produto__precos"><span class="produto__preco">{produto.preco}</span>{preco_de}</div></div>'
    )


def rodape() -> str:
    loja = "".join(f"<span>{escape(item)}</span>" for item in MENU)
    atendimento = "".join(f"<span>{escape(item)}</span>" for item in ATENDIMENTO)
    return (
        '<footer class="rodape">'
        '<div class="rodape__coluna"><span class="rodape__titulo">Heish Moda Praia</span>'
        '<span class="rodape__texto">Moda praia feminina. Enviamos para todo o Brasil.</span>'
        '<span class="rodape__direitos">© Heish Moda Praia. Todos os direitos reservados.</span></div>'
        f'<div class="rodape__coluna"><span class="rodape__titulo">Loja</span>{loja}</div>'
        f'<div class="rodape__coluna"><span class="rodape__titulo">Atendimento</span>{atendimento}</div>'
        '</footer><div class="politicas">Termos e políticas</div>'
    )


def montar_tela(tela: Tela, pasta: Path, logo: str) -> str:
    largura_banner, altura_banner = tela.banner_tamanho
    banner = imagem_embutida(pasta / "banners" / f"{tela.banner}.webp", largura_banner, altura_banner)
    categorias = "".join(cartao_categoria(tela, categoria, pasta) for categoria in CATEGORIAS)
    produtos = "".join(cartao_produto(tela, produto, pasta) for produto in PRODUTOS)
    return (
        f'<main class="tela tela--{tela.variante}" data-tela="{tela.variante}">'
        f'<div class="aviso">{SETA_ESQUERDA}<span>Enviamos para todo o Brasil</span>{SETA_DIREITA}</div>'
        f"{cabecalho(tela, logo)}"
        f'<img class="banner" src="{banner}" width="{largura_banner}" height="{altura_banner}" alt="">'
        '<section class="legenda"><span class="sobretitulo">Biquíni Sirena</span>'
        '<h1 class="titulo-banner">Escolha o seu favorito</h1><span class="botao">Comprar agora</span></section>'
        f'<section class="secao"><h2 class="titulo-secao">Compre por categoria</h2><div class="categorias">{categorias}</div></section>'
        f'<section class="secao"><h2 class="titulo-secao">Todos os produtos</h2><div class="vitrine">{produtos}</div></section>'
        '<div class="ver-todos"><span class="botao botao--contorno">Ver todos os produtos</span></div>'
        '<section class="novidades"><h2 class="novidades__titulo">Receba novidades e promoções</h2>'
        '<div class="novidades__form"><span class="campo">E-mail</span><span class="botao">Cadastrar</span></div></section>'
        f"{rodape()}</main>"
    )


def main() -> None:
    pasta_heish, pasta_fontes, saida = (Path(argumento) for argumento in sys.argv[1:4])
    logo = em_base64((pasta_heish / "logo-heish.png").read_bytes(), "image/png")
    telas = "".join(montar_tela(tela, pasta_heish, logo) for tela in (COMPUTADOR, CELULAR))
    documento = (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        "<title>Heish Moda Praia · Página inicial</title>"
        f"<style>{fontes_embutidas(pasta_fontes)}{CSS}</style></head>"
        f'<body><div class="prancha">{telas}</div></body></html>'
    )
    saida.write_text(documento, encoding="utf-8")
    print(f"{saida}  {saida.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
