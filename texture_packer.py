from collections import defaultdict
from functools import reduce
from .utils.image_retrieval import ImagePackData, retrieve_images_and_uvs
from .utils.image_packing import calculate_uv_ratios, pack_uvs
from .utils.image_packing import size_group_images
import bpy

def denormalized(x: float):
    if x > 1.0 or x < 0.0:
        return True
    
    return False

## This class, as it stands, is functionally a singleton; however, given further work on the UI,
## transitioning to multiple copies ought to be simple.
class TexturePacker:
    """Manages the state of an unpacked selection of UVs."""

    def __init__(self, objs: list[bpy.types.Object], node_blacklist: set[bpy.types.Node]):
        (self.image_packs, self.uvs) = retrieve_images_and_uvs(objs, node_blacklist)

        # Initial sorting of image_packs ought to be by material input.
        self.socket_images = {}
        for im_pack_data in self.image_packs.values():
            socket = im_pack_data.socket
            
            if not socket in self.socket_images:
                self.socket_images[socket] = []
            
            self.socket_images[socket].append(im_pack_data)

        # We generate our UIList components--surmising each shader input a separate pack.
        self.ui_list = bpy.context.window_manager.fpack_ui_list
        for i, socket in enumerate(self.socket_images.keys()):
            ui_group = self.ui_list.add()
            ui_group.socket = socket
            ui_group.target_group = i

    def build(self, max_res):
        """Constructs all requisite atlas textures and UVs. Returns True on success, False on failure."""
        (uv_reference_surface_areas, uv_widths_normalized, uv_heights_normalized) = calculate_uv_ratios(self.image_packs, self.uvs, max_res)
        if reduce(lambda a, b: a + b, uv_reference_surface_areas, 0) > max_res**2:
            return False 

        for image in self.image_packs:
            self.image_packs[image].load_image()

        # It's necessary to fetch the image_packs associated with each group by UV to ensure proportionality.
        group_images: defaultdict[int, list[ImagePackData]] = defaultdict(lambda: []) # We leverage a dictionary, as groups may be non-contiguous due to limitations in Blender's property system.

        for config in self.ui_list:
            for image_pack in self.socket_images[config.socket]:
                group_images[config.target_group].append(image_pack)
        
        # Resize our images as appropriate, saving the scaling information such that we may detect
        # relative maximum sizes of our atlases.
        group_scales = size_group_images(group_images, uv_reference_surface_areas)
        pack_uvs(self.uvs)

        return True