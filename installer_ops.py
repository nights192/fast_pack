from subprocess import call

import sys
import os
import bpy

class InstallPillow(bpy.types.Operator):
    """Installs Python's Pillow library. (May take a while)"""

    bl_idname = "arcfpack.install_pillow"
    bl_label = "Install Pillow"

    def execute(self, context):
        bl_env = dict(os.environ)
        bl_env["PYTHONNOUSERSITE"] = "1" # Necessary so as to avoid spurious checks to user modules.

        call([sys.executable, '-m', 'pip', 'install', 'Pillow', '--upgrade'], shell=True, env=bl_env)

        ## TODO: Check for operation success.
        bpy.types.WindowManager.pillow_installed = True

        self.report({'INFO'}, 'Pillow installation complete')
        return {'FINISHED'}