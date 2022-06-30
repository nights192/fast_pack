import bpy

class FastPackMenu(bpy.types.Panel):
    bl_label = "FastPack"
    bl_idname = "ARC_PT_FastPack_Menu"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FastPack'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        model_loaded = scene.fpack_ui_list_index >= 0 and len(scene.fpack_ui_list) > 0
        
        row = layout.row()
        row.label(text="Material Groups:")

        row = layout.row()
        row.template_list("ARC_UL_IPList", "FPack_SocketList", scene, "fpack_ui_list", scene, "fpack_ui_list_index")

        # Should we have searched the involved objects, we may permit group editing.
        if model_loaded:
            item = scene.fpack_ui_list[scene.fpack_ui_list_index]

            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(item, "target_group")

        col = layout.column(align=True)
        col.operator("arcfpack.refresh_texture_packer", text="Process Objects", icon="CONSOLE")