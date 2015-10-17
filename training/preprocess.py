import re
import string

def prepareentitylist(X, path, clen):
    f = open(path, 'r')
    stops = f.read().splitlines()
    rm_idx = []
    out = []
    flag = False
    for idx,line in enumerate(X):
	if flag:
	    flag = False
	    continue
	cols = line.split("\t")
	if len(cols) > 1:
	    cand = re.sub(r'[0-9]+','#'," ".join([word for word in cols[1].split() if word not in stops]))
	    cand = filter(lambda x:x in string.printable, cand)
	    words = cand.split()
	    if (idx % 3) == 0:
		out.append(" ".join(words[-clen:]).lower())
	    elif (idx % 3) == 2:
		out.append(" ".join(words[:clen]).lower())
	    elif (idx % 3) == 1:
		if len(words) == 0:
		    out.pop()
		    flag = True;
		else:
		    out.append(" ".join(words).lower())
	else:
	    if (idx % 3) == 1:
		out.pop()
		flag = True
	    else:
		out.append("")
    return out
