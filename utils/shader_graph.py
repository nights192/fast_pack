from enum import Enum
from collections import deque
from typing import Dict, Set

import bpy

class LinkDirection(Enum):
    """An enumeration representing the direction from whence a connection in a graph flows."""

    TO = 0
    FROM = 1

class GraphNode:
    """A node within a graph structure representing a shadergraph node.

    Attributes:
        node (bpy.types.Node): The corresponding shadergraph node.
        n_from ({str -> [GraphNode]}): A socket-name dictionary for the output sockets of a given node.
        n_to ({str -> [GraphNode]}): A socket-name dictionary for the input sockets of a given node.
    """

    def __init__(self, node):
        self.node = node
        self.n_from = {}
        self.n_to = {}
    
    def first_from_link(self, slot: str) -> 'GraphNode':
        """A utility function fetching the first GraphNode connected to a socket."""
        return self.n_from[slot][0]
    
    def first_to_link(self, slot: str) -> 'GraphNode':
        """A utility function fetching the first GraphNode connected to a socket."""
        return self.n_to[slot][0]
    
    def add_link(self, direction: LinkDirection, slot: str, g_node: 'GraphNode'):
        io_dict = self.n_to if direction == LinkDirection.TO else self.n_from
        
        if not (slot in io_dict):
            io_dict[slot] = []
        
        io_dict[slot].append(g_node)
    
    def __str__(self):
        return f'{self.node}\nFROM {self.n_from}\n\nTO: {self.n_to}\n\n\n'

def build_node_relations(mat: bpy.types.Material) -> Dict[bpy.types.Node, GraphNode]:
    """Returns a dictionary pointing to the nodes of our graph, such that we may traverse it in O(n) time rather than O(n^2)."""

    relations = {}
    
    for link in mat.node_tree.links:
        if not (link.from_node in relations):
            relations[link.from_node] = GraphNode(link.from_node)
        
        if not (link.to_node in relations):
            relations[link.to_node] = GraphNode(link.to_node)
        
        relations[link.from_node].add_link(LinkDirection.FROM, link.from_socket.name, relations[link.to_node])
        relations[link.to_node].add_link(LinkDirection.TO, link.to_socket.name, relations[link.from_node])

    return relations

def fetch_search_roots(graph: Dict[bpy.types.Node, GraphNode], blacklist: set[bpy.types.Node] = set()):
    """Given a graph dictionary generated by build_node_relations and a blacklist set of invalid head nodes,
    this function generates an array of graph heads to be traversed.
    """

    roots = []
    
    ## We start from the head of our DAG to isolate relevant output nodes for image packing.
    start = None
    for g_node in graph.values():
        if g_node.node.bl_idname == 'ShaderNodeOutputMaterial':
            start = g_node
            break
    
    ## We'll now trace to the first relevant, non-blacklisted materials via BFS.
    node_stack = deque([start.first_to_link('Surface')])
    
    while len(node_stack) != 0:
        cur_node = node_stack.pop()
        
        # A mix shader dictates a complication in our texture relations; hence, we'll treat its sources as subtrees.
        if cur_node.node.bl_idname == 'ShaderNodeMixShader':
            for to_node in cur_node.n_to['Shader']:
                node_stack.append(to_node)
                    
        elif not cur_node.node.bl_idname in blacklist:
            roots.append(cur_node)
    
    return roots

def grab_socket_image_nodes(mesh: bpy.types.Mesh, g_node: GraphNode, socket: str) -> list[bpy.types.ShaderNodeTexImage]:
    """Given a starting position in the graph and a socket id, crawl and locate
    all connected images, treating the inputs as though they were a DAG.
    """

    res = []
    
    node_stack = deque([node for node in g_node.n_to[socket]])
    while len(node_stack) != 0:
        cur_node = node_stack.pop()
        
        if cur_node.node.bl_idname == "ShaderNodeTexImage":            
            res.append(cur_node.node)
        else:
            for cur_socket in cur_node.n_to.values():
                for node in cur_socket:
                    node_stack.append(node)
    
    return res

def grab_socket_images(mesh: bpy.types.Mesh, g_node: GraphNode, socket: str) -> list[(bpy.types.Image, str, str, str)]:
    """Given a starting position in the graph and a socket id, crawl and locate
    all connected images, treating the inputs as though they were a DAG.
    """

    res = []
    
    node_stack = deque([node for node in g_node.n_to[socket]])
    while len(node_stack) != 0:
        cur_node = node_stack.pop()
        
        if cur_node.node.bl_idname == "ShaderNodeTexImage":
            uv = mesh.uv_layers.active.name
            
            if 'Vector' in cur_node.n_to:
                uv = cur_node.n_to['Vector'][0].node.uv_map
            
            res.append((cur_node.node.image, uv, cur_node.node.interpolation, socket))
        else:
            for cur_socket in cur_node.n_to.values():
                for node in cur_socket:
                    node_stack.append(node)
    
    return res