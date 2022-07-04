from dataclasses import dataclass
from collections import defaultdict
import enum
from logging import root
from PIL import Image
import numpy as np
from .shader_graph import fetch_search_roots, build_node_relations, grab_socket_images, grab_socket_image_nodes
import bpy

@dataclass
class UVReference:
    """Provides a list of loop incides and their commensurate lookup information. Used in a list to keep track of related, cross-object UVs.
    
    Attributes:
        object (bpy.types.Object): The given UV loops' object.
        object_uv_slot (int): The given UV loops' UV slot within the object.
        contents ([int]): List of UV loop indices.
    """
    object: bpy.types.Object
    object_uv_slot: int
    contents: list[int]

@dataclass
class ImagePackData:
    """Element describing an individual texture requiring packaging.
    
    Attributes:
        image (Image): PIL Image representing the Blender image.
        bl_image (bpy.types.Image): Originating Blender image object.
        uv_index (int): An index towards an entry in a list of lists of UVReferences.
    """

    image: Image
    bl_image: bpy.types.Image
    uv_index: int
    interpolation: str
    socket: str

    ## For convenience--as our process operates in phases due to the
    ## global nature of the final atlas' data.
    def load_image(self):
        self.image = load_image(self.bl_image)

class MaterialUVSymbol:
    """A symbol representing an as of-yet unresolved reference to a model's sub-UV table.

    Attributes:
        uv_index (int): A presumptive relationship with an entry in a sub-UV table.
        images ((bpy.types.Image, str, str)): A list of tuples beholden to this link; leveraged contagiously to determine uv_index, consisting of the Image, its interpolation, and the socket through which it had been discovered.
    """

    def __init__(self, uv_index: int = None, images: list[(bpy.types.Image, str, str)] = None):
        if images == None:
            self.images = []
        else:
            self.images = images
        
        self.uv_index = uv_index
    
    def __str__(self):
        return f'Link: {self.uv_index} | {self.images}'

def load_image(bl_image: bpy.types.Image) -> Image:
    """Generates a PIL Image from a Blender image."""

    bl_data = np.asarray(bl_image.pixels)
    (width, height) = bl_image.size
    channels = bl_image.channels

    default_channels = np.array([0.0, 0.0, 0.0, 1.0])
    image_data = np.tile(default_channels, (height, width, 1))
    bl_data = bl_data.reshape((height, width, channels))
    
    image_data[:, :, 0:channels] = bl_data
    image_data *= 255
    image_data = np.rint(image_data).astype('uint8')
    
    image = Image.fromarray(image_data)
    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return image

def fetch_obj_material_loops(obj: bpy.types.Object) -> list[list[list[int]]]:
    mesh: bpy.types.Mesh = obj.data
    res = [[[] for uv in mesh.uv_layers] for mat in obj.material_slots]
    
    default_uv = mesh.uv_layers.active
    for i, uv in enumerate(mesh.uv_layers):
        uv_loops_accounted = set()
        uv.active = True
        
        for poly in mesh.polygons:
            for loop_range in poly.loop_indices:
                if not loop_range in uv_loops_accounted:
                    res[poly.material_index][i].append(loop_range)
                    uv_loops_accounted.add(loop_range)
    
    default_uv.active = True
    
    return res

def retrieve_images_and_uvs(target_objs: list[bpy.types.Object], node_blacklist: set[bpy.types.Node]) -> tuple[dict[bpy.types.Image, ImagePackData], list[list[UVReference]]]:
    """Given a list of target objects, isolate all independent images and UV map partitions present."""

    images = {}
    uvs = []

    for obj in target_objs:
        mesh = obj.data
        
        uv_slots = {uv.name : i for i, uv in enumerate(mesh.uv_layers)}
        obj_uvs = fetch_obj_material_loops(obj)

        for i, slot in enumerate(obj.material_slots):
            mat = slot.material
            
            material_uvs = obj_uvs[i]
            
            # Each of these corresponds to a UV in material_uvs.
            uv_links = [MaterialUVSymbol(None, None) for _ in material_uvs]
            
            root_nodes = fetch_search_roots(build_node_relations(mat), node_blacklist)
            mat_images = [elem for root_node in root_nodes for socket in root_node.n_to for elem in grab_socket_images(mesh, root_node, socket)]
            
            parsed_images = set()
            
            for (image, uv, interp, src_socket) in mat_images:
                if image in parsed_images:
                    continue
                
                parsed_images.add(image)
                
                # No need to explicitly scan this image later; hence, we continue,
                # updating our uv link resolution if necessary.
                if image in images:
                    if owning_mat_uv.uv_index == None:
                        owning_mat_uv.uv_index = images[image].uv_index
                    
                    continue
                
                owning_mat_uv = uv_links[uv_slots[uv]]
                owning_mat_uv.images.append((image, interp, src_socket))
            
            for uv_slot, link in enumerate(uv_links):
                # Should the link be divorced from all discovered
                # sub-UVs...
                if link.uv_index == None:
                    link.uv_index = len(uvs)
                    uvs.append([]) # We instantiate a new sub-UV list.
                
                uv_index = link.uv_index
                
                link_ref = UVReference(obj, uv_slot, material_uvs[uv_slot])
                uvs[uv_index].append(link_ref)
                
                for (image, interp, src_socket) in link.images:
                    image_data = ImagePackData(None, image, uv_index, interp, src_socket)
                    images[image] = image_data
    
    return (images, uvs)

def load_atlases(groups: list[int]) -> list[bpy.types.Image]:
    return [bpy.data.images.load(f"//{group}.png") for group in groups]

def replace_images(target_objs: list[bpy.types.Object], node_blacklist: set[bpy.types.Node], group_images: defaultdict[int, list[ImagePackData]], baked_textures: list[bpy.types.Image]):
    """Replaces shader images with their atlased alternatives. (Destructive)"""

    image_groups = {pack.bl_image : group_index for group_index, pack_list in group_images.items() for pack in pack_list}

    for obj in target_objs:
        for slot in obj.material_slots:
            root_nodes = fetch_search_roots(build_node_relations(slot.material), node_blacklist)
            mat_images = [elem for root_node in root_nodes for socket in root_node.n_to for elem in grab_socket_image_nodes(obj.data, root_node, socket)]
            
            for image_node in mat_images:
                image_node.image = baked_textures[image_groups[image_node.image]]