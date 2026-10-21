"""Aeroporto Internacional de Guarulhos (GRU) em microescala LEGO, como maquete de arquitetura.

Sem aviões: quem identifica GRU é o próprio sítio, como nas fotos aéreas. Pistas 10L/28R
(3.700 m, a do norte) e 10R/28L (3.000 m), a 375 m uma da outra; duas taxiways paralelas;
pátios de concreto em placas. De oeste para leste: terminal de cargas (TECA) e Terminal 1;
Terminal 2 com os dois módulos de telhado escuro em sheds (ex-TPS1 e TPS2, com a dobra entre
eles), a torre de escritórios listrada e os dois píeres com a cabeceira branca; o píer remoto de
cobertura branca; a torre de controle; o Terminal 3 com o píer comprido e o edifício-garagem;
hangares e bombeiros. No lado terra, o viaduto de embarque, as passarelas cobertas verdes, os
estacionamentos lotados com faixas de mata, o parque de combustível e a Rodovia Hélio Smidt;
em volta, os bairros de Guarulhos e, ao sul das pistas, a Base Aérea de São Paulo.

Grade: x 0..96 de oeste para leste, z 0..64 de sul para norte (o fundo do LDraw, +z, é o
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
WIDTH, DEPTH = 96, 64

TILE_ROW = {n: bk.TILES[(1, n)] for n in (1, 2, 3, 4, 6, 8)}
PLATE_ROW = {n: bk.PLATES[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
BRICK_ROW = {n: bk.BRICKS[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
GLASS_ROW = {1: "3005", 2: "3065", 4: "3066", 6: "3067b"}
GRILLE_ROW = {1: "3070b", 2: "2412b"}
VENT_ROW = {1: "3005", 2: "2877"}
SMALL_TILES = {(1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 8), (2, 2), (2, 3), (2, 4), (2, 6)}

STAGES = ["1 base, pistas e taxiways", "2 pátios", "3 terminais", "4 torre e lado ar", "5 lado terra", "6 cidade"]
SLUG = ["base_pistas", "patios", "terminais", "torre_lado_ar", "lado_terra", "cidade"]
VIEW = (-125, 36)        # do noroeste, sobre o lado terra, como a primeira foto aérea
SUN = (140, 45)          # sol do norte (hemisfério sul), um pouco a leste

CAR_COLORS = ["white"] * 40 + ["lbg"] * 35 + ["black"] * 8 + ["dbg"] * 5 + ["dark_red"] * 5 + \
             ["dark_blue"] * 4 + ["red"] * 3
ROW_COLORS = ["lbg"] * 5 + ["white"] * 3 + ["dbg"] * 2


# ------------------------------------------------------------------------ helpers
def rect(x0, z0, x1, z1):
    return {(x, z) for x in range(x0, x1) for z in range(z0, z1)}


# pátios: pistas de táxi em asfalto (faixa ao sul e entre os píeres) e o resto em concreto
TAXILANES = (rect(1, 22, 85, 23) | rect(26, 23, 28, 32) | rect(37, 23, 39, 32) | rect(49, 23, 51, 33)
             | rect(60, 23, 62, 37) | rect(76, 23, 78, 34))
APRON = (rect(1, 22, 17, 29) | rect(17, 22, 26, 30) | rect(26, 22, 39, 32) | rect(39, 22, 52, 33)
         | rect(52, 22, 58, 37) | rect(58, 22, 72, 37) | rect(72, 22, 85, 34) | rect(85, 22, 94, 25))


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


def pave(m, cells, color, big=(4, 4), origin=(2, 2), sizes=SMALL_TILES):
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


def cars(m, rng, x0, x1, z, skip=(), level=0):
    """Fileira de carros estacionados vista do alto: grelhas 1x2 (o friso faz a fila de carros)
    e tiles 1x1 nas cores da frota, quase sem vaga livre."""
    x = x0
    while x < x1:
        if x in skip:
            x += 1
            continue
        if x + 1 < x1 and x + 1 not in skip and rng.random() < 0.55:
            m.add_part("2412b", rng.choice(ROW_COLORS), x, z, level)
            x += 2
        else:
            m.add_part("3070b", rng.choice(CAR_COLORS), x, z, level)
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
    for x in (0, 32, 64):
        for z in (0, 32):
            m.add_part("3811", "green", x, z, -0.5)
    runway(m, 2, 94, 16)                        # 10L/28R, 3.700 m
    runway(m, 12, 87, 6)                        # 10R/28L, 3.000 m
    for x in (17, 33, 50, 67, 83):              # cruzamentos entre as pistas
        run(m, 8, 16, x, 0, "lbg", along="z")
    exits = (8, 24, 38, 47, 61, 74, 88)
    for z in (19, 21):                          # taxiways paralelas e saídas rápidas da 10L
        run(m, 3, 93, z, 0, "lbg")
    for x in exits:
        m.add_part("3070b", "lbg", x, 18, 0)
        m.add_part("3070b", "lbg", x, 20, 0)
    for x0, x1, z in ((9, 17, 20), (25, 37, 20), (48, 56, 20), (62, 73, 20), (75, 85, 20),
                      (26, 32, 18), (52, 60, 18), (18, 23, 8), (68, 74, 15), (34, 40, 15)):
        run(m, x0, x1, z, 0, "dark_orange", catalog=PLATE_ROW, skip=exits)   # terra vermelha
    for x, z in ((3, 6), (3, 7), (6, 6), (6, 7), (9, 6), (9, 7), (89, 6), (89, 7), (92, 6), (92, 7),
                 (95, 6), (95, 7), (0, 16), (0, 17), (95, 16), (95, 17)):
        m.add_part("98138", "white", x, z, 0)  # luzes de aproximação


# ------------------------------------------------------------------------ 3 terminais
def t2_module(m, x0, x1, z0, tower=()):
    """Módulo do T2, 4 de fundo: fachada do pátio em concreto e vidro, fachada do meio-fio
    de vidro, telhado de sheds escuros com faixas claras entre as baias e o conector claro
    ao longo do lado ar."""
    windows = [(x, x + 2, "trans_black", GLASS_ROW) for x in range(x0 + 2, x1 - 2, 4)]
    run(m, x0, x1, z0, 0, "lbg", windows, catalog=BRICK_ROW)
    for z in (z0 + 1, z0 + 2):
        run(m, x0, x1, z, 0, "lbg", catalog=BRICK_ROW)
    glass(m, x0, x1, z0 + 3, 0)
    run(m, x0, x1, z0, 3, "lbg")
    for x in range(x0, x1):
        band = (x - x0) % 4 == 3
        if x in tower:                                     # só a fileira da frente do telhado
            m.add_part("3070b" if band else "54200", "lbg" if band else "dbg", x, z0 + 3, 3, 0 if band else 90)
        elif band:
            m.add_part("63864", "lbg", x, z0 + 1, 3, 90)
        else:
            m.add_part("85984", "dbg", x, z0 + 1, 3, 90)
            m.add_part("54200", "dbg", x, z0 + 3, 3, 90)


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
    """Cabeceira do píer: caixa branca de 4 x 3, mais alta que o píer."""
    glass(m, x0, x0 + 4, z0, 0)
    run(m, z0 + 1, z0 + 3, x0, 0, "lbg", along="z", catalog=BRICK_ROW)
    run(m, z0 + 1, z0 + 3, x0 + 3, 0, "lbg", along="z", catalog=BRICK_ROW)
    run(m, x0 + 1, x0 + 3, z0 + 2, 0, "lbg", catalog=BRICK_ROW)
    m.add_part("3020", "white", x0, z0, 3)
    m.add_part("3710", "white", x0, z0 + 2, 3)
    m.add_part("87079", "white", x0, z0, 4)
    m.add_part("2431", "white", x0, z0 + 2, 4)


def stage_terminals(m):
    m.group = STAGES[2]
    # Terminal 2: ex-TPS1 (oeste) e ex-TPS2 (leste), deslocados um stud, como a dobra do prédio
    t2_module(m, 26, 39, 32, tower=range(35, 38))
    t2_module(m, 39, 52, 33)
    for i in range(9):                                     # torre de escritórios listrada
        m.add_part("3021", "black" if i % 3 == 2 else "white", 35, 33, 3 + i)
    m.add_part("26603", "white", 35, 33, 12)
    pier(m, 31, 26, 32, west=(27, 30), east=(28, 31))       # píer do TPS1
    pier_head(m, 30, 23)
    pier(m, 44, 26, 33, west=(27, 30), east=(28, 31))       # píer do TPS2
    pier_head(m, 43, 23)
    for x in (53, 54):                                     # píer remoto de cobertura branca
        glass(m, 24, 31, x, 0, along="z")
        run(m, 24, 31, x, 3, "white", along="z")
    # Terminal 3: prédio principal com marquise e volume superior recuado, píer comprido ao sul
    run(m, 58, 72, 37, 0, "lbg", [(x, x + 2, "trans_black", GLASS_ROW) for x in range(59, 70, 3)], catalog=BRICK_ROW)
    glass(m, 58, 72, 41, 0)
    for x in (58, 71):
        run(m, 38, 41, x, 0, "lbg", along="z", catalog=BRICK_ROW)
    m.add_part("3456", "white", 58, 37, 3)                 # laje; a última fileira é a marquise
    run(m, 58, 72, 37, 4, "lbg")
    run(m, 58, 72, 42, 4, "white")
    run(m, 58, 72, 38, 4, "lbg", [(x, x + 2, "trans_black", GLASS_ROW) for x in range(60, 70, 4)], catalog=BRICK_ROW)
    glass(m, 58, 72, 41, 4)
    for x in (58, 71):
        run(m, 39, 41, x, 4, "lbg", along="z", catalog=BRICK_ROW)
    for z in (38, 40):                                     # cobertura escura com faixas de claraboia
        m.add_part("91988", "dbg", 58, z, 7)
        for x, pid, col, rot in ((58, "87079", "dbg", 0), (62, "3069b", "lbg", 90), (63, "69729", "dbg", 0),
                                 (69, "3069b", "lbg", 90), (70, "3068b", "dbg", 0)):
            m.add_part(pid, col, x, z, 8, rot)
    pier(m, 68, 23, 37, west=(24, 27, 30, 33), east=(25, 28, 31, 34))
    # Terminal 1 (ex-TPS4): caixa baixa de cobertura clara
    box_walls(m, 18, 30, 24, 34, 0, "glass", "glass")
    m.add_part("3032", "lbg", 18, 30, 3)
    m.add_part("69729", "white", 18, 30, 4)
    m.add_part("3068b", "white", 18, 32, 4)
    m.add_part("2412b", "lbg", 20, 32, 4)
    m.add_part("2412b", "lbg", 20, 33, 4)
    m.add_part("3068b", "white", 22, 32, 4)


# ------------------------------------------------------------------------ 4 torre e lado ar
def stage_airside(m):
    m.group = STAGES[3]
    tx, tz = 56, 33                                        # torre de controle
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
    m.add_part("3002", "lbg", 54, 35, 0)                   # prédio de apoio na base da torre
    m.add_part("26603", "lbg", 54, 35, 3)
    # terminal de cargas (TECA): galpão grande, docas de caminhão ao norte
    box_walls(m, 2, 29, 16, 37, 0, ("lbg", BRICK_ROW), ("dbg", VENT_ROW))
    m.add_part("3456", "lbg", 2, 29, 3)
    m.add_part("91988", "lbg", 2, 35, 3)
    for z in (29, 31, 33, 35):
        m.add_part("69729", "lbg", 2, z, 4)
        m.add_part("69729", "lbg", 10, z, 4)
        if z in (31, 35):                                  # casas de máquinas
            m.add_part("2412b", "dbg", 8, z, 4)
            m.add_part("2412b", "dbg", 8, z + 1, 4)
        else:
            m.add_part("3068b", "white", 8, z, 4)
    # bombeiros (SCI): portões vermelhos para o pátio
    run(m, 76, 82, 34, 0, "red", [(76, 77, "lbg", BRICK_ROW), (78, 79, "lbg", BRICK_ROW), (80, 81, "lbg", BRICK_ROW)],
        catalog={1: "3005"})
    run(m, 76, 82, 36, 0, "lbg", catalog=BRICK_ROW)
    m.add_part("3005", "lbg", 76, 35, 0)
    m.add_part("3005", "lbg", 81, 35, 0)
    m.add_part("3795", "white", 76, 35, 3)
    m.add_part("3666", "white", 76, 34, 3)
    m.add_part("69729", "white", 76, 35, 4)
    m.add_part("6636", "lbg", 76, 34, 4)
    # hangares de manutenção com teto em arco
    for z0 in (25, 31):
        run(m, z0, z0 + 5, 85, 0, "lbg", along="z", catalog=BRICK_ROW)
        run(m, z0, z0 + 5, 92, 0, "lbg", along="z", catalog=BRICK_ROW)
        run(m, 86, 92, z0 + 4, 0, "lbg", catalog=BRICK_ROW)
        for z in range(z0, z0 + 5):
            m.add_part("61678", "white", 85, z, 3, 90)
            m.add_part("61678", "white", 89, z, 3, 270)
    # Base Aérea de São Paulo (BASP), ao sul das pistas: hangares em abóbada e prédios
    for x0 in (19, 25, 31):
        run(m, x0, x0 + 4, 0, 0, "lbg", catalog=BRICK_ROW)
        run(m, x0, x0 + 4, 3, 0, "lbg", catalog=BRICK_ROW)
        for x in range(x0, x0 + 4):
            m.add_part("93273", "lbg", x, 0, 3)
    for x0, z0, w in ((38, 0, 4), (43, 0, 3), (38, 2, 2)):
        m.add_part(bk.BRICKS[(2, w)], "white", x0, z0, 0)
        m.add_part(bk.TILES[(2, w)], "dbg", x0, z0, 3)
    pave(m, rect(18, 4, 47, 6), "lbg", big=None)
    # parque de combustível: tanques brancos dentro do dique
    for x in (1, 4, 7):
        for z in (44, 47):
            m.add_part("3941", "white", x, z, 0)
            m.add_part("14769", "lbg", x, z, 3)
    run(m, 1, 10, 43, 0, "lbg", catalog=PLATE_ROW)
    run(m, 1, 10, 49, 0, "lbg", catalog=PLATE_ROW)
    # torres de iluminação dos pátios
    taken = m.ground_cells() | TAXILANES
    for x, z in ((10, 25), (21, 26), (29, 25), (36, 28), (40, 28), (48, 27), (52, 31), (58, 28), (64, 30),
                 (72, 27), (80, 30), (90, 23)):
        if (x, z) not in taken:
            mast(m, x, z)


# ------------------------------------------------------------------------ 5 lado terra
def stage_landside(m, rng):
    m.group = STAGES[4]
    # viaduto de embarque do T2 sobre a via de desembarque
    for x in (25, 31, 37, 43, 49, 55):
        m.add_part("3062b", "lbg", x, 37, 0)
    run(m, 24, 56, 37, 3, "lbg", catalog=PLATE_ROW)
    run(m, 24, 56, 37, 4, "dbg")
    # passarelas cobertas verdes: espinha ao longo do meio-fio e dois braços pelo estacionamento
    for x in (26, 30, 34, 38, 42, 46, 51):
        m.add_part("3062b", "lbg", x, 39, 0)
    run(m, 26, 52, 39, 3, "bright_green", catalog=PLATE_ROW)
    run(m, 26, 52, 39, 4, "bright_green")
    branch = {30, 47}
    for x in branch:
        for z in (42, 45, 48):
            m.add_part("3062b", "lbg", x, z, 0)
        run(m, 40, 49, x, 3, "bright_green", along="z", catalog=PLATE_ROW)
        run(m, 40, 49, x, 4, "bright_green", along="z")
    # faixa de mata entre os dois estacionamentos
    for x in range(23, 56, 2):
        if not {x, x + 1} & branch:
            tree(m, x, 44, big=True)
    # estacionamentos lotados: T2, a leste do T3 e do T1
    for z in (40, 41, 43, 46, 48, 49):
        cars(m, rng, 23, 57, z, skip=branch)
    for z in (39, 40, 42, 43, 45, 46, 48):
        cars(m, rng, 74, 85, z)
    for z in (36, 37, 39, 40, 42, 43):
        cars(m, rng, 17, 22, z)
    # edifício-garagem do T3: térreo ventilado, laje de estacionamento com carros e mureta
    box_walls(m, 58, 44, 72, 50, 0, ("lbg", VENT_ROW), ("lbg", VENT_ROW))
    m.add_part("3456", "dbg", 58, 44, 3)
    run(m, 58, 72, 44, 4, "lbg", catalog=PLATE_ROW)
    run(m, 58, 72, 49, 4, "lbg", catalog=PLATE_ROW)
    for z in (45, 47, 48):
        cars(m, rng, 58, 72, z, level=4)
    for x in range(3, 16, 3):                              # carretas nas docas do TECA
        m.add_part("3069b", "white", x, 37, 0, 90)
    # galpões de apoio (comissária, manutenção) e terraplenagem a leste
    m.add_part("2456", "lbg", 87, 38, 0)
    m.add_part("69729", "white", 87, 38, 3)
    m.add_part("2456", "lbg", 89, 41, 0)
    m.add_part("69729", "white", 89, 41, 3)
    run(m, 86, 96, 48, 0, "dark_orange", catalog=PLATE_ROW)
    run(m, 87, 96, 47, 0, "dark_orange", catalog=PLATE_ROW)
    # calçadas, vias de meio-fio, acessos, marginal e Rodovia Hélio Smidt
    walks = rect(26, 36, 39, 37) | rect(26, 39, 52, 40) | rect(30, 40, 31, 50) | rect(47, 40, 48, 50) | rect(58, 42, 72, 43)
    pave(m, walks, "lbg", big=None)
    roads = (rect(22, 37, 58, 39) | rect(17, 34, 26, 35) | rect(22, 35, 23, 50) | rect(57, 39, 58, 50)
             | rect(57, 43, 73, 44) | rect(73, 36, 74, 50) | rect(0, 50, 96, 53) | rect(1, 37, 17, 43)
             | rect(23, 42, 57, 43) | rect(23, 47, 57, 48) | rect(74, 41, 85, 42) | rect(74, 44, 85, 45)
             | rect(74, 47, 85, 48) | rect(74, 49, 85, 50) | rect(17, 38, 22, 39) | rect(17, 41, 22, 42))
    pave(m, roads, "dbg", big=None)
    # árvores soltas no lado terra
    for x, z, big in ((19, 45, True), (20, 47, False), (17, 48, True), (24, 35, False), (11, 44, True), (13, 46, False),
                      (14, 44, False), (88, 45, True), (91, 45, False), (86, 37, False), (94, 44, True), (75, 37, False),
                      (83, 37, True), (78, 38, False), (93, 39, False), (16, 46, False)):
        need = rect(x, z, x + 2, z + 2) if big else {(x, z)}
        if not need & m.ground_cells():
            tree(m, x, z, big=big)


# ------------------------------------------------------------------------ 6 cidade
ROOFS = ["dark_orange"] * 7 + ["reddish_brown"] * 4 + ["lbg"] * 4 + ["tan"] * 2 + ["dark_tan"] * 2 + ["white", "dbg"]


def city_block(m, rng, x0, z0, w, d):
    """Quarteirão visto do alto: mosaico miúdo de lotes (placas na cor do telhado: cerâmica,
    fibrocimento, laje), casas de duas águas, sobrados com caixa-d'água, algum prédio e
    árvores; às vezes um galpão industrial."""
    cells = rect(x0, z0, x0 + w, z0 + d)
    if rng.random() < 0.1 and w >= 4 and d >= 4:
        m.fill_layers(None, (0, 1), "lbg", cells=cells)
        m.add_part("2456" if w >= 6 else "3001", "lbg", x0, z0 + 1, 1)
        m.add_part("69729" if w >= 6 else "87079", "white", x0, z0 + 1, 4)
        return
    if rng.random() < 0.3:                                 # prédio de apartamentos
        x, z = rng.randrange(x0, x0 + w - 1), rng.randrange(z0, z0 + d - 1)
        col = rng.choice(["white", "tan", "lbg"])
        m.add_part("3003", col, x, z, 0)
        m.add_part("3003", col, x, z, 3)
        m.add_part("3068b", "lbg", x, z, 6)
        cells -= rect(x, z, x + 2, z + 2)
    while cells:
        x, z = min(cells, key=lambda c: (c[1], c[0]))
        square = {(x + 1, z), (x, z + 1), (x + 1, z + 1)} <= cells
        pair = (x + 1, z) in cells
        r = rng.random()
        if square and r < 0.12:                            # casa de duas águas
            col = rng.choice(["dark_orange", "dark_orange", "reddish_brown"])
            m.add_part("85984", col, x, z, 0, 180)
            m.add_part("85984", col, x, z + 1, 0, 0)
            cells -= rect(x, z, x + 2, z + 2)
        elif square and r < 0.45:
            m.add_part("3022", rng.choice(ROOFS), x, z, 0)
            cells -= rect(x, z, x + 2, z + 2)
        elif pair and r < 0.75:
            m.add_part("3023", rng.choice(ROOFS), x, z, 0)
            cells -= {(x, z), (x + 1, z)}
        elif pair and r < 0.82:                            # sobrado, às vezes com caixa-d'água
            m.add_part("3004", rng.choice(["white", "tan", "lbg"]), x, z, 0)
            if rng.random() < 0.4:
                m.add_part("3794b", "lbg", x, z, 3)
                m.add_part("98138", "blue", x + 0.5, z, 4)
            cells -= {(x, z), (x + 1, z)}
        elif r < 0.9:
            tree(m, x, z)
            cells.discard((x, z))
        else:
            m.add_part("3024", rng.choice(ROOFS), x, z, 0)
            cells.discard((x, z))


def stage_city(m, rng):
    m.group = STAGES[5]
    streets_x = list(range(6, WIDTH, 7))
    for x in streets_x:                                    # ruas norte-sul
        run(m, 54, DEPTH, x, 0, "dbg", along="z")
    for z in (54, 59):                                     # ruas leste-oeste
        run(m, 0, WIDTH, z, 0, "dbg", skip=set(streets_x))
    edges = [0] + [x + 1 for x in streets_x]
    for i, x0 in enumerate(edges):
        x1 = streets_x[i] if i < len(streets_x) else WIDTH
        for z0, z1 in ((55, 59), (60, DEPTH)):
            city_block(m, rng, x0, z0, x1 - x0, z1 - z0)
    for x in range(1, WIDTH - 1, 3):                       # arborização ao longo da rodovia
        tree(m, x, 53, big=x % 2 == 0)
    # bairros ao sul (Cumbica) e na cabeceira oeste
    for x0, z0, w, d in ((50, 0, 6, 4), (57, 0, 6, 4), (64, 0, 6, 4), (71, 0, 6, 4), (78, 0, 6, 4), (85, 0, 6, 4),
                         (0, 0, 5, 4), (6, 0, 5, 4), (12, 0, 5, 3)):
        city_block(m, rng, x0, z0, w, d)
    run(m, 48, WIDTH, 4, 0, "dbg")


# ------------------------------------------------------------------------ 2 pátios
def stage_aprons(m):
    m.group = STAGES[1]
    pave(m, TAXILANES, "dbg", big=None)                    # pistas de táxi do pátio, em asfalto
    pave(m, APRON, "lbg")                                  # pátios em placas de concreto


# ------------------------------------------------------------------------ montagem
def build(upto=len(STAGES), render=True, size=1400):
    os.makedirs(RENDERS, exist_ok=True)
    rng = random.Random(1985)                              # ano da inauguração de Cumbica
    m = bk.Model("Aeroporto Internacional de Guarulhos (GRU) - microescala")
    stage_base(m)                                          # os prédios entram antes do pavimento,
    stage_terminals(m)                                     # que só ocupa o que sobrou livre
    stage_airside(m)
    stage_landside(m, rng)
    stage_city(m, rng)
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
