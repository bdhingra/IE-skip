from guineapig import *
import math

#parse params
params = GPig.getArgvParams()
testFile = params['testFile']
featFile = params['featFile']
idFile = params['idFile']

# supporting functions
def parseFeats(row):
    f = row.split()
    fid = f[0]
    fe = {}
    for item in f[1:]:
	wc = item.split(':')
	fe[int(wc[0])] = int(float(wc[1]))
    return (fid,fe)

def combineFeats(row):
    key = row[0]
    ent = key[0]
    lab = key[1]

    f = row[1]
    out = {}
    for item in f:
	for k in set(item):
	    out[k] = out.get(k,0) + item[k]
    return (ent,lab,out)

# main
class TestBOWFeats(Planner):
    # Read inputs and parse
    test = ReadLines(testFile) | ReplaceEach(by=lambda row:(row.split('\t')[0].lower(),row.split('\t')[2][:-1].lower()))
    feats = ReadLines(featFile) | ReplaceEach(by=lambda row:parseFeats(row))
    ids = ReadLines(idFile) | ReplaceEach(by=lambda row:(row.split('\t')[1],row.split('\t')[2][:-1].lower()))

    # join test entities with features
    testids = Join(Jin(test, by=lambda (e,l):e), Jin(ids, by=lambda (i,e):e)) | ReplaceEach(by=lambda ((e1,l),(i,e2)):(i,e1,l))
    testfeats = Join(Jin(testids, by=lambda (i,e,l):i), Jin(feats, by=lambda (i,f):i)) | ReplaceEach(by=lambda ((i1,e,l),(i2,f)):(i1,e,l,f))

    # group all mentions of same entity
    combinetest = Group(testfeats, by=lambda (i,e,l,f):(e,l), retaining=lambda (i,e,l,f):f) | ReplaceEach(by=lambda row:combineFeats(row))

    # tf-idf
    docfreq = Flatten(feats, by=lambda (i,f):f.keys()) | Group(by=lambda key:key, reducingTo=ReduceToCount())
    ndoc = Group(feats, by=lambda row:'any', reducingTo=ReduceToCount()) | ReplaceEach(by=lambda (dummy,ndoc):ndoc)
    flattest = Flatten(combinetest, by=lambda (e,l,f):map(lambda (k,v):(e,l,k,v), f.iteritems()))
    uentvec = Join(Jin(flattest, by=lambda (e,l,k,v):k), Jin(docfreq, by=lambda (k,v):k)) | ReplaceEach(by=lambda ((e,l,k1,tf),(k2,df)):(e,l,k1,tf,df))
    uentvec2 = Augment(uentvec, sideview=ndoc, loadedBy=lambda v:GPig.onlyRowOf(v)) | ReplaceEach(by=lambda ((e,l,k,tf,df),ndoc):(e,l,k,math.log(tf+1)*math.log(ndoc/df)))
    norm = Group(uentvec2, by=lambda (e,l,k,tfidf):(e,l), retaining=lambda (e,l,k,tfidf):tfidf*tfidf, reducingTo=ReduceToSum())
    entvec = Join(Jin(norm, by=lambda ((e,l),z):(e,l)), Jin(uentvec2, by=lambda (e,l,k,w):(e,l))) | \
	    ReplaceEach(by=lambda (((e1,l1),z),(e2,l2,k,w)):(e1,l1,k,w/math.sqrt(z))) | \
	    Group(by=lambda (e,l,k,t):(e,l), retaining=lambda (e,l,k,t):(k,t)) | \
	    Format(by=lambda ((e,l),flist):'%s\t%s\t%s' % (e,l,' '.join(['%d:%f' % (k,v) for k,v in flist])))

if __name__ == "__main__":
    planner = TestBOWFeats()
    planner.main(sys.argv)
