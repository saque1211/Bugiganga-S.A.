# Aeroporto de Guarulhos (GRU) — microescala LEGO

O aeroporto inteiro em **1065 peças**, base de 96 x 48 studs (duas baseplates 48x48),
**78 tipos de peça** e 174 combinações peça+cor, só cores comuns. Abra `guarulhos_gru.ldr`
no BrickLink Studio, LDCad ou LeoCAD (cada etapa é um `STEP`). A lista de compras está em
`guarulhos_gru_pecas.csv` (número da peça, nome oficial, cor, quantidade).

Todas as peças vêm da biblioteca oficial LDraw. O script baixa cada peça pelo número e para
se ela não existir, então não há peça inventada.

Orientação como no mapa, com o norte para cima: pistas e o Rio Baquirivu-Guaçu ao norte;
de oeste para leste, TECA, T1, T2, torre, T3, hangar e bombeiros; lado terra ao sul.

| etapa | peças | conteúdo |
|---|---|---|
| 1 base e pistas | 185 | baseplates, 09L/27R (mais curta) e 09R/27L com cabeceiras, marcas de toque e eixo, luzes de aproximação, ligações, saídas, taxiway paralela, rio |
| 2 pátios e sinalização | 38 | pátio em placas LBG, linhas de entrada, torres de iluminação, placas de taxiway e pista |
| 3 terminais | 257 | T2 em dois módulos (ex-TPS1 e ex-TPS2) com telhado escuro listrado, marquise e píeres envidraçados; T3 com píer de vidro, fachada com pilares, marquise e lanternim; T1 com cobertura em abóbada; TECA com docas e telhado em dente de serra |
| 4 torre e lado ar | 63 | torre de controle, hangar com teto em arco, bombeiros com torre de treinamento, carros de bombeiro, contêineres LD3, cerca |
| 5 pontes de embarque | 33 | 11 fingers, dois deles no A380 |
| 6 aviões e veículos | 218 | 16 aviões: LATAM, GOL, Azul, TAP, American, Emirates (A380 de 4 motores), LATAM Cargo; um alinhado na 09R e um na taxiway; ônibus de pátio, escadas, catering, bagagem, tanque e pushback |
| 7 lado terra | 271 | viadutos de embarque do T2 e do T3, estacionamento com as passarelas cobertas verdes, hotel com janelas, edifício-garagem, parque de combustível, Rodovia Hélio Smidt, carros, táxis, ônibus, caminhões, árvores |

Renders em `renders/`: `final_iso_front_left.png` (vista do lado da cidade, como nas fotos
aéreas), `final_top.png`, `final_iso_back_right.png` e uma imagem por etapa.

## Regenerar

```
python3 build_gru.py --final
```

Monta as etapas (render e contagem em cada uma), confere colisões e peças soltas, exporta o
`.ldr`, a lista de peças e os renders finais. As peças LDraw são baixadas sob demanda para
`LDRAW_CACHE` (padrão `~/.cache/ldraw`).

`brickkit.py` é o kit de modelagem (add_parts, fill_layers, place_local, mirror_z, describe,
check, render, export_ldr, export_bom); `ldraw.py` lê a biblioteca LDraw.
