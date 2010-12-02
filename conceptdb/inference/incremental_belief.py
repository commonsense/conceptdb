from scipy import sparse
from csc import divisi2
from csc.divisi2.ordered_set import OrderedSet
from csc.divisi2.reconstructed import ReconstructedMatrix
import numpy as np
import codecs
import random

EPS = 1e-6

def make_diag(array):
    return sparse.dia_matrix(([array], [0]), shape=(len(array), len(array)))

def nonzero(vec):
    return np.nonzero(vec)[0]

def parallel(x1, x2):
    if x1 <= 0 or x2 <= 0:
        return 0
    return 1./(1./x1 + 1./x2)

class Node(object):
    def __init__(self, node):
        self.node = node
        self.outgoing_edges = []
        self.incoming_edges = []

    def add_outgoing_edge(self, edge, weight):
        self.outgoing_edges.append((edge, weight))

    def add_incoming_edge(self, edge, weight):
        self.incoming_edges.append((edge, weight))

   
class BeliefNetwork(object):
    def __init__(self, output=None):
        self.nodes = OrderedSet()
        self.node_objs = {} #dict mapping node name to Node object
        self._node_conjunctions = None
        self._fast_matrix = None
        self._fast_conjunctions = None

    @staticmethod
    def load(node_file, matrix_file, conjunction_file):
        trust = BeliefNetwork()
        nodes = divisi2.load(node_file)
        for node in nodes:
            trust.nodes.add(node)
            trust.node_objs[node] = Node(node)          
        trust._fast_matrix = divisi2.load(matrix_file)
        trust._fast_conjunctions = divisi2.load(conjunction_file)
        return trust
    
    def add_nodes(self, nodes):
        for node in nodes:
            self.nodes.add(node)
            self.node_objs[node] = Node(node)

    def scan_edge(self, source, dest):
        self.nodes.add(source)
        self.nodes.add(dest)
        self.node_objs[source] = Node(source)
        self.node_objs[dest] = Node(dest)


    def initialize_matrices(self): 
        self.justification = ReconstructedMatrix.make_random(self.nodes, self.nodes, 3)
        self.justification.right = self.justification.left.T

    def add_edge(self, source, dest, weight, conjunction = False):
        
        self.node_objs[source].add_outgoing_edge(dest, weight)
        if conjunction:
            self.node_objs[dest].add_incoming_edge(source, weight) #weight here?

    def add_conjunction(self, sources, dest, weight):
        for i, source in enumerate(sources):
            self.add_edge(source, dest, weight, conjunction = True)

    def add_conjunction_piece(self, source, dest, weight):
        self.add_edge(source, dest, weight, conjunction = True)

    def iterate(self, n=1000):
        for iter in xrange(n):
            for node in self.nodes:
                print node, '=>',
                self.activate_node(node)
                print self.justification.row_named(node).top_items()
        return self.justification

    def activate_node(self, node):
        index = self.nodes.index(node)
        activation = 1.0
        self.learn_justification(index, index, activation)
        curr = index
        for iter in xrange(20):
            #get the nodes that this node has outgoing edges to
            nz = self.node_objs[node].outgoing_edges
            if len(nz) == 0:
                break
            choice = random.choice(xrange(len(nz)))
            next = nz[choice][0]
            conj = self.node_objs[next].incoming_edges
            for con in conj:
                conj_index = self.nodes.index(con[0])
                if conj_index != curr:
                    #FIXME: unsure of how to calculate this value
                    factor =  self.justification[index, conj_index] #* conj[0, conj_index]
                    activation = parallel(activation, factor)
            print self.nodes[self.nodes.index(next)], ('(%4.4f) =>' % activation),
            self.learn_justification(index, self.nodes.index(next), activation)
            if activation == 0:
                break
            curr = next
    
    def learn_justification(self, source, target, activation=1.0):
        self.justification.hebbian_step(source, target, activation)

def graph_from_conceptnet(output='conceptnet'):
    import conceptdb
    from conceptdb.justify import Reason
    conceptdb.connect('conceptdb')

    bn = BeliefNetwork(output=output)
    for reason in Reason.objects:
        reason_name = '/c/%s' % reason.id
        if reason.target == '/sentence/None': continue
        print len(bn.nodes), reason_name
        bn.add_conjunction(reason.factors, reason_name, reason.weight)
        bn.add_edge(reason_name, reason.target, 1.0)
    return bn

def graph_from_file(filename):
    bn = BeliefNetwork(output=None)
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
    bn.initialize_matrices()
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
                if 'dependencies' in props and len(props['dependencies']) > 1:
                    bn.add_conjunction_piece(source, target, weight)
                else:
                    bn.add_edge(source, target, weight)
    file.close()
    
    bn.make_fast_matrix()
    bn.make_fast_conjunctions()
    divisi2.save(list(bn.nodes), filename+'.nodelist.pickle')
    divisi2.save(bn._fast_matrix, filename+'.matrix.pickle')
    divisi2.save(bn._conjunction_matrix, filename+'.conjunctions.pickle')
    
    return bn

def demo():
    bn = BeliefNetwork()
    bn.add_nodes(('root', 'A', 'B', 'C', 'D', 'E', 'F', 'G'))
    bn.initialize_matrices()
    bn.add_edge('root', 'A', 0.25)
    bn.add_edge('root', 'B', 0.75)
    bn.add_edge('A', 'C', -1.0)
    bn.add_edge('B', 'C', 1.0)
    bn.add_conjunction(('A', 'B'), 'D', 1.0)
    bn.add_edge('A', 'E', 1.0)
    bn.add_edge('B', 'E', 1.0)
    bn.add_conjunction(('C', 'G'), 'F', 1.0)
    bn.add_edge('B', 'G', -1.0)
    bn.iterate(10000)
    return bn

def run_conceptnet(filename='conceptdb.graph'):
    bn = graph_from_file(filename)
    return bn

