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
from .ui import FastPackMenu

classes = [
    RefreshTexturePacker,
    FastPackMenu
]

def register():
    bpy.types.Scene.fpack_state = []

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)