import re, string
from classQuery import  *
from classSParts import  SParts
import toolRead
import pdb

class Redescription:

    diff_score = Query.diff_length + 1
    print_info_full = SParts.infos.keys() + ["card_"+ label for label in SParts.labels] + list(SParts.labels)
    print_info = SParts.infos.keys() + ["card_"+ label for label in SParts.labels]
    print_info_tex = [("acc", 3, "$%1.3f$"), ("card_gamma", 0, "$%i$"), ("pval", 3, "$%1.3f$")]
    
    def __init__(self, nqueryL=None, nqueryR=None, nsupps = None, nN = -1, nPrs = [-1,-1]):
        self.queries = [nqueryL, nqueryR]
        if nsupps is not None:
            self.sParts = SParts(nN, nsupps, nPrs)
            self.dict_supp_info = None
        else:
            self.sParts = None
            self.dict_supp_info = {}
        self.lAvailableCols = [None, None]
        self.vectorABCD = None
        self.status = 1
        self.track = []
        
    def fromInitialPair(initialPair, data):
        queryL = Query()
        queryR = Query()
        queryL.extend(None, initialPair[0])
        queryR.extend(None, initialPair[1])
        (suppL, missL) = data.literalSuppMiss(0, initialPair[0])
        (suppR, missR) = data.literalSuppMiss(1, initialPair[1])
        r = Redescription(queryL, queryR, [suppL, suppR, missL, missR], data.nbRows(), [len(suppL)/float(data.N),len(suppR)/float(data.N)])
        r.track = [(0, initialPair[0].term.col), (1, initialPair[1].term.col)]
        return r
    fromInitialPair = staticmethod(fromInitialPair)

    def fromQueriesPair(queries, data):
        r = Redescription(queries[0].copy(), queries[1].copy())
        r.recompute(data)
        r.track = [tuple([0] + sorted(r.queries[0].invCols())), tuple([1] + sorted(r.queries[1].invCols()))]
        return r
    fromQueriesPair = staticmethod(fromQueriesPair)

    def getInfoDict(self):
        if self.dict_supp_info is None and self.sParts is not None:
            self.dict_supp_info = self.sParts.toDict()
        if self.dict_supp_info is not None:
            return self.dict_supp_info
        return {}

    def dropSupport(self):
        if self.sParts is not None:
            self.dict_supp_info.toDict()
            self.sParts = None

    def compare(self, y):
        if self.score() > y.score():
            return Redescription.diff_score
        elif self.score() == y.score():
            return Query.comparePair(self.queries[0], self.queries[1], y.queries[0], y.queries[1])
        else:
            return -Redescription.diff_score

    def interArea(self, redB, side):
        if redB is not None:
            return len(redB.supp(side) & self.supp(side))* len(redB.invColsSide(side) & self.invColsSide(side))
        return 0
    def unionArea(self, redB, side):
        if redB is not None:
            return len(redB.supp(side) | self.supp(side))* len(redB.invColsSide(side) | self.invColsSide(side))
        return 0
    def overlapAreaSide(self, redB, side):
        areaU = self.unionArea(redB, side)
        if areaU != 0:
            return self.interArea(redB, side) / float(areaU)
        return 0
    def overlapAreaTotal(self, redB):
        areaUL = self.unionArea(redB, 0)
        areaUR = self.unionArea(redB, 1)
        if areaUL+areaUR != 0:
            return (self.interArea(redB, 0) + self.interArea(redB, 1)) / float(areaUL+areaUR)
        return 0
    def overlapAreaL(self, redB):
        return self.overlapAreaSide(redB, 0)
    def overlapAreaR(self, redB):
        return self.overlapAreaSide(redB, 1)
    def overlapAreaMax(self, redB):
        return max(self.overlapAreaSide(redB, 0), self.overlapAreaSide(redB, 1))
    
    def oneSideIdentical(self, redescription):
        return self.queries[0] == redescription.queries[0] or self.queries[1] == redescription.queries[1]

    def equivalent(self, y):
       return abs(self.compare(y)) < Redescription.diff_balance
        
    # def __hash__(self):
    #      return int(hash(self.queries[0])+ hash(self.queries[1])*100*self.score())
        
    def __len__(self):
        return self.length(0) + self.length(1)
        
    def acc(self):
        return self.sParts.acc()

    def lenI(self):
        return self.sParts.lenI()

    def suppI(self):
        return self.sParts.suppI()

    def supp(self, side=0):
        return self.sParts.supp(side)
    
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
    
    def partsNoMiss(self):
        return self.sParts.sParts[:4]
    
    def query(self, side):
        return self.queries[side]
    
    def probas(self):
        return self.sParts.probas()
    
    def length(self, side):
        return len(self.queries[side])
        
    def availableColsSide(self, side):
        if self.lAvailableCols[side] is not None and self.length(1-side) != 0:
            return self.lAvailableCols[side]
        return set() 
    def nbAvailableCols(self):
        if self.lAvailableCols[0] is not None and self.lAvailableCols[1] is not None:
            return len(self.lAvailableCols[0]) + len(self.lAvailableCols[1])
        return -1
    def updateAvailable(self, souvenirs):
        nb_extensions = 0
        for side in [0, 1]:
            if self.lAvailableCols[side] is None or len(self.lAvailableCols[side]) != 0:
                self.lAvailableCols[side] =  souvenirs.availableMo[side] - souvenirs.extOneStep(self, side)
                nb_extensions += len(souvenirs.availableMo[side]) - self.length(side) - len(self.lAvailableCols[side])
        return nb_extensions
    def removeAvailables(self):
        self.lAvailableCols = [set(),set()]

    def update(self, data=None, side= -1, opBool = None, literal= None, suppX=None, missX=None):
        if side == -1 :
            self.removeAvailables()
        else:
            op = Op(opBool)
            self.queries[side].extend(op, literal)
            self.sParts.update(side, op.isOr(), suppX, missX)
            self.dict_supp_info = None
            if self.lAvailableCols[side] is not None:
                self.lAvailableCols[side].remove(literal.col())
            self.track.append((side, literal.col()))

    def setFull(self, max_var=None):
        if max_var is not None:
            for side in [0,1]:
                if self.length(side) >= max_var:
                    self.lAvailableCols[side] = set()
                
    def kid(self, data, side= -1, op = None, literal= None, suppX= None, missX=None):
        kid = self.copy()
        kid.update(data, side, op, literal, suppX, missX)
        return kid
            
    def copy(self):
        r = Redescription(self.queries[0].copy(), self.queries[1].copy(), \
                             self.sParts.supparts(), self.sParts.N, self.probas())
        for side in [0,1]:
            if self.lAvailableCols[side] is not None:
                r.lAvailableCols[side] = set(self.lAvailableCols[side])
        r.status = self.status
        r.track = list(self.track)
        return r

    def recomputeQuery(self, side, data= None):
        return self.queries[side].recompute(side, data)
    
    def invLiteralsSide(self, side):
        return self.queries[side].invLiterals()

    def invLiterals(self):
        return [self.invLiteralsSide(0), self.invLiteralsSide(1)]
    
    def invColsSide(self, side):
        return self.queries[side].invCols()

    def invCols(self):
        return [self.invColsSide(0), self.invColsSide(1)]

    def recompute(self, data):
        (nsuppL, missL) = self.recomputeQuery(0, data)
        (nsuppR, missR) = self.recomputeQuery(1, data)
#        print self.disp()
#        print ' '.join(map(str, nsuppL)) + ' \t' + ' '.join(map(str, nsuppR))
        if len(missL) + len(missR) > 0:
            self.sParts = SParts(data.N, [nsuppL, nsuppR, missL, missR])
        else:
            self.sParts = SParts(data.N, [nsuppL, nsuppR])
        self.prs = [self.queries[0].proba(0, data), self.queries[1].proba(1, data)]
        self.dict_supp_info = None
    
    def check(self, data):
        result = 0
        details = None
        if self.sParts is not None:
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

    def getQueryLU(self, details=None):
        if details.has_key('names'):
            return self.queries[0].dispU(details['names'][0])
        return ""
    
    def getQueryRU(self, details=None):
        if details.has_key('names'):
            return self.queries[1].dispU(details['names'][1])
        return ""
    def getAcc(self, details=None):
        return round(self.acc(), 3)

    def getTrackStr(self, details=None):
        return ";".join(["%s:%s" % (t[0], ",".join(map(str,t[1:]))) for t in self.track])

    def getTrack(self, details=None):
        return self.track

    def getEnabled(self, details=None):
        return 1*(self.status>0)

    def getStatus(self, details=None):
        return self.status

    def flipEnabled(self):
        self.status = -self.status

    def setEnabled(self):
        self.status = 1
    def setDisabled(self):
        self.status = -1

    def setDiscarded(self):
        self.status = -2

    def getPVal(self, details):
        return round(self.pVal(), 3)

    def getSupp(self, details):
        return len(self.suppI())


##### PRINTING AND PARSING METHODS
    #### FROM HERE ALL PRINTING AND READING
    def __str__(self):
        str_av = ["?", "?"]
        for side in [0,1]:
            if self.availableColsSide(side) is not None:
                str_av[side] = "%d" % len(self.availableColsSide(side))
        return ('%s + %s terms:' % tuple(str_av)) + ('\t (%i): %s\t%s' % (len(self), self.disp(), self.getTrackStr()))

    def dispQueries(self, names= [None, None], lenIndex=0):
        return self.queries[0].disp(names[0], lenIndex) +"\t"+ self.queries[1].disp(names[1], lenIndex)

    def dispQueriesTex(self, names= [None, None], lenField=0):
        if lenField > 0:
            return string.ljust(self.queries[0].dispTex(names[0]), lenField)[:lenField] + "\t" + string.ljust(self.queries[1].dispTex(names[1]), lenField)[:lenField]
        return self.queries[0].dispTex(names[0]) +"\t"+ self.queries[1].dispTex(names[1])

    def dispQueriesU(self, names= [None, None], lenField=0):
        if lenField > 0:
            return string.ljust(self.queries[0].dispU(names[0]), lenField)[:lenField] + "\t" + string.ljust(self.queries[1].dispU(names[1]), lenField)[:lenField]
        return self.queries[0].dispU(names[0]) +"\t"+ self.queries[1].dispU(names[1])

    def dispTexPrelude():
        return "" + \
        "\\documentclass{article}\n"+ \
        "\\usepackage{amsmath}\n"+ \
        "\\usepackage{amsfonts}\n"+ \
        "\\usepackage{amssymb}\n"+ \
        "\\usepackage{booktabs}\n"+ \
        "\\usepackage[mathletters]{ucs}\n"+ \
        "\\usepackage[utf8x]{inputenc}\n"+ \
        "\\newcommand{\\iLHS}{\\mathbf{L}} % index for left hand side\n"+ \
        "\\newcommand{\\iRHS}{\\mathbf{R}} % index for right hand side\n"+ \
        "\\newcommand{\\pValue}{$p$\\nobreakdash-\\hspace{0pt}value}\n"+ \
        "\\DeclareMathOperator*{\\jacc}{J}\n"+ \
        "\\DeclareMathOperator*{\\supp}{supp}\n"+ \
        "\\begin{document}\n"+ \
        "\\begin{table}[h]\n"+ \
        "\\scriptsize\n" + \
        "\\begin{tabular}{@{\\hspace*{1ex}}p{0.027\\textwidth}@{}p{0.35\\textwidth}@{\\hspace*{1em}}p{0.4\\textwidth}@{\\hspace*{1em}}rrr@{\\hspace*{0.5ex}}}\n" + \
        "\\toprule\n" + \
        " & $q_\\iLHS$ & $q_\\iRHS$ & $\\jacc(R)$ & $\\supp(R)$ & \\pValue \\\\\n" + \
        "\\midrule"
    dispTexPrelude = staticmethod(dispTexPrelude)
    
    def dispTexConc():
        return ""+ \
        "\\bottomrule"+ \
        "\\end{tabular}\n"+ \
        "\\end{table}\n"+ \
        "\\end{document}"
    dispTexConc = staticmethod(dispTexConc)

    def dispTexHeader():
        return ' & $q_\iLHS$ & $q_\iRHS$ & $\\jacc$ & $\\supp$ & \\pValue  \\\\'
    dispTexHeader = staticmethod(dispTexHeader)

    def dispTexLine(self, queryId, names = [None, None]):
        queryidStr = '(%i)' % queryId
        format_list = []
        return queryidStr + ' & ' + self.queries[0].dispTex(names[0])+' & '+self.queries[1].dispTex(names[1])+ ' & ' +self.dispCaracteristiquesTex()+' \\\\'

    def dispLPartsSimple(self):
        info_tmp = self.getInfoDict()
        return " ".join([str(info_tmp.get(info_key, "-")) for info_key in Redescription.print_info])
        
    def dispLParts(self): 
        info_tmp = self.getInfoDict()
        return " ".join(["%s:%s" % (info_key, info_tmp.get(info_key, "-")) for info_key in Redescription.print_info])

    def dispCaracteristiquesTex(self):
        info_tmp = self.getInfoDict()
        details = []
        for (info_key, info_round, info_format) in Redescription.print_info_tex:
            tmp = "-"
            if info_tmp.has_key(info_key):
                tmp = info_format % round(info_tmp[info_key], info_round)
            details.append(tmp)
            
        return " & ".join(details)

    def dispCaracteristiquesSimple(self):
        return self.dispLPartsSimple()

    def dispU(self, names= [None, None], lenIndex=0):
        str_red = self.dispQueriesU(names, lenIndex) +"\t"+ self.dispLPartsSimple()
        return str_red

    def disp(self, names= [None, None], lenIndex=0):
        return self.dispQueries(names, lenIndex) +"\t"+ self.dispLPartsSimple()
        
    def dispSupp(self):
        return self.sParts.dispSupp()
    
    def write(self, output, suppOutput):
        output.write(self.disp()+'\n')
        output.flush()
        if suppOutput is not None:
            suppOutput.write(self.sParts.dispSupp()+'\n')
            suppOutput.flush()

    def fromXML(self, node):
        self.queries = [None, None]
        dsi = {}
        for query_data in node.getElementsByTagName("query"):
            side = toolRead.getTagData(query_data, "side", int)
            if side not in [0,1]:
                print "Unknown side (%s)!" % side
            else:
                query_tmp = toolRead.getTagData(query_data, "ids_expression")
                self.queries[side] = Query.parse(query_tmp)
        supp_tmp = node.getElementsByTagName("support")
        self.track = [tuple([0] + sorted(self.queries[0].invCols())), tuple([1] + sorted(self.queries[1].invCols()))]
        if len(supp_tmp) == 1:
            for child in toolRead.children(supp_tmp[0]):
                if toolRead.isElementNode(child):
                    supp_key = toolRead.tagName(child)
                    supp_val = None
                    if child.hasChildNodes():
                        supp_val = toolRead.getValues(child, int, "row")
                    else:
                        supp_val = toolRead.getValue(child, float)
                    if supp_val is not None:
                        dsi[supp_key] = supp_val
            if sum([len(dsi.get(i, [])) for i in SParts.labels]):
                self.sParts = SParts(dsi)
            else:
                self.sParts = None
            self.dict_supp_info = dsi

    def toXML(self, full=True, names= [None, None]):
        strd = "<redescription>\n"

        for side in [0,1]:
            strd += "\t<query>\n"
            strd += "\t\t<side>%d</side>\n" % side
            strd += "\t\t<ids_expression><![CDATA[\"%s\"]]></ids_expression>\n" % self.queries[side].disp()
            if names[side] is not None:
                strd += "\t\t<names_expression><![CDATA[\"%s\"]]></names_expression>\n" % self.queries[side].disp(names[side])
            strd += "\t</query>\n"
        
        strd += "\t<support>\n"
        tmp_info = self.getInfoDict()
        if full:
            keys = Redescription.print_info_full
        else:
            keys = Redescription.print_info
        for supp_key in keys:
            if tmp_info.has_key(supp_key):
                supp_val = tmp_info[supp_key]
                if type(supp_val) in [list, set]:
                    strd += "\t\t<%s>\n" % supp_key
                    for row in supp_val:
                        strd += "\t\t\t<row>%d</row>\n" % row
                        strd += "\t\t</%s>\n" % supp_key
                else:
                    strd += "\t\t<%s><value>%s</value></%s>\n" % (supp_key, supp_val, supp_key)
        strd += "\t</support>\n"        
        strd += "</redescription>\n"
        return strd
    
    def parseQueries(string):
        parts = string.rsplit('\t')
        if len(parts) >= 2:
            if parts[0].startswith('('):
                queryL = CWQuery.parse(parts[0])
                queryR = CWQuery.parse(parts[1])
            else:
                queryL = Query.parse(parts[0])
                queryR = Query.parse(parts[1])
        else:
            queryL = Query()
            queryR = Query()

        if len(parts) >= 3:
            lpartsList = {}
            info_parts = parts[2].split(" ")
            for info_part in info_parts:
                tmp = info_part.split(":")
                if len(tmp) == 2:
                    lpartsList[tmp[0]] = float(tmp[1])
        else:
            lpartsList = None
        return (queryL, queryR, lpartsList)
    parseQueries = staticmethod(parseQueries)

    def parse(stringQueries, stringSupport = None, data = None):
        (queryL, queryR, lpartsList) = Redescription.parseQueries(stringQueries)

        r = None
        if data is not None and stringSupport is not None and type(stringSupport) == str and re.search('\t', stringSupport) :
            supportsS = SParts.parseSupport(stringSupport, data.N)
            if supportsS is not None:
                r = Redescription(queryL, queryR, supportsS.supparts(), data.nbRows(), [set(),set()], [ queryL.proba(0, data), queryR.proba(1, data)])

                tmp = r.getInfoDict()
                for key in lpartsList.keys():
                    if tmp.get(key, None) != lpartsList[key]:
                        raise Warning("Something wrong in the supports ! (%s: %s ~ %s)\n" \
                                  % (key, tmp.get(key, None), lpartsList[key]))
        if r is None:
            r = Redescription(queryL, queryR)
            r.supp_info = lpartsList
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

