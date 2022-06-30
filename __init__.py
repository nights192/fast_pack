bl_info = {
    "name": "FastPack",
    "description": "A flexible texture-atlasing tool.",
    "author": "Archie",
    "blender": (3, 0, 0),
    "location": "View3D",
    "category": "Object",
}

import bpy
from .ops import RefreshTexturePacker
from .ui import ImagePackingGroup
from .ui import ARC_UL_IPList
from .ui import FastPackMenu

classes = [
    ImagePackingGroup,
    RefreshTexturePacker,
    ARC_UL_IPList,
    FastPackMenu
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.fpack_ui_list = bpy.props.CollectionProperty(type=ImagePackingGroup)
    bpy.types.Scene.fpack_ui_list_index = bpy.props.IntProperty(name="FastPack socket index", default=0)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.fpack_ui_list
    del bpy.types.Scene.fpack_ui_list_index