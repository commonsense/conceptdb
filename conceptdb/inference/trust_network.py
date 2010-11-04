from scipy import sparse
from csc import divisi2
from csc.divisi2.ordered_set import OrderedSet
import numpy as np
import codecs

EPS = 1e-6

class TrustNetwork(object):
    def __init__(self, output=None):
        self.nodes = OrderedSet()
        self._node_matrix = None
        self._node_conjunctions = None
        self._fast_matrix = None
        self._fast_conjunctions = None

    @staticmethod
    def load(node_file, matrix_file, conjunction_file):
        trust = TrustNetwork()
        nodes = divisi2.load(node_file)
        trust.nodes = OrderedSet(nodes)
        trust._fast_matrix = divisi2.load(matrix_file)
        trust._fast_conjunctions = divisi2.load(conjunction_file)
        return trust
    
    def add_nodes(self, nodes):
        for node in nodes:
            self.nodes.add(node)

    def scan_edge(self, source, dest):
        self.nodes.add(source)
        self.nodes.add(dest)

    def make_matrices(self):
        self._node_matrix = sparse.dok_matrix((len(self.nodes), len(self.nodes)))
        self._node_conjunctions = sparse.dok_matrix((len(self.nodes), len(self.nodes)))

    def add_edge(self, source, dest, weight):
        source_idx = self.nodes.index(source)
        dest_idx = self.nodes.index(dest)
        self._node_matrix[source_idx, dest_idx] = weight
        self._node_matrix[dest_idx, source_idx] = weight

    def add_conjunction(self, sources, dest, weight):
        dest_idx = self.nodes.index(dest)
        for i, source in enumerate(sources):
            self.add_edge(source, dest, weight)
            source_idx = self.nodes.index(source)
            self._node_conjunctions[source_idx, dest_idx] = 1.0

    def add_conjunction_piece(self, source, dest, weight):
        source_idx = self.nodes.index(source)
        dest_idx = self.nodes.index(dest)
        self._node_matrix[source_idx, dest_idx] = weight
        self._node_conjunctions[source_idx, dest_idx] = 1.0

    def make_fast_matrix(self):
        self._fast_matrix = self._node_matrix.tocsr()

    def make_fast_conjunctions(self):
        self._fast_conjunctions = self._node_conjunctions.tocsr()

    def get_matrix(self):
        if self._fast_matrix is None:
            self.make_fast_matrix()
        return self._fast_matrix

    def get_conjunctions(self):
        if self._fast_conjunctions is None:
            self.make_fast_conjunctions()
        return self._fast_conjunctions

    def spreading_activation(self, vec=None, root=None):
        if vec is None:
            vec = np.ones((len(self.nodes),))
        cmat = self.get_conjunctions()
        nmat = self.get_matrix()

        for iter in xrange(100):
            conj_sums = cmat * vec
            conj_par = 1.0/(np.maximum(EPS, cmat * (1.0 / np.maximum(EPS, vec))))
            conj_factor = np.minimum(1.0, conj_par / conj_sums)
            newvec = nmat.dot(vec) * conj_factor + vec
            if root is not None and newvec[self.nodes.index(root)] < 0.0:
                newvec = -newvec
            newvec /= np.max(newvec)
            print newvec
            vec = newvec
        return vec

def graph_from_conceptnet(output=None):
    import conceptdb
    from conceptdb.justify import Reason
    conceptdb.connect('conceptdb')

    bn = TrustNetwork(output=output)
    for reason in Reason.objects:
        reason_name = '/c/%s' % reason.id
        if reason.target == '/sentence/None': continue
        print len(bn.graph), reason_name
        bn.add_conjunction(reason.factors, reason_name, reason.weight)
        bn.add_edge(reason_name, reason.target, 1.0)
    return bn

def graph_from_file(filename):
    bn = TrustNetwork(output=None)
    found_conjunctions = set()
    counter = 0
    with codecs.open(filename, encoding='utf-8') as file:
        for line in file:
            print 'scan:', counter
            counter += 1
            line = line.strip()
            if line:
                source, target, prop_str = line.split('\t')
                bn.scan_edge(source, target)
    bn.make_matrices()
    total = counter
    counter = 0
    with codecs.open(filename, encoding='utf-8') as file:
        for line in file:
            print 'add edge:', counter, '/', total
            counter += 1
            line = line.strip()
            if line:
                source, target, prop_str = line.split('\t')
                props = eval(prop_str)
                weight = props['weight']
                dependencies = None
                if 'dependencies' in props and len(props['dependencies']) > 1:
                    bn.add_conjunction_piece(source, target, weight)
                else:
                    bn.add_edge(source, target, weight)
    file.close()
    return bn

def demo():
    bn = TrustNetwork()
    bn.add_nodes(('root', 'A', 'B', 'C', 'D', 'E', 'F', 'G'))
    bn.make_matrices()
    bn.add_edge('root', 'A', 1.0)
    bn.add_edge('root', 'B', 3.0)
    bn.add_edge('A', 'C', -1.0)
    bn.add_edge('B', 'C', 1.0)
    bn.add_conjunction(('A', 'B'), 'D', 1.0)
    bn.add_edge('A', 'E', 1.0)
    bn.add_edge('B', 'E', 1.0)
    bn.add_conjunction(('C', 'G'), 'F', 1.0)
    bn.add_edge('B', 'G', -1.0)

    results = bn.spreading_activation(np.ones((len(bn.nodes),)), root='root')
    print results
    return bn

def run_conceptnet(filename='conceptdb.graph'):
    out = codecs.open(filename, 'w', encoding='utf-8')
    bn = graph_from_conceptnet(out)
    out.close()
    return bn

if __name__ == '__main__':
    belief_net = demo()

