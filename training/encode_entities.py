import tools
import string

# paths
data_path = '../drugdata/exp2/processed.txt'
vector_path = '../drugdata/exp2/vectors.txt'

# model
embed_map = tools.load_googlenews_vectors()
model = tools.load_model(embed_map)

# load entities
f = open(data_path, 'r')
x = f.read().splitlines()
x = x[1:1000:3]

# process
xp = []
for line in x:
    if line:
	xp.append(filter(lambda x:x in string.printable, line))

# encod new sentences
vectors = tools.encode(model, xp)

# save
f = open(vector_path, 'w')
for line in vectors:
    f.write('%s\n' % line)
