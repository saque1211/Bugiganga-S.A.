# GRU Terminal 3 — microescala LEGO

Aeroporto Internacional de Guarulhos com foco no Terminal 3: **321 peças**, base de 40 x 32 studs,
55 tipos de peça, só cores comuns. Abra `guarulhos_gru.ldr` no BrickLink Studio, LDCad ou LeoCAD
(cada etapa é um `STEP`).

| etapa | peças | conteúdo |
|---|---|---|
| 1 base | 54 | 6 placas estruturais DBG, grama, pista de taxiamento em asfalto liso (tiles DBG), pátio LBG |
| 2 sinalização | 23 | eixo e borda brancos na pista, linhas de entrada e barras de parada amarelas, separação das posições |
| 3 terminal | 107 | 30 x 7 studs + beiral, 3 tijolos de altura, fachadas de vidro trans-clear com pilares brancos, interior escuro com laje, cobertura branca de tiles com casas de máquinas |
| 4 torre | 18 | fuste fino de 1x1 redondo, cabine trans-black, antena e prédio de apoio |
| 5 pontes | 18 | 3 fingers LBG sobre colunas, do lado ar até a porta dianteira esquerda |
| 6 aviões | 48 + 15 | Azul (cauda azul), LATAM (maior, cauda azul-escuro com vermelho), GOL (cauda laranja); caminhão-tanque e trem de bagagem em cada posição |
| 7 lado terra | 38 | viaduto de embarque com meio-fio, guarda-corpo, 3 veículos no viaduto e 1 na via de baixo, árvores |

Renders em `renders/`: `final_iso_front_left.png`, `final_top.png`, `final_iso_back_right.png`
(lado terra) e uma imagem por etapa.

## Regenerar

```
python3 build_gru.py --final
```

Monta as etapas (render + contagem em cada uma), roda a checagem de colisões e peças soltas,
exporta o `.ldr` e os renders finais. A geometria das peças vem da biblioteca LDraw oficial,
baixada sob demanda para `LDRAW_CACHE` (padrão `~/.cache/ldraw`).

`brickkit.py` é o kit de modelagem (add_parts, fill_layers, describe, check, render, export_ldr);
`ldraw.py` lê a biblioteca LDraw.
