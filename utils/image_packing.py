from collections import defaultdict
from dataclasses import dataclass
from .image_retrieval import ImagePackData
from .image_retrieval import UVReference
from ..ui import ImagePackingGroup
from PIL import Image

import functools
import math
import bpy

## Could be trivially made generic; however, this is unlikely to come up elsewhere in the packer.
@dataclass
class UVRectangle:
    """Describes a portion of a UV map tied to a given sub-UV set."""

    uv_index: int
    x: float
    y: float
    width: float
    height: float

    def overlaps(self, rect: 'UVRectangle') -> bool:
        own_rx = self.x + self.width
        own_ry = self.y + self.height
        rect_rx = rect.x + rect.width
        rect_ry = rect.y + rect.height

        return own_rx >= rect.x and own_ry >= rect.y and self.x <= rect_rx and self.y <= rect_ry

def resize_algorithm(image_pack: ImagePackData) -> int:
    """Translates from Blender's string-enum of resize options to PIL's."""

    match image_pack.interpolation:
        case 'Linear':
            return Image.LINEAR
        
        case 'Closest':
            return Image.NEAREST
        
        case 'Cubic':
            return Image.CUBIC
        
        case _:
            return Image.LINEAR

def calculate_uv_ratios(images: dict[bpy.types.Image, ImagePackData], uvs, max_res: int):
    # We must calculate the maximum percentage surface area occupied by our images per UV. This is to be a barometer for what must be resized.
    uv_max_surface_areas = [0] * len(uvs)
    uv_max_surface_widths = [0] * len(uvs)
    uv_max_surface_heights = [0] * len(uvs)

    for image_pack in images.values():
        (w, h) = image_pack.bl_image.size
        area = w * h

        uv_max_surface_widths[image_pack.uv_index] = w if w > uv_max_surface_widths[image_pack.uv_index] else uv_max_surface_widths[image_pack.uv_index]
        uv_max_surface_heights[image_pack.uv_index] = h if h > uv_max_surface_heights[image_pack.uv_index] else uv_max_surface_heights[image_pack.uv_index]
        uv_max_surface_areas[image_pack.uv_index] = area if area > uv_max_surface_areas[image_pack.uv_index] else uv_max_surface_areas[image_pack.uv_index]
    
    uv_surface_widths_normalized = list(map(lambda x: x / max_res, uv_max_surface_widths))
    uv_surface_heights_normalized = list(map(lambda x: x / max_res, uv_max_surface_heights))

    return (uv_max_surface_areas, uv_surface_widths_normalized, uv_surface_heights_normalized)

def size_group_images(group_images, uv_reference_surface_areas) -> defaultdict[int, float]:
    """Ensures that all images in an image group are scaled to a single ratio with the UV map, returning the
    amount each group is scaled compared to their canonical sizes.
    """

    group_scales = defaultdict(lambda: 0)
    for i, group in group_images.items():
        group_scale = 0

        for pack in group:
            (w, h) = pack.bl_image.size

            scale = (w * h) / uv_reference_surface_areas[pack.uv_index]
            group_scale = scale if scale > group_scale else group_scale
        
        # As all UV images will be uniformly scaled, we may convert the surface area scale to a dimensional
        # one by taking the square root.
        group_scale = group_scale**0.5
        group_scales[i] = group_scale

        for pack in group:
            (w, h) = pack.bl_image.size

            scale_factor = group_scale / ((w * h) / uv_reference_surface_areas[pack.uv_index])**0.5
            pack.image.resize((w * scale_factor, h * scale_factor), resize_algorithm(pack))
    
    return group_scales

## Unfortunately, the process of attaining cell displacement requires first obtaining a consistent reference anchor;
## hence, a loop is necessary. (The process would otherwise be degenerative should a corrupt UV span multiple ranges.)
def get_uv_cell_displacement(mesh: bpy.types.Mesh, uv_slot: int, indices: list[int]) -> tuple[int, int]:
    """Fetches the number of 0-1 "cells" along each axis a UV map is translated."""

    (anchor_u, anchor_v) = (None, None)

    for loop_index in indices:
        (u, v) = mesh.uv_layers[uv_slot].data[loop_index].uv

        if (anchor_u == None or u < anchor_u) and (anchor_v == None or v < anchor_v):
            (anchor_u, anchor_v) = (u, v)

    return (math.floor(anchor_u), math.floor(anchor_v))

def normalize_uvs(uvs: list[list[UVReference]]):
    """Normalizes all model UV-spaces. (Destructive)"""

    for sub_uv in uvs:
        for reference in sub_uv:
            mesh = reference.object.data
            uv_slot = reference.object_uv_slot

            (offset_u, offset_v) = get_uv_cell_displacement(mesh, uv_slot, reference.contents)
            for loop_index in reference.contents:
                loop = mesh.uv_layers[uv_slot].data[loop_index]

                loop.uv[0] -= offset_u
                loop.uv[1] -= offset_v

def pack_uvs(uvs: list[list[UVReference]]) -> list[UVRectangle]:
    """Packs all UVs in a given UV-list, returning a list of normalized transforms for the positions of the resulting rectangles."""

    normalize_uvs(uvs)

    return []

