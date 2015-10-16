import vocab
import train

def removeID(X):
    out = []
    for line in X:
	cols = line.split("\t")
	if len(cols) > 1:
	    out.append(cols[1].lower())
	else:
	    out.append("")
    return out

def removeStopWords(X, path):
    f = open(path, 'r')
    stops = f.read().splitlines()
    out = []
    for line in X:
	out.append(" ".join([word for word in line.split() if word not in stops]))
    return out

# paths for input, output
data_path = '../../data/drugdata/stuffForBD.gp'
dict_path = '../drugdata/dict.pkl'
out_path = '../drugdata/output.npz'
stop_path = '../preprocess/punctuations.txt'

# params
#N = 5000
max_e = 10
dispF = 10
max_w = 50
saveF = 10;

# load the data and put in list
f = open(data_path, 'r')
X = f.read().splitlines()

# preprocess
X = removeID(X)
X = removeStopWords(X, stop_path)

# store for future
f = open('../drugdata/processed.txt','w')
for item in X:
    f.write('%s\n' % item)

# choose subset of data
#X = X[:N]

# build dictionary
worddict, wordcount = vocab.build_dictionary(X)
vocab.save_dictionary(worddict, wordcount, dict_path)

# train
train.trainer(X, saveto=out_path, dictionary=dict_path, saveFreq=saveF, max_epochs=max_e, dispFreq=dispF, maxlen_w=max_w)
