import vocab
import train

# paths for input, output
data_path = '../drugdata/stuffForBD.gp'
dict_path = '../drugdata/dict.txt'
out_path = '../drugdata/output.npz'

# params
N = 5000

# load the data and put in list
f = open(data_path, 'r')
X = f.readlines()

# choose subset of data
X = X[:N]

# build dictionary
worddict, wordcount = vocab.build_dictionary(X)
vocab.save_dictionary(worddict, wordcount, dict_path)

# train
train.trainer(X, saveto=out_path, dictionary=dict_path)
