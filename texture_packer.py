from .utils.image_retrieval import retrieve_images_and_uvs
import bpy

## This class, as it stands, is functionally a singleton; however, given further work on the UI,
## transitioning to multiple copies ought to be simple.
class TexturePacker:
    """Manages the state of an unpacked selection of UVs."""

    def __init__(self, objs, node_blacklist):
        (self.images, self.uvs) = retrieve_images_and_uvs(objs, node_blacklist)

        # Adumbrating our strategy for initially grouping the atlases here.
        socket_images = {}
        for im_pack_data in self.images.values():
            socket = im_pack_data.socket
            
            if not socket in socket_images:
                socket_images[socket] = []
            
            socket_images[socket].append(im_pack_data)

        # We generate our UIList components--surmising each shader input a separate pack.
        self.ui_list = bpy.context.window_manager.fpack_ui_list
        for i, socket in enumerate(socket_images.keys()):
            ui_group = self.ui_list.add()
            ui_group.socket = socket
            ui_group.target_group = i
