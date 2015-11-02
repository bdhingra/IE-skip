import tools
import string
import numpy as np
import cPickle as pkl

# paths
data_path = '../drugdata/exp2/processed.txt'
vector_path = '../drugdata/exp2/vectors.txt'
stop_path = '../preprocess/punctuations.txt'
model_save_path = '../drugdata/exp2/extmodel.pkl'
ent_path = '../drugdata/exp2/test_ent.txt'

# params
clen = 6
reload_ = False

# model
if not reload_:
    embed_map = tools.load_googlenews_vectors()
    model = tools.load_model(embed_map)
    with open(model_save_path, 'w') as f:
	pkl.dump(model, f)
else:
    model = pkl.load(open(model_save_path, 'r'))

# load entities
with open(data_path, 'r') as f:
    x = f.read().splitlines()
x = x[1::3]

# process
xp = []
for line in x:
    if line:
	xp.append(filter(lambda x: x in string.printable, line))
xp = list(set(xp))
with open(ent_path,'w') as f:
    for item in xp:
	f.write('%s\n' % item)

# encod new sentences
vectors = tools.encode(model, xp)

# save
np.save(vector_path, vectors)
