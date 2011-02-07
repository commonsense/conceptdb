from scipy import sparse
from scipy.sparse.linalg.dsolve import linsolve
import numpy as np

A = sparse.lil_matrix((20, 20))
b = np.zeros((20,))

# initial conductances
Z0 = 0.1
Z1 = 0.1
Z24 = 1
Z34 = 3

# indices (not actual voltages or currents!)
V01 = 0
V02 = 1
V03 = 2
V04 = 3
V12 = 4
V13 = 5
V14 = 6
V23 = 7
V24 = 8
V34 = 9

I01 = 10
I02 = 11
I03 = 12
I04 = 13
I12 = 14
I13 = 15
I14 = 16
I23 = 17
I24 = 18
I34 = 19

# voltage/current source
A[0, V01] = 1; b[0] = -10 # volts

# Conservation of current
A[2, I01] = -1; A[2, I12] = 1;  A[2, I13] = 1;  A[2, I14] = 1
A[3, I02] = -1; A[3, I12] = -1; A[3, I23] = 1;  A[3, I24] = 1
A[4, I03] = -1; A[4, I13] = -1; A[4, I23] = -1; A[4, I34] = 1
A[5, I04] = -1; A[5, I14] = -1; A[5, I24] = -1; A[5, I34] = -1

# Voltage sums
A[6, V02] = -1; A[6, V01] = 1; A[6, V12] = 1
A[7, V14] = -1; A[7, V12] = 1; A[7, V24] = 1
A[8, V24] = -1; A[8, V23] = 1; A[8, V34] = 1
A[9, V03] = 1;  A[9, V34] = 1; A[9, V04] = -1
A[1, V14] = 1;  A[1, V04] = -1; A[1, V01] = 1
#A[10,V04] = -1; A[10,V03] = 1; A[10,V34] = 1
#A[11,V14] = -1; A[11,V12] = 1; A[11,V24] = 1
#A[12,V14] = -1; A[12,V13] = 1; A[12,V34] = 1

# Potential difference = current * conductance
A[10,I01] = -1; A[10,V01] = Z0
A[11,I02] = -1; A[11,V02] = Z0
A[12,I03] = -1; A[12,V03] = Z0
A[13,I04] = -1; A[13,V04] = Z0

A[14,I12] = -1; A[14,V12] = Z1
A[15,I13] = -1; A[15,V13] = Z1
A[16,I14] = -1; A[16,V14] = Z1

A[19,I23] = -1
A[17,I24] = -1; A[17,V24] = Z24
A[18,I34] = -1; A[18,V34] = Z34

dense = A.toarray()

