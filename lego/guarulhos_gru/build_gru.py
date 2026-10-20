"""Aeroporto Internacional de Guarulhos (GRU), Terminal 3, em microescala LEGO.

Monta o modelo por etapas (base, sinalização, terminal, torre, pontes, aviões, lado terra),
renderizando e descrevendo cada etapa, depois confere peças soltas/colisões e exporta
guarulhos_gru.ldr.

Grade: x 0..40 (esquerda→direita), z 0..32 (frente = lado ar → fundo = lado terra),
alturas em plates. Uso: python3 build_gru.py [--etapa N] [--sem-render]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import brickkit as bk  # noqa: E402

RENDERS = os.path.join(HERE, "renders")

GROUND = 2                  # topo do pátio/pista (2 camadas de plates)
TERM = (5, 19, 35, 26)      # caixa do terminal: x0, z0, x1, z1
ROOF = (4, 18, 36, 27)      # cobertura com beiral de 1 stud
WALL_TOP = 10               # paredes de 3 tijolos, do nível 1 ao 10
NOSE_Z = 17                 # todos os narizes param em z = 17
# (companhia, coluna da fuselagem, comprimento, asa, cauda, detalhe da cauda, motores)
STANDS = [("Azul", 10, 8, "2x3", "blue", "blue", "blue"),
          ("LATAM", 20, 10, "2x4", "dark_blue", "red", "lbg"),
          ("GOL", 30, 8, "2x3", "orange", "orange", "lbg")]
# sinalização sobre a pista (x0, z, comprimento, rot): borda branca, eixo branco, linhas de entrada
EDGE_LINE = [(x, 2, 8, 0) for x in range(0, 40, 8)]
CENTRE_LINE = [(x, 4, 3, 0) for x in range(0, 40, 5)]
LEAD_INS = [(c, 5, NOSE_Z - lf - 5, 90) for _, c, lf, *_ in STANDS]


def _cells(marks, z_max=99):
    """Rectangles covered by tile marks, clipped to z < z_max."""
    out = []
    for x, z, n, rot in marks:
        w, d = (n, 1) if rot == 0 else (1, n)
        out.append((x, z, x + w, min(z + d, z_max)))
    return out


def stage_base(m):
    m.group = "1 base"
    bottom = m.fill_layers((0, 0, 40, 32), (0, 1), "dbg", sizes={(16, 16), (8, 16)})  # estrutura
    zones = [((0, 0, 40, 2), "green"),            # grama na frente
             ((0, 2, 40, 7), "dbg"),              # pista de taxiamento
             ((2, 7, 38, 19), "lbg"),             # pátio de aeronaves
             ((0, 7, 2, 19), "green"), ((38, 7, 40, 19), "green"),
             ((0, 19, 5, 26), "green"),           # grama à esquerda do terminal
             ((35, 19, 40, 26), "lbg"),           # pátio da torre
             ((0, 26, 40, 32), "dbg")]            # via do lado terra
    for rect, color in zones:                     # cada zona cruza as emendas da estrutura
        m.fill_layers(rect, (1, 2), color, below=bottom)
    # asfalto liso na pista: tiles DBG em volta das faixas, que entram no mesmo nível
    marks = _cells(EDGE_LINE + CENTRE_LINE + LEAD_INS, z_max=7)
    m.fill_layers((0, 2, 40, 7), (GROUND, GROUND + 1), "dbg", "tile", exclude=marks)


def stage_signage(m):
    m.group = "2 sinalização"
    for x, z, n, rot in EDGE_LINE + CENTRE_LINE:  # faixa de borda e eixo tracejado, brancos
        m.add_part(bk.TILES[(1, n)], "white", x, z, GROUND, rot)
    for x, z, n, rot in LEAD_INS:                 # linhas de entrada nas posições, amarelas
        m.add_part(bk.TILES[(1, n)], "yellow", x, z, GROUND, rot)
    for _, c, *_ in STANDS:
        m.add_part("63864", "yellow", c - 1, NOSE_Z, GROUND)  # barra de parada
    for x in (15, 25):                            # separação entre posições
        m.add_part("2431", "yellow", x, 9, GROUND, 90)
        m.add_part("2431", "yellow", x, 13, GROUND, 90)


def stage_terminal(m):
    m.group = "3 terminal"
    x0, z0, x1, z1 = TERM
    for x, rot in ((x0, 270), (x1 - 1, 90)):      # laterais brancas
        m.add_part("14716", "white", x, z0, 1)
        m.add_part("4215b", "white", x, z0 + 1, 1, rot)
        m.add_part("14716", "white", x, z0 + 5, 1)
        m.add_part("14716", "white", x, z1 - 1, 1)
    pillars = [10, 17, 22, 29]
    bays = [(6, 10), (11, 17), (18, 22), (23, 29), (30, 34)]
    for z in (z0, z1 - 1):                        # fachadas de vidro, lado ar e lado terra
        for px in pillars:
            m.add_part("14716", "white", px, z, 1)
        for a, b in bays:
            m.fill_layers((a, z, b, z + 1), (1, WALL_TOP), "trans_clear", "glass")
    # interior visto pelo vidro: núcleo escuro de 2 tijolos e laje branca do piso de embarque
    m.fill_layers((8, 21, 32, 23), (1, 7), "dbg", "brick")
    m.fill_layers((6, 20, 34, 24), (7, 8), "white")
    m.fill_layers(ROOF, (WALL_TOP, WALL_TOP + 1), "white")
    # cobertura: arremate 1x8 na frente e painéis 2x4 em amarração corrida; a última fileira
    # cobre a emenda da faixa 1xN de placas do beiral de trás e a mantém presa
    rx0, rz0, rx1, rz1 = ROOF
    for x in range(rx0, rx1, 8):
        m.add_part("4162", "white", x, rz0, WALL_TOP + 1)
    hvac = {8, 14, 24, 30}
    for row, z in enumerate(range(rz0 + 1, rz1, 2)):
        x = rx0
        if row % 2 == 0:
            m.add_part("3068b", "white", x, z, WALL_TOP + 1)
            x += 2
        while x < rx1:
            if row == 1 and x in hvac:            # casa de máquinas: 2 grelhas 1x2
                m.add_part("2412b", "lbg", x, z, WALL_TOP + 1)
                m.add_part("2412b", "lbg", x, z + 1, WALL_TOP + 1)
                x += 2
            elif x + 4 <= rx1 and not (row == 1 and x + 2 in hvac):
                m.add_part("87079", "white", x, z, WALL_TOP + 1)
                x += 4
            else:
                m.add_part("3068b", "white", x, z, WALL_TOP + 1)
                x += 2


def stage_tower(m):
    m.group = "4 torre"
    tx, tz = 36, 20
    m.add_part("3941", "white", tx, tz, GROUND)
    m.add_part("3941", "white", tx, tz, GROUND + 3)
    m.add_part("87580", "white", tx, tz, GROUND + 6)          # jumper: 1 stud no centro
    for i in range(5):                                         # fuste fino
        m.add_part("3062b", "white", tx + 0.5, tz + 0.5, GROUND + 7 + 3 * i)
    top = GROUND + 22
    m.add_part("4032a", "white", tx, tz, top)                  # base da cabine
    for dx in (0, 1):
        for dz in (0, 1):
            m.add_part("3062b", "trans_black", tx + dx, tz + dz, top + 1)
    m.add_part("4032a", "dbg", tx, tz, top + 4)
    m.add_part("4740", "lbg", tx, tz, top + 5)
    m.add_part("3957a", "white", tx + 0.5, tz + 0.5, top + 6)  # antena
    m.add_part("3002", "white", 36, 23, GROUND)                # prédio de apoio
    m.add_part("26603", "white", 36, 23, GROUND + 3)


def stage_bridges(m):
    m.group = "5 pontes"
    for _, c, *_ in STANDS:
        bx = c - 1
        m.add_part("6141", "black", bx, NOSE_Z - 2, GROUND)        # rodas
        m.add_part("3062b", "lbg", bx, NOSE_Z - 2, GROUND + 1)      # coluna móvel
        m.add_part("3062b", "lbg", bx, TERM[1] - 1, GROUND)        # coluna junto ao terminal
        m.add_part("6141", "lbg", bx, TERM[1] - 1, GROUND + 3)
        m.add_part("3710", "lbg", bx, NOSE_Z - 2, GROUND + 4, 90)   # túnel 1x4
        m.add_part("2431", "lbg", bx, NOSE_Z - 2, GROUND + 5, 90)


def plane(m, c, lf, wing, tail, accent, engine):
    z0 = NOSE_Z - lf
    zw = z0 + (3 if lf == 8 else 4)                     # fileira de trás da asa
    left, right, span = ("43722", "43723", 3) if wing == "2x3" else ("41769", "41770", 4)
    m.add_part("6141", "black", c, NOSE_Z - 1, GROUND)  # trem do nariz
    m.add_part("6141", "black", c, zw, GROUND)          # trem principal
    ez = zw if wing == "2x3" else zw + 1
    m.add_part("6141", engine, c - 2, ez, GROUND)       # motores (seguram as asas)
    m.add_part("6141", engine, c + 2, ez, GROUND)
    m.add_part(bk.PLATES[(1, lf)], "white", c, z0, GROUND + 1, 90)
    m.add_part(left, "white", c - span, zw, GROUND + 1, 90)
    m.add_part(right, "white", c + 1, zw, GROUND + 1, 270)
    m.add_part("3623", "white", c - 1, z0, GROUND + 2)  # estabilizador horizontal
    m.add_part("3024", "white", c, z0 + 1, GROUND + 2)  # apoio da deriva
    m.add_part("26603", "white", c - 1, zw, GROUND + 2)  # raiz das asas
    for z, n in ((z0 + 2, zw - z0 - 2), (zw + 2, NOSE_Z - 2 - (zw + 2))):
        m.add_part(bk.TILES[(1, n)], "white", c, z, GROUND + 2, 90 if n > 1 else 0)
    m.add_part("3070b", "black", c, NOSE_Z - 2, GROUND + 2)    # cabine
    m.add_part("98138", "white", c, NOSE_Z - 1, GROUND + 2)    # nariz
    m.add_part("3040b", tail, c, z0, GROUND + 3, 180)           # deriva enflechada
    m.add_part("54200", accent, c, z0, GROUND + 6, 180)


def ground_service(m, c, lf):
    """Caminhão-tanque à frente da asa direita e trem de bagagem atrás dela."""
    zw = NOSE_Z - lf + (3 if lf == 8 else 4)
    m.add_part("3023", "white", c + 2, zw + 2, GROUND, 90)
    m.add_part("3069b", "lbg", c + 2, zw + 2, GROUND + 1, 90)
    m.add_part("6141", "yellow", c + 2, zw - 1, GROUND)
    m.add_part("3070b", "lbg", c + 3, zw - 1, GROUND)
    m.add_part("3070b", "lbg", c + 4, zw - 1, GROUND)


def stage_planes(m):
    for name, c, lf, wing, tail, accent, engine in STANDS:
        m.group = f"6 avião {name}"
        plane(m, c, lf, wing, tail, accent, engine)
    m.group = "6 serviços de pátio"
    for _, c, lf, *_ in STANDS:
        ground_service(m, c, lf)


def stage_landside(m):
    m.group = "7 lado terra"
    deck = GROUND + 3
    for x in (0, 10, 20, 30):                     # viaduto de embarque
        m.add_part("3941", "lbg", x + 2, 27, GROUND)
        m.add_part("3941", "lbg", x + 6, 27, GROUND)
        m.add_part("3030", "dbg", x, 26, deck)
    for x in range(0, 40, 8):
        m.add_part("4162", "lbg", x, 26, deck + 1)    # meio-fio / calçada de embarque
        m.add_part("4162", "white", x, 29, deck + 1)  # guarda-corpo
    for x, z, color, n in [(7, 27, "white", 2), (14, 27, "red", 2), (22, 28, "blue", 4)]:
        m.add_part(bk.PLATES[(1, n)], color, x, z, deck + 1)    # táxi, carro e ônibus no viaduto
        m.add_part(bk.TILES[(1, n)], "white" if n > 2 else color, x, z, deck + 2)
    m.add_part("3023", "yellow", 30, 30, GROUND)                 # carro na via inferior
    m.add_part("3069b", "yellow", 30, 30, GROUND + 1)
    for x, z in ((1, 20), (3, 21), (1, 23), (3, 24)):                     # árvores
        m.add_part("6141", "reddish_brown", x, z, GROUND)
        m.add_part("4589", "green", x, z, GROUND + 1)


STAGES = [("base", stage_base), ("sinalizacao", stage_signage), ("terminal", stage_terminal),
          ("torre", stage_tower), ("pontes", stage_bridges), ("avioes", stage_planes),
          ("lado_terra", stage_landside)]


def build(upto=len(STAGES), render=True):
    os.makedirs(RENDERS, exist_ok=True)
    m = bk.Model("Aeroporto Internacional de Guarulhos (GRU) - Terminal 3, microescala")
    for i, (name, fn) in enumerate(STAGES[:upto], 1):
        fn(m)
        print(m.describe(f"etapa {i}: {name}").split("\ninventário")[0])
        if render:
            path = os.path.join(RENDERS, f"etapa_{i}_{name}.png")
            m.render(path, "iso_front_left", size=1000, caption=f"etapa {i}: {name} ({len(m.parts)} peças)")
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
    report = m.check()
    if args.final:
        if report["collisions"] or report["loose"]:
            sys.exit("modelo com problemas: corrija antes de exportar")
        print("export:", m.export_ldr(os.path.join(HERE, "guarulhos_gru.ldr"), author="Bugiganga S.A. / brickkit"))
        cap = f"GRU Terminal 3 - microescala - {len(m.parts)} peças"
        for view in ("iso_front_left", "top", "iso_back_right"):
            print("render:", m.render(os.path.join(RENDERS, f"final_{view}.png"), view, size=1600,
                                      caption=f"{cap} - {view}"))


if __name__ == "__main__":
    main()
