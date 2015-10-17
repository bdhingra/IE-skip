import tools
import string
import preprocess

# paths
data_path = '../drugdata/exp2/processed.txt'
vector_path = '../drugdata/exp2/vectors.txt'
stop_path = '../preprocess/punctuations.txt'

# params
clen = 6

# model
embed_map = tools.load_googlenews_vectors()
model = tools.load_model(embed_map)

# load entities
f = open(data_path, 'r')
x = f.read().splitlines()
x = x[:3000]

# process
#xp = []
#for line in x:
#    if line:
#	xp.append(filter(lambda x:x in string.printable, line))
x = preprocess.prepareentitylist(x, stop_path, clen)

# encod new sentences
vectors = tools.encode(model, x[1::3])

# save
f = open(vector_path, 'w')
for line in vectors:
    f.write('%s\n' % line)
