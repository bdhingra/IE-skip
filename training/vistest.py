import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import LabelEncoder

# paths
vec_path = '../drugdata/exp2/test_vec.npy'
data_path = '../../data/test_data_labeled_new_21_files_latest1.txt'
fig_path = '../drugdata/exp2/test_fig.png'

# load
x = np.load(open(vec_path,'r'))
with open(data_path,'r') as f:
    d = f.read().splitlines()
ents = [l.split('\t')[0] for l in d]
labels = [l.split('\t')[2] for l in d]

# pca
pca = PCA(n_components=2)
xp = pca.fit_transform(x)

# plot
le = LabelEncoder()
ll = le.fit_transform(labels)
plt.figure()
for c,i,n in zip("rgby",[0,1,2,3],le.classes_):
    plt.scatter(xp[ll==i,0],xp[ll==i,1],c=c,label=n)
plt.legend()
plt.savefig(fig_path)
