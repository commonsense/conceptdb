from scipy import sparse
from scipy.sparse.linalg.dsolve import linsolve
from csc.divisi2.ordered_set import OrderedSet
import numpy as np
import networkx as nx

def make_diag(d):
    return sparse.dia_matrix(([d], [0]), shape=(len(d), len(d)))

GND = '~ground~'

class BeliefNetwork(object):
    def __init__(self, groundG=1.0):
        self.graph = nx.Graph()
        self.conjunctions = set()
        self.groundG = groundG

        self.nodes = None
        self.edges = None
        self.voltage = None

    def add_edge(self, source, dest, G):
        self.graph.add_edge(source, dest, weight=G)

    def add_conjunction(self, sources, dest, G):
        self.conjunctions.add((sources, dest, G))
        for source in sources:
            self.add_edge(self, source, dest, G)

    def ordered_nodes():
        nodes = self.graph.nodes()
        nodes.remove(GND)
        nodes.sort()
        return nodes

    def finalize(self):
        for node in self.graph.nodes():
            self.graph.add_edge(node, GND, weight=self.groundG)
            self.nodes = OrderedSet(self.ordered_nodes())
            self.edges = OrderedSet(sorted(self.graph.edges()))
            self.voltage = np.ones(len(G))
