# Revisão das fotos com fundo branco

As 65 fotos desta pasta foram geradas por `scripts/fundo_branco.py` e conferidas uma a uma, comparando original, máscara e resultado. 55 foram aprovadas. As 10 abaixo têm defeito pontual e ficam aqui apenas como registro: não devem ir para a loja sem correção.

## Fotos com ressalva

| Foto | Problema |
|---|---|
| 4110610_01 | Sobra de parede dentro da alça da bolsa. |
| 4171636_01 | Recorte limpo, mas as pernas estão em sombra dura na foto original. |
| 4171636_02 | Mesma sombra nas pernas e original em baixa resolução. |
| 4175122_01 | Sobra de piso junto ao tornozelo e sombra dura nas pernas. |
| 4233271_01 | Pernas terminam em corte inclinado, onde havia a moldura de um espelho. |
| 4468164_01 | A modelo se apoiava em um cubo que foi removido e ficou apoiada no ar. |
| 4567819_02 | A bandeira vermelha da cena ficou no recorte. |
| 4567819_03 | Resto de folha verde entre o tronco e o braço. |
| 4568136_01 | Dois fios de cabelo saíram azulados, visíveis só com zoom. |
| 4611471_02 | A ponteira dourada do cordão sumiu. |

## Capas de vitrine

As capas ficam em `capas-vitrine/` e são montadas por `scripts/capas_vitrine.py`, que define a foto usada em cada produto. Três casos fogem da regra de usar a foto 01:

- **4110610, Biquíni Sirena Suplex:** usa a foto 02, porque a 01 tem a sobra na bolsa.
- **4171636, Maiô Santorini** e **4175122, Maiô Riviera:** a capa termina na coxa, acima da sombra. As duas fotos originais são pequenas, então a capa sai em baixa resolução. O ideal é refazer essas fotos com luz uniforme.
- **4568136, Biquíni Sirena em poliamida:** usa a foto 01, apesar dos dois fios azulados, por ser a foto principal dos anúncios.
