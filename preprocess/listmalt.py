from guineapig import *
import sys
import logging
import collections

#parse params
params = GPig.getArgvParams()
INPUT = params.get('input','prescription-sample-processed/paragraph_ss_filter_parsed.txt')
CHUNKER = params.get('chunker','npPOS')  #ne also might work
LISTS = params.get('lists', 'coord') # trivial or trivialAndCoord also works
MIN_SENTENCE_LEN = 6
MAX_SENTENCE_LEN = 100
if params.get('help'):
    print 'params: input:FILE,  chunker:npPOS|ne,  lists:coord|trivial'
    sys.exit(1)
print >>sys.stderr,'params: chunker',CHUNKER,'lists',LISTS

#for assigning ids - note this will not parallelize!
nextIndex = 0

class ReadBlocks(Reader):
    """ Returns blocks of lines in a file. """
    def __init__(self,src,isEndBlock=lambda line:line=="\n"):
        Reader.__init__(self,src)
        self.isEndBlock = isEndBlock
    def rowGenerator(self):
        buf = []
        for line in sys.stdin:
            if self.isEndBlock(line):
                yield buf
                buf = []
            else:
                buf.append(line)
        if buf:
            yield buf
    def __str__(self):
        return 'ReadBlocks("%s")' % self.src + self.showExtras()

class Token(object):
    """Encodes a single malt-parsed token."""
    def __init__(self, sid, index, word, stem, neTag, pos, edgeLabel, parent):
        self.sid = sid
        self.index = index
        self.word = word
        self.stem = stem
        self.neTag = neTag
        self.pos = pos
        self.edgeLabel = edgeLabel
        self.parent = parent
    def __repr__(self):
        return "Token(" + ",".join(map(repr, [self.sid, self.index, self.word, self.stem, self.neTag, self.pos, self.edgeLabel, self.parent]))+")"

    #override this when the token format varies
    @staticmethod 
    def parseLine(line):
        (i,w,stem,chunk1,pos,chunk2,j,edgeLabel) = line.strip().split("\t")
        global nextIndex
        nextIndex += 1
        sentIndex = nextIndex
        sid = "s_%s" % (sentIndex)
        return Token(sid,int(i),w,stem,chunk1,pos,edgeLabel,int(j))

class Sentence(object):

    """Encodes a malt-parsed sentence."""
    def __init__(self,sdict):
        self.sdict = sdict
    def __repr__(self):
        return "Sentence(" + repr(self.sdict) + ")"

    @staticmethod
    def parseBlock(block):
	sdict = {}
        for line in block:
            tok = Token.parseLine(line)
            sdict[tok.index] = tok
        global nextIndex
        nextIndex += 1
        return Sentence(sdict)

    def numWords(self):
        return len(self.sdict)+1

    def sid(self):
        """Sentence id."""
        return self.sdict[1].sid

    def words(self,lo=None,hi=None):
        """List of words."""
        if lo and not hi: hi = lo
        if not lo: lo=1
        if not hi: hi=len(self.sdict)
        return [self.sdict[i].word for i in range(lo,hi+1)]

    def neChunks(self):
        """Find named-entity chunks."""
        def insideNEChunk(self,tok): return tok.neTag!='O'
        def inSameChunkAs(self,tok,prevTok): return tok.neTag==prevTok.neTag
        for chunk in self._findChunks(insideNEChunk,inSameChunkAs):
            yield chunk

    def npViaPOSChunks(self):
        def insideNPChunk(self,tok): 
            return tok.pos.startswith('NN') or tok.pos.startswith('JJ') 
        def npChunkFilter(self,buf): 
            #logging.warn('buf = ' + " ".join(map(lambda i:self.sdict[i].word, buf)))
            #logging.warn('pos = ' + " ".join(map(lambda i:self.sdict[i].pos, buf)))
            tokensWhichAreProperNouns = map(lambda i:self.sdict[i].pos=='NNP',buf)
            #logging.warn('NNPs = ' + str(tokensWhichAreProperNouns))
            if any(tokensWhichAreProperNouns) and tokensWhichAreProperNouns[-1]:
                #discard anything but the final sequence of proper nouns
                lo = hi = max(buf)
                while (lo>1 and self.sdict[lo-1].pos=='NNP'):
                    lo -= 1
                #logging.warn('final NNP sequence: '+str((lo,hi)))
                yield (lo,hi)
            else:
                #logging.warn('not a NNP sequence here')
                #verify that there is at least one noun
                tokensWhichAreNouns = map(lambda i:self.sdict[i].pos.startswith('NN'),buf)
                if any(tokensWhichAreNouns):
                    #logging.warn('passed noun test')
                    yield(min(buf),max(buf))
        for chunk in self._findChunks(insideNPChunk,chunkFilter=npChunkFilter):
            yield chunk

    def _findChunks(self,isInsideChunk,inSameChunkAs=lambda sent,tok,prevTok:True,chunkFilter=lambda buf:(min(buf),max(buf))):
        """Iterator over chunks in a sentence.  Chunks are defined as the
        longest sequences of tokens that are (a) inside a chunk and
        (b) is inside the same chunk asthe previous token, as specified
        by the two function arguments."""
        buf = []
        for i in range(1,len(self.sdict)+1):
            toki = self.sdict[i]
            if isInsideChunk(self,toki):
                if i>1 and not inSameChunkAs(self,toki,self.sdict[i-1]):
                    if buf: 
                        for chunk in chunkFilter(self,buf): yield chunk
                    buf = []
                buf = buf + [i]
            else:
                if buf: 
                    for chunk in chunkFilter(self,buf): yield chunk
                buf = []
        if buf: 
            for chunk in chunkFilter(self,buf): yield chunk

    def head(self,lo,hi):
        """Head word of a phrase, or None if there is no single head."""
        results = set()
        for k in range(lo,hi+1):
            #move up the dep tree until you're outside the range
            while lo <= self.sdict[k].parent <= hi:
                k = self.sdict[k].parent
            results.add(k)
        if len(results)==1:
            for k in results:
                return k
        else:
            return None #multiple heads
        
class CoordList(object):
    """Encodes a list of coordinate terms, eg "red, white and blue",
    from a single sentence."""
    def __init__(self,i,entries=None):
        self.root = i
        self.entries = {} if entries==None else entries

    def addListEntry(self,i,j,h):
        self.entries[h] = (i,j,h)

    def lo(self):
        return min([i for (i,j,h) in self.entries.values()]) 

    def hi(self):
        return max([j for (i,j,h) in self.entries.values()]) 

    def __repr__(self):
        return "CoordList(" + str(self.root) + "," + repr(self.entries)+")"

    def cListId(self,s):
        return '%s_%d' % (s.sid(),self.root)

    def size(self):
        return len(self.entries)

    def contextFeatures(self,sent,n,feats=None):
        """Compute features associated with the left andright tokens around the list."""
        if feats==None: feats = {}
        stems = ['^']+[sent.sdict[j].stem.lower() for j in range(1,sent.numWords())]
        i = self.lo()
        j = self.hi()+1
        for k in range(1,n+1):
            lngram = "_".join(stems[i-k:i])
            feats['left%dgram=%s' % (k,lngram)] = 1
            rngram = "_".join(stems[j:j+k])
            feats['right%dgram=%s' % (k,rngram)] = 1
            if i-k>=1: feats['lefttok=%s' % stems[i-k]] = 1
            if j+k<sent.numWords(): feats['righttok=%s' % stems[j+k]] = 1
        return feats

    def depTreeFeatures(self,sent,feats=None):
        """Compute features associated with the dependency tree."""
        if feats==None: feats = {}
        #walk up the tree to a verb
        i = self.root
        path = []
        closestVerbIndex = 0
        while (i>0):
            if path:
                #feats[ "->".join(path) + "=" + sent.sdict[i].stem] = 1
                #feats['a'*len(path) + "=" + sent.sdict[i].stem] = 1
                #feats['a*_has_' + sent.sdict[i].stem] = 1
                if sent.sdict[i].pos.startswith("V"):
                    if not closestVerbIndex: 
                        closestVerbIndex = i
                        feats['v_'+sent.sdict[i].stem] = 1
                        feats['vp_'+"_".join(path)] = 1
                    else:
                        feats['av_'+sent.sdict[i].stem] = 1                        
            path.append(sent.sdict[i].edgeLabel)
            i = sent.sdict[i].parent
        #find modifiers of the closest verb
        for i in range(1,sent.numWords()):
            if sent.sdict[i].parent==closestVerbIndex:
                feats['vmod_'+sent.sdict[i].stem] = 1
        return feats

    def asString(self,sent,withFeatures=True):
        if self.entries:
            buf = "list: <"+" ".join(sent.words(self.lo(), self.hi()))+">"
        else:
            return "empty list: <" +str(self.root) + ">"
        if withFeatures:
            buf += " dfeats: "+repr(self.depTreeFeatures(sent).keys())
            buf += " cfeats: "+repr(self.contextFeatures(sent,3).keys())
        buf += " in: "+" ".join(sent.words())
        return buf

    def asStringWithContext(self,sent,window):
        #lo = max(self.lo()-window,0)
        #hi = min(self.hi()+window,sent.numWords() - 1)
        #return str( sent.words(lo,self.lo()-1) ) + str( sent.words(self.lo(),self.hi()) ) + str( sent.words(self.hi()+1,hi) ) + str(sent.words())
	lo = max(self.lo()-window,0)
	hi = min(self.hi()+window,sent.numWords()-1)
	if self.lo() == 1:
	    cbefore = []
	else:
	    cbefore = sent.words(lo,self.lo()-1)
	if self.hi() == sent.numWords()-1:
	    cafter = []
	else:
	    cafter = sent.words(self.hi()+1,hi)
        return ( cbefore , sent.words(self.lo(),self.hi()) , cafter ) 

    @staticmethod
    def findTrivialLists(sent,chunks,trivialOnly=False):
        """Return a coordlist object for each single chunk."""
        result = {}
        npsInNonTrivialLists = set()
        if trivialOnly:
            for cl in CoordList.findCoordLists(sent,chunks,minLen=2).values():
                for np in cl.entries.values():
                    npsInNonTrivialLists.add(np,)
        #if npsInNonTrivialLists: print >>sys.stderr,len(npsInNonTrivialLists),'list nps',npsInNonTrivialLists,'from',sent.words()
        for (i,j) in chunks:
            h = sent.head(i,j)
            if h:
                if (i,j,h) in npsInNonTrivialLists:
                    pass
                    #print >>sys.stderr,'discarding',(i,j,h),'ie',repr(sent.words(i,j)),'from',sent.words()                    
                else:
                    result[h] = CoordList(h)
                    result[h].addListEntry(i,j,h)
        return result

    @staticmethod
    def findCoordLists(sent,chunks,minLen=3):
        """Return a dictionary of CoordList structures, indexed
        by position of the root for the CoordList's."""
        # look for anything that is an NMOD of a conjunction,
        # eg 'blue' in 'red white and blue', and store a
        # new CoordList in result, indexed by position of the
        # 'root' token, eg blue in this case
        result = {}
        for j,tokj in sent.sdict.items():        
            if tokj.pos=='CC' and tokj.edgeLabel=='NMOD':
                r = tokj.parent
                result[r] = CoordList(r)
        #divvy the chunks up into CoordList's from result 
        for (i,j) in chunks:
            h = sent.head(i,j)
            if h:
                htok = sent.sdict[h]
                if (htok.parent in result) and (htok.edgeLabel=='NMOD'):
                    result[htok.parent].addListEntry(i,j,h)
                if (h in result):
                    result[h].addListEntry(i,j,h)
        #delete short lists
        for h in result.keys():
            if result[h].size()<minLen: del result[h]
        #done
        return result

def sentFileName(s):
    if s.sdict[1].word=='FILENAME':
        return s.sdict[3].word
    else:
        return 'LAST'

class ListMalt(Planner):

    blocks = ReadBlocks(INPUT)
    sents = ReplaceEach(blocks, by=lambda block:Sentence.parseBlock(block))
    
    sentInfo = ReplaceEach(sents, by=lambda s:(s.sid(),sentFileName(s))) | Format(by=lambda (sid,info):'\t'.join([sid,info]))

    realSents = Filter(sents, by=lambda s:MIN_SENTENCE_LEN<=s.numWords()<=MAX_SENTENCE_LEN)
    viewableSents = ReplaceEach(realSents, by=lambda s:(s.sid(),s.words()))  #something I can read, for debugging


    #pairs 

    #TODO: neChunker is not well tested....
    if CHUNKER=='ne':
        chunkedSents = ReplaceEach(realSents, by=lambda s:(s, list(s.neChunks())))
    elif CHUNKER=='npPOS':
        chunkedSents = ReplaceEach(realSents, by=lambda s:(s, list(s.npViaPOSChunks())))
    else:
        assert False,'unknown chunker '+CHUNKER

    if LISTS=='coord':
        sentencesWithLists = \
            ReplaceEach(chunkedSents, by=lambda(s,chunks):(s,CoordList.findCoordLists(s,chunks,minLen=3))) \
            | Filter(by=lambda(s,coordLists):coordLists)
    elif LISTS=='trivial':
        sentencesWithLists = \
            ReplaceEach(chunkedSents, by=lambda(s,chunks):(s,CoordList.findTrivialLists(s,chunks))) \
            | Filter(by=lambda(s,coordLists):coordLists)
    elif LISTS=='trivialOnly':
        sentencesWithLists = \
            ReplaceEach(chunkedSents, by=lambda(s,chunks):(s,CoordList.findTrivialLists(s,chunks,trivialOnly=True))) \
            | Filter(by=lambda(s,coordLists):coordLists)
    elif LISTS=='trivialOrCoord':
        sentencesWithNonTrivialLists = \
            ReplaceEach(chunkedSents, by=lambda(s,chunks):(s,CoordList.findCoordLists(s,chunks,minLen=2))) \
            | Filter(by=lambda(s,coordLists):coordLists)
        sentencesWithTrivialLists = \
            ReplaceEach(chunkedSents, by=lambda(s,chunks):(s,CoordList.findTrivialLists(s,chunks,trivialOnly=True))) \
            | Filter(by=lambda(s,coordLists):coordLists)
        sentencesWithLists = Union(sentencesWithTrivialLists,sentencesWithNonTrivialLists)
    else:
        assert False,'bad list option :'+LISTS+' - legal options are coord, trivial, trivialOnly, trivialOrCoord'

    #main output 1: lists as a graph, in format: listId <TAB> listItem

    listsWithItems = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,cList) for cList in coordLists.values()]) \
                     | Flatten(by=lambda(s,cList):[(cList.cListId(s), s.words(i,j)) for (i,j,h) in cList.entries.values()])
    listsAsGraph = Format(listsWithItems, by=lambda(lid,words):'%s\t%s' % (lid,(" ".join(words)).lower()))

    stuffForBD = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,cList) for cList in coordLists.values()]) \
                 | Flatten(by=lambda(s,cList):[(cList.cListId(s),c) for c in cList.asStringWithContext(s,5)]) | \
		 Format(by=lambda(row):'%s\t%s' % (row[0]," ".join(row[1])))

    #main output 2: lists with features, in format: listId <TAB> feat1 <TAB> ...
    listsWithDFeats = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,cList) for cList in coordLists.values()]) \
                      | ReplaceEach(by=lambda(s,cList):(cList.cListId(s),cList.depTreeFeatures(s))) \
                      | Format(by=lambda(lid,fdict): '%s\t%s' % (lid,(" ".join(fdict.keys()))))

    listsWithCFeats = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,cList) for cList in coordLists.values()]) \
                      | ReplaceEach(by=lambda(s,cList):(cList.cListId(s),cList.contextFeatures(s,3))) \
                      | Format(by=lambda(lid,fdict): '%s\t%s' % (lid,(" ".join(fdict.keys()))))

    listsWithFeats = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,cList) for cList in coordLists.values()]) \
                      | ReplaceEach(by=lambda(s,cList):(cList.cListId(s),cList.depTreeFeatures(s),cList.contextFeatures(s,3))) \
                      | Format(by=lambda(lid,fdict1,fdict2): '%s\t%s' % (lid,(" ".join(fdict1.keys()+fdict2.keys()))))
                     
    #main output 3: lists in human-readable form
    readableLists = Flatten(sentencesWithLists, by=lambda(s,coordLists):[(x.cListId(s),x.asString(s,withFeatures=False)) for x in coordLists.values()]) \
                    | Format(by=lambda(lid,readable):lid+"\t"+readable)

    # various debug outputs

    viewableLists = Flatten(sentencesWithLists, by=lambda(s,coordLists):[x.asString(s) for x in coordLists.values()])

    listDepFeatures = \
        Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,x) for x in coordLists.values()]) \
        | Flatten(by=lambda(s,clist):clist.depTreeFeatures(s).keys())

    listContextFeatures = \
        Flatten(sentencesWithLists, by=lambda(s,coordLists):[(s,x) for x in coordLists.values()]) \
        | Flatten(by=lambda(s,clist):clist.contextFeatures(s,4).keys())

if __name__ == "__main__":
    planner = ListMalt()
    planner.setEvaluator(GPig.SafeEvaluator({'Token':Token,'Sentence':Sentence,'CoordList':CoordList}))
    planner.main(sys.argv)
