"""
This module is used for duplicates removing. There are 2 classes: PublicationsGroup for duplicates and
GroupsContainer for PublicationsGroup objects.
"""
from typing import Iterable

import numpy as np
from networkx import connected_components
from scipy.sparse import csgraph
import networkx as nx


class PublicationsGraph:
    def __init__(self):
        self._graph = nx.Graph()

    def add_vertex(self, pub_id):
        self._graph.add_node(pub_id)

    def add_edge(self, pub_id_1, pub_id_2):
        self._graph.add_edge(pub_id_1, pub_id_2)

    def connected_components(self):
        return list(connected_components(self._graph))
