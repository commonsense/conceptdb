# CORONA algorithm: Computation of Reliability of Networked Agents
# 
# This is meant to be an extension of SALSA that allows conjunctions, and
# that doesn't get stuck in local ruts.

# Steps to implement:
#   - Read in the graph using networkx.
#   - Iterate over the graph doing the random walk.
#   - Accumulate results.
#   - ???

import networkx as nx
import numpy as np
import random
import codecs
from csc import divisi2

# Constants
DOWN, UP = 1, -1

def load_graph(filename, encoding='utf-8'):
    return nx.read_edgelist(codecs.open(filename, encoding=encoding),
                            data=True, delimiter='\t',
                            create_using=nx.DiGraph())

def run_corona(graph, iterations=100):
    graph.graph['steps_up'] = 0
    graph.graph['steps_down'] = 0
    for node in graph.nodes_iter():
        graph.node[node]['steps_up'] = 0
        graph.node[node]['steps_down'] = 0
        graph.node[node]['hub'] = 1.0 / len(graph)
        graph.node[node]['authority'] = 0
    for iter in xrange(iterations):
        corona_step(graph)

def corona_step(graph):
    """
    Do a random walk for every node in the graph, and accumulate hub and
    authority scores for each node.
    """
    
    for node in graph.nodes_iter():
        corona_random_walk(graph, node, direction=UP)
        corona_random_walk(graph, node, direction=DOWN)

    total_up = graph.graph['steps_up']
    total_down = graph.graph['steps_down']
    for node in graph.nodes_iter():
        graph.node[node]['hub'] = graph.node[node]['steps_up'] / float(total_up)
        graph.node[node]['authority'] = graph.node[node]['steps_down'] / float(total_down)

def corona_random_walk(graph, node, direction=None):
    """
    Do a random walk from a given node. The direction of the initial step
    may be specified or chosen randomly.

    If it is not possible to walk in the given direction, the walk will
    terminate.
    """
    if direction is None:
        direction = random.choice([UP, DOWN])
    
    if direction == UP:
        choices = graph.predecessors(node)
        accumulator = 'steps_up'
    elif direction == DOWN:
        choices = graph.successors(node)
        accumulator = 'steps_down'
    else:
        raise ValueError("Invalid direction")
    
    probability_target = random.random()
    total_weight = 0.0

    for next_node in choices:
        total_weight += edge_weight(graph, node, next_node, direction)
    if total_weight == 0:
        # Terminate the walk here.
        return

    probability_used = 0.0
    for next_node in choices:
        probability_used += edge_weight(graph, node, next_node, direction) / total_weight
        if probability_target < probability_used:
            graph.node[next_node][accumulator] += 1
            graph.graph[accumulator] += 1
            return corona_random_walk(graph, next_node)
    assert False, "Ran out of probability"

def node_weight(graph, node):
    """
    What is the total weight on this node, both from its hub score and its
    authority score?
    """
    return graph.node[node]['hub'] + graph.node[node]['authority']

def edge_weight(graph, n1, n2, direction=DOWN):
    """
    Get the weight of the edge from `n1` to `n2`, taking conjunctions
    into account.
    """
    if direction == UP:
        n1, n2 = n2, n1
    edge_data = graph[n1][n2]
    multiplier = 1.0
    if 'dependencies' in edge_data:
        baseline = node_weight(graph, n1)
        inv_parallel = 0.0
        for n3 in edge_data['dependencies']:
            weight = node_weight(graph, n3)
            if weight <= 0:
                # This depends on a conjunction that cannot be satisfied.
                return 0.0
            inv_parallel += 1.0/weight
        multiplier = 1.0/inv_parallel/baseline
    return edge_data['weight'] * multiplier

def edge_matrix(graph, nodes, direction=DOWN, final=False):
    """
    This is a *terribly slow* way of getting the adjacency matrix for corona.
    Fix it.
    """
    n = len(graph)
    mat = np.zeros((n,n))
    for row in xrange(n):
        for col in xrange(n):
            if nodes[col] in graph[nodes[row]]:
                mat[row,col] += edge_weight(graph, nodes[row], nodes[col])
    if direction == UP:
        #mat = np.maximum(0, mat.T)
        mat = mat.T
    sums = np.abs(mat).sum(axis=1)
    for row in xrange(n):
        if sums[row] == 0:
            if not final:
                mat[row,0] = 1.0
        else:
            mat[row,:] /= sums[row]
    return mat

def run_eigen(graph, tol=1e-6):
    n = len(graph)
    nodes = graph.nodes()
    for node in nodes:
        graph.node[node]['hub'] = 1.0/n
        graph.node[node]['authority'] = 0.0
    vec = np.ones((n,), 'f') / n
    for iter in xrange(1000):
        print iter
        matrix_down = edge_matrix(graph, nodes, DOWN)
        matrix_up = edge_matrix(graph, nodes, UP)
        matrix = (matrix_down + matrix_up) / 2.0
        #matrix = matrix_down

        vlast = vec
        w, v = np.linalg.eig(matrix.T)
        vec = v[:, 0]

        # fix a root node if necessary
        vec = (vec / vec[0]).real
        hub = np.dot(vec, edge_matrix(graph, nodes, UP, True))
        authority = np.dot(vec, edge_matrix(graph, nodes, DOWN, True))

        for i, node in enumerate(nodes):
            graph.node[node]['hub'] = hub[i]
            graph.node[node]['authority'] = authority[i]
            graph.node[node]['activation'] = vec[i]
            graph.node[node]['vec'] = list(v[i])

        err = np.absolute(vec - vlast).sum()
        if err < n*tol:
            break

    return graph

def demo():
    graph = load_graph('test.graph')
    run_eigen(graph)
    return graph

if __name__ == '__main__':
    result = demo()
