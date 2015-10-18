import numpy as np
import random as rnd
import string
import sys

# paths
entpath = '../drugdata/exp2/test_ent.txt'
vecpath = '../drugdata/exp2/vectors.txt.npy'
outpath = '../drugdata/exp2/knn.txt'

# params
k = 10
n = 1000

# load vectors
vec = np.load(open(vecpath,'r'))

# load entities
with open(entpath, 'r') as f:
    xp = f.read().splitlines()

# choose random subset
assert len(xp) == len(vec), "vectors not the same length as entity list"
test_idx = rnd.sample(range(len(xp)), n)
test_vec = [vec[idx] for idx in test_idx]
test_ent = [xp[idx] for idx in test_idx]

# find k-nearest neighbours to test set
f = open(outpath,'w')
for i,e in enumerate(test_ent):
    v = test_vec[i]
    d = np.linalg.norm(vec-v,axis=1)
    min_idx = d.argsort()[:k]
    ke = [xp[ii] for ii in min_idx]
    kd = [d[ii] for ii in min_idx]
    f.write('%s\n' % e)
    for idx, item in enumerate(ke):
	f.write('%s\t%f\n' % (ke[idx],kd[idx]))
    f.write('\n\n')
f.close()
