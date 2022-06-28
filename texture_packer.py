from .utils.image_packing import retrieve_images_and_uvs
import bpy

class TexturePacker:
    def __init__(self, objs, node_blacklist):
        (self.images, self.uvs) = retrieve_images_and_uvs(objs, node_blacklist)

        # Adumbrating our strategy for initially grouping the atlases here.
        socket_images = {}
        for im_pack_data in self.images.values():
            socket = im_pack_data.socket
            
            if not socket in socket_images:
                socket_images[socket] = []
            
            socket_images[socket].append(im_pack_data)
