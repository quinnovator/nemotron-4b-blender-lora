import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.save_as_mainfile(filepath=out, check_existing=False, compress=False)
