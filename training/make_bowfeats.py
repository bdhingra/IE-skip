import numpy as np
import scipy as sp
from sklearn.feature_extraction import DictVectorizer
from sklearn.svm import SVC
from sklearn import cross_validation
from sklearn.preprocessing import LabelEncoder

featFile = '../preprocess/gpig_views/entvec.gp'
saveFile = '../../data/test_with.txt'
outFile = '../../data/out_bow.txt'

ent = []
lab = []
feats = []
with open(featFile,'r') as f:
    for line in f:
	parse = line.split('\t')
	ent.append(parse[0])
	lab.append(parse[1])
	d = {}
	for item in parse[2].split():
	    f = item.split(':')
	    d[int(f[0])] = float(f[1])
	feats.append(d)

with open(saveFile,'w') as f:
    for idx,item in enumerate(ent):
	f.write('%s\t%s\n' % (item, lab[idx]))
# labels -> int
le = LabelEncoder()
lab = le.fit_transform(lab)

v = DictVectorizer()

# train and test
#trx = feats[:400]
#trainx = v.fit_transform(trx)
#trainy = lab[:400]
#tex = feats[401:]
#testx = v.transform(tex)
#testy = lab[401:]
x = v.fit_transform(feats)
y = lab

C = [1e8]
#sc = np.zeros(len(C))
# svm
for idc,c in enumerate(C):
    clf = SVC(C=c)
    #clf.fit(trainx,trainy)
    #sc[idc] = clf.score(testx,testy)
    sc = cross_validation.cross_val_score(clf, x, y, cv=5)
    print "C = %f, score = %f, std = %f" % (c,sc.mean(), sc.std())
    print sc

with open(outFile,'w') as f:
    f.write("C = %f, score = %f\n\n" % (c,sc[idc]))
    for (e,t,p) in zip(ent[401:],testy,clf.predict(testx)):
        f.write('%s\t%s\t%s\n' % (e,t,p))
