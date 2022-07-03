import bpy

class ImagePackingGroup(bpy.types.PropertyGroup):
    socket: bpy.props.StringProperty(name="Socket Name")

    target_group: bpy.props.IntProperty(name="Target Group", description="The target grouping id for related images to be included under",
    default=0, subtype='UNSIGNED', min=0)

class ARC_UL_IPList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row.row()

            row.label(text=item.socket)
            row.label(text=str(item.target_group))

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")