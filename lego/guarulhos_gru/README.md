# Aeroporto de Guarulhos (GRU) — microescala LEGO

O aeroporto inteiro como maquete de arquitetura, sem aviões e sem a cidade em volta. São
**1400 peças** numa base de 96 x 48 studs (duas baseplates 48x48), de **50 tipos de peça**, em
102 combinações de peça e cor. O aeroporto ocupa a base inteira: a grama ficou só entre as
pistas e nas faixas laterais, como no sítio real. Abra `guarulhos_gru.ldr` no BrickLink Studio,
LDCad ou LeoCAD; cada etapa é um `STEP`. A lista de compras está em `guarulhos_gru_pecas.csv`
(número da peça, nome oficial, cor e quantidade).

Todas as peças vêm da biblioteca oficial LDraw. O script baixa cada peça pelo número e para
se ela não existir, então não há peça inventada.

## O que está na maquete

O layout segue as fotos aéreas e os dados oficiais:

- **Pistas**: 10L/28R, de 3.700 m, ao norte, e 10R/28L, de 3.000 m (antes eram 09L/27R e
  09R/27L). Na maquete elas estão um pouco mais próximas que os 375 m reais, para sobrar menos
  grama. Têm cabeceiras zebradas, pontos de visada, marcas de toque, luzes de aproximação,
  antenas do ILS, cruzamentos entre as pistas, duas taxiways paralelas com saídas rápidas, as
  faixas de terra vermelha e a via perimetral.
- **Pátios**: placas de concreto em grade, com pistas de táxi de asfalto entre os píeres, a via
  de serviço junto ao T2, equipamentos de rampa e torres de iluminação.
- **Terminal 2**: os dois módulos dos antigos TPS1 e TPS2, deslocados um do outro como a dobra do
  prédio real. Cada módulo tem o conector claro do lado ar, a marquise branca sobre o meio-fio e
  o volume central mais alto, com janelas altas e telhado escuro em sheds. Sobre o TPS1 fica a
  torre de escritórios listrada. Os dois píeres têm cabeceira branca e 23 pontes de embarque
  ao todo. Há também o píer remoto de cobertura branca e o corredor até o T3.
- **Terminal 3**: prédio principal com marquise e volume superior recuado, cobertura escura com
  claraboias e casas de máquinas, o píer comprido com dez pontes e o edifício-garagem com carros
  na laje.
- **Outros prédios**: a torre de controle entre o T2 e o T3, o Terminal 1 (ex-TPS4), o terminal
  de cargas (TECA) com carretas nas docas, os bombeiros, dois hangares de manutenção lado a lado,
  a área de apoio com galpões e equipamentos, e o parque de combustível.
- **Lado terra**: viaduto de embarque e via de desembarque, as passarelas cobertas verdes (a
  espinha ao longo do meio-fio e os dois braços), os estacionamentos lotados com a faixa de mata
  no meio, o estacionamento do T1, a locadora de carros, o pátio de carretas e a Rodovia Hélio
  Smidt.

Orientação como no mapa: x de oeste para leste, z de sul para norte. O fundo do modelo no LDraw
(+z) é o norte, então a vista de cima fica com o norte para cima. A escala é de cerca de 40 m
por stud nas pistas. Os prédios estão um pouco ampliados e as alturas exageradas umas duas
vezes, como numa maquete.

| etapa | peças | conteúdo |
|---|---|---|
| 1 base, pistas e taxiways | 180 | baseplates, via perimetral, as duas pistas com marcações, cruzamentos, taxiways, saídas, terra vermelha, luzes de aproximação, antenas do ILS |
| 2 pátios | 176 | pistas de táxi e via de serviço em asfalto, pátios em placas de concreto |
| 3 terminais | 319 | T2 (dois módulos, torre de escritórios, dois píeres com cabeceira, píer remoto, corredor), T3 (prédio e píer), T1 |
| 4 torre e lado ar | 162 | torre de controle, TECA, bombeiros, hangares, área de apoio, parque de combustível, equipamentos de rampa, torres de iluminação |
| 5 lado terra | 563 | viaduto, passarelas verdes, estacionamentos, mata, edifício-garagem do T3, locadora, galpões de apoio, vias e Rodovia Hélio Smidt |

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
