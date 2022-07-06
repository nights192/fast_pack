import bpy

class InstallerMenu(bpy.types.Panel):
    bl_label = "FastPack"
    bl_idname = "ARC_PT_FastPack_Installer_Menu"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FastPack'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="This addon requires Pillow. Press to install.")
        row = layout.row()
        row.label(text="(May require admin.)")

        row = layout.row()
        row.operator("arcfpack.install_pillow", text="Install Pillow", icon="CONSOLE")

        if bpy.types.WindowManager.pillow_installed:
            row = layout.row()
            row.label(text="Complete!")

            row = layout.row()
            row.label(text="Restart Blender.")

