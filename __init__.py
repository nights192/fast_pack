bl_info = {
    "name": "FastPack",
    "description": "A flexible texture-atlasing tool.",
    "author": "Archie",
    "version": (0, 95),
    "blender": (3, 0, 0),
    "location": "View3D",
    "category": "Object",
}

import bpy
from .ui import ImagePackingGroup

classes = []

## We load the bulk of our addon should Pillow be present; otherwise, we need only initialize what's present
## in the installer.
try:
    from PIL import Image
    from .ops import RefreshTexturePacker
    from .ops import PackTextures
    from .ui import ARC_UL_IPList
    from .ui import FastPackMenu

    classes = [
        ImagePackingGroup,
        RefreshTexturePacker,
        PackTextures,
        ARC_UL_IPList,
        FastPackMenu
    ]

except ImportError:
    from .installer_ops import InstallPillow
    from .ui import InstallerMenu

    classes = [
        ImagePackingGroup,
        InstallPillow,
        InstallerMenu
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.WindowManager.fpack_ui_list = bpy.props.CollectionProperty(type=ImagePackingGroup)
    bpy.types.WindowManager.fpack_ui_list_index = bpy.props.IntProperty(name="FastPack Socket Index", default=0)
    bpy.types.WindowManager.fpack_max_res = bpy.props.IntProperty(name="FastPack Max Res", default=4096)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.WindowManager.fpack_max_res
    del bpy.types.WindowManager.fpack_ui_list
    del bpy.types.WindowManager.fpack_ui_list_index