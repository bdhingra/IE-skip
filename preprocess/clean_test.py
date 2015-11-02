out = []
seen = set()
labels = set(['drug','disease','symptom','ingredient'])
with open('gpig_views/entvec.gp','r') as f:
    for line in f:
	row = line.split('\t')
	if row[1] in labels:
	    if row[0] not in seen:
		seen.add(row[0])
		out.append('\t'.join(row))
	    else:
		print row[0]
	else:
	    print row[0]

with open('cleantest.txt','w') as f:
    for item in out:
	f.write(item)
