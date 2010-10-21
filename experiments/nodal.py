from scipy import sparse
from scipy.sparse.linalg.dsolve import linsolve
import numpy as np

def make_diag(d):
    return sparse.dia_matrix(([d], [0]), shape=(len(d), len(d)))

A = sparse.dok_matrix((10, 4))
b = np.zeros((4,))

# initial conductances
Yp = 0.0
Yg = 1
Y01 = 1
Y02 = 1
Y13 = 1
Y23 = 3

# Assign an index to every edge. 0 = power, 4 = ground
e01 = 0
e02 = 1
e03 = 2
e04 = 3
e12 = 4
e13 = 5
e14 = 6
e23 = 7
e24 = 8
e34 = 9

# A, the potential difference matrix
A[[e01, e02, e03, e04], 0] = -1
A[[e12, e13, e14], 1] = -1
A[[e23, e24], 2] = -1
A[e34, 3] = -1
A[[e03, e13, e23], 3] = 1
A[[e02, e12], 2] = 1
A[e01, 1] = 1

x = np.array([1.0, 1.0, 1.0, 1.0])
for i in xrange(100):
    #Y = [Y01, Y02, 0, 0, 0, Y13, Yg, Y23, Yg, Yg]
    Y = [Y01, Y02, 0, 0, 0, Y13*x[2], Yg, Y23*x[1], Yg, Yg]
    G = make_diag(Y)
    f = np.array(([1,0,0,0]))

    S = A.T * G * A
    x = linsolve.spsolve(S, f)
    #x = (x + newx) / 2
    x /= x[0]
    print x
