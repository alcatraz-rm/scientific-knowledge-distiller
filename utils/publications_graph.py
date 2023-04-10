"""
This module is used for duplicates removing.
"""
import networkx as nx


class PublicationsGraph:
    def __init__(self):
        self._graph = nx.Graph()

    def add_vertex(self, pub_id):
        self._graph.add_node(pub_id)

    def add_edge(self, pub_id_1, pub_id_2):
        self._graph.add_edge(pub_id_1, pub_id_2, length=5)

    def connected_components(self):
        return list(nx.connected_components(self._graph))
