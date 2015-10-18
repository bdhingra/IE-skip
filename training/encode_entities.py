import tools
import string
import numpy as np
import cPickle as pkl

# paths
data_path = '../drugdata/exp2/processed.txt'
vector_path = '../drugdata/exp2/vectors.txt'
stop_path = '../preprocess/punctuations.txt'
model_save_path = '../drugdata/exp2/extmodel.pkl'

# params
clen = 6

# model
embed_map = tools.load_googlenews_vectors()
model = tools.load_model(embed_map)
with open(model_save_path, 'w') as f:
    pkl.dump(model, f)

# load entities
with open(data_path, 'r') as f:
    x = f.read().splitlines()
x = x[1:3000:3]

# process
xp = []
for line in x:
    if line:
	xp.append(filter(lambda x: x in string.printable, line))

# encod new sentences
vectors = tools.encode(model, xp)

# save
np.save(vector_path, vectors)
