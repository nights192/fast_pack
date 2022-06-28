from ..texture_packer import TexturePacker
import bpy

class RefreshTexturePacker(bpy.types.Operator):
    """Fetches the requisite information to compile a list of packable textures"""

    bl_idname = "arcfpack.refresh_texture_packer"
    bl_label = "Update texture packing scene state"

    def execute(self, context):
        # TODO: Provide means to exclude nodes from blacklist.
        bpy.types.Scene.fpack_state = TexturePacker([obj for obj in bpy.data.objects if obj.type == "MESH"], {'ShaderNodeBsdfTransparent'})
        return {'FINISHED'}