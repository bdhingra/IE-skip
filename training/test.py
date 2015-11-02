#import matplotlib
#matplotlib.use('Agg')

#import matplotlib.pyplot as plt
import tools
import string
import numpy as np
import cPickle as pkl
import re
import math

from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn import cross_validation
from sklearn.feature_extraction import DictVectorizer

# paths
stop_path = '../preprocess/punctuations.txt'
model_save_path = '../drugdata/exp2/extmodel.pkl'
vec_save_path = '../drugdata/exp2/test_vec.npy'
fig_save_path = '../drugdata/exp2/test_fig.png'
outFile = '../drugdata/exp2/out_emb.txt'
bowFeatFile = '../../data/cleantest.txt'

# params
reload_model = True
reload_vectors = True
ndims = 1200
Ce = 1e4
Cb = 1e8
K = 10

with open(stop_path,'r') as f:
    stops = f.read().splitlines()

# bow feats
ent = []
labels = []
bowfeats = []
with open(bowFeatFile,'r') as f:
    for line in f:
	parse = line.split('\t')
	ent.append(parse[0])
	labels.append(parse[1])
	d = {}
	for item in parse[2].split():
	    f = item.split(':')
	    d[int(f[0])] = float(f[1])
	bowfeats.append(d)

# model
# load entities
#labels = []
#ent = []
#with open(data_path, 'r') as f:
#    for line in f:
#	labels.append(line.split('\t')[1][:-1])
#	ent.append(line.split('\t')[0])
if not reload_vectors:
    if not reload_model:
	embed_map = tools.load_googlenews_vectors()
	model = tools.load_model(embed_map)
	with open(model_save_path, 'w') as f:
	    pkl.dump(model, f)
    else:
	model = pkl.load(open(model_save_path, 'r'))

    # process
    xp = []
    for entity in ent:
	#line = re.sub(r'[0-9]+','#'," ".join([word for word in entity.split('_') if word not in stops])).lower()
	line = " ".join([word for word in entity.split('_') if word not in stops]).lower()
	xp.append(filter(lambda x: x in string.printable, line))

    # encode new sentences
    vectors = tools.encode(model, xp)
    with open(vec_save_path, 'w') as f:
	np.save(f, vectors)
else:
    vectors = np.load(open(vec_save_path,'r'))

print len(vectors)
print len(labels)
print ent[0]
print labels[0]
print set(labels)

# labels -> int
le = LabelEncoder()
lab = le.fit_transform(labels)

v = DictVectorizer()
xb = v.fit_transform(bowfeats)
y = lab

# retain 1200 dims
pca = PCA()
vec_dr = pca.fit_transform(vectors)
xe = vec_dr[:,:ndims]

# cross val
skf = cross_validation.StratifiedKFold(y, n_folds=K)

# svm
out = []
p = np.zeros(K)
pb = np.zeros(K)
pe = np.zeros(K)
i = 0
for train_index, test_index in skf:
    e_tr = [ent[ii] for ii in train_index]
    e_te = [ent[ii] for ii in test_index]
    xb_tr = xb[train_index]
    xb_te = xb[test_index]
    xe_tr = xe[train_index]
    xe_te = xe[test_index]
    y_tr = y[train_index]
    y_te = y[test_index]

    clfb = SVC(C=Cb)
    clfe = SVC(C=Ce)

    clfb.fit(xb_tr, y_tr)
    clfe.fit(xe_tr, y_tr)
    pb[i] = 1-clfb.score(xb_te, y_te)
    pe[i] = 1-clfe.score(xe_te, y_te)

    for idx,item in enumerate(e_te):
	bp = le.inverse_transform(clfb.predict(xb_te[idx]))
	ep = le.inverse_transform(clfe.predict(xe_te[idx]))
	out.append([item, np.array_str(le.inverse_transform(y_te[idx])), np.array_str(bp), np.array_str(ep)])

    p[i] = pb[i] - pe[i]
    i = i+1

# t statistic
print pb
print pe
print pb.mean()
print pe.mean()
print p.mean()*math.sqrt(K)/np.std(p,ddof=1)

with open(outFile,'w') as f:
    for item in out:
	f.write(' '.join(item) + '\n')

#for idc,c in enumerate(C):
#    clf = SVC(C=c)
#    #clf.fit(trainx,trainy)
#    #sc[idn,idc] = clf.score(testx,testy)
#    #print sc[idn,idc]
#    sc = cross_validation.cross_val_score(clf, x, y, cv=5)
#    print "n = %d, C = %f, avg score = %f, std = %f" % (n,c,sc.mean(), sc.std())
#    print sc

#with open(outFile,'w') as f:
    #f.write("n = %d, C = %f, avg score = %f, std = %f" % (n,c,sc.mean(), sc.std()))
    #for (e,t,p) in zip(ent[401:],testy,clf.predict(testx)):
	#if not t==p:
	    #f.write('%s\t%s\t%s\n' % (e,t,p))
