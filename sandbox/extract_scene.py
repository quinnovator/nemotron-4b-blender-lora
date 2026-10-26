"""Dump the scene's mesh objects as JSON: world-space bounds from evaluated geometry."""
import json
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
deps = bpy.context.evaluated_depsgraph_get()
objects = {}
for ob in bpy.context.scene.objects:
    if ob.type != "MESH":
        continue
    ev = ob.evaluated_get(deps)
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    n_faces = len(mesh.polygons)
    ev.to_mesh_clear()
    if pts:
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
    else:
        lo = hi = list(ob.matrix_world.translation)
    objects[ob.name] = {
        "location": list(ob.matrix_world.translation),
        "bbox_min": lo, "bbox_max": hi,
        "dims": [h - l for h, l in zip(hi, lo)],
        "center": [(h + l) / 2 for h, l in zip(hi, lo)],
        "n_verts": len(pts), "n_faces": n_faces,
        "visible": not ob.hide_render,
    }
with open(out, "w") as f:
    json.dump({"objects": objects}, f)
