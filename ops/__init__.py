from ..texture_packer import TexturePacker
from ..utils.image_packing import get_file_name
import bpy

class RefreshTexturePacker(bpy.types.Operator):
    """Fetches the requisite information to compile a list of packable textures"""

    bl_idname = "arcfpack.refresh_texture_packer"
    bl_label = "Update texture packing scene state"

    # Note: We store our resulting object in bpy.types.Scene.fpack_state .
    def execute(self, context):
        # TODO: Provide means to exclude nodes from blacklist.
        context.window_manager.fpack_ui_list.clear() # Clear out any leftover data.
        bpy.types.WindowManager.fpack_state = TexturePacker([obj for obj in bpy.context.selected_objects if obj.type == "MESH"], {'ShaderNodeBsdfTransparent'})

        return {'FINISHED'}

class PackTextures(bpy.types.Operator):
    """Packs listed textures"""

    bl_idname = "arcfpack.pack_textures"
    bl_label = "Pack textures"

    def execute(self, context):
        # As the operations undertaken are mutable, we split off into a new file.
        #original_file = f'{bpy.path.abspath("//")}/{bpy.path.basename(bpy.data.filepath)}'
        bpy.ops.wm.save_as_mainfile(filepath=f'{bpy.path.abspath("//")}/{get_file_name()}_baked.blend')

        if not context.window_manager.fpack_state.build(context.window_manager.fpack_max_res):
            #bpy.ops.wm.open_mainfile(filepath=original_file)
            pass
        
        bpy.ops.wm.save_mainfile()
        return {'FINISHED'}