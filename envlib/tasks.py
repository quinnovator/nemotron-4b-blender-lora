"""Task templates. A task is (template name, sampled params); checks are rebuilt from params.

Each template provides:
  sample_params(rng) -> dict      JSON-serialisable parameters
  prompt(params) -> str           the user message
  checks(params) -> fn(state) -> list[bool]
  oracle(params) -> str           a known-good bpy solution (preflight, tests, SFT warm start)
"""
import numpy as np

POS_TOL = 0.03      # metres
SIZE_TOL = 0.03
CONTACT_TOL = 0.03

NAMES = ["Crate", "Block", "Box", "Pedestal", "Plinth", "Brick", "Slab",
         "Ball", "Orb", "Marble", "Globe", "Bead", "Pillar", "Post", "Stone"]
SIDES = {"+X": (0, 1), "-X": (0, -1), "+Y": (1, 1), "-Y": (1, -1)}
SIDE_WORDS = {"+X": "on its +X side (the direction of increasing x)",
              "-X": "on its -X side (the direction of decreasing x)",
              "+Y": "on its +Y side (the direction of increasing y)",
              "-Y": "on its -Y side (the direction of decreasing y)"}


def _r(x, nd=2):
    return float(round(float(x), nd))


def _pick_names(rng, k):
    return [str(n) for n in rng.choice(NAMES, size=k, replace=False)]


def _obj(state, name):
    return (state or {}).get("objects", {}).get(name)


def _close(a, b, tol):
    return abs(a - b) <= tol


def _is_box(o, size):
    """Axis-aligned box of the given edge length (or [x, y, z] sizes)."""
    sizes = size if isinstance(size, (list, tuple)) else [size] * 3
    return (o is not None and o["n_verts"] >= 8
            and all(_close(d, s, SIZE_TOL) for d, s in zip(o["dims"], sizes)))


def _is_sphere(o, radius):
    return (o is not None and o["n_verts"] >= 24
            and all(_close(d, 2 * radius, SIZE_TOL * 2) for d in o["dims"]))


def _on_ground(o):
    return o is not None and _close(o["bbox_min"][2], 0.0, POS_TOL)


def _xy_at(o, x, y):
    return o is not None and _close(o["center"][0], x, POS_TOL) and _close(o["center"][1], y, POS_TOL)


def _shape_check(o, p):
    return _is_sphere(o, p["radius"]) if p["shape"] == "sphere" else _is_box(o, p["size"])


def _shape_words(p):
    if p["shape"] == "sphere":
        return f'a UV sphere named "{p["name"]}" with radius {p["radius"]:.2f} m'
    return f'a cube named "{p["name"]}" with edge length {p["size"]:.2f} m'


def _shape_code(p, x, y, z):
    if p["shape"] == "sphere":
        return (f'bpy.ops.mesh.primitive_uv_sphere_add(radius={p["radius"]}, '
                f'location=({x}, {y}, {z}))\nbpy.context.active_object.name = "{p["name"]}"\n')
    return (f'bpy.ops.mesh.primitive_cube_add(size={p["size"]}, location=({x}, {y}, {z}))\n'
            f'bpy.context.active_object.name = "{p["name"]}"\n')


def _half_h(p):
    return p["radius"] if p["shape"] == "sphere" else p["size"] / 2


class StackTemplate:
    """2-3 cubes stacked into a centred tower on the ground."""

    def sample_params(self, rng):
        n = int(rng.choice([2, 2, 3]))
        names = _pick_names(rng, n)
        sizes = sorted((_r(rng.uniform(0.3, 1.6)) for _ in range(n)), reverse=True)
        return {"names": names, "sizes": sizes,
                "x": _r(rng.uniform(-3, 3)), "y": _r(rng.uniform(-3, 3))}

    def prompt(self, p):
        base = (f'Create a cube named "{p["names"][0]}" with edge length {p["sizes"][0]:.2f} m, '
                f'resting on the ground and centred at x = {p["x"]:.2f}, y = {p["y"]:.2f}.')
        rest = "".join(
            f' Then stack a cube named "{n}" with edge length {s:.2f} m directly on top of '
            f'"{below}", centred on it.'
            for n, s, below in zip(p["names"][1:], p["sizes"][1:], p["names"]))
        return base + rest

    def checks(self, p):
        def fn(state):
            out = []
            objs = [_obj(state, n) for n in p["names"]]
            for i, (o, s) in enumerate(zip(objs, p["sizes"])):
                out.append(_is_box(o, s))
                if i == 0:
                    out.append(_on_ground(o))
                    out.append(_xy_at(o, p["x"], p["y"]))
                else:
                    below = objs[i - 1]
                    out.append(o is not None and below is not None
                               and _close(o["bbox_min"][2], below["bbox_max"][2], CONTACT_TOL))
                    out.append(below is not None and _xy_at(o, below["center"][0], below["center"][1]))
            return out
        return fn

    def oracle(self, p):
        code, z = "import bpy\n", 0.0
        for n, s in zip(p["names"], p["sizes"]):
            code += _shape_code({"shape": "cube", "name": n, "size": s}, p["x"], p["y"], round(z + s / 2, 4))
            z += s
        return code


class NextToTemplate:
    """An anchor cube, and a second object resting on the ground touching one of its sides."""

    def sample_params(self, rng):
        a, b = _pick_names(rng, 2)
        other = {"name": b, "shape": str(rng.choice(["cube", "sphere"]))}
        if other["shape"] == "sphere":
            other["radius"] = _r(rng.uniform(0.2, 0.8))
        else:
            other["size"] = _r(rng.uniform(0.3, 1.4))
        return {"anchor": a, "size": _r(rng.uniform(0.5, 2.0)),
                "x": _r(rng.uniform(-3, 3)), "y": _r(rng.uniform(-3, 3)),
                "side": str(rng.choice(list(SIDES))), "other": other}

    def prompt(self, p):
        return (f'Create a cube named "{p["anchor"]}" with edge length {p["size"]:.2f} m, resting '
                f'on the ground and centred at x = {p["x"]:.2f}, y = {p["y"]:.2f}. Then place '
                f'{_shape_words(p["other"])} resting on the ground, touching "{p["anchor"]}" '
                f'{SIDE_WORDS[p["side"]]}, centred along that face.')

    def _target(self, p):
        axis, sign = SIDES[p["side"]]
        c = [p["x"], p["y"]]
        c[axis] += sign * (p["size"] / 2 + _half_h(p["other"]))
        return c, axis, sign

    def checks(self, p):
        def fn(state):
            a, b = _obj(state, p["anchor"]), _obj(state, p["other"]["name"])
            (tx, ty), axis, sign = self._target(p)
            other_axis = 1 - axis
            gap_ok = False
            if a is not None and b is not None:
                gap = (b["bbox_min"][axis] - a["bbox_max"][axis] if sign > 0
                       else a["bbox_min"][axis] - b["bbox_max"][axis])
                gap_ok = -CONTACT_TOL <= gap <= CONTACT_TOL
            aligned = (a is not None and b is not None
                       and _close(b["center"][other_axis], a["center"][other_axis], POS_TOL))
            return [_is_box(a, p["size"]), _on_ground(a), _xy_at(a, p["x"], p["y"]),
                    _shape_check(b, p["other"]), _on_ground(b), gap_ok, aligned]
        return fn

    def oracle(self, p):
        (tx, ty), _, _ = self._target(p)
        o = p["other"]
        return ("import bpy\n"
                + _shape_code({"shape": "cube", "name": p["anchor"], "size": p["size"]},
                              p["x"], p["y"], p["size"] / 2)
                + _shape_code(o, round(tx, 4), round(ty, 4), _half_h(o)))


class BetweenTemplate:
    """Held-out relation: an object on the ground exactly midway between two others."""

    def sample_params(self, rng):
        a, b, c = _pick_names(rng, 3)
        pa = [_r(rng.uniform(-4, 4)), _r(rng.uniform(-4, 4))]
        ang = rng.uniform(0, 2 * np.pi)
        dist = rng.uniform(3.0, 6.0)
        pc = [_r(pa[0] + dist * np.cos(ang)), _r(pa[1] + dist * np.sin(ang))]
        mid = {"name": b, "shape": str(rng.choice(["cube", "sphere"]))}
        if mid["shape"] == "sphere":
            mid["radius"] = _r(rng.uniform(0.2, 0.6))
        else:
            mid["size"] = _r(rng.uniform(0.3, 1.0))
        return {"a": a, "a_size": _r(rng.uniform(0.4, 1.2)), "a_xy": pa,
                "c": c, "c_size": _r(rng.uniform(0.4, 1.2)), "c_xy": pc, "mid": mid}

    def prompt(self, p):
        return (f'Create a cube named "{p["a"]}" with edge length {p["a_size"]:.2f} m resting on '
                f'the ground, centred at x = {p["a_xy"][0]:.2f}, y = {p["a_xy"][1]:.2f}, and a cube '
                f'named "{p["c"]}" with edge length {p["c_size"]:.2f} m resting on the ground, '
                f'centred at x = {p["c_xy"][0]:.2f}, y = {p["c_xy"][1]:.2f}. Then place '
                f'{_shape_words(p["mid"])} resting on the ground, exactly halfway between '
                f'"{p["a"]}" and "{p["c"]}".')

    def checks(self, p):
        mx = (p["a_xy"][0] + p["c_xy"][0]) / 2
        my = (p["a_xy"][1] + p["c_xy"][1]) / 2

        def fn(state):
            a, c, m = (_obj(state, p["a"]), _obj(state, p["c"]), _obj(state, p["mid"]["name"]))
            return [_is_box(a, p["a_size"]), _on_ground(a), _xy_at(a, *p["a_xy"]),
                    _is_box(c, p["c_size"]), _on_ground(c), _xy_at(c, *p["c_xy"]),
                    _shape_check(m, p["mid"]), _on_ground(m), _xy_at(m, mx, my)]
        return fn

    def oracle(self, p):
        mx = (p["a_xy"][0] + p["c_xy"][0]) / 2
        my = (p["a_xy"][1] + p["c_xy"][1]) / 2
        m = p["mid"]
        return ("import bpy\n"
                + _shape_code({"shape": "cube", "name": p["a"], "size": p["a_size"]},
                              *p["a_xy"], p["a_size"] / 2)
                + _shape_code({"shape": "cube", "name": p["c"], "size": p["c_size"]},
                              *p["c_xy"], p["c_size"] / 2)
                + _shape_code(m, round(mx, 4), round(my, 4), _half_h(m)))


TEMPLATES = {"stack": StackTemplate(), "next_to": NextToTemplate(),
             "between": BetweenTemplate()}            # "between" = held-out template


def checks_for(task):
    return TEMPLATES[task["template"]].checks(task["params"])


def oracle_for(task):
    return TEMPLATES[task["template"]].oracle(task["params"])
