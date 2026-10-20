"""Aeroporto Internacional de Guarulhos (GRU) inteiro, em microescala LEGO.

Pistas 09L/27R e 09R/27L, taxiway paralela, pátios, Terminal 1, os dois módulos do
Terminal 2 (ex-TPS1 e TPS2: telhado escuro listrado e píeres em Π), Terminal 3 com o píer
de pontes, torre, terminal de cargas (TECA), hangar, bombeiros, parque de combustível e o
lado terra: viadutos de embarque, estacionamento com as passarelas cobertas verdes,
edifício-garagem, hotel e a Rodovia Hélio Smidt. Só peças da biblioteca LDraw oficial.

Grade de trabalho: x 0..96 (oeste → leste), z 0..48 (pistas → rodovia), alturas em plates
com o topo das baseplates no nível 0; pavimento (placas e tiles) vai do 0 ao 1. No fim o
layout é espelhado de frente para trás (Model.mirror_z), para ficar como o real visto de
cima com o norte para cima: pistas ao norte, T1 a oeste, T3 a leste; a frente do modelo
passa a ser o lado da rodovia. Os fingers ficam do lado esquerdo dos aviões depois disso.
Uso: python3 build_gru.py [--etapa N] [--sem-render] [--final]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import brickkit as bk  # noqa: E402

RENDERS = os.path.join(HERE, "renders")
PAVE = 1  # topo do pavimento

TILE_ROW = {n: bk.TILES[(1, n)] for n in (1, 2, 3, 4, 6, 8)}
PLATE_ROW = {n: bk.PLATES[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
BRICK_ROW = {n: bk.BRICKS[(1, n)] for n in (1, 2, 3, 4, 6, 8, 10, 12)}
GLASS_ROW = {1: "3005", 2: "3065", 4: "3066", 6: "3067b"}
GRILLE_ROW = {1: "3005", 2: "2877"}

LIVERIES = {  # fuselagem, cauda, detalhe da cauda, motores
    "LATAM": ("white", "dark_blue", "red", "lbg"),
    "LATAM Cargo": ("white", "dark_blue", "dark_blue", "lbg"),
    "GOL": ("white", "orange", "orange", "lbg"),
    "Azul": ("white", "blue", "white", "blue"),
    "TAP": ("white", "red", "green", "lbg"),
    "Emirates": ("white", "red", "green", "lbg"),
    "American": ("lbg", "blue", "red", "lbg"),
}


# ------------------------------------------------------------------------ helpers
def run(m, a0, a1, fixed, level, color, marks=(), along="x", catalog=TILE_ROW, studs=()):
    """1-wide row from a0 to a1 (exclusive), longest pieces first.

    marks: (b0, b1, color[, catalog]) segments with their own colour/pieces; studs: cells
    that get a 1x1 plate instead of a tile, so something can stand there.
    """
    cell = {a: (color, catalog) for a in range(a0, a1)}
    for mark in marks:
        for a in range(mark[0], mark[1]):
            cell[a] = (mark[2], mark[3] if len(mark) > 3 else catalog)
    a = a0
    while a < a1:
        col, cat = cell[a]
        if a in studs:
            pieces, b = [(a, PLATE_ROW[1])], a + 1
        else:
            b = a
            while b < a1 and cell[b] == (col, cat) and b not in studs:
                b += 1
            pieces, pos = [], a
            while pos < b:
                n = max(k for k in cat if k <= b - pos)
                pieces.append((pos, cat[n]))
                pos += n
        for pos, pid in pieces:
            if along == "x":
                m.add_part(pid, col, pos, fixed, level, 0)
            else:
                m.add_part(pid, col, fixed, pos, level, 90)
        a = b


def tile_roof(m, x0, x1, z0, z1, level, color, hvac=()):
    """Roof of 2-deep rows of 2x6/2x4/2x2 tiles in running bond; hvac = 2x2 grille units (x, z)."""
    units = {(x, z) for x, z in hvac}
    for row, z in enumerate(range(z0, z1 - 1, 2)):
        x = x0
        if row % 2 and x1 - x0 >= 4:
            m.add_part("3068b", color, x, z, level)
            x += 2
        while x < x1:
            nxt = min([u[0] for u in units if u[1] == z and u[0] >= x] + [x1])
            if (x, z) in units:
                m.add_part("2412b", "lbg", x, z, level)
                m.add_part("2412b", "lbg", x, z + 1, level)
                x += 2
                continue
            for w, pid in ((6, "69729"), (4, "87079"), (2, "3068b")):
                if x + w <= nxt:
                    m.add_part(pid, color, x, z, level)
                    x += w
                    break
            else:
                run(m, z, z + 2, x, level, color, along="z")
                x += 1
    if (z1 - z0) % 2:
        run(m, x0, x1, z1 - 1, level, color)


def narrowbody(liv):
    body, tail, accent, engine = LIVERIES[liv]
    return [("6141", "black", 0, 4, 0, 0), ("6141", engine, -1, 2, 0, 0), ("6141", engine, 1, 2, 0, 0),
            ("3710", body, 0, 1, 1, 90), ("24307", body, -2, 2, 1, 90), ("24299", body, 1, 2, 1, 270),
            ("3623", body, -1, 0, 1, 0), ("3040b", tail, 0, 0, 2, 180), ("54200", accent, 0, 0, 5, 180),
            ("63864", body, -1, 2, 2, 0), ("3070b", "black", 0, 3, 2, 0), ("98138", body, 0, 4, 2, 0)]


def widebody(liv):
    body, tail, accent, engine = LIVERIES[liv]
    return [("6141", "black", 0, 6, 0, 0), ("6141", engine, -2, 2, 0, 0), ("6141", engine, 2, 2, 0, 0),
            ("3666", body, 0, 1, 1, 90), ("43722", body, -3, 2, 1, 90), ("43723", body, 1, 2, 1, 270),
            ("3623", body, -1, 0, 1, 0), ("3040b", tail, 0, 0, 2, 180), ("54200", accent, 0, 0, 5, 180),
            ("63864", body, -1, 2, 2, 0), ("3069b", body, 0, 3, 2, 90), ("3070b", "black", 0, 5, 2, 0),
            ("98138", body, 0, 6, 2, 0)]


def a380(liv):
    body, tail, accent, engine = LIVERIES[liv]
    return [("6141", "black", 0, 8, 0, 0), ("6141", engine, -2, 4, 0, 0), ("6141", engine, -3, 3, 0, 0),
            ("6141", engine, 2, 4, 0, 0), ("6141", engine, 3, 3, 0, 0),
            ("3460", body, 0, 1, 1, 90), ("41769", body, -4, 3, 1, 90), ("41770", body, 1, 3, 1, 270),
            ("3623", body, -1, 0, 1, 0), ("3040b", tail, 0, 0, 2, 180), ("54200", accent, 0, 0, 5, 180),
            ("3070b", body, 0, 2, 2, 0), ("26603", body, -1, 3, 2, 0), ("3069b", body, 0, 5, 2, 90),
            ("3070b", "black", 0, 7, 2, 0), ("98138", body, 0, 8, 2, 0)]


MODELS = {"narrow": (narrowbody, 5, 5), "wide": (widebody, 7, 7), "a380": (a380, 9, 9)}

# (modelo, companhia, coluna da fuselagem, z da cauda, rumo); rumo 0 = nariz para o fundo (+z).
# Com rumo 90/270 (avião atravessado) os campos são a fileira da fuselagem e o x mínimo.
PLANES = [
    ("narrow", "Azul", 36, 13, 0), ("narrow", "GOL", 27, 21, 0), ("narrow", "GOL", 33, 21, 0),     # T2 A
    ("narrow", "LATAM", 54, 13, 0), ("narrow", "LATAM", 45, 21, 0), ("narrow", "Azul", 51, 21, 0),  # T2 B
    ("a380", "Emirates", 64, 14, 0), ("wide", "LATAM", 73, 16, 0),                                 # T3
    ("narrow", "TAP", 80, 18, 0), ("narrow", "American", 85, 18, 0),
    ("narrow", "GOL", 13, 21, 0), ("narrow", "Azul", 18, 21, 0),                                   # T1
    ("wide", "LATAM Cargo", 4, 19, 0),                                                             # TECA
    ("narrow", "Azul", 92, 19, 180),                                                               # hangar
    ("narrow", "LATAM", 7, 5, 90),                                                                 # pista 09R
    ("narrow", "GOL", 11, 62, 270),                                                                # taxiway
]


def plane_specs(model, airline):
    return MODELS[model][0](airline)


def plane_at(model, column, tail_z, heading):
    """Minimum corner of the plane footprint, from its fuselage column and tail row (rumo 0/180)
    or, for rumo 90/270, from the fuselage row and the tail column."""
    fn, length, span = MODELS[model]
    half = (span - 1) // 2
    if heading in (0, 180):
        return column - half, tail_z
    return tail_z, column - half


def gear_cells():
    """Cells under the gear of the planes standing on tiles (runway and taxiway)."""
    cells = set()
    for model, airline, col, tail, heading in PLANES:
        if heading in (90, 270):
            specs = plane_specs(model, airline)
            for spec, (x, z, _, _) in zip(specs, bk.local_rects(specs, plane_at(model, col, tail, heading), heading)):
                if spec[4] == 0:
                    cells.add((int(x), int(z)))
    return cells


def jetbridge(m, x, z_terminal, n=2):
    """Finger LBG de n studs saindo para o norte (−z) da fachada em z_terminal, na coluna x."""
    specs = [("3062b", "lbg", 0, n - 1, 0, 0), (PLATE_ROW[n], "lbg", 0, 0, 3, 90),
             ("2412b" if n == 2 else TILE_ROW[n], "lbg", 0, 0, 4, 90)]
    m.place_local(specs, (x, z_terminal - n), 180, PAVE)


def car(m, x, z, level, color, rot=0, kind="car"):
    if kind == "car":
        m.add_part("3023", color, x, z, level, rot)
        m.add_part("3069b", color, x, z, level + 1, rot)
    elif kind == "hatch":  # para-brisa inclinado na frente
        m.add_part("3023", color, x, z, level, rot)
        m.add_part("54200", "trans_black", x + (rot == 0), z + (rot == 90), level + 1, (270 - rot) % 360)
        m.add_part("3070b", color, x, z, level + 1)
    elif kind == "taxi":
        m.add_part("3023", "white", x, z, level, rot)
        m.add_part("2412b", "white", x, z, level + 1, rot)
    elif kind == "bus":
        m.add_part("3710", color, x, z, level, rot)
        m.add_part("2431", "white", x, z, level + 1, rot)
    elif kind == "truck":  # chassi, baú e cabine
        m.add_part("3623", "dbg", x, z, level, rot)
        m.add_part("3004", color, x, z, level + 1, rot)
        m.add_part("3070b", "trans_clear", x + 2 * (rot == 0), z + 2 * (rot == 90), level + 1)


def tree(m, x, z, level=0, kind="pine"):
    if kind == "pine":
        m.add_part("6141", "reddish_brown", x, z, level)
        m.add_part("4589", "dark_green" if (x + z) % 2 else "green", x, z, level + 1)
    elif kind == "round":
        m.add_part("6141", "reddish_brown", x, z, level)
        m.add_part("4032a", "green", x - 0.5, z - 0.5, level + 1)
    else:
        m.add_part("33291", "bright_green", x, z, level)


# ------------------------------------------------------------------------ etapas
def stage_base(m):
    m.group = "1 base e pistas"
    m.add_part("4186", "green", 0, 0, -0.5)
    m.add_part("4186", "green", 48, 0, -0.5)
    studs = gear_cells()
    for x0, x1, z0 in ((9, 87, 1), (0, 96, 6)):   # 09L/27R (3.000 m) e 09R/27L (3.700 m)
        edge = [(x0 + 1, x0 + 4, "white"), (x0 + 10, x0 + 14, "white"),
                (x1 - 14, x1 - 10, "white"), (x1 - 4, x1 - 1, "white")]
        avail = (x1 - 6) - (x0 + 6)
        n = (avail + 4) // 7
        start = x0 + 6 + (avail - (7 * n - 4)) // 2
        centre = [(d, d + 3, "white") for d in range(start, start + 7 * n, 7)]
        for dz, marks in ((0, edge), (1, centre), (2, edge)):
            run(m, x0, x1, z0 + dz, 0, "dbg", marks, studs={x for x, z in studs if z == z0 + dz})
    run(m, 0, 96, 0, 0, "dark_azure")              # Rio Baquirivu-Guaçu, na divisa norte
    for x in (2, 4, 6, 89, 91, 93):                # luzes de aproximação da 09L/27R
        m.add_part("6141", "trans_clear", x, 2, 0)
    for x in (18, 46, 74):                         # ligações entre as pistas
        m.add_part("3068b", "dbg", x, 4, 0)
    for x in (12, 34, 58, 82):                     # saídas da 09R para a taxiway
        m.add_part("3069b", "dbg", x, 9, 0)
    for z, color in ((10, "dbg"), (11, "yellow"), (12, "dbg")):   # taxiway paralela
        run(m, 0, 96, z, 0, color, studs={x for x, zz in studs if zz == z})


def stage_aprons(m):
    m.group = "2 pátios e sinalização"
    m.fill_layers((0, 13, 96, 33), (0, 1), "lbg", seams={"x": [48]})
    for model, airline, col, tail, heading in PLANES:  # linhas de entrada atrás das caudas
        if heading == 0 and tail > 13:
            run(m, max(13, tail - 3), tail, col, PAVE, "yellow", along="z")
    for x in (20, 39, 58, 88):                         # torres de iluminação do pátio
        m.add_part("3957a", "lbg", x, 15, PAVE)
    for x, z, color in ((15, 9, "yellow"), (37, 9, "yellow"), (55, 9, "yellow"), (85, 9, "yellow"),
                        (24, 5, "red"), (68, 5, "red")):  # placas de taxiway e de pista
        m.add_part("85984", color, x, z, 0)


def t2_module(m, x0):
    north, south = 27, 32
    for level, color_n, cat_n, color_s, cat_s in ((1, "lbg", BRICK_ROW, "lbg", BRICK_ROW),
                                                  (4, "black", GRILLE_ROW, "trans_clear", GLASS_ROW)):
        run(m, x0, x0 + 18, north, level, color_n, catalog=cat_n)
        run(m, x0, x0 + 18, south, level, color_s, catalog=cat_s)
        run(m, north + 1, south, x0, level, "lbg", along="z", catalog=BRICK_ROW)
        run(m, north + 1, south, x0 + 17, level, "lbg", along="z", catalog=BRICK_ROW)
    m.fill_layers((x0, 27, x0 + 18, 34), (7, 8), "lbg")      # laje + marquise sobre o meio-fio
    run(m, x0, x0 + 18, 27, 8, "lbg")
    m.add_part("69729", "lbg", x0, 28, 8, 90)                   # telhado listrado escuro, pontas claras
    for i in range(5):
        m.add_part("69729", "dbg", x0 + 2 + 3 * i, 28, 8, 90)
        m.add_part("6636", "black", x0 + 4 + 3 * i, 28, 8, 90)
    m.add_part("6636", "lbg", x0 + 17, 28, 8, 90)
    for px in (x0 + 1, x0 + 15):                                # píeres envidraçados
        for x in (px, px + 1):
            run(m, 19, 27, x, PAVE, "trans_clear", along="z", catalog=GLASS_ROW)
        m.add_part("3034", "lbg", px, 19, 4, 90)
        m.add_part("87079", "white", px, 19, 5, 90)
        m.add_part("87079", "white", px, 23, 5, 90)


def stage_terminals(m):
    m.group = "3 terminais"
    t2_module(m, 21)   # Terminal 2, ex-TPS1
    t2_module(m, 39)   # Terminal 2, ex-TPS2
    # Terminal 3: píer envidraçado ao longo do pátio e prédio principal de 3 andares
    m.fill_layers((60, 24, 88, 25), (PAVE, 4), "trans_clear", "glass")
    run(m, 25, 28, 60, PAVE, "white", along="z", catalog=BRICK_ROW)
    run(m, 25, 28, 87, PAVE, "white", along="z", catalog=BRICK_ROW)
    pier = m.fill_layers((60, 24, 88, 28), (4, 5), "lbg")
    m.fill_layers((60, 24, 88, 28), (5, 6), "white", "tile", below=pier)
    for x, z in ((62, 28), (62, 32), (85, 28), (85, 32)):
        m.add_part("14716", "white", x, z, PAVE)
    for x in (69, 78):
        m.add_part("14716", "white", x, 32, PAVE)
    for level in (1, 4, 7):
        for a, b in ((63, 69), (70, 78), (79, 85)):            # vidro entre os pilares
            run(m, a, b, 32, level, "trans_clear", catalog=GLASS_ROW)
        run(m, 63, 85, 28, level, "lbg" if level == 1 else "trans_clear",
            catalog=BRICK_ROW if level == 1 else GLASS_ROW)
        run(m, 29, 32, 62, level, "white", along="z", catalog=BRICK_ROW)
        run(m, 29, 32, 85, level, "white", along="z", catalog=BRICK_ROW)
    # cobertura com marquise de 2 studs: placas de 8 de fundo para a marquise ficar presa às paredes
    m.fill_layers((61, 27, 87, 35), (10, 11), "white", sizes={(8, 16), (8, 8), (2, 8)})
    tile_roof(m, 61, 87, 27, 31, 11, "white", hvac=[(64, 29), (71, 27), (79, 29)])
    tile_roof(m, 61, 87, 33, 35, 11, "white")
    m.add_part("3068b", "white", 61, 31, 11)
    m.add_part("3068b", "white", 85, 31, 11)
    for z in (31, 32):                                          # lanternim de vidro no meio da cobertura
        run(m, 63, 85, z, 11, "trans_clear", catalog=GLASS_ROW)
    m.fill_layers((63, 31, 85, 33), (14, 15), "white")
    tile_roof(m, 63, 85, 31, 33, 15, "white")
    # Terminal 1 (ex-TPS4): baixo, com janelas
    win = [(13, 15, "trans_clear", GLASS_ROW), (17, 19, "trans_clear", GLASS_ROW)]
    run(m, 12, 20, 28, PAVE, "white", win, catalog=BRICK_ROW)
    run(m, 12, 20, 32, PAVE, "white", win, catalog=BRICK_ROW)
    run(m, 29, 32, 12, PAVE, "white", along="z", catalog=BRICK_ROW)
    run(m, 29, 32, 19, PAVE, "white", along="z", catalog=BRICK_ROW)
    m.add_part("3033", "lbg", 11, 27, 4)
    for x in range(11, 21):                                     # cobertura em abóbada
        m.add_part("93273", "white", x, 28, 5)
    run(m, 11, 21, 27, 5, "lbg")
    run(m, 11, 21, 32, 5, "lbg")
    # Terminal de cargas (TECA): galpão com docas e telhado em dente de serra
    docks = [(1, 3, "dbg"), (4, 6, "dbg"), (7, 9, "dbg")]
    run(m, 0, 10, 27, PAVE, "lbg", docks, catalog=BRICK_ROW)
    run(m, 0, 10, 27, 4, "lbg", catalog=GRILLE_ROW)
    for level, color in ((1, "lbg"), (4, "white")):
        run(m, 0, 10, 32, level, color, catalog=BRICK_ROW)
        run(m, 28, 32, 0, level, color, along="z", catalog=BRICK_ROW)
        run(m, 28, 32, 9, level, color, along="z", catalog=BRICK_ROW)
    m.add_part("3033", "lbg", 0, 27, 7)
    for z in (27, 29, 31):
        m.add_part("3037", "white", 0, z, 8)
        m.add_part("3037", "white", 4, z, 8)
        m.add_part("3039", "white", 8, z, 8)


def stage_airside(m):
    m.group = "4 torre e lado ar"
    tx, tz = 57, 25                                             # torre de controle
    m.add_part("3941", "white", tx, tz, PAVE)
    m.add_part("3941", "white", tx, tz, PAVE + 3)
    m.add_part("87580", "white", tx, tz, PAVE + 6)
    for i in range(6):
        m.add_part("3062b", "white", tx + 0.5, tz + 0.5, PAVE + 7 + 3 * i)
    top = PAVE + 25
    m.add_part("4032a", "white", tx, tz, top)
    for dx in (0, 1):
        for dz in (0, 1):
            m.add_part("3062b", "trans_black", tx + dx, tz + dz, top + 1)
    m.add_part("4032a", "dbg", tx, tz, top + 4)
    m.add_part("4740", "lbg", tx, tz, top + 5)
    m.add_part("3957a", "white", tx + 0.5, tz + 0.5, top + 6)
    for level in (1, 4, 7):                                     # hangar com teto em arco
        run(m, 18, 26, 88, level, "white", along="z", catalog=BRICK_ROW)
        run(m, 18, 26, 95, level, "white", along="z", catalog=BRICK_ROW)
        run(m, 89, 95, 25, level, "lbg", catalog=BRICK_ROW)
    for z in range(18, 26):
        m.add_part("61678", "white", 88, z, 10, 90)
        m.add_part("61678", "white", 92, z, 10, 270)
    run(m, 89, 95, 28, PAVE, "red", catalog={1: "3005", 2: "3004"})   # bombeiros (SCI): 3 portões
    run(m, 89, 95, 31, PAVE, "white", catalog=BRICK_ROW)
    run(m, 29, 31, 89, PAVE, "white", along="z", catalog=BRICK_ROW)
    run(m, 29, 31, 94, PAVE, "white", along="z", catalog=BRICK_ROW)
    m.add_part("3032", "red", 89, 28, 4)
    m.add_part("2453b", "red", 95, 29, PAVE)                    # torre de treinamento
    for x in (88, 92):                                          # cerca do lado ar
        m.add_part("30055", "white", x, 33, 0)
    for x in (89, 92):
        m.add_part("3623", "red", x, 26, PAVE)
        m.add_part("3069b", "red", x, 26, PAVE + 1)
        m.add_part("3070b", "trans_clear", x + 2, 26, PAVE + 1)
    for x, z, pid, color, rot in ((9, 24, "54200", "lbg", 90), (10, 24, "54200", "white", 90),
                                  (9, 25, "54200", "lbg", 90), (10, 25, "3024", "dbg", 0),
                                  (10, 22, "6141", "yellow", 0)):   # contêineres LD3 e trator
        m.add_part(pid, color, x, z, PAVE, rot)


def stage_bridges(m):
    """Fingers na coluna col + 1: depois do espelhamento ficam na porta esquerda do avião."""
    m.group = "5 pontes de embarque"
    for model, airline, col, tail, heading in PLANES:
        if heading != 0:
            continue
        if tail == 13 and 21 <= col <= 57:
            jetbridge(m, col + 1, 19)          # ponta do píer do T2
        elif 21 <= col <= 57 and tail == 21:
            jetbridge(m, col + 1, 27)          # fachada do T2 entre os píeres
        elif col >= 60:
            jetbridge(m, col + 1, 24)          # píer do T3
    jetbridge(m, 66, 24, 3)                    # segunda ponte do A380 (deck superior)


def stage_planes(m):
    for model, airline, col, tail, heading in PLANES:
        m.group = f"6 aviões ({airline})"
        m.place_local(plane_specs(model, airline), plane_at(model, col, tail, heading), heading, PAVE)
    m.group = "6 veículos de pátio"
    for x in (12, 16):                                          # ônibus de pátio do T1
        car(m, x, 27, PAVE, "blue", kind="bus")
    m.add_part("3040b", "lbg", 12, 25, PAVE, 180)               # escadas
    m.add_part("3040b", "lbg", 17, 25, PAVE, 180)
    for x, z in ((70, 21), (77, 21)):                           # trens de bagagem
        m.add_part("6141", "yellow", x, z, PAVE)
        m.add_part("3070b", "lbg", x, z - 1, PAVE)
        m.add_part("3070b", "lbg", x, z - 2, PAVE)
    m.add_part("3023", "white", 58, 21, PAVE, 90)               # caminhão-tanque
    m.add_part("3069b", "lbg", 58, 21, PAVE + 1, 90)
    for x in (30, 48):                                          # caminhões de catering entre os aviões do T2
        m.add_part("3023", "white", x, 22, PAVE, 90)
        m.add_part("3004", "white", x, 22, PAVE + 1, 90)
    m.add_part("3024", "dbg", 64, 23, PAVE)                     # trator de pushback do A380
    m.add_part("3070b", "yellow", 64, 23, PAVE + 1)


def stage_landside(m):
    m.group = "7 lado terra"
    m.fill_layers((11, 33, 88, 37), (0, 1), "dbg", seams={"x": [48]})   # vias de meio-fio
    for x0, x1, piers in ((21, 57, (23, 31, 39, 47, 55)), (60, 88, (62, 70, 78, 85))):
        for x in piers:                                         # viadutos de embarque
            m.add_part("3941", "lbg", x, 34, PAVE)
        m.fill_layers((x0, 33, x1, 37), (4, 5), "dbg")
        run(m, x0, x1, 33, 5, "lbg")                            # calçada
        run(m, x0, x1, 36, 5, "white")                          # guarda-corpo
    for x, z, color, kind in ((24, 34, "white", "taxi"), (33, 35, "red", "hatch"), (41, 34, "white", "taxi"),
                              (48, 35, "blue", "bus"), (64, 34, "yellow", "car"), (72, 35, "white", "taxi"),
                              (80, 34, "white", "bus"), (14, 35, "dark_red", "hatch"), (18, 34, "white", "car")):
        car(m, x, z, 5 if x > 20 else PAVE, color, kind=kind)
    for z in (33, 36):                                          # abrigo de ônibus com teto curvo
        m.add_part("3062b", "lbg", 12, z, PAVE)
    m.add_part("93273", "white", 12, 33, 4)
    m.fill_layers((21, 37, 57, 43), (0, 1), "dbg", seams={"x": [48]})   # estacionamento do T2
    for i, (x, z, color) in enumerate(((22, 38, "red"), (24, 38, "white"), (26, 38, "lbg"), (31, 38, "blue"),
                                       (33, 38, "white"), (37, 38, "black"), (43, 38, "dark_red"), (50, 38, "white"),
                                       (53, 38, "yellow"), (24, 41, "lbg"), (32, 41, "red"), (44, 41, "white"),
                                       (52, 41, "blue"), (55, 41, "white"))):
        car(m, x, z, PAVE, color, rot=90, kind=("car", "hatch", "car", "hatch", "taxi")[i % 5])
    for x in (29, 47):                                          # passarelas cobertas verdes
        m.add_part("3062b", "lbg", x, 38, PAVE)
        m.add_part("3062b", "lbg", x, 42, PAVE)
        m.add_part("3666", "bright_green", x, 37, 4, 90)
        m.add_part("6636", "bright_green", x, 37, 5, 90)
    for x in (34, 41):
        m.add_part("3062b", "lbg", x, 40, PAVE)
    run(m, 30, 46, 40, 4, "bright_green", catalog=PLATE_ROW)
    run(m, 30, 46, 40, 5, "bright_green")
    m.add_part("3032", "lbg", 57, 38, 0, 90)                    # hotel
    run(m, 38, 44, 57, PAVE, "trans_clear", along="z", catalog=GLASS_ROW)
    run(m, 38, 44, 60, PAVE, "trans_clear", along="z", catalog=GLASS_ROW)
    run(m, 58, 60, 38, PAVE, "trans_clear", catalog=GLASS_ROW)
    run(m, 58, 60, 43, PAVE, "trans_clear", catalog=GLASS_ROW)
    for x, z, rot in [(57, z, 90) for z in (38, 40, 42)] + [(60, z, 90) for z in (38, 40, 42)] + [(58, 38, 0), (58, 43, 0)]:
        frame = m.add_part("60592", "white", x, z, 4, rot)
        m.add_inset("60601", "trans_light_blue", frame)
    run(m, 38, 44, 57, 10, "white", along="z", catalog=BRICK_ROW)
    run(m, 38, 44, 60, 10, "white", along="z", catalog=BRICK_ROW)
    run(m, 58, 60, 38, 10, "white", catalog=BRICK_ROW)
    run(m, 58, 60, 43, 10, "white", catalog=BRICK_ROW)
    m.add_part("3032", "white", 57, 38, 13, 90)
    m.add_part("69729", "white", 57, 38, 14, 90)
    m.add_part("2412b", "lbg", 59, 41, 14, 90)
    m.add_part("3957a", "white", 60, 39, 14)
    m.add_part("3027", "dbg", 66, 37, 0)                        # edifício-garagem do T3
    for level in (PAVE, 5):
        for x in (66, 73, 81):
            for z in (37, 42):
                m.add_part("3062b", "lbg", x, z, level)
        m.add_part("3027", "dbg", 66, 37, level + 3)
    for x in (66, 74):
        m.add_part("4162", "lbg", x, 37, 9)
        m.add_part("4162", "lbg", x, 42, 9)
    for x in (67, 74):                                          # guarda-corpo vazado do 1º piso
        m.add_part("3633", "lbg", x, 37, 5)
        m.add_part("3633", "lbg", x, 42, 5)
    for x, color in ((68, "white"), (70, "red"), (75, "blue"), (78, "lbg")):
        car(m, x, 39, 9, color, rot=90)
    m.add_part("41539", "lbg", 1, 35, 0)                        # parque de combustível
    for i, (x, z) in enumerate(((2, 36), (6, 36), (2, 40), (6, 40))):
        m.add_part("3941", "white", x, z, PAVE)
        m.add_part("4032a" if i % 2 else "4740", "white", x, z, PAVE + 3)
    m.add_part("3633", "lbg", 1, 35, PAVE)
    m.add_part("3633", "lbg", 5, 35, PAVE)
    m.add_part("3033", "dbg", 11, 37, 0)                        # estacionamento do T1
    for x, color in ((12, "white"), (14, "lbg"), (17, "red"), (19, "white")):
        car(m, x, 38, PAVE, color, rot=90)
    m.fill_layers((0, 44, 96, 48), (0, 1), "dbg", seams={"x": [48]})   # Rodovia Hélio Smidt
    for x in range(2, 96, 8):
        m.add_part("3069b", "white", x, 46, PAVE)
    for x, z, color, kind in ((6, 44, "red", "car"), (25, 45, "white", "car"), (40, 44, "blue", "truck"),
                              (63, 45, "white", "bus"), (82, 44, "lbg", "car"), (15, 47, "yellow", "car"),
                              (52, 47, "white", "truck"), (88, 47, "black", "car")):
        car(m, x, z, PAVE, color, kind=kind)
    hedge = [(x, 43, ("pine", "bush")[i % 2]) for i, x in enumerate((22, 25, 27, 31, 33, 37, 39, 43, 45, 49, 51, 55))]
    for x, z, kind in hedge + [(2, 33, "pine"), (6, 33, "pine"), (9, 34, "bush"), (62, 39, "round"),
                               (63, 42, "round"), (89, 38, "round"), (92, 40, "pine"), (94, 36, "round"),
                               (90, 42, "bush"), (13, 43, "pine"), (19, 43, "pine")]:
        tree(m, x, z, 0, kind)


STAGES = [("base_pistas", stage_base), ("patios", stage_aprons), ("terminais", stage_terminals),
          ("torre_lado_ar", stage_airside), ("pontes", stage_bridges), ("avioes", stage_planes),
          ("lado_terra", stage_landside)]


def build(upto=len(STAGES), render=True):
    os.makedirs(RENDERS, exist_ok=True)
    m = bk.Model("Aeroporto Internacional de Guarulhos (GRU) - microescala")
    ends = []
    for name, fn in STAGES[:upto]:
        fn(m)
        ends.append(len(m.parts))
    m.mirror_z(48)
    for i, ((name, _), end) in enumerate(zip(STAGES, ends), 1):
        stage = bk.Model(m.name)
        stage.parts = m.parts[:end]
        print(stage.describe(f"etapa {i}: {name}").split("\ninventário")[0])
        if render:
            path = os.path.join(RENDERS, f"etapa_{i}_{name}.png")
            stage.render(path, "iso_front_left", size=1400, caption=f"etapa {i}: {name} ({end} peças)")
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
        for view in ("iso_front_left", "top", "iso_back_right"):
            print("render:", m.render(os.path.join(RENDERS, f"final_{view}.png"), view, size=2000,
                                      caption=f"{cap} - {view}"))


if __name__ == "__main__":
    main()
