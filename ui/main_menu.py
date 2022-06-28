import bpy

class FastPackMenu(bpy.types.Panel):
    bl_label = "FastPack"
    bl_idname = "ARC_PT_FastPack_Menu"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FastPack'

    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.operator("arcfpack.refresh_texture_packer", text="Process Objects", icon="CONSOLE")