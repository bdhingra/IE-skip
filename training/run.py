import vocab
import train
import re
import preprocess
import homogeneous_data
import cPickle as pkl
import sys

# paths for input, output
data_path = '../../data/drugdata/stuffForBD.gp'
proc_data_path = '../drugdata/exp3/processed.txt'
dict_path = '../drugdata/exp3/dict.pkl'
out_path = '../drugdata/exp3/output.npz'
stop_path = '../preprocess/punctuations.txt'

reload_ = True

# params
N = 500001
max_e = 5
dispF = 1
max_w = 50
saveF = 1000
batch = 64
clen = 6

if not reload_:
    # load the data and put in list
    f = open(data_path, 'r')
    X = f.read().splitlines()

    # preprocess
    X = preprocess.prepareentitylist(X, stop_path, clen)

    # store for future
    f = open(proc_data_path,'w')
    for item in X:
	f.write('%s\n' % item)
else:
    f = open(proc_data_path,'r')
    X = f.read().splitlines()

# subset
X = X[:N]

# build dictionary
worddict, wordcount = vocab.build_dictionary(X)
vocab.save_dictionary(worddict, wordcount, dict_path)

# train
train.trainer(X, saveto=out_path, dictionary=dict_path, saveFreq=saveF, max_epochs=max_e, dispFreq=dispF, maxlen_w=max_w, batch_size=batch)
