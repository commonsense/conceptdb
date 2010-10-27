from scipy import sparse
from scipy.sparse import linalg as sparse_linalg
from csc import divisi2
from csc.divisi2.ordered_set import OrderedSet
import numpy as np
import networkx as nx
import codecs

def make_diag(array):
    return sparse.dia_matrix(([array], [0]), shape=(len(array), len(array)))

def make_product_operator(*matrices):
    shape = (matrices[0].shape[0], matrices[-1].shape[-1])

    def matvec(vec):
        for mat in matrices[::-1]:
            vec = mat * vec
        return vec
    return sparse_linalg.LinearOperator(shape, matvec, dtype=matrices[0].dtype)

class BeliefNetwork(object):
    def __init__(self, ground_weight=1.0, output=None):
        self.graph = nx.Graph()
        self.conjunctions = set()
        self.ground_weight = ground_weight

        self.nodes = None
        self.edges = None
        self._edge_matrix = None
        self._conductance = None

        self.output = output

    def add_edge(self, source, dest, weight, dependencies=None):
        props = {'weight': weight}
        if dependencies is not None:
            props['dependencies'] = dependencies
        self.graph.add_edge(source, dest, **props)
        if self.output:
            self.output.write("%s\t%s\t%r\n" % (source, dest, props))

    def add_conjunction(self, sources, dest, weight):
        sources = tuple(sources)
        self.conjunctions.add((sources, dest, weight))
        for i, source in enumerate(sources):
            self.add_edge(source, dest, weight,
                          dependencies=sources)

    def ordered_nodes(self):
        return sorted(self.graph.nodes())

    def finalize(self):
        self.nodes = OrderedSet(self.ordered_nodes())
        self.edges = OrderedSet(sorted(self.graph.edges()))

    def update_arrays(self):
        n_edges = len(self.edges) + len(self.nodes)
        offset = len(self.edges)
        mat = sparse.dok_matrix((n_edges, len(self.nodes)))
        vec = np.zeros((n_edges,))
        for source, dest in self.graph.edges():
            edge_num = self.edges.index((source, dest))
            weight = self.graph.get_edge_data(source, dest)['weight']
            source_idx = self.nodes.index(source)
            mat[edge_num, source_idx] = -1.0
            dest_idx = self.nodes.index(dest)
            mat[edge_num, dest_idx] = 1.0
            vec[edge_num] = weight

        # Add edges to ground
        for node in self.graph.nodes():
            node_num = self.nodes.index(node)
            adjusted_node_num = node_num + offset
            mat[adjusted_node_num, node_num] = -1.0
            vec[adjusted_node_num] = self.ground_weight
        self._edge_matrix = mat.tocsr()
        self._edge_matrix_transpose = mat.T.tocsr()
        self._conductance = vec
        return mat, vec

    def get_edge_matrix(self):
        if self.nodes is None: self.finalize()
        if self._edge_matrix is None:
            self.update_arrays()
        return self._edge_matrix

    def get_edge_matrix_transpose(self):
        if self.nodes is None: self.finalize()
        if self._edge_matrix is None:
            self.update_arrays()
        return self._edge_matrix_transpose
    
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
                selected_potentials[source] = \
                    potentials[self.nodes.index(source)]
            product = np.product(np.maximum(0, selected_potentials.values()))
            for source in sources:
                multipliers[self.edges.index((source, dest))] = \
                    product/selected_potentials[source]
        return np.concatenate([multipliers, np.ones((len(potentials),))])

    def get_system_matrix(self, potentials):
        A_T = self.get_edge_matrix_transpose()
        A = self.get_edge_matrix()
        G = self.get_conductance_multipliers(potentials)\
          * self.get_conductance()
        return make_product_operator(A_T, make_diag(G), A)

    def solve_system(self, potentials, current):
        system = self.get_system_matrix(potentials)
        new_potentials = sparse_linalg.cg(system, current)[0]
        return new_potentials

    def run_analog(self, root, epsilon=1e-6):
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

def graph_from_conceptnet(output=None):
    import conceptdb
    from conceptdb.justify import Reason
    conceptdb.connect('conceptdb')

    bn = BeliefNetwork(output=output)
    for reason in Reason.objects:
        reason_name = '/c/%s' % reason.id
        if reason.target == '/sentence/None': continue
        print len(bn.graph), reason_name
        bn.add_conjunction(reason.factors, reason_name, reason.weight)
        bn.add_edge(reason_name, reason.target, 1.0)
    return bn

def graph_from_file(filename):
    bn = BeliefNetwork(output=None)
    found_conjunctions = set()
    with open(filename) as file:
        for line in file:
            line = line.strip()
            if line:
                source, target, prop_str = line.split('\t')
                props = eval(prop_str)
                weight = props['weight']
                dependencies = None
                if 'dependencies' in props:
                    dependencies = props['dependencies']
                    if target not in found_conjunctions:
                        found_conjunctions.add(target)
                        bn.conjunctions.add((dependencies, target, weight))
                bn.add_edge(source, target, weight, dependencies)
    return bn


def demo():
    bn = BeliefNetwork()
    bn.add_edge('root', 'A', 1.0)
    bn.add_edge('root', 'B', 3.0)
    bn.add_edge('A', 'C', -1.0)
    bn.add_edge('B', 'C', 1.0)
    bn.add_conjunction(('A', 'B'), 'D', 1.0)
    bn.add_edge('A', 'E', 1.0)
    bn.add_edge('B', 'E', 1.0)
    bn.add_conjunction(('C', 'D'), 'F', 1.0)
    bn.finalize()

    results = bn.run_analog('root')
    print results

def run_conceptnet(filename='conceptdb.graph'):
    out = codecs.open(filename, 'w', encoding='utf-8')
    bn = graph_from_conceptnet(out)
    out.close()
    return bn

if __name__ == '__main__':
    belief_net = demo()

