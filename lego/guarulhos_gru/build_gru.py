"""Aeroporto Internacional de Guarulhos (GRU) em microescala LEGO, como maquete de arquitetura.

Sem aviões e sem a cidade em volta: o aeroporto ocupa a base inteira, como nas fotos aéreas.
Pistas 10L/28R (3.700 m, a do norte) e 10R/28L (3.000 m), a cerca de 375 m uma da outra; duas
taxiways paralelas; pátios de concreto em placas com pistas de táxi de asfalto. De oeste para
leste: terminal de cargas (TECA) e Terminal 1; Terminal 2 com os dois módulos de telhado escuro
em sheds (ex-TPS1 e TPS2, com a dobra entre eles), a torre de escritórios listrada e os dois
píeres com a cabeceira branca; o píer remoto de cobertura branca; a torre de controle; o
corredor até o Terminal 3, com o píer comprido e o edifício-garagem; bombeiros, hangares e a
área de manutenção. No lado terra, o viaduto de embarque, as passarelas cobertas verdes, os
estacionamentos lotados com a faixa de mata, o pátio de carretas, o parque de combustível, a
locadora de carros e a Rodovia Hélio Smidt.

Grade: x 0..96 de oeste para leste, z 0..48 de sul para norte (o fundo do LDraw, +z, é o
norte, então a vista de cima fica com o norte para cima). Alturas em plates com o topo das
baseplates no nível 0; pavimento é tile de 1 plate. Cerca de 40 m por stud nas pistas, prédios
um pouco ampliados e alturas exageradas umas duas vezes, como numa maquete.
Uso: python3 build_gru.py [--etapa N] [--sem-render] [--final]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import brickkit as bk  # noqa: E402

RENDERS = os.path.join(HERE, "renders")
WIDTH, DEPTH = 96, 48

TILE_ROW = {n: bk.TILES[(1, n)] for n in (1, 2, 3, 4, 6, 8)}
PLATE_ROW = {n: bk.PLATES[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
BRICK_ROW = {n: bk.BRICKS[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
GLASS_ROW = {1: "3005", 2: "3065", 4: "3066", 6: "3067b"}
GRILLE_ROW = {1: "3070b", 2: "2412b"}
VENT_ROW = {1: "3005", 2: "2877"}
SMALL_TILES = {(1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 8), (2, 2), (2, 3), (2, 4), (2, 6)}

STAGES = ["1 base, pistas e taxiways", "2 pátios", "3 terminais", "4 torre e lado ar", "5 lado terra"]
SLUG = ["base_pistas", "patios", "terminais", "torre_lado_ar", "lado_terra"]
VIEW = (-125, 36)        # do noroeste, sobre o lado terra, como a primeira foto aérea
SUN = (140, 45)          # sol do norte (hemisfério sul), um pouco a leste

CAR_COLORS = ["white"] * 40 + ["lbg"] * 35 + ["black"] * 8 + ["dbg"] * 5 + ["dark_red"] * 5 + \
             ["dark_blue"] * 4 + ["red"] * 3
ROW_COLORS = ["lbg"] * 5 + ["white"] * 3 + ["dbg"] * 2
GSE_COLORS = ["white"] * 3 + ["lbg"] * 2 + ["dbg"]


# ------------------------------------------------------------------------ helpers
def rect(x0, z0, x1, z1):
    return {(x, z) for x in range(x0, x1) for z in range(z0, z1)}


# asfalto do pátio: a pista de táxi ao sul, as faixas entre os píeres e a via de serviço junto ao T2
ASPHALT = (rect(0, 15, 96, 16) | rect(26, 16, 28, 27) | rect(37, 16, 39, 27) | rect(49, 16, 51, 28)
           | rect(60, 16, 62, 32) | rect(76, 16, 78, 27) | rect(26, 26, 39, 27) | rect(39, 27, 52, 28))
# o resto dos pátios em placas de concreto (os prédios já estão no lugar quando o pavimento entra)
APRON = (rect(0, 16, 17, 22) | rect(0, 22, 2, 30) | rect(16, 22, 17, 29) | rect(17, 16, 26, 29)
         | rect(26, 16, 39, 27) | rect(39, 16, 52, 28) | rect(52, 16, 58, 32) | rect(58, 16, 72, 32)
         | rect(72, 16, 96, 30))


def run(m, a0, a1, fixed, level, color, marks=(), along="x", catalog=TILE_ROW, skip=()):
    """1-wide row from a0 to a1 (exclusive), longest pieces first.

    marks: (b0, b1, color[, catalog]) segments with their own colour/pieces; skip: cells left empty.
    """
    cell = {a: (color, catalog) for a in range(a0, a1)}
    for mark in marks:
        for a in range(max(mark[0], a0), min(mark[1], a1)):
            cell[a] = (mark[2], mark[3] if len(mark) > 3 else catalog)
    out, a = [], a0
    while a < a1:
        if a in skip:
            a += 1
            continue
        col, cat = cell[a]
        b = a
        while b < a1 and cell[b] == (col, cat) and b not in skip:
            b += 1
        while a < b:
            n = max(k for k in cat if k <= b - a)
            if along == "x":
                out.append(m.add_part(cat[n], col, a, fixed, level, 0))
            else:
                out.append(m.add_part(cat[n], col, fixed, a, level, 90))
            a += n
    return out


def free(m, cells):
    return set(cells) - m.ground_cells()


def pave(m, cells, color, big=(4, 4), origin=(2, 0), sizes=SMALL_TILES):
    """Pavimento de tiles nas células livres: placas grandes alinhadas numa grade (juntas
    regulares, como concreto), o resto com as maiores que couberem."""
    cells = free(m, cells)
    out = []
    if big and cells:
        bw, bd = big
        xs, zs = [c[0] for c in cells], [c[1] for c in cells]
        for z in range(origin[1] + (min(zs) - origin[1]) // bd * bd, max(zs) + 1, bd):
            for x in range(origin[0] + (min(xs) - origin[0]) // bw * bw, max(xs) + 1, bw):
                block = rect(x, z, x + bw, z + bd)
                if block <= cells:
                    out.append(m.add_part(bk.TILES[(min(big), max(big))], color, x, z, 0, 0 if bw >= bd else 90))
                    cells -= block
    if cells:
        out += m.fill_layers(None, (0, 1), color, "tile", cells=cells, sizes=sizes)
    return out


def glass(m, a0, a1, fixed, level, along="x", posts="lbg"):
    """Fachada de vidro fumê com montantes de concreto nas pontas."""
    return run(m, a0, a1, fixed, level, "trans_black", [(a0, a0 + 1, posts, BRICK_ROW), (a1 - 1, a1, posts, BRICK_ROW)],
               along=along, catalog=GLASS_ROW)


def box_walls(m, x0, z0, x1, z1, level, south, north, side="lbg"):
    """Paredes de um bloco: south/north = 'glass' ou (cor, catálogo); laterais na cor `side`."""
    for z, face in ((z0, south), (z1 - 1, north)):
        if face == "glass":
            glass(m, x0, x1, z, level)
        else:
            run(m, x0, x1, z, level, face[0], catalog=face[1])
    for x in (x0, x1 - 1):
        run(m, z0 + 1, z1 - 1, x, level, side, along="z", catalog=BRICK_ROW)


def shed(m, x0, z0, w, wall="lbg", roof="white"):
    """Galpão baixo de 2 x w: tijolos e telhado de tiles."""
    m.add_part(bk.BRICKS[(2, w)], wall, x0, z0, 0)
    m.add_part(bk.TILES[(2, w)], roof, x0, z0, 3)


def mast(m, x, z):
    """Torre de iluminação do pátio: barra de 3 numa placa redonda de pino aberto."""
    base = m.add_part("85861", "lbg", x, z, 0)
    m.add_held("87994", "lbg", base, (x * bk.STUD + 10, -bk.PLATE - 58, z * bk.STUD + 10))


def tree(m, x, z, level=0, big=False, color=None):
    """Árvore: placa redonda 1x1, ou tronco e copa 2x2 alinhada sobre ele (big)."""
    color = color or ("dark_green" if (x * 7 + z * 3) % 3 else "green")
    if big:
        m.add_part("6141", "reddish_brown", x, z, level)
        m.add_part("4032a", color, x, z, level + 1)
    else:
        m.add_part("6141", color, x, z, level)


def cars(m, rng, x0, x1, z, skip=(), level=0, colors=CAR_COLORS, rows=ROW_COLORS):
    """Fileira de carros estacionados vista do alto: grelhas 1x2 (o friso faz a fila de carros)
    e tiles 1x1 nas cores da frota, quase sem vaga livre."""
    x = x0
    while x < x1:
        if x in skip:
            x += 1
            continue
        if x + 1 < x1 and x + 1 not in skip and rng.random() < 0.55:
            m.add_part("2412b", rng.choice(rows), x, z, level)
            x += 2
        else:
            m.add_part("3070b", rng.choice(colors), x, z, level)
            x += 1


# ------------------------------------------------------------------------ 1 base, pistas
def runway(m, x0, x1, z0):
    """Pista de 2 studs: cabeceiras zebradas (grelha branca atravessada), marcas de toque e
    pontos de visada; as duas fileiras com juntas desencontradas."""
    for x in (x0, x1 - 1):
        m.add_part("2412b", "white", x, z0, 0, 90)
    marks = [(x0 + 3, x0 + 5, "white"), (x0 + 8, x0 + 11, "white"), (x0 + 14, x0 + 15, "white"),
             (x1 - 15, x1 - 14, "white"), (x1 - 11, x1 - 8, "white"), (x1 - 5, x1 - 3, "white")]
    run(m, x0 + 1, x1 - 1, z0, 0, "dbg", marks)
    run(m, x0 + 1, x1 - 1, z0 + 1, 0, "dbg", marks + [(x0 + 15, x0 + 19, "dbg", {4: "2431", 1: "3070b"})])


def stage_base(m):
    m.group = STAGES[0]
    m.add_part("4186", "green", 0, 0, -0.5)
    m.add_part("4186", "green", 48, 0, -0.5)
    run(m, 0, WIDTH, 0, 0, "dbg")               # via perimetral ao sul
    runway(m, 2, 94, 9)                         # 10L/28R, 3.700 m
    runway(m, 12, 87, 1)                        # 10R/28L, 3.000 m
    for x in (17, 33, 50, 67, 83):              # cruzamentos entre as pistas
        run(m, 3, 9, x, 0, "lbg", along="z")
    exits = (8, 24, 38, 47, 61, 74, 88)
    for z in (12, 14):                          # taxiways paralelas e saídas rápidas da 10L
        run(m, 3, 93, z, 0, "lbg")
    for x in exits:
        m.add_part("3070b", "lbg", x, 11, 0)
        m.add_part("3070b", "lbg", x, 13, 0)
    for x0, x1, z in ((9, 17, 13), (25, 37, 13), (48, 56, 13), (62, 73, 13), (75, 85, 13), (26, 32, 11),
                      (52, 60, 11), (18, 23, 3), (40, 46, 3), (34, 40, 8), (56, 62, 8), (68, 74, 8)):
        run(m, x0, x1, z, 0, "dark_orange", catalog=PLATE_ROW, skip=exits)   # terra vermelha
    for x, z in ((3, 1), (3, 2), (6, 1), (6, 2), (9, 1), (9, 2), (89, 1), (89, 2), (92, 1), (92, 2),
                 (95, 1), (95, 2), (0, 9), (0, 10), (95, 9), (95, 10)):
        m.add_part("98138", "white", x, z, 0)  # luzes de aproximação
    for x, z in ((11, 6), (84, 6), (19, 4), (80, 4)):
        m.add_part("3062b", "white", x, z, 0)  # antenas de rampa do ILS, junto ao ponto de toque
        m.add_part("6141", "red", x, z, 3)


# ------------------------------------------------------------------------ 3 terminais
def t2_module(m, x0, x1, z0, tower=()):
    """Módulo do T2, 4 de fundo. No térreo, a fachada do pátio em concreto e vidro, a do
    meio-fio em vidro sob a marquise branca e o conector claro ao longo do lado ar; no meio, o
    volume mais alto com janelas altas e o telhado de sheds escuros com faixas claras entre
    as baias."""
    windows = [(x, x + 2, "trans_black", GLASS_ROW) for x in range(x0 + 2, x1 - 2, 4)]
    run(m, x0, x1, z0, 0, "lbg", windows, catalog=BRICK_ROW)
    for z in (z0 + 1, z0 + 2):
        run(m, x0, x1, z, 0, "lbg", catalog=BRICK_ROW)
    glass(m, x0, x1, z0 + 3, 0)
    run(m, x0, x1, z0, 3, "lbg")
    run(m, x0, x1, z0 + 3, 3, "white")
    run(m, x0, x1, z0 + 1, 3, "lbg", catalog=BRICK_ROW)
    glass(m, x0, x1, z0 + 2, 3)
    for x in range(x0, x1):
        if x in tower:
            continue
        if (x - x0) % 4 == 3:
            m.add_part("3069b", "lbg", x, z0 + 1, 6, 90)
        else:
            m.add_part("85984", "dbg", x, z0 + 1, 6, 90)


def pier(m, x0, z_tip, z_root, west=(), east=(), roof="dbg"):
    """Píer de 2 studs (colunas x0 e x0+1) do z_tip ao z_root: vidro fumê, telhado de chapa
    ondulada e pontes de embarque recolhidas (rotunda e passarela) nos lados oeste e leste."""
    for x in (x0, x0 + 1):
        glass(m, z_tip, z_root, x, 0, along="z")
    for z in west:
        m.add_part("3062b", "lbg", x0 - 1, z, 0)
        m.add_part("3069b", "lbg", x0 - 1, z, 3)
    for z in east:
        m.add_part("3062b", "lbg", x0 + 2, z, 0)
        m.add_part("3069b", "lbg", x0 + 1, z, 3)
    run(m, z_tip, z_root, x0, 3, roof, along="z", catalog=GRILLE_ROW, skip=west)
    run(m, z_tip, z_root, x0 + 1, 3, roof, along="z", catalog=GRILLE_ROW, skip=east)


def pier_head(m, x0, z0):
    """Cabeceira do píer: caixa branca de 4 x 3, mais alta que o píer, com duas pontes de
    embarque de cada lado (a passarela sai do canto da laje)."""
    glass(m, x0, x0 + 4, z0, 0)
    run(m, z0 + 1, z0 + 3, x0, 0, "lbg", along="z", catalog=BRICK_ROW)
    run(m, z0 + 1, z0 + 3, x0 + 3, 0, "lbg", along="z", catalog=BRICK_ROW)
    run(m, x0 + 1, x0 + 3, z0 + 2, 0, "lbg", catalog=BRICK_ROW)
    m.add_part("3020", "white", x0, z0, 3)
    m.add_part("3710", "white", x0, z0 + 2, 3)
    run(m, x0 + 1, x0 + 3, z0, 4, "white")
    run(m, x0, x0 + 4, z0 + 1, 4, "white")
    run(m, x0 + 1, x0 + 3, z0 + 2, 4, "white")
    for z in (z0, z0 + 2):
        for x_out, x_tile in ((x0 - 1, x0 - 1), (x0 + 4, x0 + 3)):
            m.add_part("3062b", "lbg", x_out, z, 0)
            m.add_part("6141", "lbg", x_out, z, 3)
            m.add_part("3069b", "lbg", x_tile, z, 4)


def stage_terminals(m):
    m.group = STAGES[2]
    # Terminal 2: ex-TPS1 (oeste) e ex-TPS2 (leste), deslocados um stud, como a dobra do prédio
    t2_module(m, 26, 39, 27, tower=range(35, 38))
    t2_module(m, 39, 52, 28)
    for i in range(9):                                     # torre de escritórios listrada
        m.add_part("3021", "black" if i % 3 == 2 else "white", 35, 28, 6 + i)
    m.add_part("26603", "white", 35, 28, 15)
    pier(m, 31, 19, 27, west=(20, 22, 24, 26), east=(21, 23, 25))      # píer do TPS1
    pier_head(m, 30, 16)
    pier(m, 44, 19, 28, west=(20, 22, 24, 26), east=(21, 23, 25, 27))  # píer do TPS2
    pier_head(m, 43, 16)
    for x in (53, 54):                                     # píer remoto de cobertura branca
        glass(m, 17, 24, x, 0, along="z")
        run(m, 17, 24, x, 3, "white", along="z")
    glass(m, 52, 59, 31, 0)                                # corredor de ligação T2-T3
    run(m, 52, 59, 31, 3, "lbg")
    # Terminal 3: prédio principal com marquise e volume superior recuado, píer comprido ao sul
    run(m, 58, 72, 32, 0, "lbg", [(x, x + 2, "trans_black", GLASS_ROW) for x in range(59, 70, 3)], catalog=BRICK_ROW)
    glass(m, 58, 72, 36, 0)
    for x in (58, 71):
        run(m, 33, 36, x, 0, "lbg", along="z", catalog=BRICK_ROW)
    m.add_part("3456", "white", 58, 32, 3)                 # laje; a última fileira é a marquise
    run(m, 58, 72, 32, 4, "lbg")
    run(m, 58, 72, 37, 4, "white")
    run(m, 58, 72, 33, 4, "lbg", [(x, x + 2, "trans_black", GLASS_ROW) for x in range(60, 70, 4)], catalog=BRICK_ROW)
    glass(m, 58, 72, 36, 4)
    for x in (58, 71):
        run(m, 34, 36, x, 4, "lbg", along="z", catalog=BRICK_ROW)
    for z in (33, 35):                                     # cobertura escura com faixas de claraboia
        m.add_part("91988", "dbg", 58, z, 7)
        for x, pid, col, rot in ((58, "87079", "dbg", 0), (62, "3069b", "lbg", 90), (63, "69729", "dbg", 0),
                                 (69, "3069b", "lbg", 90)):
            m.add_part(pid, col, x, z, 8, rot)
        m.add_part("2412b", "lbg", 70, z, 8)               # casa de máquinas
        m.add_part("2412b", "lbg", 70, z + 1, 8)
    pier(m, 68, 16, 32, west=(17, 20, 23, 26, 29), east=(18, 21, 24, 27, 30))
    # Terminal 1 (ex-TPS4): caixa baixa de cobertura clara
    box_walls(m, 18, 25, 24, 29, 0, "glass", "glass")
    m.add_part("3032", "lbg", 18, 25, 3)
    m.add_part("69729", "white", 18, 25, 4)
    m.add_part("3068b", "white", 18, 27, 4)
    m.add_part("2412b", "lbg", 20, 27, 4)
    m.add_part("2412b", "lbg", 20, 28, 4)
    m.add_part("3068b", "white", 22, 27, 4)


# ------------------------------------------------------------------------ 4 torre e lado ar
def stage_airside(m, rng):
    m.group = STAGES[3]
    tx, tz = 56, 26                                        # torre de controle
    m.add_part("3941", "white", tx, tz, 0)
    m.add_part("87580", "white", tx, tz, 3)
    for i in range(3):
        m.add_part("3062b", "white", tx + 0.5, tz + 0.5, 4 + 3 * i)
    m.add_part("4032a", "white", tx, tz, 13)
    for dx in (0, 1):
        for dz in (0, 1):
            m.add_part("3062b", "trans_black", tx + dx, tz + dz, 14)
    m.add_part("4032a", "white", tx, tz, 17)
    m.add_part("4740", "white", tx, tz, 18)
    m.add_part("3002", "lbg", 54, 28, 0)                   # prédio de apoio na base da torre
    m.add_part("26603", "lbg", 54, 28, 3)
    # terminal de cargas (TECA): galpão grande, docas de caminhão ao norte
    box_walls(m, 2, 22, 16, 30, 0, ("lbg", BRICK_ROW), ("dbg", VENT_ROW))
    m.add_part("3456", "lbg", 2, 22, 3)
    m.add_part("91988", "lbg", 2, 28, 3)
    for z in (22, 24, 26, 28):
        m.add_part("69729", "lbg", 2, z, 4)
        m.add_part("69729", "lbg", 10, z, 4)
        if z in (24, 28):                                  # casas de máquinas
            m.add_part("2412b", "dbg", 8, z, 4)
            m.add_part("2412b", "dbg", 8, z + 1, 4)
        else:
            m.add_part("3068b", "white", 8, z, 4)
    # bombeiros (SCI): portões vermelhos para o pátio
    run(m, 73, 79, 27, 0, "red", [(73, 74, "lbg", BRICK_ROW), (75, 76, "lbg", BRICK_ROW), (77, 78, "lbg", BRICK_ROW)],
        catalog={1: "3005"})
    run(m, 73, 79, 29, 0, "lbg", catalog=BRICK_ROW)
    m.add_part("3005", "lbg", 73, 28, 0)
    m.add_part("3005", "lbg", 78, 28, 0)
    m.add_part("3795", "white", 73, 28, 3)
    m.add_part("3666", "white", 73, 27, 3)
    m.add_part("69729", "white", 73, 28, 4)
    m.add_part("6636", "lbg", 73, 27, 4)
    # hangares de manutenção lado a lado, portões para o pátio, e a área de apoio atrás deles
    for x0 in (80, 88):
        run(m, 18, 23, x0, 0, "lbg", along="z", catalog=BRICK_ROW)
        run(m, 18, 23, x0 + 7, 0, "lbg", along="z", catalog=BRICK_ROW)
        run(m, x0 + 1, x0 + 7, 22, 0, "lbg", catalog=BRICK_ROW)
        for z in range(18, 23):
            m.add_part("61678", "white", x0, z, 3, 90)
            m.add_part("61678", "white", x0 + 4, z, 3, 270)
    shed(m, 81, 24, 6)
    shed(m, 89, 24, 6, roof="lbg")
    for z in (27, 28):                                     # equipamentos de rampa estacionados
        cars(m, rng, 81, 95, z, colors=GSE_COLORS, rows=GSE_COLORS)
    # parque de combustível: tanques brancos dentro do dique
    for x in (0, 3, 6):
        for z in (38, 41):
            m.add_part("3941", "white", x, z, 0)
            m.add_part("14769", "lbg", x, z, 3)
    run(m, 0, 10, 37, 0, "lbg", catalog=PLATE_ROW)
    run(m, 0, 10, 44, 0, "lbg", catalog=PLATE_ROW)
    run(m, 38, 44, 9, 0, "lbg", along="z", catalog=PLATE_ROW)
    # equipamentos de rampa junto às raízes dos píeres
    taken = m.ground_cells() | ASPHALT
    for x, z in ((28, 24), (29, 24), (28, 25), (29, 25), (34, 24), (35, 25), (40, 25), (41, 26), (42, 26),
                 (47, 25), (48, 26), (65, 30), (66, 31), (65, 31), (71, 29), (72, 30), (63, 31)):
        if (x, z) not in taken:
            m.add_part("3070b", rng.choice(GSE_COLORS), x, z, 0)
    # torres de iluminação dos pátios
    taken = m.ground_cells() | ASPHALT
    for x, z in ((8, 18), (21, 19), (28, 21), (35, 22), (40, 22), (48, 21), (52, 25), (57, 21), (64, 23),
                 (73, 20), (79, 24), (91, 16)):
        if (x, z) not in taken:
            mast(m, x, z)


# ------------------------------------------------------------------------ 5 lado terra
def stage_landside(m, rng):
    m.group = STAGES[4]
    # viaduto de embarque do T2 sobre a via de desembarque
    for x in (25, 31, 37, 43, 49, 55):
        m.add_part("3062b", "lbg", x, 32, 0)
    run(m, 24, 56, 32, 3, "lbg", catalog=PLATE_ROW)
    run(m, 24, 56, 32, 4, "dbg")
    # passarelas cobertas verdes: espinha ao longo do meio-fio e dois braços pelo estacionamento
    for x in (26, 30, 34, 38, 42, 46, 51):
        m.add_part("3062b", "lbg", x, 34, 0)
    run(m, 26, 52, 34, 3, "bright_green", catalog=PLATE_ROW)
    run(m, 26, 52, 34, 4, "bright_green")
    branch = {30, 47}
    for x in branch:
        for z in (37, 40, 43):
            m.add_part("3062b", "lbg", x, z, 0)
        run(m, 35, 44, x, 3, "bright_green", along="z", catalog=PLATE_ROW)
        run(m, 35, 44, x, 4, "bright_green", along="z")
    # faixa de mata entre os dois estacionamentos
    for x in range(23, 56, 2):
        if not {x, x + 1} & branch:
            tree(m, x, 39, big=True)
    # estacionamentos lotados: T2, T1, locadora e a leste do T3
    for z in (35, 36, 38, 41, 43, 44):
        cars(m, rng, 23, 57, z, skip=branch)
    for z in (30, 31, 33, 34, 36):
        cars(m, rng, 17, 22, z)
    for z in (37, 38, 40, 41, 43, 44):
        cars(m, rng, 11, 22, z)
    for z in (31, 32, 34, 35, 37, 38, 40, 41, 43, 44):
        cars(m, rng, 74, 86, z)
    # edifício-garagem do T3: térreo ventilado, laje de estacionamento com carros e mureta
    box_walls(m, 58, 39, 72, 45, 0, ("lbg", VENT_ROW), ("lbg", VENT_ROW))
    m.add_part("3456", "dbg", 58, 39, 3)
    run(m, 58, 72, 39, 4, "lbg", catalog=PLATE_ROW)
    run(m, 58, 72, 44, 4, "lbg", catalog=PLATE_ROW)
    for z in (40, 42, 43):
        cars(m, rng, 58, 72, z, level=4)
    for x in range(3, 16, 3):                              # carretas nas docas do TECA
        m.add_part("3069b", "white", x, 30, 0, 90)
    # prédios de apoio a leste: comissária, oficina e pátio de equipamentos
    shed(m, 87, 32, 6)
    shed(m, 87, 34, 6, wall="white", roof="lbg")
    shed(m, 89, 37, 6, roof="lbg")
    for z in (41, 43):
        cars(m, rng, 87, 95, z, colors=GSE_COLORS, rows=GSE_COLORS)
    # calçadas, vias de meio-fio, acessos, marginal e Rodovia Hélio Smidt
    walks = (rect(26, 31, 39, 32) | rect(23, 34, 57, 35) | rect(30, 35, 31, 45) | rect(47, 35, 48, 45)
             | rect(58, 37, 72, 38) | rect(0, 37, 10, 45) | rect(86, 31, 96, 45))
    pave(m, walks, "lbg", big=None)
    roads = (rect(16, 29, 26, 30) | rect(22, 30, 26, 34) | rect(22, 32, 58, 34) | rect(22, 34, 23, 45)
             | rect(57, 34, 58, 45) | rect(57, 38, 74, 39) | rect(72, 30, 74, 45) | rect(72, 30, 96, 31)
             | rect(0, 45, 96, 48) | rect(0, 30, 17, 37) | rect(23, 37, 57, 38) | rect(23, 42, 57, 43)
             | rect(17, 32, 22, 33) | rect(17, 35, 22, 36) | rect(10, 37, 11, 45) | rect(11, 39, 22, 40)
             | rect(11, 42, 22, 43) | rect(74, 33, 86, 34) | rect(74, 36, 86, 37) | rect(74, 39, 86, 40)
             | rect(74, 42, 86, 43))
    pave(m, roads, "dbg", big=None)


# ------------------------------------------------------------------------ 2 pátios
def stage_aprons(m):
    m.group = STAGES[1]
    pave(m, ASPHALT, "dbg", big=None)                      # pistas de táxi e via de serviço, em asfalto
    pave(m, APRON, "lbg")                                  # pátios em placas de concreto


# ------------------------------------------------------------------------ montagem
def build(upto=len(STAGES), render=True, size=1400):
    os.makedirs(RENDERS, exist_ok=True)
    rng = random.Random(1985)                              # ano da inauguração de Cumbica
    m = bk.Model("Aeroporto Internacional de Guarulhos (GRU) - microescala")
    stage_base(m)                                          # os prédios entram antes do pavimento,
    stage_terminals(m)                                     # que só ocupa o que sobrou livre
    stage_airside(m, rng)
    stage_landside(m, rng)
    stage_aprons(m)
    m.sort_groups(STAGES)
    m.parts = [p for p in m.parts if STAGES.index(p.group) < upto]
    ends = [sum(1 for p in m.parts if STAGES.index(p.group) <= i) for i in range(upto)]
    for i, end in enumerate(ends):
        stage = bk.Model(m.name)
        stage.parts = m.parts[:end]
        print(stage.describe(f"etapa {i + 1}: {STAGES[i]}").split("\ninventário")[0])
        if render:
            path = os.path.join(RENDERS, f"etapa_{i + 1}_{SLUG[i]}.png")
            stage.render(path, VIEW, size=size, caption=f"etapa {i + 1}: {STAGES[i]} ({end} peças)", sun=SUN)
            print("render:", path)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", type=int, default=len(STAGES))
    ap.add_argument("--sem-render", action="store_true")
    ap.add_argument("--final", action="store_true", help="check, export e renders finais")
    args = ap.parse_args()
    m = build(args.etapa, not args.sem_render)
    print(m.describe())
    rare = sorted({bk.color_name(p.color) for p in m.parts if p.color not in bk.COMMON})
    print("cores fora da lista comum:", ", ".join(rare) or "nenhuma")
    print("tipos de peça:", len({p.pid for p in m.parts}))
    report = m.check()
    if args.final:
        if report["collisions"] or report["loose"]:
            sys.exit("modelo com problemas: corrija antes de exportar")
        print("export:", m.export_ldr(os.path.join(HERE, "guarulhos_gru.ldr"), author="Bugiganga S.A. / brickkit"))
        print("lista de peças:", m.export_bom(os.path.join(HERE, "guarulhos_gru_pecas.csv")))
        cap = f"Aeroporto de Guarulhos (GRU) - microescala - {len(m.parts)} peças"
        for name, view in (("aerea_noroeste", VIEW), ("top", "top"), ("aerea_oeste", (-100, 30)),
                           ("iso_front_right", "iso_front_right")):
            print("render:", m.render(os.path.join(RENDERS, f"final_{name}.png"), view, size=2000,
                                      caption=f"{cap} - {name}", sun=SUN))


if __name__ == "__main__":
    main()
