"""Minimal LDraw library access: fetch part files on demand, flatten geometry, read colours.

Part files come from a static mirror of the official LDraw library and are cached
locally (LDRAW_CACHE, default ~/.cache/ldraw). They are parsed as plain data only.
"""
import os
import pickle
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

import numpy as np

LDRAW_URL = "https://raw.githubusercontent.com/gkjohnson/ldraw-parts-library/master/complete/ldraw/"
CACHE = os.environ.get("LDRAW_CACHE", os.path.expanduser("~/.cache/ldraw"))

# Primitives that are real, connectable studs on top of a part, and the hollow bottom
# tubes that take a stud from below (solid 1xN pins, stud3, do not).
TOP_STUDS = {"stud.dat", "stud2.dat", "stud2a.dat", "stud6.dat", "stud6a.dat", "stud10.dat",
             "stud13.dat", "stud15.dat", "stud17a.dat", "stud2s.dat"}
TUBES = {"stud4.dat", "stud4a.dat", "stud4o.dat", "stud4s.dat", "stud4h.dat", "stud16.dat"}

EDGE_OF = 100000  # colour code offset meaning "edge colour of <code>"


def _fetch(rel):
    """Return local path of library file `rel` (e.g. 'parts/3001.dat'), or None if absent."""
    local = os.path.join(CACHE, rel)
    missing = local + ".missing"
    if os.path.exists(local):
        return local
    if os.path.exists(missing):
        return None
    os.makedirs(os.path.dirname(local), exist_ok=True)
    tmp = local + ".part"
    r = subprocess.run(["curl", "-sS", "-f", "--retry", "3", "--max-time", "60", "-o", tmp, LDRAW_URL + rel],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if os.path.exists(tmp):
            os.remove(tmp)
        if "404" in r.stderr:
            open(missing, "w").close()
            return None
        raise RuntimeError(f"download failed for {rel}: {r.stderr.strip()}")
    os.replace(tmp, local)
    return local


def _candidates(name):
    name = name.strip().lower().replace("\\", "/")
    if name.startswith("s/"):
        return ["parts/" + name]
    if name.startswith(("48/", "8/")):
        return ["p/" + name]
    return ["parts/" + name, "p/" + name]


def resolve(name):
    for rel in _candidates(name):
        path = _fetch(rel)
        if path:
            return path
    raise FileNotFoundError(f"LDraw file not found in library: {name}")


def _refs(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            tok = line.split()
            if len(tok) >= 15 and tok[0] == "1":
                out.append(" ".join(tok[14:]))
    return out


def prefetch(names, workers=16, strict=True):
    """Download a set of parts and, breadth first, everything they reference.

    With strict=False, names missing from the library are skipped and returned.
    """
    def get(name):
        try:
            return resolve(name)
        except FileNotFoundError:
            if strict:
                raise
            return None

    seen, missing, frontier = set(), [], [n.lower() for n in names]
    with ThreadPoolExecutor(workers) as pool:
        while frontier:
            frontier = [n for n in dict.fromkeys(frontier) if n not in seen]
            seen.update(frontier)
            paths = list(pool.map(get, frontier))
            missing += [n for n, p in zip(frontier, paths) if p is None]
            frontier = [r.lower() for p in paths if p for r in _refs(p)]
    return missing


class Geometry:
    """Flattened geometry of one file in its own coordinates.

    tris: (N,3,3) float32, tri_col: (N,) int; lines: (M,2,3), line_col: (M,) int.
    Colour 16 means "main colour of the instance", 24 its edge colour.
    studs/tubes: (K,3) positions of top studs / bottom tubes, with the stud axis
    (K,3) pointing in the stud's "up" direction for studs.
    stud_tri: (N,) bool, triangles that belong to stud primitives.
    """

    __slots__ = ("tris", "tri_col", "lines", "line_col", "studs", "stud_up", "tubes", "stud_tri", "title")

    def __init__(self):
        self.tris = np.zeros((0, 3, 3), np.float32)
        self.tri_col = np.zeros(0, np.int32)
        self.lines = np.zeros((0, 2, 3), np.float32)
        self.line_col = np.zeros(0, np.int32)
        self.studs = np.zeros((0, 3), np.float32)
        self.stud_up = np.zeros((0, 3), np.float32)
        self.tubes = np.zeros((0, 3), np.float32)
        self.stud_tri = np.zeros(0, bool)
        self.title = ""


def _recolor(codes, colour):
    if colour == 16:
        return codes
    out = codes.copy()
    out[codes == 16] = colour
    out[codes == 24] = EDGE_OF + colour
    return out


_GEOM = {}


def geometry(name):
    key = name.strip().lower().replace("\\", "/")
    if key in _GEOM:
        return _GEOM[key]
    path = resolve(key)
    tris, tcol, lines, lcol, studs, sup, tubes, stri = [], [], [], [], [], [], [], []
    title = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            tok = raw.split()
            if not tok:
                continue
            kind = tok[0]
            if kind == "0":
                if not title and len(tok) > 1 and not tok[1].startswith(("!", "//")) and tok[1] not in ("Name:", "Author:", "BFC"):
                    title = " ".join(tok[1:])
                continue
            if kind == "1" and len(tok) >= 15:
                col = int(tok[1])
                v = np.array(tok[2:14], np.float64)
                pos, mat = v[:3], v[3:].reshape(3, 3)
                sub = " ".join(tok[14:]).lower().replace("\\", "/")
                base = sub.split("/")[-1]
                g = geometry(sub)
                if len(g.tris):
                    tris.append((g.tris.reshape(-1, 3) @ mat.T + pos).reshape(-1, 3, 3))
                    tcol.append(_recolor(g.tri_col, col))
                    stri.append(np.full(len(g.tris), base in TOP_STUDS) | g.stud_tri)
                if len(g.lines):
                    lines.append((g.lines.reshape(-1, 3) @ mat.T + pos).reshape(-1, 2, 3))
                    lcol.append(_recolor(g.line_col, col))
                if base in TOP_STUDS:
                    up = mat @ np.array([0.0, -1.0, 0.0])
                    studs.append(pos[None])
                    sup.append((up / np.linalg.norm(up))[None])
                elif base in TUBES:
                    tubes.append(pos[None])
                else:
                    if len(g.studs):
                        studs.append(g.studs @ mat.T + pos)
                        u = g.stud_up @ mat.T
                        sup.append(u / np.linalg.norm(u, axis=1, keepdims=True))
                    if len(g.tubes):
                        tubes.append(g.tubes @ mat.T + pos)
            elif kind == "2" and len(tok) >= 8:
                lines.append(np.array(tok[2:8], np.float64).reshape(1, 2, 3))
                lcol.append(np.array([int(tok[1])]))
            elif kind == "3" and len(tok) >= 11:
                tris.append(np.array(tok[2:11], np.float64).reshape(1, 3, 3))
                tcol.append(np.array([int(tok[1])]))
                stri.append(np.zeros(1, bool))
            elif kind == "4" and len(tok) >= 14:
                q = np.array(tok[2:14], np.float64).reshape(4, 3)
                tris.append(np.stack([q[[0, 1, 2]], q[[0, 2, 3]]]))
                tcol.append(np.array([int(tok[1])] * 2))
                stri.append(np.zeros(2, bool))
    g = Geometry()
    g.title = title
    if tris:
        g.tris = np.concatenate(tris).astype(np.float32)
        g.tri_col = np.concatenate(tcol).astype(np.int32)
        g.stud_tri = np.concatenate(stri)
    if lines:
        g.lines = np.concatenate(lines).astype(np.float32)
        g.line_col = np.concatenate(lcol).astype(np.int32)
    if studs:
        g.studs = np.concatenate(studs).astype(np.float32)
        g.stud_up = np.concatenate(sup).astype(np.float32)
    if tubes:
        g.tubes = np.concatenate(tubes).astype(np.float32)
    _GEOM[key] = g
    return g


def part_geometry(part_id):
    """Geometry of a top-level part, cached on disk as a pickle next to the library files."""
    key = part_id.lower()
    if key in _GEOM:
        return _GEOM[key]
    pk = os.path.join(CACHE, "flat", key.replace("/", "_") + ".pkl")
    if os.path.exists(pk):
        with open(pk, "rb") as f:
            g = pickle.load(f)
        _GEOM[key] = g
        return g
    g = geometry(key)
    os.makedirs(os.path.dirname(pk), exist_ok=True)
    with open(pk, "wb") as f:
        pickle.dump(g, f)
    return g


_COLOUR_RE = re.compile(r"!COLOUR\s+(\S+)\s+CODE\s+(\d+)\s+VALUE\s+#([0-9A-Fa-f]{6})\s+EDGE\s+#([0-9A-Fa-f]{6})(.*)")


def colours():
    """{code: (name, (r,g,b), (er,eg,eb), alpha)} from LDConfig.ldr."""
    out = {}
    with open(resolve_config(), encoding="utf-8") as f:
        for line in f:
            m = _COLOUR_RE.search(line)
            if not m:
                continue
            name, code, val, edge, rest = m.groups()
            am = re.search(r"ALPHA\s+(\d+)", rest)
            rgb = tuple(int(val[i:i + 2], 16) for i in (0, 2, 4))
            ergb = tuple(int(edge[i:i + 2], 16) for i in (0, 2, 4))
            out[int(code)] = (name, rgb, ergb, int(am.group(1)) if am else 255)
    return out


def resolve_config():
    path = _fetch("LDConfig.ldr")
    if not path:
        raise FileNotFoundError("LDConfig.ldr")
    return path
