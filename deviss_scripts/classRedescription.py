import re, pdb
from classLog import Log
from classQuery import  *
from classSParts import  SParts
from classCWQuery import  *

class Redescription:
    logger = Log(0)
    nbVariables = 3
    diff_terms = Query.diff_terms
    diff_cols = Query.diff_cols
    diff_op = Query.diff_op
    diff_balance = Query.diff_balance
    diff_length = Query.diff_length
    diff_score = diff_length + 1
    trackHisto = False
        
    def settings(setts):
        (Redescription.nbVariables, Redescription.trackHisto) = (setts.param['nb_variables'], setts.param['track_histo'])
        SParts.setMethodPVal(setts.param['method_pval'].capitalize()) 
    settings = staticmethod(settings)

    def histoUpdate(self, opk=None, side=None):
        if Redescription.trackHisto:
            if type(opk) == int :
                self.histo = [k]
            elif type(self.histo) == list and opk!= None and side != None:
                self.histo.append(int(opk)*(side+1)) 


    def __init__(self, nqueryL, nqueryR, nsupps = None, nN = -1, navailableCols = [set(),set()], nPrs = [-1,-1], nHisto=None):
        if Redescription.trackHisto:
            if type(nHisto) == list :
                self.histo = nHisto
            else:
                self.histo = []

        self.queries = [nqueryL, nqueryR]
        if nsupps != None:
            self.sParts = SParts(nN, nsupps, nPrs)
        else:
            self.sParts = None
            self.readInfo = []
        self.lAvailableCols = navailableCols
        self.vectorABCD = None
        
    def fromInitialPair(initialPair, data):
        queryL = Query()
        queryR = Query()
        queryL.extend(None, initialPair[0])
        queryR.extend(None, initialPair[1])
        (suppL, missL) = data.termSuppMiss(0, initialPair[0])
        (suppR, missR) = data.termSuppMiss(1, initialPair[1])
        r = Redescription(queryL, queryR, [suppL, suppR, missL, missR], data.nbRows(), data.nonFull(), [len(suppL)/float(data.N),len(suppR)/float(data.N)])  
        return r
    fromInitialPair = staticmethod(fromInitialPair)

    def fromQueriesPair(queries, data):
        r = Redescription(queries[0].copy(), queries[1].copy())
        r.recompute(data)
        return r
    fromQueriesPair = staticmethod(fromQueriesPair)

    def compare(x, y):
        if x.score() > y.score():
            return Redescription.diff_score
        elif x.score() == y.score():
            return Query.comparePair(x.queries[0], x.queries[1], y.queries[0], y.queries[1])
        else:
            return -Redescription.diff_score
    compare = staticmethod(compare)

    def equivalent(self, y):
       return abs(Redescription.compare(self, y)) < Redescription.diff_balance

    def __cmp__(self, other):
        if other == None:
            return 1
        else:
            return Redescription.compare(self,other)
        
    def __hash__(self):
        return int(hash(self.queries[0])+ hash(self.queries[1])*100*self.score())
        
    def __len__(self):
        return len(self.queries[0]) + len(self.queries[1])
        
    def oneSideIdentical(self, redescription, count_ids= [0,0], max_iden = 0):
        found = False
        if self.queries[0] == redescription.queries[0]:
            count_ids[0] += 1
            found |= (count_ids[0] >= max_iden)
        if self.queries[1] == redescription.queries[1]:
            count_ids[1] += 1
            found |= (count_ids[1] >= max_iden)
        return found

    def acc(self):
        return self.sParts.acc()

    def opacc(self):
        return self.sParts.opacc()

    def lenI(self):
        return self.sParts.lenI()

    def suppI(self):
        return self.sParts.suppI()
    
    def lenO(self):
        return self.sParts.lenO()

    def suppO(self):
        return self.sParts.suppO()
    
    def lenU(self):
        return self.sParts.lenU()

    def suppU(self):
        return self.sParts.suppU()

    def pVal(self):
        return self.sParts.pVal()

    def score(self):
        return self.acc()

    def supports(self):
        return self.sParts
    
    def query(self, side):
        return self.queries[side]
    
    def probas(self):
        return self.sParts.probas()
    
    def fullLength(self, side):
        return len(self.queries[side]) >= self.nbVariables
    def length(self, side):
        return len(self.queries[side])
        
    def availableColsSide(self, side):
        return self.lAvailableCols[side]
    def nbAvailableColsSide(self, side):
        return len(self.lAvailableCols[side])
    def nbAvailableCols(self):
        return self.nbAvailableColsSide(0) + self.nbAvailableColsSide(1)
    def updateAvailable(self, souvenirs):
        nb_extensions = [0,0]
        for side in [0,1]:
            if self.nbAvailableColsSide(side) > 0:
                self.lAvailableCols[side] =  souvenirs.availableMo[side] - souvenirs.extOneStep(self, side)
                nb_extensions[side] = len(souvenirs.availableMo[side]) - self.length(side) - self.nbAvailableColsSide(side)
        return nb_extensions[0]+nb_extensions[1]

    def removeAvailables(self):
        self.lAvailableCols = [set(),set()]

    def update(self, data=None, side= -1, opBool = None, term= None, suppX=None, missX=None):
        raise Error('Not to be used!')
        if side == -1 :
            self.removeAvailables()
        else:
            op = Op(opBool)
            if Redescription.trackHisto:
                self.histoUpdate(op, side)
            self.queries[side].extend(op, term)
            self.sParts.update(side, op.isOr(), suppX, missX)
            if len(self.queries[side]) >= self.nbVariables :
                self.lAvailableCols[side] = set()
            else:
                self.lAvailableCols[side].remove(term.col())
                
    def kid(self, data, side= -1, op = None, term= None, suppX= None, missX=None):
        kid = self.copy()
        kid.update(data, side, op, term, suppX, missX)
        return kid

    def cousin(self, data, side= -1, op = None, term_ext=None, terms_adj=None):
        cousin = self.copy()
        cousin.adjustRed(None, terms_adj)
        cousin.extendRed(data, side, op, term_ext)
        return cousin

    def extendRed(self, data=None, side= -1, opBool = None, term_ext=None):
        if side != -1 :
            self.queries[side].extend(opBool, term_ext)
            if data != None:
                self.recompute(data)

    def adjustRed(self, data=None, terms_adj=None):
        if terms_adj != None:
            ok = True
            for term_adj in terms_adj:
                ok &= self.queries[term_adj['side']].buk[term_adj['buk']][term_adj['pos']].squeeze(term_adj['op'],term_adj['terms'])
            if not ok:
                raise Error("Error while updating cousin!")
            if data != None:
                self.recompute(data)
            
    def copy(self):
        if Redescription.trackHisto and type(self.histo) == list :
            histo = list(self.histo)
        else:
            histo = None
        return Redescription(self.queries[0].copy(), self.queries[1].copy(), \
                             self.sParts.copSupp(), self.sParts.N, \
                             [set(self.lAvailableCols[0]),set(self.lAvailableCols[1] )], self.probas(), histo)

    def recomputeQuery(self, side, data= None):
        return self.queries[side].recompute(side, data)
    
    def invTermsSide(self, side):
        return self.queries[side].invTerms()

    def invTerms(self):
        return [self.invTermsSide(0), self.invTermsSide(1)]
    
    def invColsSide(self, side):
        return self.queries[side].invCols()

    def invCols(self):
        return [self.invColsSide(0), self.invColsSide(1)]

    def invSignedSide(self, side):
        return self.queries[side].invSigned()

    def invSigned(self):
        a = []
        for i in self.invSignedSide(0):
            a.append((0, i[0], i[1]))
        for i in self.invSignedSide(1):
            a.append((1, i[0], i[1]))
        return a

    def invStr(self):
        a = []
        for i in self.invSignedSide(0):
            a.append(Redescription.encoInvStr(0, i[0], i[1]))
        for i in self.invSignedSide(1):
            a.append(Redescription.encoInvStr(1, i[0], i[1]))
        a.sort()
        return ':'.join(a)

    def invStrQueries(queries):
        a = []
	for qi in range(len(queries)):
            for i in queries[qi].invSigned():
            	a.append(Redescription.encoInvStr(qi, i[0], i[1]))
        a.sort()
        return ':'.join(a)
    invStrQueries = staticmethod(invStrQueries)

    def encoInvStr(side, col, neg):
        return "%d-%d-%d" % (side, col, neg)
    encoInvStr = staticmethod(encoInvStr)

    def decoInvStr(partStr):
        m = re.match(r"^(?P<side>\d*)-(?P<col>\d*)-(?P<neg>\d*)$", partStr)
        (side, col, neg) = (None, None, None)
        if m!=None:
            try:
                (side, col, neg) = (int(m.group('side')), int(m.group('col')), m.group('neg') == 1)
            except ValueError:
                side = None
        return (side, col, neg)
    decoInvStr = staticmethod(decoInvStr)

    def getTerm(self, side, bukNb, posNb):
        return self.queries[side].getTerm(bukNb, posNb)

    def searchTerm(self, partStr):
        (side, col, neg) = Redescription.decoInvStr(partStr)
        if side != None:
            tmp = self.queries[side].searchTerm(col, neg)
            if tmp != None:
                tmp.update({'side': side, 'col': col})
                return tmp
    
    def recompute(self, data):
        (nsuppL, missL) = self.recomputeQuery(0, data)
        (nsuppR, missR) = self.recomputeQuery(1, data)
        if len(missL) + len(missR) > 0:
            self.sParts = SParts(data.N, [nsuppL, nsuppR, missL, missR])
        else:
            self.sParts = SParts(data.N, [nsuppL, nsuppR])
        self.prs = [self.queries[0].proba(0, data), self.queries[1].proba(1, data)]
    
    def check(self, data):
        result = 0
        details = None
        if self.sParts != None:
            (nsuppL, missL) = self.recomputeQuery(0, data)
            (nsuppR, missR) = self.recomputeQuery(1, data)
            
            details = ( len(nsuppL.symmetric_difference(self.sParts.supp(0))) == 0, \
                     len(nsuppR.symmetric_difference(self.sParts.supp(1))) == 0, \
                     len(missL.symmetric_difference(self.sParts.miss(0))) == 0, \
                     len(missR.symmetric_difference(self.sParts.miss(1))) == 0 )        
            result = 1
            for detail in details:
                result*=detail
        return (result, details)

    def hasMissing(self):
        return self.sParts.hasMissing()

    def __str__(self):
        return self.dispSimple()

    def dispLong(self):
        return '%i + %i items:\t (%i): %s' \
               % (self.nbAvailableColsSide(0), self.nbAvailableColsSide(1), \
                  len(self), self.disp())
         
    def dispLPartsSimple(self):
        if self.sParts == None:
            return SParts.dispCharListSimple(self.readInfo)
        else:
            return SParts.dispCharListSimple(self.sParts.listLPartsChar())
        
    def dispLParts(self): 
        if self.sParts == None:
            return SParts.dispCharList(self.readInfo)
        else:
            return SParts.dispCharList(self.sParts.listLPartsChar())

    def dispQueriesSimple(self, lenIndex=0, names= [None, None]):
        return '%s %s' % (self.queries[0].disp(lenIndex, names[0]), self.queries[1].disp(lenIndex, names[1]))
    
    def dispSimple(self, lenIndex=0, names= [None, None]):
        str_red = '%s\t%s\t%s' % (self.queries[0].disp(lenIndex, names[0]), self.queries[1].disp(lenIndex, names[1]), self.dispLPartsSimple())
        if Redescription.trackHisto:
            str_red += ('\thisto:%s' % self.histo)
        return str_red

    def dispPrintHeader():
        return ' & $q_\iLHS$ & $q_\iRHS$ & $\\jacc$ & $\\supp$ & \\pValue  \\\\'
    dispPrintHeader = staticmethod(dispPrintHeader)

    def dispPrint(self, queryId, names = [None, None]):
        queryidStr = '(%i)' % queryId
        format_list = []
        return queryidStr + ' & ' + self.queries[0].dispPrint(names[0])+' & '+self.queries[1].dispPrint(names[1])+ ' & ' +self.dispCaracteristiquesPrint()+' \\\\'

    def dispCaracteristiquesPrint(self):
        if self.sParts != None:
            return '$%1.3f$ & $%i$ & $%1.3f$' \
             % (round(self.acc(),3), self.lenI(), round(self.pVal(),3))
        elif hasattr(self, 'readInfo'):
            dict_info = dict([[item[0], item[2]] for item in self.readInfo])
            return '$%1.3f$ & $%i$ & $%1.3f$' \
             % (round(dict_info['acc'],3), dict_info['gamma'], round(dict_info['pVal'],3))
        else:
            return 'Non printable redescription'

    
    def dispCaracteristiquesSimple(self):
        return self.dispLPartsSimple()
        
    def disp(self, lenIndex=0, names= [None, None]):
        str_red = '%s\t<==>\t%s\t%s' % (self.queries[0].disp(lenIndex, names[0]), self.queries[1].disp(lenIndex, names[1]), self.dispLParts())
        if Redescription.trackHisto:
            str_red += ('\tHISTO:%s' % self.histo)
        return str_red

    def dispSupp(self):
        return self.sParts.dispSupp()
    
    def write(self, output, suppOutput):
        output.write(self.dispSimple()+'\n')
        output.flush()
        if suppOutput != None:
            suppOutput.write(self.sParts.dispSupp()+'\n')
            suppOutput.flush()

    def parseQueries(string):
        parts = string.rsplit('\t')

        if len(parts) >= 2:
            queryL = Query.parse(parts[0])
            queryR = Query.parse(parts[1])
        else:
            queryL = Query()
            queryR = Query()

        if len(parts) >= 3:
            lpartsList = SParts.parseLPartsChar(parts[2])
        else:
            lpartsList = []
        return (queryL, queryR, lpartsList)
    parseQueries = staticmethod(parseQueries)

    def parse(stringQueries, stringSupport = None, data = None):
        (queryL, queryR, lpartsList) = Redescription.parseQueries(stringQueries)

        r = None
        if data != None and stringSupport != None and type(stringSupport) == str and re.search('\t', stringSupport) :
            supportsS = SParts.parseSupport(stringSupport, data.N)
            if supportsS != None:
                r = Redescription(queryL, queryR, supportsS.copSupp(), data.nbRows(), [set(),set()], [ queryL.proba(0, data), queryR.proba(1, data)])

                if lpartsList[3:] != r.sParts.listLPartsChar()[3:]:
                    raise Warning("Something wrong in the supports ! (%s ~ %s)\n" \
                                  % (SParts.dispCharList(lpartsList), SParts.dispCharList(r.sParts.listLPartsChar()) ))
        if r == None:
            r = Redescription(queryL, queryR)
            r.readInfo = lpartsList
        return r
    parse = staticmethod(parse)
            
    def load(queriesFp, supportsFp = None, data= None):
        stringQueries = queriesFp.readline()
        indComm = stringQueries.find('#')
        comment = ''
        if indComm != -1 :
            comment = stringQueries[indComm:].rstrip()
            stringQueries = stringQueries[:indComm]
        
        if type(supportsFp) == file :
            stringSupp = supportsFp .readline()
            indComm = stringSupp.find('#')
            commentSupp = ''
            if indComm != -1 :
                commentSupp = stringSupp[indComm:].rstrip()
                stringSupp = stringSupp[:indComm]

        else: stringSupp= None; commentSupp = ''
        return (Redescription.parse(stringQueries, stringSupp, data), comment, commentSupp)
    load = staticmethod(load)