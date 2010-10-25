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
        self._edge_matrix = None
        self._conductance = None

    def add_edge(self, source, dest, weight):
        self.graph.add_edge(source, dest, weight=weight)

    def add_conjunction(self, sources, dest, weight):
        self.conjunctions.add((sources, dest, weight))
        for source in sources:
            self.add_edge(source, dest, weight)

    def ordered_nodes(self):
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
        for source, dest in self.graph.edges():
            edge_num = self.edges.index((source, dest))
            if source == GND:
                source, dest = dest, source
            weight = self.graph.get_edge_data(source, dest)['weight']
            source_idx = self.nodes.index(source)
            mat[edge_num, source_idx] = -1.0
            if dest != GND:
                dest_idx = self.nodes.index(dest)
                mat[edge_num, dest_idx] = 1.0
            vec[edge_num] = weight
        self._edge_matrix = mat
        self._conductance = vec
        return mat, vec

    def get_edge_matrix(self):
        if self.nodes is None: self.finalize()
        if self._edge_matrix is None:
            self.update_arrays()
        return self._edge_matrix

    def get_conductance(self):
        if self.nodes is None: self.finalize()
        if self._conductance is None:
            self.update_arrays()
        return self._conductance

    def get_conductance_multipliers(self, potentials):
        assert len(potentials) == len(self.nodes)
        multipliers = np.ones((len(self.edges),))
        for sources, dest, weight in self.conjunctions:
            selected_potentials = {}
            for source in sources:
                selected_potentials[source] = potentials[self.nodes.index(source)]
            product = np.product(selected_potentials.values())
            for source in sources:
                multipliers[self.edges.index((source, dest))] = product/selected_potentials[source]
        return multipliers

    def get_system_matrix(self, potentials):
        A = self.get_edge_matrix()
        G = self.get_conductance_multipliers(potentials) * self.get_conductance()
        return A.T * make_diag(G) * A

    def solve_system(self, potentials, current):
        system = self.get_system_matrix(potentials)
        new_potentials = linsolve.spsolve(system, current)
        return new_potentials

    def run(self, root, epsilon=1e-6):
        potentials = np.ones((len(self.nodes),))
        converged = False
        root_index = self.nodes.index(root)
        current = np.zeros((len(self.nodes),))
        current[root_index] = 1.0

        for i in xrange(100):
            new_potentials = self.solve_system(potentials, current)
            new_potentials /= new_potentials[root_index]
            diff = (potentials - new_potentials)
            potentials = new_potentials
            print potentials
            if np.linalg.norm(diff) < epsilon:
                converged = True
                break
        if not converged: print "Warning: failed to converge"
        return zip(self.nodes, potentials)

if __name__ == '__main__':
    bn = BeliefNetwork()
    bn.add_edge('root', 'A', 1.0)
    bn.add_edge('root', 'B', 3.0)
    bn.add_edge('A', 'C', -1.0)
    bn.add_edge('B', 'C', 1.0)
    bn.add_conjunction(('A', 'B'), 'D', 1.0)
    bn.add_edge('A', 'E', 1.0)
    bn.add_edge('B', 'E', 1.0)
    bn.finalize()

    results = bn.run('root')
    print list(bn.nodes)

