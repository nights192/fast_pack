from collections import defaultdict
from dataclasses import dataclass
from .image_retrieval import ImagePackData
from .image_retrieval import UVReference
from ..ui import ImagePackingGroup
from ..exceptions import PackingException
from PIL import Image

import functools
import math
import re
import numpy as np
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

    def could_overlap(self, x, y, rect: 'UVRectangle') -> bool:
        if rect.x == None:
            return False
        
        x2 = x + self.width
        y2 = y + self.height

        rx2 = rect.x + rect.width
        ry2 = rect.y + rect.height

        print(f"Item 1: Point 1: ({x}, {y})\tPoint 2: (P{x2}, {y2})")
        print(f"Item 2: Point 1: ({rect.x}, {rect.y})\tPoint 2: (P{rx2}, {ry2})")

        overlaps_horizontally = (x <= rect.x and rect.x < x2) or (rect.x < x and x < rx2)
        print(overlaps_horizontally)

        overlaps_vertically = (y <= rect.y and rect.y < y2) or (rect.y < y and y < ry2)
        print(overlaps_vertically)

        return overlaps_horizontally and overlaps_vertically

    def overlaps(self, rect: 'UVRectangle') -> bool:
        self.could_overlap(self.x, self.y, rect)

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

def calculate_uv_ratios(images: dict[bpy.types.Image, ImagePackData], uvs: list[list[UVReference]], max_res: int):
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

def get_file_name():
    file_with_type = bpy.path.basename(bpy.data.filepath)
    
    return re.match(r'.+(?=\.blend$)', file_with_type).group(0)

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

def rect_area(rect: UVRectangle) -> float:
    return rect.width * rect.height

def place_rect(packing_rects: list[UVRectangle], rect: UVRectangle, stride_x: float, stride_y: float) -> bool:
    """Attempts to place a UVRectangle within a normalized space, returning its success."""

    ## Deeply sub-optimal; however, this saves us from persisting a variable outside the function,
    ## or leveraging a goto. It would be difficult for there to be a sufficient amount of small images to
    ## make this unacceptably slow.
    for y in np.arange(0.0, 1.0 - rect.width, stride_y):
        for x in np.arange(0.0, 1.0 - rect.height, stride_x):
            success = True
            for col_rect in packing_rects:
                success = success and not rect.could_overlap(x, y, col_rect)
            
            if success:
                (rect.x, rect.y) = (x, y)

                return True

    return False

def pack_rects(packing_rects: list[UVRectangle]) -> bool:
    """Packs a list of UVRectangles into a normalized space, returning its success status. (Destructive)"""

    packing_rects.sort(key=rect_area, reverse=True)

    # We'll leverage the minimum image-dimensions as our scan-stride for this, so as to save processing power.
    (stride_x, stride_y) = (1.0, 1.0)
    for rect in packing_rects:
        if rect.width < stride_x:
            stride_x = rect.width
        
        if rect.height < stride_y:
            stride_y = rect.height
    
    for rect in packing_rects:
        if not place_rect(packing_rects, rect, stride_x, stride_y):
            return False

    return True

def pack_uvs(uvs: list[list[UVReference]], uv_widths_normalized, uv_heights_normalized) -> list[UVRectangle]:
    """Packs all UVs in a given UV-list, returning a list of normalized transforms for the positions of the resulting rectangles."""

    packing_rects = [UVRectangle(i, None, None, 0.0, 0.0) for i in range(0, len(uvs))]
    normalize_uvs(uvs)

    # Given that Python's zip function's results are lazy, it's cheaper to pre-build the array and iterate thereafter.
    for i, (width, height) in enumerate(zip(uv_widths_normalized, uv_heights_normalized)):
        packing_rects[i].width = width
        packing_rects[i].height = height

    if not pack_rects(packing_rects):
        raise PackingException

    for rect in packing_rects:
        uv_group = uvs[rect.uv_index]

        for uv_reference in uv_group:
            mesh = uv_reference.object.data
            uv_slot = uv_reference.object_uv_slot

            for loop_index in uv_reference.contents:
                loop = mesh.uv_layers[uv_slot].data[loop_index]
                loop.uv[0] = (loop.uv[0] * rect.width) + rect.x
                loop.uv[1] = (loop.uv[1] * rect.height) + rect.y

    return packing_rects

def pack_images(group_images: defaultdict[int, list[ImagePackData]], group_scales: defaultdict[int, float], transforms: list[UVRectangle], max_res: int):
    transforms_by_uv = {rect.uv_index : rect for rect in transforms}

    for i, group in group_images.items():
        scale = group_scales[i]
        group_image = Image.new('RGBA', (math.floor(max_res * scale), math.floor(max_res * scale)), color=(0, 0, 0, 0))

        for image_pack in group:
            (_, height) = image_pack.image.size

            x_transform = transforms_by_uv[image_pack.uv_index].x * max_res * scale
            y_transform = (1.0 - transforms_by_uv[image_pack.uv_index].y) * max_res * scale - height
            group_image.paste(image_pack.image, (math.floor(x_transform), math.floor(y_transform)))
        
        group_image.save(f'{bpy.path.abspath("//")}/{i}.png')


