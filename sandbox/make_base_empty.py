"""Run with host Blender: blender -b --factory-startup --python sandbox/make_base_empty.py

Writes sandbox/base_empty.blend, an empty scene (no objects) in metres, Z up.
"""
import os

import bpy

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
    for block in list(coll):
        coll.remove(block)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_empty.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, check_existing=False, compress=False)
print("wrote", out)
