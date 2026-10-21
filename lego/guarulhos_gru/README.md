# Aeroporto de Guarulhos (GRU) — microescala LEGO

O aeroporto inteiro como maquete de arquitetura, sem aviões: **1694 peças** numa base de
96 x 64 studs (seis baseplates 32x32), **57 tipos de peça** e 135 combinações peça+cor. Abra
`guarulhos_gru.ldr` no BrickLink Studio, LDCad ou LeoCAD; cada etapa é um `STEP`. A lista de
compras está em `guarulhos_gru_pecas.csv` (número da peça, nome oficial, cor e quantidade).

Todas as peças vêm da biblioteca oficial LDraw. O script baixa cada peça pelo número e para
se ela não existir, então não há peça inventada.

## O que está na maquete

O layout segue as fotos aéreas e os dados oficiais:

- **Pistas**: 10L/28R, de 3.700 m, ao norte, e 10R/28L, de 3.000 m, a 375 m uma da outra (antes
  eram 09L/27R e 09R/27L). Têm cabeceiras zebradas, pontos de visada, marcas de toque, luzes de
  aproximação, cruzamentos entre as pistas, duas taxiways paralelas com saídas rápidas e as
  faixas de terra vermelha das laterais.
- **Pátios**: placas de concreto em grade, com as pistas de táxi de asfalto entre os píeres e
  torres de iluminação.
- **Terminal 2**: os dois módulos dos antigos TPS1 e TPS2, deslocados um do outro como a dobra do
  prédio real. Têm telhado escuro em sheds com faixas claras, o conector claro do lado ar, a
  fachada de vidro do meio-fio e a torre de escritórios listrada. Os dois píeres têm cabeceira
  branca e pontes de embarque recolhidas. Há também o píer remoto de cobertura branca.
- **Terminal 3**: prédio principal com marquise e volume superior recuado, cobertura escura com
  claraboias, o píer comprido com oito pontes e o edifício-garagem com carros na laje.
- **Outros prédios**: a torre de controle entre o T2 e o T3, o Terminal 1 (ex-TPS4), o terminal
  de cargas (TECA) com carretas nas docas, os bombeiros, os hangares de manutenção, o parque de
  combustível e, ao sul das pistas, a Base Aérea de São Paulo com três hangares em abóbada.
- **Lado terra**: viaduto de embarque e via de desembarque, as passarelas cobertas verdes (a
  espinha ao longo do meio-fio e os dois braços), os estacionamentos lotados com a faixa de mata
  no meio e a Rodovia Hélio Smidt arborizada.
- **Cidade**: bairros de Guarulhos ao norte e ao sul. Os quarteirões são um mosaico de telhados
  de cerâmica, fibrocimento e laje, com casas de duas águas, sobrados com caixa-d'água, prédios
  baixos, galpões e árvores.

Orientação como no mapa: x de oeste para leste, z de sul para norte. O fundo do modelo no LDraw
(+z) é o norte, então a vista de cima fica com o norte para cima. A escala é de cerca de 40 m
por stud nas pistas. Os prédios estão um pouco ampliados e as alturas exageradas umas duas
vezes, como numa maquete.

| etapa | peças | conteúdo |
|---|---|---|
| 1 base, pistas e taxiways | 161 | baseplates, as duas pistas com marcações, cruzamentos, taxiways, saídas, terra vermelha, luzes de aproximação |
| 2 pátios | 135 | pistas de táxi de asfalto e pátios em placas de concreto |
| 3 terminais | 259 | T2 (dois módulos, torre de escritórios, dois píeres com cabeceira, píer remoto), T3 (prédio e píer), T1 |
| 4 torre e lado ar | 154 | torre de controle, TECA, bombeiros, hangares, Base Aérea, parque de combustível, torres de iluminação |
| 5 lado terra | 462 | viaduto, passarelas verdes, estacionamentos, mata, edifício-garagem do T3, galpões, vias e Rodovia Hélio Smidt |
| 6 cidade | 523 | ruas e quarteirões ao norte e ao sul, arborização da rodovia |

Os renders estão em `renders/`:

- `final_aerea_noroeste.png`: vista do noroeste sobre o lado terra, como a foto aérea clássica.
- `final_top.png`: vista de cima, com o norte para cima.
- `final_aerea_oeste.png`: vista do oeste, ao longo dos terminais.
- `final_iso_front_right.png`: vista do sudeste, do lado das pistas.
- Uma imagem por etapa.

## Regenerar

```
python3 build_gru.py --final
```

O comando monta as etapas (com render e contagem de cada uma), confere colisões e peças soltas,
exporta o `.ldr`, a lista de peças e os renders finais. As peças LDraw são baixadas sob demanda
para `LDRAW_CACHE` (padrão `~/.cache/ldraw`).

`brickkit.py` é o kit de modelagem (add_parts, fill_layers, place_local, describe, check,
render, export_ldr, export_bom). O render tem sol com sombras, oclusão de cantos e uma paleta
próxima das peças reais. `ldraw.py` lê a biblioteca LDraw.
