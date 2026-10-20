"""brickkit: local LEGO modelling kit on top of the LDraw library.

Same workflow as the brickbuilder MCP: place parts on a stud grid (add_part / add_parts),
fill volumes with as few parts as possible (fill_layers), then describe, check (collisions
and loose parts), render previews and export an .ldr file.

Grid: x and z in studs, level in plates (bottom of the part). Model front is -Z (LDraw).
"""
import math
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import ldraw

STUD, PLATE = 20.0, 8.0

PLATES = {(1, 1): "3024", (1, 2): "3023", (1, 3): "3623", (1, 4): "3710", (1, 6): "3666", (1, 8): "3460",
          (1, 10): "4477", (1, 12): "60479", (2, 2): "3022", (2, 3): "3021", (2, 4): "3020", (2, 6): "3795",
          (2, 8): "3034", (2, 10): "3832", (2, 12): "2445", (2, 14): "91988", (2, 16): "4282",
          (4, 4): "3031", (4, 6): "3032", (4, 8): "3035", (4, 10): "3030", (4, 12): "3029",
          (6, 6): "3958", (6, 8): "3036", (6, 10): "3033", (6, 12): "3028", (6, 14): "3456",
          (6, 16): "3027", (6, 24): "3026", (8, 8): "41539", (8, 16): "92438", (16, 16): "91405"}
BRICKS = {(1, 1): "3005", (1, 2): "3004", (1, 3): "3622", (1, 4): "3010", (1, 6): "3009", (1, 8): "3008",
          (1, 10): "6111", (1, 12): "6112", (2, 2): "3003", (2, 3): "3002", (2, 4): "3001", (2, 6): "2456",
          (2, 8): "3007"}
TILES = {(1, 1): "3070b", (1, 2): "3069b", (1, 3): "63864", (1, 4): "2431", (1, 6): "6636", (1, 8): "4162",
         (2, 2): "3068b", (2, 3): "26603", (2, 4): "87079", (2, 6): "69729"}
GLASS = {(1, 2): "3065", (1, 4): "3066", (1, 6): "3067b"}
KINDS = {"plate": (PLATES, 1), "brick": (BRICKS, 3), "tile": (TILES, 1), "glass": (GLASS, 3)}

# name -> LDraw code; common colours (marked * in list_colors) are the safe, widely available ones.
COLORS = {"black": 0, "blue": 1, "green": 2, "red": 4, "bright_green": 10, "yellow": 14, "white": 15,
          "tan": 19, "orange": 25, "lime": 27, "dark_tan": 28, "reddish_brown": 70, "lbg": 71, "dbg": 72,
          "medium_blue": 73, "bright_light_orange": 191, "dark_blue": 272, "dark_green": 288,
          "dark_red": 320, "dark_azure": 321, "medium_azure": 322, "coral": 353, "sand_green": 378,
          "trans_red": 36, "trans_black": 40, "trans_light_blue": 43, "trans_yellow": 46, "trans_clear": 47}
COMMON = {0, 1, 2, 4, 14, 15, 19, 25, 28, 70, 71, 72, 191, 272, 288, 320, 321, 36, 40, 43, 47}

ISO = math.degrees(math.atan(1 / math.sqrt(2)))  # true isometric elevation, 35.26 degrees
VIEWS = {  # (azimuth, elevation) in degrees; azimuth 0 = camera in front (-Z), 90 = on the right (+X)
    "iso_front_left": (-45, ISO), "iso_front_right": (45, ISO), "iso_back_left": (-135, ISO),
    "iso_back_right": (135, ISO), "front": (0, 0), "top": (0, 90), "bird_front_left": (-35, 48),
}

_ROT = {0: np.eye(3), 90: np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float),
        180: np.diag([-1.0, 1, -1]), 270: np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)}


def list_colors():
    pal = ldraw.colours()
    for name, code in sorted(COLORS.items(), key=lambda kv: kv[1]):
        cname, rgb, _, alpha = pal[code]
        mark = "*" if code in COMMON else " "
        print(f"{mark} {code:4d} {name:20s} {cname:22s} #{bytes(rgb).hex()}{'  (trans)' if alpha < 255 else ''}")


def color_name(code):
    pal = ldraw.colours()
    return pal[code][0] if code in pal else str(code)


class _Shape:
    """Per part-id data derived from the LDraw geometry, in part coordinates."""

    def __init__(self, pid):
        g = ldraw.part_geometry(pid + ".dat")
        self.pid, self.title, self.g = pid, g.title, g
        body = g.tris[~g.stud_tri].reshape(-1, 3).astype(np.float64)
        self.bmin, self.bmax = body.min(0), body.max(0)
        up = np.abs(g.stud_up[:, 1] + 1) < 1e-3 if len(g.studs) else np.zeros(0, bool)
        self.studs = g.studs[up].astype(np.float64)
        self.tubes = g.tubes.astype(np.float64)
        self.hull = _hull2d(np.unique(np.round(body[:, [0, 2]], 2), axis=0))


_SHAPES = {}


def shape(pid):
    if pid not in _SHAPES:
        _SHAPES[pid] = _Shape(pid)
    return _SHAPES[pid]


def _hull2d(pts):
    """Convex hull, counter-clockwise in the (x, z) plane (monotone chain)."""
    pts = sorted(map(tuple, pts))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out

    lower, upper = half(pts), half(reversed(pts))
    return np.array(lower[:-1] + upper[:-1])


def _inside(hull, pts, margin=1.0):
    """Which points (N,2) lie inside the counter-clockwise hull by at least `margin` LDU."""
    a = hull
    e = np.roll(hull, -1, axis=0) - a
    ln = np.hypot(e[:, 0], e[:, 1])
    cross = (e[None, :, 0] * (pts[:, None, 1] - a[None, :, 1])
             - e[None, :, 1] * (pts[:, None, 0] - a[None, :, 0])) / ln
    return np.all(cross >= margin, axis=1)


class Part:
    __slots__ = ("pid", "color", "x", "z", "level", "rot", "group", "w", "d", "h", "R", "pos")

    def __init__(self, pid, color, x, z, level, rot, group):
        s = shape(pid)
        self.pid, self.color, self.x, self.z, self.level, self.rot, self.group = pid, color, x, z, level, rot, group
        self.R = _ROT[rot % 360]
        corners = np.array([[a, b, c] for a in (s.bmin[0], s.bmax[0]) for b in (s.bmin[1], s.bmax[1])
                            for c in (s.bmin[2], s.bmax[2])]) @ self.R.T
        rmin, rmax = corners.min(0), corners.max(0)
        self.w = round((rmax[0] - rmin[0]) / STUD * 2) / 2
        self.d = round((rmax[2] - rmin[2]) / STUD * 2) / 2
        self.h = round((rmax[1] - rmin[1]) / PLATE)
        self.pos = np.array([x * STUD - rmin[0], -level * PLATE - rmax[1], z * STUD - rmin[2]])

    @property
    def top(self):
        return self.level + self.h

    def world(self, local):
        return local @ self.R.T + self.pos

    def label(self):
        return f"{self.pid} {color_name(self.color)} @({self.x:g},{self.z:g}) L{self.level} r{self.rot}"


class Model:
    def __init__(self, name):
        self.name = name
        self.parts = []
        self.group = None

    # ----------------------------------------------------------------- building
    def add_part(self, pid, color, x, z, level, rot=0, group=None):
        p = Part(pid, COLORS.get(color, color), x, z, level, rot, group or self.group)
        self.parts.append(p)
        return p

    def add_parts(self, specs, group=None):
        """specs: iterable of (pid, color, x, z, level[, rot])."""
        return [self.add_part(*spec, group=group) for spec in specs]

    def remove(self, parts):
        drop = {id(p) for p in parts}
        self.parts = [p for p in self.parts if id(p) not in drop]

    def fill_layers(self, region, levels, color, kind="plate", exclude=(), group=None, sizes=None,
                    seams=None, below=(), max_len=None):
        """Fill rectangle region=(x0, z0, x1, z1) from level l0 up to l1 with as few parts as possible.

        Greedy largest-first packing. Each layer avoids putting a joint right on top of a
        joint of the layer below (running bond). For the first layer, the joints to bridge
        come from `seams` = {"x": [...], "z": [...]} and/or the parts in `below`.
        """
        catalog, step = KINDS[kind]
        color = COLORS.get(color, color)
        x0, z0, x1, z1 = region
        l0, l1 = levels
        region_cells = {(x, z) for x in range(x0, x1) for z in range(z0, z1)}
        for ex in exclude:
            region_cells -= {(x, z) for x in range(ex[0], ex[2]) for z in range(ex[1], ex[3])}
        opts = []
        for (a, b), pid in catalog.items():
            if (sizes and (a, b) not in sizes) or (max_len and b > max_len):
                continue
            opts.append((a * b, 0, (b, a), pid))
            if a != b:
                opts.append((a * b, 90, (a, b), pid))
        opts.sort(key=lambda o: -o[0])
        seams = seams or {}
        joints_below = ({("v", x, z) for x in seams.get("x", []) for z in range(z0, z1)}
                        | {("h", x, z) for z in seams.get("z", []) for x in range(x0, x1)})
        for p in below:
            joints_below |= _edges(int(p.x), int(p.z), int(p.w), int(p.d), region_cells)
        placed = []
        for level in range(l0, l1, step):
            cells, joints = set(region_cells), set()
            while cells:
                cx, cz = min(cells, key=lambda c: (c[1], c[0]))
                best = None
                for area, rot, (w, d), pid in opts:
                    if any((cx + i, cz + j) not in cells for i in range(w) for j in range(d)):
                        continue
                    edges = _edges(cx, cz, w, d, region_cells)
                    bad = len(edges & joints_below)
                    if best is None or bad < best[0]:
                        best = (bad, rot, w, d, pid, edges)
                    if bad == 0:
                        break
                _, rot, w, d, pid, edges = best
                placed.append(self.add_part(pid, color, cx, cz, level, rot, group))
                cells -= {(cx + i, cz + j) for i in range(w) for j in range(d)}
                joints |= edges
            joints_below = joints
        return placed

    # ----------------------------------------------------------------- reports
    def describe(self, title=None):
        lines = [f"== {title or self.name}: {len(self.parts)} peças =="]
        if not self.parts:
            return lines[0]
        groups = Counter(p.group for p in self.parts)
        lines.append("por etapa: " + ", ".join(f"{g}={n}" for g, n in groups.items()))
        x0 = min(p.x for p in self.parts); x1 = max(p.x + p.w for p in self.parts)
        z0 = min(p.z for p in self.parts); z1 = max(p.z + p.d for p in self.parts)
        top = max(p.top for p in self.parts)
        lines.append(f"dimensões: {x1 - x0:g} x {z1 - z0:g} studs, altura {top} plates ({top / 3:.1f} tijolos)")
        inv = Counter((p.pid, p.color) for p in self.parts)
        lines.append(f"inventário ({len(inv)} tipos peça+cor):")
        for (pid, col), n in sorted(inv.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {n:3d} x {pid:7s} {shape(pid).title[:40]:40s} {color_name(col)}")
        return "\n".join(lines)

    @staticmethod
    def _connect_data(p):
        """World stud keys, receptor keys and occupied half-stud cells of one part."""
        s = shape(p.pid)
        hull = p.world(np.c_[s.hull[:, 0], np.zeros(len(s.hull)), s.hull[:, 1]])[:, [0, 2]]
        bottom = int(round(-p.level * PLATE))
        # occupancy: half-stud cells whose centre is inside the part outline, every plate level
        hx = np.arange(round(p.x * 2), round((p.x + p.w) * 2))
        hz = np.arange(round(p.z * 2), round((p.z + p.d) * 2))
        half = np.array([(a, b) for a in hx for b in hz])
        inside = _inside(hull, (half + 0.5) * STUD / 2, 0.5)
        occ = {(int(a), int(b), lv) for a, b in half[inside] for lv in range(p.level, p.level + p.h)}
        # receptors: anti-stud cells under the outline plus hollow tubes, at the part bottom
        cells = np.array([(p.x + i + 0.5, p.z + j + 0.5) for i in range(int(round(p.w)))
                          for j in range(int(round(p.d)))]) * STUD
        rec = [(int(round(x)), bottom, int(round(z))) for x, z in cells[_inside(hull, cells, 2.0)]]
        if len(s.tubes):
            rec += [(int(round(t[0])), bottom, int(round(t[2]))) for t in p.world(s.tubes)]
        studs = [(int(round(v[0])), int(round(v[1])), int(round(v[2]))) for v in p.world(s.studs)] if len(s.studs) else []
        return studs, rec, occ

    def check(self, verbose=True):
        data = [self._connect_data(p) for p in self.parts]
        owner, clashes = {}, set()
        for i, (_, _, occ) in enumerate(data):
            for c in occ:
                j = owner.setdefault(c, i)
                if j != i:
                    clashes.add((min(i, j), max(i, j)))
        receptors = defaultdict(set)
        for i, (_, rec, _) in enumerate(data):
            for k in rec:
                receptors[k].add(i)
        adj = [set() for _ in self.parts]
        for i, (studs, _, _) in enumerate(data):
            for k in studs:
                for j in receptors.get(k, ()):
                    if j != i:
                        adj[i].add(j)
                        adj[j].add(i)
        comp, comps = [-1] * len(self.parts), []
        for i in range(len(self.parts)):
            if comp[i] >= 0:
                continue
            stack, members = [i], []
            comp[i] = len(comps)
            while stack:
                k = stack.pop()
                members.append(k)
                for j in adj[k]:
                    if comp[j] < 0:
                        comp[j] = len(comps)
                        stack.append(j)
            comps.append(members)
        main = max(comps, key=len) if comps else []
        loose = sorted(set(range(len(self.parts))) - set(main))
        report = {"parts": len(self.parts), "collisions": sorted(clashes), "loose": loose,
                  "components": len(comps), "adjacency": adj}
        if verbose:
            print(f"check_model: {len(self.parts)} peças, {len(comps)} grupo(s) conectado(s), "
                  f"{len(clashes)} colisão(ões), {len(loose)} peça(s) solta(s)")
            for i, j in sorted(clashes)[:40]:
                print(f"  COLISÃO  {self.parts[i].label()}  x  {self.parts[j].label()}")
            for i in loose[:60]:
                print(f"  SOLTA    [{self.parts[i].group}] {self.parts[i].label()}")
        return report

    # ----------------------------------------------------------------- export
    def export_ldr(self, path, title=None, author="brickkit"):
        order = list(dict.fromkeys(p.group for p in self.parts))
        out = [f"0 {title or self.name}", f"0 Name: {path.split('/')[-1]}", f"0 Author: {author}",
               "0 !LDRAW_ORG Unofficial_Model"]
        for gi, group in enumerate(order):
            out.append(f"0 // {group}")
            for p in (q for q in self.parts if q.group == group):
                nums = [*p.pos, *p.R.ravel()]
                out.append(f"1 {p.color} " + " ".join(_fmt(v) for v in nums) + f" {p.pid}.dat")
            out.append("0 STEP")
        with open(path, "w", newline="\r\n") as f:
            f.write("\n".join(out) + "\n")
        return path

    # ----------------------------------------------------------------- render
    def render(self, path, view="iso_front_left", size=1600, ss=2, caption=None):
        return render(self.parts, path, view, size, ss, caption)


def _edges(x, z, w, d, region):
    """Unit joint segments around a w x d piece at (x, z); region borders are not joints."""
    out = set()
    for j in range(d):
        if (x - 1, z + j) in region:
            out.add(("v", x, z + j))
        if (x + w, z + j) in region:
            out.add(("v", x + w, z + j))
    for i in range(w):
        if (x + i, z - 1) in region:
            out.add(("h", x + i, z))
        if (x + i, z + d) in region:
            out.add(("h", x + i, z + d))
    return out


def _fmt(v):
    v = float(v)
    return str(int(round(v))) if abs(v - round(v)) < 1e-6 else f"{v:.4f}".rstrip("0")


# ====================================================================== renderer
def _world_geometry(parts):
    pal = ldraw.colours()

    def rgb_alpha(codes):
        out, alpha = np.zeros((len(codes), 3)), np.ones(len(codes))
        for code in np.unique(codes):
            m = codes == code
            edge = code >= ldraw.EDGE_OF
            base = int(code - ldraw.EDGE_OF if edge else code)
            _, rgb, _, a = pal.get(base, ("?", (255, 0, 255), (0, 0, 0), 255))
            col = np.array(rgb, float)
            if edge:
                col = col * 0.45 if base != 0 else np.array([95.0, 95, 95])
            out[m] = col / 255.0
            alpha[m] = a / 255.0
        return out, alpha

    T, TC, L, LC = [], [], [], []
    for p in parts:
        g = shape(p.pid).g
        T.append(p.world(g.tris.reshape(-1, 3)).reshape(-1, 3, 3))
        c = g.tri_col.copy()
        c[c == 16] = p.color
        c[c == 24] = ldraw.EDGE_OF + p.color
        TC.append(c)
        if len(g.lines):
            L.append(p.world(g.lines.reshape(-1, 3)).reshape(-1, 2, 3))
            c = g.line_col.copy()
            c[(c == 16) | (c == 24)] = ldraw.EDGE_OF + p.color
            c[c < ldraw.EDGE_OF] += ldraw.EDGE_OF
            LC.append(c)
    tris = np.concatenate(T)
    tcol, talpha = rgb_alpha(np.concatenate(TC))
    lines = np.concatenate(L)
    lcol, lalpha = rgb_alpha(np.concatenate(LC))
    return tris, tcol, talpha, lines, lcol, lalpha


def _basis(view):
    az, el = VIEWS[view] if isinstance(view, str) else view
    a, e = math.radians(az), math.radians(el)
    to_cam = np.array([math.sin(a) * math.cos(e), -math.sin(e), -math.cos(a) * math.cos(e)])
    f = -to_cam / np.linalg.norm(to_cam)
    up = np.array([0.0, -1.0, 0.0]) if el < 89.9 else np.array([0.0, 0.0, 1.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    return f, r, np.cross(r, f)


def _raster(P, D, W, H, zbuf, ids_buf, ids):
    """Z-buffer rasterisation of triangles P (N,3,2 pixel coords) with depths D (N,3)."""
    if not len(P):
        return
    x0 = np.floor(P[:, :, 0].min(1)).astype(np.int64); x1 = np.floor(P[:, :, 0].max(1)).astype(np.int64)
    y0 = np.floor(P[:, :, 1].min(1)).astype(np.int64); y1 = np.floor(P[:, :, 1].max(1)).astype(np.int64)
    area = ((P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 1] - P[:, 0, 1])
            - (P[:, 1, 1] - P[:, 0, 1]) * (P[:, 2, 0] - P[:, 0, 0]))
    keep = (x1 >= 0) & (y1 >= 0) & (x0 < W) & (y0 < H) & (np.abs(area) > 1e-9)
    x0, y0 = np.clip(x0, 0, W - 1), np.clip(y0, 0, H - 1)
    x1, y1 = np.clip(x1, 0, W - 1), np.clip(y1, 0, H - 1)
    S = np.maximum(x1 - x0, y1 - y0) + 1
    zf, idf = zbuf.ravel(), ids_buf.ravel()

    def commit(pix, d, t):
        m = d < zf[pix]
        pix, d, t = pix[m], d[m], t[m]
        if not len(pix):
            return
        order = np.lexsort((d, pix))
        pix, d, t = pix[order], d[order], t[order]
        first = np.ones(len(pix), bool)
        first[1:] = pix[1:] != pix[:-1]
        zf[pix[first]] = d[first]
        idf[pix[first]] = t[first]

    def bary(p, ar, cx, cy):
        w0 = ((p[..., 2, 0] - p[..., 1, 0]) * (cy - p[..., 1, 1]) - (p[..., 2, 1] - p[..., 1, 1]) * (cx - p[..., 1, 0])) / ar
        w1 = ((p[..., 0, 0] - p[..., 2, 0]) * (cy - p[..., 2, 1]) - (p[..., 0, 1] - p[..., 2, 1]) * (cx - p[..., 2, 0])) / ar
        return w0, w1, 1.0 - w0 - w1

    lo = 0
    for s in (1, 2, 4, 8, 16, 32, 64):
        idx = np.nonzero(keep & (S > lo) & (S <= s))[0]
        lo = s
        oy, ox = np.mgrid[0:s, 0:s]
        chunk = max(1, 2_000_000 // (s * s))
        for k in range(0, len(idx), chunk):
            ii = idx[k:k + chunk]
            px, py = x0[ii, None, None] + ox, y0[ii, None, None] + oy
            p = P[ii][:, None, None]
            w0, w1, w2 = bary(p, area[ii][:, None, None], px + 0.5, py + 0.5)
            inside = (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
            inside &= (px <= x1[ii, None, None]) & (py <= y1[ii, None, None])
            d = D[ii]
            depth = w0 * d[:, 0, None, None] + w1 * d[:, 1, None, None] + w2 * d[:, 2, None, None]
            tid = np.broadcast_to(ids[ii][:, None, None], inside.shape)
            commit((py * W + px)[inside], depth[inside], tid[inside])
    for i in np.nonzero(keep & (S > 64))[0]:  # big triangles: one at a time over their own bbox
        ys, xs = np.mgrid[y0[i]:y1[i] + 1, x0[i]:x1[i] + 1]
        w0, w1, w2 = bary(P[i], area[i], xs + 0.5, ys + 0.5)
        inside = (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
        depth = w0 * D[i, 0] + w1 * D[i, 1] + w2 * D[i, 2]
        commit((ys * W + xs)[inside], depth[inside], np.full(int(inside.sum()), ids[i]))


def render(parts, path, view="iso_front_left", size=1600, ss=2, caption=None):
    """Orthographic render with flat shading and LDraw edge lines, saved as PNG."""
    tris, tcol, talpha, lines, lcol, lalpha = _world_geometry(parts)
    f, r, u = _basis(view)
    V = tris.reshape(-1, 3)
    sx, sy, dep = V @ r, V @ u, V @ f
    minx, maxx, miny, maxy = sx.min(), sx.max(), sy.min(), sy.max()
    foot = 40 if caption else 0
    W0 = size
    H0 = int(round(size * min(max((maxy - miny) / (maxx - minx), 0.45), 1.2))) + foot
    W, H = W0 * ss, H0 * ss
    pad = 0.05
    scale = min(W * (1 - 2 * pad) / (maxx - minx), (H - foot * ss) * (1 - 2 * pad) / (maxy - miny))
    ox = (W - (maxx - minx) * scale) / 2 - minx * scale
    oy = (H - foot * ss - (maxy - miny) * scale) / 2 + maxy * scale
    P = np.stack([sx * scale + ox, oy - sy * scale], 1).reshape(-1, 3, 2)
    D = dep.reshape(-1, 3)

    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]).astype(np.float64)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-9
    n[ok] /= ln[ok, None]
    n[(n @ f) > 0] *= -1  # two-sided: always shade the side facing the camera
    key = np.array([-0.45, -1.0, -0.65]); key /= np.linalg.norm(key)
    fill = np.array([0.8, -0.3, 0.4]); fill /= np.linalg.norm(fill)
    shade = 0.42 + 0.58 * np.clip(n @ key, 0, 1) + 0.12 * np.clip(n @ fill, 0, 1)
    shaded = np.clip(tcol * shade[:, None], 0, 1)

    zbuf, ids = np.full((H, W), np.inf), np.full((H, W), -1, np.int64)
    oi = np.nonzero(ok & (talpha >= 0.99))[0]
    _raster(P[oi], D[oi], W, H, zbuf, ids, oi)
    zt, idt = zbuf.copy(), np.full((H, W), -1, np.int64)
    ti = np.nonzero(ok & (talpha < 0.99))[0]
    _raster(P[ti], D[ti], W, H, zt, idt, ti)

    t = np.linspace(0, 1, H)[:, None, None]
    img = (np.array([0.94, 0.955, 0.97]) * (1 - t) + np.array([0.80, 0.84, 0.88]) * t) * np.ones((H, W, 3))
    hit = ids >= 0
    img[hit] = shaded[ids[hit]]

    def draw_lines(sel, zref, bias=1.6):
        if not sel.any():
            return
        Lw = lines[sel].reshape(-1, 3)
        lp = np.stack([Lw @ r * scale + ox, oy - Lw @ u * scale], 1).reshape(-1, 2, 2)
        ld = (Lw @ f).reshape(-1, 2)
        cols = lcol[sel]
        seg = np.hypot(lp[:, 1, 0] - lp[:, 0, 0], lp[:, 1, 1] - lp[:, 0, 1])
        cnt = np.minimum(np.ceil(seg).astype(np.int64) + 1, 4000)
        line_of = np.repeat(np.arange(len(cnt)), cnt)
        tt = (np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)) / np.maximum(cnt[line_of] - 1, 1)
        x = lp[line_of, 0, 0] + tt * (lp[line_of, 1, 0] - lp[line_of, 0, 0])
        y = lp[line_of, 0, 1] + tt * (lp[line_of, 1, 1] - lp[line_of, 0, 1])
        d = ld[line_of, 0] + tt * (ld[line_of, 1] - ld[line_of, 0])
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))[:ss * ss]:
            ix, iy = np.floor(x).astype(np.int64) + dx, np.floor(y).astype(np.int64) + dy
            m = (ix >= 0) & (iy >= 0) & (ix < W) & (iy < H)
            m[m] &= d[m] <= zref[iy[m], ix[m]] + bias
            img[iy[m], ix[m]] = cols[line_of[m]]

    opaque_lines = lalpha >= 0.99
    draw_lines(opaque_lines, zbuf)
    th = idt >= 0  # nearest transparent surface: let the interior show, with a faint sky tint
    a = np.clip(talpha[idt[th]] * 0.8, 0, 0.85)[:, None]
    glass = shaded[idt[th]] * 0.8 + np.array([0.70, 0.82, 0.95]) * 0.2
    img[th] = img[th] * (1 - a) + glass * a
    draw_lines(~opaque_lines, np.minimum(zbuf, zt))

    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    if ss > 1:
        out = out.resize((W0, H0), Image.LANCZOS)
    if caption:
        dr = ImageDraw.Draw(out)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 18)
        except OSError:
            font = ImageFont.load_default()
        dr.text((16, H0 - 30), caption, fill=(60, 66, 74), font=font)
    out.save(path)
    return path
