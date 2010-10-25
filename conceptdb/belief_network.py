from scipy import sparse
from scipy.sparse.linalg.dsolve import linsolve
from csc.divisi2.ordered_set import OrderedSet
import numpy as np
import networkx as nx

def make_diag(d):
    return sparse.dia_matrix(([d], [0]), shape=(len(d), len(d)))

GND = '~ground~'

class BeliefNetwork(object):
    def __init__(self, ground_weight=1.0):
        self.graph = nx.Graph()
        self.conjunctions = set()
        self.ground_weight = ground_weight

        self.nodes = None
        self.edges = None
        self._node_matrix = None
        self._conductance = None

    def add_edge(self, source, dest, weight):
        self.graph.add_edge(source, dest, weight=weight)

    def add_conjunction(self, sources, dest, weight):
        self.conjunctions.add((sources, dest, weight))
        for source in sources:
            self.add_edge(self, source, dest, weight)

    def ordered_nodes():
        nodes = self.graph.nodes()
        nodes.remove(GND)
        nodes.sort()
        return nodes

    def finalize(self):
        for node in self.graph.nodes():
            self.graph.add_edge(node, GND, weight=self.ground_weight)
            self.nodes = OrderedSet(self.ordered_nodes())
            self.edges = OrderedSet(sorted(self.graph.edges()))

    def update_arrays(self):
        mat = sparse.dok_matrix((len(self.edges), len(self.nodes)))
        vec = np.zeros((len(self.edges),))
        edge_num = 0
        for source, dest in self.graph.edges():
            weight = self.graph.get_edge(source, dest)['weight']
            iSource = self.nodes.index(source)
            iDest = self.nodes.index(dest)
            mat[edge_num][iSource] = -1.0
            mat[edge_num][iDest] = 1.0
            vec[edge_num] = weight
            edge_num += 1
        self._node_matrix = mat
        self._conductance = vec
        return mat, vec

    def get_node_matrix(self):
        if self.nodes is None: self.finalize()
        if self._node_matrix is None:
            self.update_arrays()
        return self._node_matrix

    def get_conductance(self):
        if self.nodes is None: self.finalize()
        if self._conductance is None:
            self.update_arrays()
        return self._conductance

    def get_conductance_multipliers(self, potential):
        assert len(potential) == len(self.nodes)
        multipliers = np.ones((len(self.nodes),))
        for sources, dest, weight in self.conjunctions:
            selected_potentials = {}
            for source in sources:
                selected_potentials[source] = potential[self.nodes.index(source)]
            product = np.product(selected_potentials.values())
            for source in sources:
                multipliers[self.nodes.index(source)] = product/selected_potentials[source]
        return multipliers

    #def get_system_matrix(self, ):
    #    A = self.get_node_matrix()

