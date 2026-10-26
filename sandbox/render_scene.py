"""Trusted render pass for the write-up: opens a saved scene and renders it with the
target layout drawn as wireframe ghosts. Usage: blender in.blend --python render_scene.py -- cfg.json out.png"""
import json
import sys

import bpy
from mathutils import Vector

cfg_path, out_path = sys.argv[sys.argv.index("--") + 1:][:2]
cfg = json.load(open(cfg_path))
scene = bpy.context.scene


def mat(name, rgb, rough=0.55, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


colors = {k: mat(f"c_{k}", v) for k, v in cfg["colors"].items()}
other = mat("c_other", (0.55, 0.55, 0.55))
for ob in list(scene.objects):
    if ob.type != "MESH":
        bpy.data.objects.remove(ob)
        continue
    ob.data.materials.clear()
    ob.data.materials.append(colors.get(ob.name, other))
    for p in ob.data.polygons:
        p.use_smooth = len(ob.data.vertices) > 24

# Ghosts: the target layout as thin glowing wireframes.
ghost = mat("ghost", cfg["ghost_rgb"], emit=2.5)
for g in cfg["ghosts"]:
    lo, hi = Vector(g["bbox_min"]), Vector(g["bbox_max"])
    c, d = (lo + hi) / 2, hi - lo
    if g["shape"] == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=d.x / 2, location=c, segments=24, ring_count=12)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        bpy.context.active_object.scale = d
    o = bpy.context.active_object
    o.name = "ghost_" + g["name"]
    w = o.modifiers.new("w", "WIREFRAME")
    w.thickness = 0.028
    w.use_relative_offset = False
    o.data.materials.append(ghost)

# Ground, camera, light.
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(mat("ground", cfg["ground_rgb"], rough=0.9))
lo, hi = Vector(cfg["bounds"][0]), Vector(cfg["bounds"][1])
center = (lo + hi) / 2
cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = max(hi.x - lo.x, hi.y - lo.y, (hi.z - lo.z) * 1.5, 2.5) * 1.55
cam = bpy.data.objects.new("cam", cam_d)
scene.collection.objects.link(cam)
cam.location = center + Vector((1.0, -1.25, 1.05)).normalized() * 30
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
sun_d = bpy.data.lights.new("sun", "SUN")
sun_d.energy = 3.2
sun_d.angle = 0.25
sun = bpy.data.objects.new("sun", sun_d)
sun.rotation_euler = (0.75, 0.15, 0.9)
scene.collection.objects.link(sun)
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*cfg["sky_rgb"], 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
scene.world = world

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = cfg.get("resolution", [960, 600])
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
