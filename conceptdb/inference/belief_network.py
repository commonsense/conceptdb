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
            vec = mat.dot(vec)
        return vec
    return sparse_linalg.LinearOperator(shape, matvec, dtype=matrices[0].dtype)

class BeliefNetwork(object):
    def __init__(self, ground_weight=1.0, output=None):
        self.graph = nx.Graph()
        self.conjunctions = set()
        self.ground_weight = ground_weight

        self.nodes = OrderedSet()
        self.edges = OrderedSet()
        self._edge_matrix = None
        self._conjunction_matrix = None
        self._edge_conductance = None

        self.output = output

    def add_edge(self, source, dest, weight, dependencies=None):
        self.nodes.add(source)
        self.nodes.add(dest)
        self.edges.add((source, dest))

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

    def update_arrays(self):
        n_edges = len(self.edges) + len(self.nodes)
        n_nodes = len(self.nodes)
        offset = len(self.edges)
        mat = sparse.dok_matrix((n_edges, n_nodes))
        conjunction_mat = sparse.dok_matrix((n_edges, n_nodes))
        vec = np.zeros((n_edges,))
        for source, dest in self.graph.edges():
            if (source, dest) not in self.edges:
                (source, dest) = (dest, source)
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
        
        # Make matrix of conjunctions, edges -> input nodes
        for sources, dest, weight in self.conjunctions:
            edge_indices = []
            node_indices = []
            for source in sources:
                if (source, dest) in self.edges:
                    edge_num = self.edges.index((source, dest))
                else:
                    edge_num = self.edges.index((dest, source))
                edge_indices.append(edge_num)
                node_indices.append(self.nodes.index(source))
            conjunction_mat[edge_indices, node_indices] = 1
            #for node_index in node_indices:
            #    unconnected_edges = [e for e in edge_indices if mat[e, node_index] == 0.0]

        self._edge_matrix = mat.tocsr()
        self._edge_matrix_transpose = mat.T.tocsr()
        self._edge_conductance = vec
        self._conjunction_matrix = conjunction_mat.tocsr()
        return mat, vec

    def make_node_matrix(self):
        self._node_matrix = nx.to_scipy_sparse_matrix(self.graph, self.nodes)

    def get_node_matrix(self):
        if self._node_matrix is None:
            self.make_node_matrix()
        return self._node_matrix

    def get_edge_matrix(self):
        if self._edge_matrix is None:
            self.update_arrays()
        return self._edge_matrix

    def get_edge_matrix_transpose(self):
        if self._edge_matrix is None:
            self.update_arrays()
        return self._edge_matrix_transpose
    
    def get_conductance(self):
        if self._edge_conductance is None:
            self.update_arrays()
        return self._edge_conductance

    def adjusted_conductances(self, equiv_conductances):
        assert len(equiv_conductances) == len(self.nodes)
        
        equiv_resistances = 1.0/np.maximum(0, equiv_conductances)
        edge_resistances = 1.0/self._edge_conductance
        combined_resistances = self._conjunction_matrix.dot(equiv_resistances)
        new_resistances = (edge_resistances + combined_resistances)
        adjusted_conductances = 1.0/new_resistances
        print adjusted_conductances
        return adjusted_conductances

    def get_system_matrix(self, conductances):
        A_T = self.get_edge_matrix_transpose()
        A = self.get_edge_matrix()
        G = self.adjusted_conductances(conductances)
        return make_product_operator(A_T, make_diag(G), A)

    def solve_system(self, known_conductances, current_source):
        """
        Get the conductance from root to each node by solving the electrical
        system.
        """
        current = np.zeros((len(self.nodes),))
        current[current_source] = 1.0
        
        system = self.get_system_matrix(known_conductances)
        A = self.get_edge_matrix()
        
        # Solve the sparse system of linear equations using cg
        new_potentials = sparse_linalg.cg(system, current)[0]
        
        # A = edges by nodes
        currents = -A.dot(new_potentials)

        potential_differences = new_potentials[current_source] - new_potentials
        current_magnitude = np.abs(self.get_edge_matrix_transpose()).dot(currents)
        conductance = 1.0/potential_differences
        return conductance

    def run_analog(self, root, epsilon=1e-6):
        conductance = np.ones((len(self.nodes),))
        converged = False
        root_index = self.nodes.index(root)

        for i in xrange(100):
            new_conductance = self.solve_system(conductance, root_index)
            diff = (np.minimum(conductance, 1000000.0)
                    - np.minimum(new_conductance, 1000000.0))
            conductance = new_conductance
            print conductance
            if np.linalg.norm(diff) < epsilon:
                converged = True
                break

        if not converged: print "Warning: failed to converge"
        return zip(self.nodes, conductance)

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
    bn = BeliefNetwork(ground_weight=10.0)
    bn.add_edge('root', 'A', 1.0)
    bn.add_edge('root', 'B', 3.0)
    bn.add_edge('A', 'C', -1.0)
    bn.add_edge('B', 'C', 1.0)
    bn.add_conjunction(('A', 'B'), 'D', 1.0)
    bn.add_edge('A', 'E', 1.0)
    bn.add_edge('B', 'E', 1.0)
    bn.add_conjunction(('C', 'G'), 'F', 1.0)
    bn.add_edge('B', 'G', -1.0)

    results = bn.run_analog('root')
    print results
    return bn

def run_conceptnet(filename='conceptdb.graph'):
    out = codecs.open(filename, 'w', encoding='utf-8')
    bn = graph_from_conceptnet(out)
    out.close()
    return bn

if __name__ == '__main__':
    belief_net = demo()

