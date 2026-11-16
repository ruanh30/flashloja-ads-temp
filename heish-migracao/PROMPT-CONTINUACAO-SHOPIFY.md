# Contexto para continuar o projeto Heish Moda Praia na Shopify

Você vai continuar um trabalho já em andamento. Leia tudo antes de agir.

## Quem sou e como trabalhar comigo
- Sou dono da Flashloja, uma plataforma SaaS de lojas virtuais, parecida com Shopify e Nuvemshop. Tudo o que fizermos também serve de referência para o editor de temas da Flashloja, feito em TypeScript.
- Responda sempre em português.
- Padrão de produção: nada improvisado, sem gambiarra, sem lógica duplicada, separação de responsabilidades, TypeScript sem `any`.
- Seja proativo. Se uma ideia for ruim, explique por quê e proponha algo melhor.
- Design: tudo inspirado em marcas grandes, nada inventado. A referência atual é a Insider Store (insiderstore.com.br).

## O cliente
Heish Moda Praia vende biquínis, maiôs e saídas de praia. Os produtos vieram do sistema FácilZap.

## A loja Shopify
- Domínio: `8tz7j0-hm.myshopify.com`. Está protegida por senha e ainda não foi lançada.
- Nome cadastrado: "Minha loja". Falta trocar para Heish Moda Praia; esse nome aparece no rodapé.
- Pagamento: só o PayPal está ativo.
- Acesso: pelo conector da Shopify (ferramentas `theme_bash`, `theme_screenshot`, `theme_commit`, `graphql_query`, `graphql_mutation`).

### Temas (atenção: dois têm o mesmo nome)
| Tema | ID | Papel | Regra |
|---|---|---|---|
| Horizon da Heish | `gid://shopify/OnlineStoreTheme/188623028474` | Não publicado | É aqui que se trabalha |
| Horizon | `188624634106` | Publicado | Não tocar |
| Dwell | `188623814906` | Não publicado | Não tocar |

Prévia: https://8tz7j0-hm.myshopify.com/?preview_theme_id=188623028474. Ela só abre com login no admin.

**Regra rígida: nunca publicar o tema sem o meu sim explícito.**

### Catálogo
- 17 produtos ativos.
- Coleções: `biquinis` com 11, `maios` com 3, `saidas-de-praia` com 4 e `todos-os-produtos` com 17, ordenada por mais vendidos e com o esgotado no fim. A coleção `frontpage` não é usada.
- Produtos de destaque: `biquini-sirena-poliamida` (R$ 60; cores Preto, Marrom, Azul Céu e Vermelho; tamanhos P, M e G) e `biquini-calca-saida-de-praia` (R$ 159,90, chamado de Kit Capri).
- Menus em Navegação: `main-menu` (Biquínis, Maiôs, Saídas de Praia, Todos os produtos, Contato) e `atendimento` (WhatsApp, Minha conta, Busca), usado no rodapé.

### Imagens enviadas (Conteúdo, Arquivos)
Banners de estúdio no padrão da Insider, em versão para computador e para celular:
- `heish-banner-sirena-estudio-computador.webp` e `heish-banner-sirena-estudio-celular.webp`
- `heish-banner-kit-capri-estudio-computador.webp` e `heish-banner-kit-capri-estudio-celular.webp`

Também existem os banners e as capas de categoria da primeira versão. Os preços R$ 60 e R$ 159,90 estão desenhados nas imagens: se o preço mudar, o banner precisa ser gerado de novo.

## O que foi feito no tema
Versões salvas com `theme_commit`, da mais antiga para a mais nova:
1. `b9dc30ab`: primeira versão premium.
2. `a309c2a6`: vitrine com 16 produtos e botão "Ver todos".
3. `33be35ff`: banner de estúdio e altura pela imagem no banner.
4. `350d0038`: remontagem completa no padrão da Insider.
5. `6670417f`: rodapé com Loja e Atendimento em sanfona no celular.

### Esqueleto da home, na ordem
1. Barra de aviso preta, no grupo do cabeçalho.
2. Cabeçalho preto e fixo, com logo circular, menu em maiúsculas e ícones brancos.
3. `hero_banner`: banner do Sirena, com o botão "Comprar" sobre a faixa azul.
4. `faixa`: seção `marquee` preta com 3 mensagens.
5. `vitrine`: seção nova "Vitrine com abas" (Todos, Biquínis, Maiôs, Saídas de Praia). Mostra 8 produtos, em 4 colunas no computador e em carrossel no celular, com botão preto "Ver todos os produtos".
6. `banner_kit`: banner do Kit Capri, no mesmo formato do primeiro.
7. `categorias`: lista de coleções com a legenda abaixo da foto.
8. Rodapé: newsletter em faixa `#F7F7F7`, rodapé preto em 3 colunas, linha fina e direitos autorais.

### Identidade, válida para o site todo
- Fonte Manrope da biblioteca da Shopify (`manrope_n4`, `manrope_n5`, `manrope_n7`).
- Cores: fundo `#FFFFFF`, texto `#3D3D3D`, títulos `#000000`, texto secundário `#666666`, linhas `#D9D9D9`, faixa suave `#F7F7F7`; cabeçalho e rodapé pretos.
- Botões: 52px de altura, raio de 6px, peso 700, maiúsculas e entreletra de 1,15px.
- Cartão de produto: nome em 15px, preço antigo riscado antes do atual, selo em contorno no canto superior direito e barra preta "Compra rápida" na base da foto.

### Arquivos do tema criados ou alterados
- `sections/product-tabs.liquid` e `blocks/_product-tab.liquid`: vitrine com abas feita só com CSS (radio e `:has`), sem JavaScript. Como a seção não lê as configurações dos blocos, cada aba devolve o handle da coleção num comentário HTML que a seção lê.
- `sections/hero.liquid`: nova opção de altura "Proporção da imagem" (`section_height: image`), para o banner não ser cortado e o botão ficar por cima.
- `assets/heish-brand.css`: camada de marca, sem `!important`, carregada por `snippets/heish-brand.liquid` dentro de `layout/theme.liquid`, depois do `content_for_header`.
- `snippets/quick-add.liquid` e os arquivos de idioma (chave `actions.quick_add`): texto "Compra rápida".
- `config/settings_data.json`, os templates (index, collection, product, search, cart, 404 e outros), `sections/header-group.json` e `sections/footer-group.json`.
- `DESIGN.md` na raiz do tema: é o contrato de design. Leia antes de qualquer mudança e mantenha atualizado.

## Repositório no GitHub
- Repositório `ruanh30/flashloja-ads-temp`, branch `claude/heish-moda-praia-flashloja-4668ce`. Não abrir pull request sem eu pedir.
- Pasta `heish-migracao/`:
  - `scripts/gerar_banner_estudio.py`: gera os banners de estúdio em Python. Rode com `python3 heish-migracao/scripts/gerar_banner_estudio.py`. Os recortes das modelos já estão salvos em `banner-estudio/`.
  - `scripts/fundo_branco.py`: recorte de fotos com o modelo BiRefNet.
  - `scripts/exportar_shopify.py`: exportação do catálogo para a Shopify.
  - `scripts/gerar_banners.py` e `scripts/capas_vitrine.py`: versão antiga dos banners e das capas.
  - `scripts/gerar_telas_figma.py`: réplica estática da home para o Figma. Está desatualizado e ainda mostra a home antiga.
  - `fontes/`: Manrope nos pesos 500 e 800, com a licença OFL, usada só pelo gerador de banners.

## Pegadinhas das ferramentas da Shopify
- `theme_bash` aceita mais ou menos uma chamada por minuto. Se responder `rate_limited`, espere 60 segundos.
- Em `theme_bash`, não separe comandos com `;` nem com `||`. O `sed` não aceita o comando `c\`, e o `awk` não interpreta `\n` dentro de `-v`. Para reescrever um arquivo, gere `arquivo.novo` e depois faça `mv`.
- Os JSON do tema começam com um comentário `/* */`. Para usar `jq`, tire o comentário com `sed '/^\/\*/,/\*\//d'` e devolva o comentário no arquivo final.
- `theme_screenshot` ignora o CSS dos blocos `{% stylesheet %}`. Para capturar direito, junte esse CSS num arquivo temporário `assets/zz-captura-temp.css`, carregue-o em `snippets/heish-brand.liquid` antes do `heish-brand.css`, tire as capturas e apague os dois antes do `theme_commit`.
- `theme_commit` só funciona em tema não publicado. Depois de salvar, confira que nada ficou pendente e que o papel de cada tema não mudou.
- Leia `/skills/editing-themes/SKILL.md` antes da primeira mudança no tema.

## Pendências
### Aguardando minha decisão
1. Trocar o nome da loja para Heish Moda Praia. Eu faço isso no admin.
2. Cadastrar as cores como amostras nos produtos, para as bolinhas de cor aparecerem nos cartões. Isso altera dados de produto, então só com o meu sim.
3. Vitrine no computador: manter a grade de 8 produtos ou trocar pelo carrossel de uma linha, como na Insider.
4. Publicar o tema. Só com o meu sim.

### Ainda não testado
- Navegador real: clique nas abas, menu do celular, sacola, busca, compra rápida e adicionar ao carrinho.
- O bloco "Você também pode gostar" da página de produto apareceu vazio nas capturas.

### Antes do lançamento
- Ativar outros meios de pagamento além do PayPal.
- Padronizar os nomes dos produtos: há "Biquini" e "Biquíni" misturados, "POLIAMIDA" em maiúsculas e "Calça flora" com minúscula.
- Fotos novas para dois produtos e nova leitura do estoque no FácilZap.
- O logo atual é uma foto redonda e fica fraco; vale fazer uma versão vetorial.

### Figma
Está parado. Preciso criar um arquivo vazio no Figma e mandar o link, e o ambiente precisa liberar o acesso de rede ao Figma. Antes de importar, atualizar `gerar_telas_figma.py` para a home nova.

## Segurança
- Nunca colar tokens ou senhas no chat. O token da API do FácilZap só pode ser enviado para `api.facilzap.app.br`, e deve ser trocado.
- Não mexer no tema publicado nem no Dwell.

Comece confirmando que entendeu o estado e me pergunte qual pendência atacar primeiro.
