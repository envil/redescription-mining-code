import re, string, numpy, codecs
from classCol import  ColM
from classQuery import  *
from classSParts import  SParts, tool_pValSupp, tool_pValOver, tool_ratio, SSetts
from classProps import WithEVals, RedProps, mapSuppNames, ACTIVE_RSET_ID, HAND_SIDE
import pdb


class Redescription(WithEVals):
    diff_score = Query.diff_length + 1
    
    ### PROPS WHAT
    info_what_dets = {}
    # info_what_dets = {"queryLHS": "self.prepareQueryLHS",
    #                   "queryRHS": "self.prepareQueryRHS",
    #                   "queryCOND": "self.prepareQueryCOND"}
    info_what = {"nbAvC": "self.nbAvailableCols()", "diffLengthQs": "self.diffLengthQs()",
                 "containsAnon": "self.containsAnon()", "isTreeCompatible" : "self.isTreeCompatible()",
                 "isBasis": "self.isBasis()"} #"track": "self.getTrack()", "status_enabled": "self.getStatus()"}
    Pwhat_match = "("+ "|".join(["extra"]+info_what.keys()+info_what_dets.keys()) +")"


    pair_map_side = {"L": 0, "R": 1}
    pair_map_how = {"areaU": "union", "areaI": "inter", "areaR": "ratio", "areaF": "fractmin", "overlap": "ratio",
                    "rowsU": ("rows", "union"), "rowsI": ("rows", "inter"), "rowsR": ("rows", "ratio"), "rowsF": ("rows", "fractmin")}
    info_pair_what_dets = {"oneSideIdentical": "self.oneSideIdentical", "bothSidesIdentical": "self.bothSidesIdentical",
                           "equivalent": "self.equivalent", "identical": "self.identical", "compare": "self.compare",
                           "sameRectangles": "self.sameRectangles",
                           "overlapAreaTotal": "self.overlapAreaTotal", "overlapAreaMax": "self.overlapAreaMax",
                           "overlapRows": "self.overlapRows"}
    info_pair_what_side = {"interAreaSide": "self.interArea", "unionAreaSide": "self.unionArea", "overlapAreaSide": "self.overlapAreaSide"}
    Pwhat_pair_match = "("+ "|".join(pair_map_how.keys()+info_pair_what_side.keys()+info_pair_what_dets.keys()) +")"

    class_letter = "r"
    RP = None
    @classmethod
    def setupRP(tcl, fields_fns=None):
        elems_typs = [(Query.class_letter, Query), (SParts.class_letter, SParts), (Redescription.class_letter, Redescription)]
        RedProps.setupProps(Query, Redescription, elems_typs)
        tcl.RP = RedProps(fields_fns)
    ### getRP(tcl, rp=None) is defined in WithEVals class 

    
    def __init__(self, nqueryL=None, nqueryR=None, nsupps = None, nN = -1, nPrs = [-1,-1], ssetts=None, iid=None):
        WithEVals.__init__(self, iid)
        if nqueryL is None: nqueryL = Query()
        if nqueryR is None: nqueryR = Query()
        self.queries = [nqueryL, nqueryR]
        if nsupps is not None:
            self.sParts = SParts(ssetts, nN, nsupps, nPrs)
            self.dict_supp_info = None
        else:
            self.sParts = None
            self.dict_supp_info = {}
        self.lAvailableCols = [None, None]
        self.extras["status"] = 1
        self.extras["track"] = []
        self.condition = None

    @classmethod
    def fromInitialPair(tcl, initialPair, data, dt={}):
        if initialPair[0] is None and initialPair[1] is None:
            return None
        supps_miss = [set(), set(), set(), set()]
        queries = [None, None]
        for side in [0,1]:
            suppS, missS = (set(), set())
            if type(initialPair[side]) is Query:
                queries[side] = initialPair[side]
                suppS, missS = initialPair[side].recompute(side, data)
            else:
                queries[side] = Query()
                if type(initialPair[side]) is Literal:
                    queries[side].extend(None, initialPair[side])                
                    suppS, missS = data.literalSuppMiss(side, initialPair[side])
            supps_miss[side] = suppS
            supps_miss[side+2] = missS

        r = tcl(queries[0], queries[1], supps_miss, data.nbRows(), [len(supps_miss[0])/float(data.nbRows()),len(supps_miss[1])/float(data.nbRows())], data.getSSetts())
        r.setTrack([(-1, -1)])

        if dt.get("litC") is not None:
            litC = dt["litC"]
            if type(litC) is list:
                # if len(litC) > 1: pdb.set_trace()
                qC = Query(OR=False, buk=litC) 
            else:                
                qC = Query(buk=[litC])                
            supp_cond, miss_cond = qC.recompute(-1, data)
            r.setCondition(qC, supp_cond)
        WithEVals.recompute(r, data)
        return r

    @classmethod
    def fromQueriesPair(tcl, queries, data):
        r = tcl(queries[0].copy(), queries[1].copy())
        r.recompute(data)        
        r.setTrack([tuple([0] + sorted(r.queries[0].invCols())), tuple([1] + sorted(r.queries[1].invCols()))])
        if len(queries) > 2 and queries[2] is not None:
            qC = queries[2]
            supp_cond, miss_cond = qC.recompute(-1, data)
            r.setCondition(qC, supp_cond)            
        return r

    @classmethod
    def fromCol(tcl, col, data):
        queries = [Query(), Query()]
        track = []
        if isinstance(col, ColM):
            queries[col.getSide()].extend(-1, Literal(False, col.getAnonTerm()))
            track.append((col.getSide(), col.getId()))
        r = tcl(queries[0], queries[1])
        r.recompute(data)        
        r.setTrack(track)
        return r
    
    def isBasis(self):        
        return (len(self.query(0)) == 0 and self.query(1).isBasis()) or \
               (len(self.query(1)) == 0 and self.query(0).isBasis())
    def containsAnon(self, side=None):
        if side is None:
            return self.query(0).containsAnon() or self.query(1).containsAnon()
        else:
            return self.query(side).containsAnon()
    def minusAnon(self, side=None):
        if side is None:
            q0noan, l0an = self.query(0).minusAnon()
            q1noan, l1an = self.query(1).minusAnon()
            return [q0noan, q1noan], [l0an, l1an]
        else:
            return self.query(side).minusAnon()
    def minusAnonRed(self, data):
        r, modr = self, 0
        if len(self) == 0:
            return r, [[],[]], modr 
        qsNoan, lsAnon = self.minusAnon()
        if (len(lsAnon[0]) + len(lsAnon[1])) > 0: ### NO anon, standard list of one-step extensions
            if (len(qsNoan[0]) + len(qsNoan[1])) == 0: ### only anon, need to start by mining pairs...
                modr = -1
                r = Redescription()
            else:
                modr = 1
                r = Redescription.fromQueriesPair(qsNoan, data)
        return r, lsAnon, modr
    
    def typeId(self):
        if self.isBasis():
            return self.query(0).typeId() or self.query(1).typeId()
        return None
    def dropSupport(self):
        if self.sParts is not None:
            self.dict_supp_info.toDict()
            self.sParts = None

    # def __hash__(self):
    #      return int(hash(self.queries[0])+ hash(self.queries[1])*100*self.score())
        
    def __len__(self):
        return self.length(0) + self.length(1)

    def usesOr(self, side=None):
        if side is not None:
            return self.queries[side].usesOr()
        return self.queries[0].usesOr() or self.queries[1].usesOr()
    def isTreeCompatible(self, side=None):
        if side is not None:
            return self.queries[side].isTreeCompatible()
        return self.queries[0].isTreeCompatible() and self.queries[1].isTreeCompatible()
            
    def supp(self, side, rset_det=None):
        if rset_det is None:
            return self.supports().supp(side)
        set_parts = self.getRSetParts(rset_det)
        if set_parts is not None:
            return set_parts.supp(side)
        
    def miss(self, side, rset_det=None):
        if rset_det is None:
            return self.supports().miss(side)
        set_parts = self.getRSetParts(rset_det)
        if set_parts is not None:
            return set_parts.miss(side)
            
    def score(self, rset_det=None):
        return self.getAcc(rset_det)

    def supports(self):
        return self.sParts

    def nbRows(self):
        return self.supports().nbRows()
    def rows(self):
        return set(range(self.nbRows()))
    
    def partsAll(self):
        return self.supports().sParts

    def partsFour(self):
        return [self.supports().suppA(), self.supports().suppB(), self.supports().suppI(), self.supports().suppO()]

    def partsThree(self):
        return [self.supports().suppA(), self.supports().suppB(), self.supports().suppI()]
    
    def partsNoMiss(self):
        return self.supports().sParts[:4]
    
    def query(self, side=None):
        if side == -1:
            return self.getQueryC()
        return self.queries[side]

    def getQueries(self):
        return self.queries

    def getQueryC(self):
        if self.condition is not None:
            return self.condition.get("q")
    def getSupportsC(self):
        if self.condition is not None:
            return self.condition.get("sparts")
    def getSuppC(self):
        if self.condition is not None:
            return self.condition.get("supp")

    def hasCondition(self):
        return self.condition is not None
    def setCondition(self, qC=None, supp_cond=None): ### here
        self.condition = None
        if qC is not None:
            if supp_cond is None:
                sparts = None
            else:
                sparts = self.supports().copy()
                sparts.update(0, False, supp_cond)
                sparts.update(1, False, supp_cond)
            self.condition = {"q": qC, "supp": supp_cond, "sparts": sparts}
    
    def probas(self):
        return self.supports().probas()

    def probasME(self, dbPrs, epsilon=0):
        return [self.queries[side].probaME(dbPrs, side, epsilon) for side in [0,1]]

    def surpriseME(self, dbPrs, epsilon=0):
        #return [-numpy.sum(numpy.log(numpy.absolute(SParts.suppVect(self.supports().nbRows(), self.supports().suppSide(side), 0) - self.queries[side].probaME(dbPrs, side)))) for side in [0,1]]
        return -numpy.sum(numpy.log(numpy.absolute(SParts.suppVect(self.supports().nbRows(), self.supports().suppI(), 0) - self.queries[0].probaME(dbPrs, 0)*self.queries[1].probaME(dbPrs, 1))))

    def exME(self, dbPrs, epsilon=0):
        prs = [self.queries[side].probaME(dbPrs, side, epsilon) for side in [0,1]]
        surprises = []
        tmp = [i for i in self.supports().suppI() if prs[0][i]*prs[1][i] == 0]
        surprises.append(-numpy.sum(numpy.log([prs[0][i]*prs[1][i] for i in self.supports().suppI()])))
        surprises.extend([-numpy.sum(numpy.log([prs[side][i] for i in self.supports().suppSide(side)])) for side in [0,1]])

        return surprises + [len(tmp) > 0]

        N = self.supports().nbRows()
        margsPr = [numpy.sum([prs[side][i] for i in self.supports().suppSide(side)]) for side in [0,1]]
        pvals = [tool_pValOver(self.supports().lenI(), N, int(margsPr[0]), int(margsPr[1])), tool_pValSupp(N, self.supports().lenI(), margsPr[0]*margsPr[1]/N**2)]
        return surprises, pvals
    
    def length(self, side):
        return len(self.queries[side])
    def diffLengthQs(self):
        return abs(self.length(0) - self.length(1))
    
    def prepareExtElems(self, data=None, single_dataset=False):
        r, lsAnon, modr = self.minusAnonRed(data)
        if modr != 0:
            for side, lits in enumerate(lsAnon):
                if len(lits) > 0 or modr == 1:
                    still_available=[l[1].colId() for l in lits]
                else:
                    still_available=None
                r.restrictAvailable(side, self.lAvailableCols[side], still_available)
        exts = []
        if modr == -1:
            for vLHS in r.lAvailableCols[0]:
                for vRHS in r.lAvailableCols[1]:
                    if (not single_dataset or vLHS != vRHS) and (not data.hasGroups(0) or not data.hasGroups(1) or data.areGroupCompat(vLHS, vRHS, 0, 1)):
                        exts.append((0, vLHS, data.col(1, vRHS)))
        elif len(r) > 0:
            for side in [0,1]:
                exts.extend([(side, v, r) for v in r.availableColsSide(side, data, single_dataset)])
        # print "EXTS", exts, self.disp(), r.disp()
        return exts, r, modr
    
    def availableColsSide(self, side, data=None, single_dataset=False, check_empty=True):
        if self.lAvailableCols[side] is not None and (not check_empty or self.length(1-side) != 0):
            tt = set(self.lAvailableCols[side])
            if single_dataset:
                tt &= set(self.lAvailableCols[1-side])
            if data is not None:
                for ss in [0,1]:
                    if data.hasGroups(ss):
                        for c in self.queries[ss].invCols():
                            tt = [t for t in tt if data.areGroupCompat(t, c, side, ss)]
            return tt
        return set() 
    def nbAvailableCols(self):
        if self.lAvailableCols[0] is not None and self.lAvailableCols[1] is not None:
            return len(self.lAvailableCols[0]) + len(self.lAvailableCols[1])
        return -1
    def updateAvailable(self, souvenirs):
        for side in [0, 1]:
            if self.lAvailableCols[side] is None:
                self.lAvailableCols[side] =  set(souvenirs.availableMo[side])
            self.lAvailableCols[side].difference_update(souvenirs.extOneStep(self, side))
    def restrictAvailable(self, side=None, org_available=None, still_available=None, not_available=None):
        if side is None:
            if still_available is None:
                still_available = [None, None]
            if org_available is None:
                org_available = [None, None]
            if not_available is None:
                not_available = [None, None]
            for side in [0,1]:
                self.restrictAvailable(side, org_available[side], still_available[side], not_available[side])
        else:
            if org_available is not None:
                if still_available is not None:
                    self.lAvailableCols[side] = org_available.intersection(still_available)
                else:
                    self.lAvailableCols[side] = set(org_available)
                if not_available is not None:
                    self.lAvailableCols[side].difference_update(not_available)

    def removeAvailables(self):
        self.lAvailableCols = [set(),set()]
            
    def update(self, data=None, side= -1, opBool = None, literal= None, suppX=None, missX=None):
        if side == -1 :
            self.removeAvailables()
        else:
            op = Op(opBool)
            self.queries[side].extend(op, literal)
            self.supports().update(side, op.isOr(), suppX, missX)
            self.dict_supp_info = None
            if self.lAvailableCols[side] is not None:
                self.lAvailableCols[side].remove(literal.colId())
            self.appendTrack(((1-side) * 1-2*int(op.isOr()), literal.colId()))

    def setFull(self, max_var=None):
        if max_var is not None:
            for side in [0,1]:
                if self.length(side) >= max_var[side]:
                    self.lAvailableCols[side] = set()
                
    def kid(self, data, side= -1, op = None, literal= None, suppX= None, missX=None):
        kid = self.copy()        
        kid.update(data, side, op, literal, suppX, missX)
        return kid
            
    def copy(self, iid=None):
        r = Redescription(self.queries[0].copy(), self.queries[1].copy(), \
                             self.supports().supparts(), self.supports().nbRows(), self.probas(), self.supports().getSSetts(), iid=iid)
        for side in [0,1]:
            if self.lAvailableCols[side] is not None:
                r.lAvailableCols[side] = set(self.lAvailableCols[side])
        r.extras = self.copyExtras()
        r.restricted_sets = {}
        for sid, rst in self.restricted_sets.items():
            r.restricted_sets[sid] = {"sParts": rst["sParts"],
                                         "prs": [rst["prs"][0], rst["prs"][1]],
                                         "rids": set(rst["rids"])}

        return r

    def recomputeQuery(self, side, data= None, restrict=None):
        return self.queries[side].recompute(side, data, restrict)
    
    def invLiteralsSide(self, side, ex_anon=False):
        return self.queries[side].invLiterals(ex_anon)

    def invLiterals(self, ex_anon=False):
        return [self.invLiteralsSide(0, ex_anon), self.invLiteralsSide(1, ex_anon)]
    
    def invColsSide(self, side, ex_anon=False):
        return self.queries[side].invCols(ex_anon)

    def invCols(self, ex_anon=False):
        return [self.invColsSide(0, ex_anon), self.invColsSide(1, ex_anon)]
                    
    def getNormalized(self, data=None, side=None):
        if side is not None:
            sides = [side]
        else:
            sides = [0,1]
        queries = [self.queries[side] for side in [0,1]]
        c = [False, False]
        for side in sides:
            queries[side], c[side] = self.queries[side].algNormalized()
        if c[0] or c[1]:
            red = Redescription.fromQueriesPair(queries, data)
            ### check that support is same
            # if self.supports() != red.supports():
            #     print "ERROR ! SUPPORT CHANGED WHEN NORMALIZING..."
            #     pdb.set_trace()
            return red, True            
        else:
            return self, False

    def getPruned(self, data):
        r, modr = self, False
        best_score = self.score()
        for side in [0,1]:
            if self.length(side) > 1:
                queries = [self.query(0), self.query(1)]
                for (ls, q) in self.query(side).minusOneLiteral():	
                    queries[side] = q
                    cand = Redescription.fromQueriesPair(queries, data)
                    if cand.score() >= best_score:
                        r, modr, best_score = (cand, True, cand.score())
        if modr:
            r, modb = r.getPruned(data)
        return r, modr

    def normalize(self, data=None):
        return self.getNormalized(data)
        
    def recompute(self, data):
        (nsuppL, missL) = self.recomputeQuery(0, data)
        (nsuppR, missR) = self.recomputeQuery(1, data)
#        print self.disp()
#        print ' '.join(map(str, nsuppL)) + ' \t' + ' '.join(map(str, nsuppR))
        if len(missL) + len(missR) > 0:
            self.sParts = SParts(data.getSSetts(), data.nbRows(), [nsuppL, nsuppR, missL, missR])
        else:
            self.sParts = SParts(data.getSSetts(), data.nbRows(), [nsuppL, nsuppR]) #TODO: recompute
        self.prs = [self.queries[0].proba(0, data), self.queries[1].proba(1, data)]
        if self.hasCondition():
            qC = self.getQueryC()
            supp_cond, miss_cond = qC.recompute(-1, data)
            self.setCondition(qC, supp_cond)                        
        self.dict_supp_info = None
        WithEVals.recompute(self, data)
        
    def check(self, data):
        result = 0
        details = None
        if self.supports() is not None: #TODO: sparts
            (nsuppL, missL) = self.recomputeQuery(0, data)
            (nsuppR, missR) = self.recomputeQuery(1, data)
            
            details = ( len(nsuppL.symmetric_difference(self.supports().supp(0))) == 0, \
                     len(nsuppR.symmetric_difference(self.supports().supp(1))) == 0, \
                     len(missL.symmetric_difference(self.supports().miss(0))) == 0, \
                     len(missR.symmetric_difference(self.supports().miss(1))) == 0 )        
            result = 1
            for detail in details:
                result*=detail
        return (result, details)

    def hasMissing(self):
        return self.supports().hasMissing()
        
    def getStatus(self):
        return self.extras["status"]
    def setStatus(self, status):
        self.extras["status"] = status
    def getEnabled(self, details={}):
        return 1*(self.getStatus()>0)
    def isEnabled(self, details={}):
        return self.getStatus()>0

    def flipEnabled(self):
        self.setStatus(-self.getStatus())

    def setEnabled(self):
        self.setStatus(1)
    def setDisabled(self):
        self.setStatus(-1)
    def setDiscarded(self):
        self.setStatus(-2)

    ##### GET FIELDS INFO INVOLVING ADDITIONAL DETAILS (PRIMARILY FOR SIREN)
    def getQueriesU(self, details={}):
        if details is not None and "names" in details:
            return self.queries[0].disp(details["names"][0], style="U") + "---" + self.queries[1].disp(details["names"][1], style="U")
        else:
            return self.queries[0].disp(style="U") + "---" + self.queries[1].disp(style="U")

    def getQueryLU(self, details={}):
        if details is not None and "names" in details:
            return self.queries[0].disp(details["names"][0], style="U") #, unicd=True)
        else:
            return self.queries[0].disp(style="U")

    def getQueryRU(self, details={}):
        if details is not None and "names" in details:
            return self.queries[1].disp(details["names"][1], style="U") #, unicd=True)
        else:
            return self.queries[1].disp(style="U")

    def setTrack(self, track=[]):
        self.extras["track"] = track
    def appendTrack(self, t, p=None):
        if p is None:
            self.extras["track"].append(t)
        else:
            self.extras["track"].insert(p,t)
    def extendTrack(self, track=[]):
        self.extras["track"].extend(track)

    def getTrack(self, details={}):
        if details is not None and ( details.get("aim", None) == "list" or details.get("format", None) == "str"):
            return ";".join(["%s:%s" % (t[0], ",".join(map(str,t[1:]))) for t in self.getTrack()])
        else:
            return self.extras["track"]

    def getSortAble(self, details={}):
        if details is not None and details.get("aim") == "sort":
            return (self.getStatus(), self.getUid())
        return ""
        
    # def getCohesion(self, details={}):
    #     return self.getDetail("cohesion")
    # def getCohesionNat(self, details={}):
    #     return self.getDetail("cohesion_nat")

    def getTypeParts(self, details={}):
        return self.supports().getTypeParts()
    def getMethodPVal(self, details={}):
        return self.supports().getMethodPVal()    


    ##### RESTRICTED SETS        
    def setRestrictedSuppSets(self, data, supp_sets=None):
        resets_ids = []
        if supp_sets is None:
            if data.hasLT():
                supp_sets = data.getLT()
            else:
                supp_sets = {ACTIVE_RSET_ID: data.nonselectedRows()}
        for sid, sset in supp_sets.items():
            old_rids = None
            if sid in self.restricted_sets:
                old_rids = self.restricted_sets[sid]["rids"]
            if len(sset) == 0:
                if sid not in self.restricted_sets or len(self.restricted_sets[sid]["rids"]) > 0:
                    resets_ids.append(sid)                    
                self.restricted_sets[sid] = {"sParts": None,
                                             "prs": None,
                                             "rids": set()}

            elif sid not in self.restricted_sets or self.restricted_sets[sid]["rids"] != sset:
                (nsuppL, missL) = self.recomputeQuery(0, data, sset)
                (nsuppR, missR) = self.recomputeQuery(1, data, sset)
                if len(missL) + len(missR) > 0:
                    rsParts = SParts(data.getSSetts(), sset, [nsuppL, nsuppR, missL, missR])
                else:
                    rsParts = SParts(data.getSSetts(), sset, [nsuppL, nsuppR])

                self.restricted_sets[sid] = {"sParts": rsParts,
                                             "prs": [self.queries[0].proba(0, data, sset),
                                                     self.queries[1].proba(1, data, sset)],
                                             "rids": set(sset)}
                resets_ids.append(sid)
                
        if len(resets_ids) > 0:
            self.dict_supp_info = None
            return True
        return False
           
    def getRSet(self, details={}):
        if type(details) is dict:
            rset_id = details.get("rset_id")
        else:
            rset_id = details
        if rset_id is not None:
            if rset_id == "cond" and self.hasCondition():
                return {"sParts": self.getSupportsC()}
            elif rset_id in self.restricted_sets:
                return self.restricted_sets[rset_id]
            elif rset_id == "all" or rset_id == ACTIVE_RSET_ID:
                return {"sParts": self.supports()}
            return None
        # elif ACTIVE_RSET_ID in self.restricted_sets:
        #     return self.restricted_sets[ACTIVE_RSET_ID]
        else:            
            return {"sParts": self.supports()}
    def getRSetParts(self, details={}):
        rset = self.getRSet(details)
        if rset is not None:
            return rset.get("sParts")
       
    def getRSetABCD(self, details={}):
        ssp = self.getRSetParts(details)
        if ssp is not None:
            return ssp.get("sParts").getVectorABCD(force_list=True, rest_ids=ssp.get("rids"))
        
    def getAccRatio(self, details={}):
        if details is not None and (details.get("rset_id_num") in self.restricted_sets \
               or details.get("rset_id_den") in self.restricted_sets):
            acc_num = self.getRSetParts(details.get("rset_id_num")).acc()
            acc_den = self.getRSetParts(details.get("rset_id_den")).acc()
            return tool_ratio(acc_num, acc_den)
        return 1.

    def getLenRatio(self, details={}):
        if details is not None and (details.get("rset_id_num") in self.restricted_sets \
               or details.get("rset_id_den") in self.restricted_sets):
            len_num = self.getRSetParts(details.get("rset_id_num")).lenI()
            len_den = self.getRSetParts(details.get("rset_id_den")).lenI()
            return tool_ratio(len_num, len_den)
        return 1.
    
    def getAcc(self, details={}):
        return self.getRSetParts(details).acc()
    def getPVal(self, details={}):
        return self.getRSetParts(details).pVal()

    def getLenP(self, details={}):
        if "part_id" in details:
            return self.getRSetParts(details).lenP(details["part_id"])
        return -1

    def getLenI(self, details={}):
        return self.getRSetParts(details).lenI()
    def getLenU(self, details={}):
        return self.getRSetParts(details).lenU()
    def getLenL(self, details={}):
        return self.getRSetParts(details).lenL()
    def getLenR(self, details={}):
        return self.getRSetParts(details).lenR()
    def getLenO(self, details={}):
        return self.getRSetParts(details).lenO()
    def getLenN(self, details={}):
        return self.getRSetParts(details).lenN()
    def getLenA(self, details={}):
        return self.getRSetParts(details).lenA()
    def getLenB(self, details={}):
        return self.getRSetParts(details).lenB()
    
    def getSuppI(self, details={}):
        return self.getRSetParts(details).suppI()
    def getSuppU(self, details={}):
        return self.getRSetParts(details).suppU()
    def getSuppL(self, details={}):
        return self.getRSetParts(details).suppL()
    def getSuppR(self, details={}):
        return self.getRSetParts(details).suppR()
    def getSuppO(self, details={}):
        return self.getRSetParts(details).suppO()
    def getSuppN(self, details={}):
        return self.getRSetParts(details).suppN()
    def getSuppA(self, details={}):
        return self.getRSetParts(details).suppA()
    def getSuppB(self, details={}):
        return self.getRSetParts(details).suppB()
    
    def getArea(self, which="I", rset_id=None, details={}):
        if which == "L" or which == "R" or which == "A" or which == "B":
            if which == "A":
                side, which_supp = "LHS", "I"
            elif which == "B":
                side, which_supp = "RHS", "I"
            else:
                side, which_supp = which+"HS", which
            lq = self.getQueryProp("len", which="q", rset_id=side, details=details)
            lsupp = self.getSPartsProp("area", which=which_supp, rset_id=rset_id, details=details)
            return lq*lsupp
        if which == "I" or which == "U":
            lqLHS = self.getQueryProp("len", which="q", rset_id="LHS", details=details)
            lqRHS = self.getQueryProp("len", which="q", rset_id="RHS", details=details)
            lsupp = self.getSPartsProp("area", which=which, rset_id=rset_id, details=details)
            return (lqLHS+lqRHS)*lsupp
        if which == "P":
            lqLHS = self.getQueryProp("len", which="q", rset_id="LHS", details=details)
            lqRHS = self.getQueryProp("len", which="q", rset_id="RHS", details=details)
            lsuppLHS = self.getSPartsProp("area", which="L", rset_id=rset_id, details=details)
            lsuppRHS = self.getSPartsProp("area", which="R", rset_id=rset_id, details=details)
            return lqLHS*lsuppLHS+lqRHS*lsuppRHS
        return -1
    def getQueryProp(self, what, which=None, rset_id=None, details={}):
        if Query.hasPropWhat(what) and rset_id in HAND_SIDE:
            if type(HAND_SIDE[rset_id]) is int:
                q = self.query(HAND_SIDE[rset_id])            
                if q is not None:
                    dts = {"side": HAND_SIDE[rset_id]}
                    if details is not None:
                        dts.update(details)
                    return q.getProp(what, which, dts)
            else:
                sides = HAND_SIDE[rset_id] or [0, 1]
                xps = self.getQueryProp(what, which, rset_id=sides[0], details=details)
                for side in sides[1:]:
                    if type(xps) is set:
                        xps.update(self.getQueryProp(what, which, rset_id=side, details=details))
                    else:
                        xps += self.getQueryProp(what, which, rset_id=side, details=details)
                return xps
    def getSPartsProp(self, what, which=None, rset_id=None, details={}):
        if SParts.hasPropWhat(what): ### info from supp parts
            rset_parts = self.getRSetParts(rset_id)
            if rset_parts is None:
                return None
            prp = rset_parts.getProp(what, which)
            if what == "supp" or what == "set":
                return mapSuppNames(prp, details)            
            return prp
        
    def getRidsProp(self, what, which=None, rset_id=None, details={}):
        if rset_id is not None and which == self.which_rids: ### ids details for split sets            
            rset_ids = self.getRestrictedRids(rset_id)
            if rset_ids is None:
                return None
            if what == "len" or what == "card":
                return len(rset_ids)
            elif what == "supp" or what == "set":
                return mapSuppNames(rset_ids, details)
            elif what == "perc":
                return tool_ratio(100.*len(rset_ids), self.nbRows())
            elif what == "ratio":
                return tool_ratio(len(rset_ids), self.nbRows())
           
    def getProp(self, what, which=None, rset_id=None, details={}):
        if what == "extra":
            return self.getExtra(which, details)
        if what == "area":
            return self.getArea(which, rset_id, details)
        if Query.hasPropWhat(what) and rset_id in HAND_SIDE:
            return self.getQueryProp(what, which, rset_id, details)
        if rset_id is not None and which == self.which_rids: ### ids details for split sets            
            return self.getRidsProp(what, which, rset_id, details)
        if SParts.hasPropWhat(what): ### info from supp parts
            return self.getSPartsProp(what, which, rset_id, details)
        elif what in Redescription.info_what_dets: ### other redescription info
            methode = eval(Redescription.info_what_dets[what])
            if callable(methode):
                return methode(details)
        elif what in Redescription.info_what: ### other redescription info
            return eval(Redescription.info_what[what])

    def getExpProp(self, exp, details={}):
        ws =self.getRP().getPrimitiveWs(exp)
        if ws[0] is not None:
            return self.getProp(ws[0], ws[1], ws[2], details)


    ###############################################        
    #### METHODS FOR COMPARING TWO REDESCRIPTIONS
    def compare(self, other, details={}):
        if self.score(details) > other.score(details):
            return Redescription.diff_score
        elif self.score(details) == other.score(details):
            return Query.comparePair(self.queries[0], self.queries[1], other.queries[0], other.queries[1])
        else:
            return -Redescription.diff_score

    def sameRectangles(self, other, details={}):
        return self.supp(0, details) == other.supp(0, details) and self.supp(1, details) != other.supp(1, details) and \
          self.invColsSide(0) != other.invColsSide(0) and self.invColsSide(1) != other.invColsSide(1)
    
    def interArea(self, other, side, details={}):
        if other is not None:
            return len(other.supp(side, details) & self.supp(side, details))* len(other.invColsSide(side) & self.invColsSide(side))
        return 0
    def unionArea(self, other, side, details={}):
        if other is not None:
            return len(other.supp(side, details) | self.supp(side, details))* len(other.invColsSide(side) | self.invColsSide(side))
        return 0
    def overlapAreaSide(self, other, side, details={}):
        if len(other.invColsSide(side) & self.invColsSide(side)) == 0:
            return 0
        areaU = self.unionArea(other, side, details)
        return tool_ratio(self.interArea(other, side, details), areaU)
    def overlapAreaTotal(self, other, details={}):
        areaUL = self.unionArea(other, 0, details)
        areaUR = self.unionArea(other, 1, details)
        return tool_ratio(self.interArea(other, 0) + self.interArea(other, 1),areaUL+areaUR)
    def overlapAreaMax(self, other, details={}):
        return max(self.overlapAreaSide(other, 0, details), self.overlapAreaSide(other, 1, details))

    def overlapRows(self, other, details={}):
        if other is not None:
            return tool_ratio(len(other.getSuppI(details) & self.getSuppI(details)), min(other.getLenI(details), self.getLenI(details)))
        return 0
    
    def oneSideIdentical(self, other, details={}):
        return self.queries[0] == other.queries[0] or self.queries[1] == other.queries[1]
    def bothSidesIdentical(self, other, details={}):
        return self.queries[0] == other.queries[0] and self.queries[1] == other.queries[1]

    def equivalent(self, other, details={}):
        return abs(self.compare(other, details)) < Query.diff_balance
    def identical(self, other, details={}):
        return (self.oneSideIdentical(other) and not self.equivalent(other)) or self.bothSidesIdentical(other)
   
    def getAreaPair(self, other, how="ratio", which="I", rset_id=None, details={}):
        rows = False
        if type(how) is tuple:
            rows = how[0] == "rows"
            how = how[1]
        if which == "L" or which == "R" or which == "A" or which == "B":
            if which == "A":
                side, which_supp = "LHS", "I"
            elif which == "B":
                side, which_supp = "RHS", "I"
            else:
                side, which_supp = which+"HS", which
            if rows:
                own_sq, other_sq = set([1]), set([1])
            else:
                own_sq = self.getQueryProp("Cset", which="q", rset_id=side, details=details)
                other_sq = other.getQueryProp("Cset", which="q", rset_id=side, details=details)
            own_ssupp = self.getSPartsProp("set", which=which_supp, rset_id=rset_id, details=details)
            other_ssupp = other.getSPartsProp("set", which=which_supp, rset_id=rset_id, details=details)
            if how == "inter":
                return len(own_sq & other_sq)* len(own_ssupp & other_ssupp)
            elif how == "union":
                return len(own_sq | other_sq)* len(own_ssupp | other_ssupp)
            elif how == "ratio":
                areaI = len(own_sq & other_sq)* len(own_ssupp & other_ssupp)
                areaU = len(own_sq | other_sq)* len(own_ssupp | other_ssupp)
                return tool_ratio(areaI, areaU)
            elif how == "fractmin":
                areaI = len(own_sq & other_sq)* len(own_ssupp & other_ssupp)
                areaU = min(len(own_sq)*len(own_ssupp), len(other_sq)*len(other_ssupp))
                return tool_ratio(areaI, areaU)

        if which == "I" or which == "U":
            if rows:
                own_sqLHS, own_sqRHS, other_sqLHS, other_sqRHS, = set([1]), set([1]), set([1]), set([1])
            else:
                own_sqLHS = self.getQueryProp("Cset", which="q", rset_id="LHS", details=details)
                own_sqRHS = self.getQueryProp("Cset", which="q", rset_id="RHS", details=details)
                other_sqLHS = other.getQueryProp("Cset", which="q", rset_id="LHS", details=details)
                other_sqRHS = other.getQueryProp("Cset", which="q", rset_id="RHS", details=details)
            own_ssupp = self.getSPartsProp("set", which=which, rset_id=rset_id, details=details)
            other_ssupp = other.getSPartsProp("set", which=which, rset_id=rset_id, details=details)
            if how == "inter":
                return (len(own_sqLHS & other_sqLHS)+len(own_sqRHS & other_sqRHS))*len(own_ssupp & other_ssupp)
            elif how == "union":
                return (len(own_sqLHS | other_sqLHS)+len(own_sqRHS | other_sqRHS))*len(own_ssupp | other_ssupp)
            elif how == "ratio":
                areaI = (len(own_sqLHS & other_sqLHS)+len(own_sqRHS & other_sqRHS))*len(own_ssupp & other_ssupp)
                areaU = (len(own_sqLHS | other_sqLHS)+len(own_sqRHS | other_sqRHS))*len(own_ssupp | other_ssupp)
                return tool_ratio(areaI, areaU)
            elif how == "fractmin":
                areaI = (len(own_sqLHS & other_sqLHS)+len(own_sqRHS & other_sqRHS))*len(own_ssupp & other_ssupp)
                areaU = min((len(own_sqLHS)+len(own_sqRHS))*len(own_ssupp),
                             (len(other_sqLHS)+len(other_sqRHS))*len(other_ssupp))
                return tool_ratio(areaI, areaU)

        if which == "P":
            if rows:
                own_sqLHS, own_sqRHS, other_sqLHS, other_sqRHS, = set([1]), set([1]), set([1]), set([1])
            else:
                own_sqLHS = self.getQueryProp("Cset", which="q", rset_id="LHS", details=details)
                own_sqRHS = self.getQueryProp("Cset", which="q", rset_id="RHS", details=details)
                other_sqLHS = other.getQueryProp("Cset", which="q", rset_id="LHS", details=details)
                other_sqRHS = other.getQueryProp("Cset", which="q", rset_id="RHS", details=details)
            own_ssuppLHS = self.getSPartsProp("set", which="L", rset_id=rset_id, details=details)
            own_ssuppRHS = self.getSPartsProp("set", which="R", rset_id=rset_id, details=details)
            other_ssuppLHS = other.getSPartsProp("set", which="L", rset_id=rset_id, details=details)
            other_ssuppRHS = other.getSPartsProp("set", which="R", rset_id=rset_id, details=details)
            if how == "inter":
                return len(own_sqLHS & other_sqLHS)*len(own_ssuppLHS & other_ssuppLHS) + \
                       len(own_sqRHS & other_sqRHS)*len(own_ssuppRHS & other_ssuppRHS)
            elif how == "union":
                return len(own_sqLHS | other_sqLHS)*len(own_ssuppLHS | other_ssuppLHS) + \
                       len(own_sqRHS | other_sqRHS)*len(own_ssuppRHS | other_ssuppRHS)
            elif how == "ratio":
                areaI = len(own_sqLHS & other_sqLHS)*len(own_ssuppLHS & other_ssuppLHS) + \
                       len(own_sqRHS & other_sqRHS)*len(own_ssuppRHS & other_ssuppRHS)
                areaU = len(own_sqLHS | other_sqLHS)*len(own_ssuppLHS | other_ssuppLHS) + \
                       len(own_sqRHS | other_sqRHS)*len(own_ssuppRHS | other_ssuppRHS)
                return tool_ratio(areaI, areaU)
            elif how == "fractmin":
                areaI = len(own_sqLHS & other_sqLHS)*len(own_ssuppLHS & other_ssuppLHS) + \
                       len(own_sqRHS & other_sqRHS)*len(own_ssuppRHS & other_ssuppRHS)
                areaU = min(len(own_sqLHS)*len(own_ssuppLHS)+len(own_sqRHS)*len(own_ssuppRHS),
                            len(other_sqLHS)*len(other_ssuppLHS)+len(other_sqRHS)*len(other_ssuppRHS))
                return tool_ratio(areaI, areaU)
        return -1
   
    def getPairProp(self, other, what, which=None, rset_id=None, details={}):
        if what in Redescription.pair_map_how:
            # xps = self.getAreaPair(other, Redescription.pair_map_how[what], which, rset_id, details)
            # print ">>>", self.disp()
            # print "<<<", other.disp()
            # x = self.overlapRows(other)
            # print what, which, rset_id, xps, x
            # return xps
            return self.getAreaPair(other, Redescription.pair_map_how[what], which, rset_id, details)

        if rset_id is not None and rset_id != "all":
            if details is None:                    
                details = {"rset_id": rset_id}
            else:
                details.update({"rset_id": rset_id})

        if what in Redescription.info_pair_what_dets: ### other redescription info
            methode = eval(Redescription.info_pair_what_dets[what])
            if callable(methode):
                return methode(other, details)
        elif what in Redescription.info_pair_what_side and which in Redescription.pair_map_side: ### other redescription info
            methode = eval(Redescription.info_pair_what_side[what])
            if callable(methode):
                return methode(other, Redescription.pair_map_side[which], details)

    def getExpPairProp(self, other, exp, details={}):
        ws = self.getRP().getPairPrimitiveWs(exp)
        if ws[0] is not None:
            return self.getPairProp(other, ws[0], ws[1], ws[2], details)
   ###############################################        
        
##### PRINTING AND PARSING METHODS
    #### FROM HERE ALL PRINTING AND READING
    def red2strLegacy(self):
        str_av = ["?", "?"]
        for side in [0,1]:
            if self.availableColsSide(side) is not None:
                str_av[side] = "%d" % len(self.availableColsSide(side))
        tmp = ('%s + %s terms:' % tuple(str_av)) + ('\t (%i): %s\t%s\t%s\t%s' % (len(self), self.dispQueries(sep=" "), self.dispStats(sep=" "), self.dispSuppL(sep=" "), self.getTrack({"format":"str"})))
        return tmp

    def __str__(self):
        str_av = ["?", "?"]
        for side in [0,1]:
            if self.availableColsSide(side) is not None:
                str_av[side] = "%d" % len(self.availableColsSide(side))

        tmp = "%s%s\t%s\t%s\t%s" % (self.class_letter, self.getUid(), self.dispQueries(sep="\t"), self.dispStats(sep=" "), self.dispSuppL(sep=" "))
        tmp += "\tlengthQs:%d nbAvC:%s+%s track:%s" % (len(self), str_av[0], str_av[1], self.getTrack({"format":"str"}))
        return tmp

    # def __str__(self):
    #     return "%s\t%s\t%s" % (self.query(0), self.query(1), self.score())
    
    def dispQueries(self, names=[None, None, None], sep='\t'):
        sides = [0, 1]
        if self.hasCondition():
            sides.append(-1)
        return sep.join(["q%s:%s" % (side, self.query(side).disp(names[side])) for side in sides])
    def dispStats(self, sep="\t"):
        if self.hasCondition():
            return self.supports().dispStats(sep)+sep+"COND:"+self.getSupportsC().dispStats(sep)
        return self.supports().dispStats(sep)
    def dispSupp(self, sep="\t"):
        if self.hasCondition():
            return self.supports().dispSupp(sep)+sep+"COND:"+self.getSupportsC().dispSupp(sep)
        return self.supports().dispSupp(sep)        
    def dispSuppL(self, sep="\t"):
        if self.hasCondition():
            return self.supports().dispSuppL(sep)+sep+"COND:"+self.getSupportsC().dispSuppL(sep)
        return self.supports().dispSuppL(sep)
    
    def prepareQuery(self, side, details={}, named=False):
        style=details.get("style", "")
        q = self.query(side)
        if q is None: return ""
        if (named or details.get("named", False)) and "names" in details:
            return q.disp(names=details["names"][side], style=style)
        return q.disp(style=style)        
    def prepareQueryRHS(self, details):
        return self.prepareQuery(1, details)
    def prepareQueryLHS(self, details):
        return self.prepareQuery(0, details)
    def prepareQueryCOND(self, details):
        return self.prepareQuery(-1, details)    
   
    def disp(self, names=[None, None], row_names=None, with_fname=False, rid="", nblines=1, delim="", last_one=False, list_fields="basic", modifiers={}, style="txt", sep=None, rp=None):
        return self.getRP(rp).disp(self, names, row_names, with_fname, rid, nblines, delim, last_one, list_fields, modifiers, style, sep)
    @classmethod   
    def parse(tcl, stringQueries, stringSupp=None, data=None, rp=None):
        if data is not None and data.hasNames():
            names = data.getNames()
        else:
            names = [None, None]
        pdb.set_trace()
        (queryL, queryR, lpartsList) = tcl.getRP(rp).parseQueries(stringQueries, names=names)
        supportsS = None
        if data is not None and stringSupp is not None and type(stringSupp) == str and re.search('\t', stringSupp):
            supportsS = SParts.parseSupport(stringSupp, data.nbRows(), data.getSSetts())
        return tcl.initParsed(queryL, queryR, lpartsList, data, supportsS)
    @classmethod   
    def initParsed(tcl, queryL, queryR, lpartsList={}, data = None, supportsS=None):
        status_enabled = None
        if "all:extra:status" in lpartsList:
            status_enabled = int(lpartsList.pop("all:extra:status"))
        if "status_enabled" in lpartsList:
            status_enabled = int(lpartsList.pop("status_enabled"))
        r = None
        if supportsS is not None:
            r = tcl(queryL, queryR, supportsS.supparts(), data.nbRows(), [set(),set()], [ queryL.proba(0, data), queryR.proba(1, data)], data.getSSetts())

            for key, v in lpartsList.items():
                tv = RedProps.getEVal(r, key)
                if tv != v:
                    raise Warning("Something wrong in the supports ! (%s: %s ~ %s)\n" \
                                    % (key, v, tv))

        if r is None:
            r = tcl(queryL, queryR)
            if data is not None:
                r.recompute(data)
            else:
                r.cache_evals = lpartsList

        if "queryCOND" in lpartsList:
            qC = lpartsList["queryCOND"]
            supp_cond = None
            if data is not None:
                supp_cond, miss_cond = qC.recompute(-1, data)
            r.setCondition(qC, supp_cond)
        if r is not None and status_enabled is not None:
            r.setStatus(status_enabled)
        return r
    
        
if __name__ == '__main__':
    # print Redescription.exp_details.keys()
    from classData import Data
    import sys

    rep = "/home/egalbrun/short/vaalikone_FILES/"
    rep = "/home/egalbrun/short/raja_time/"
    data = Data([rep+"data_LHS_lngtid.csv", rep+"data_RHS_lngtid.csv", {}, "NA"], "csv")

    rp = Redescription.getRP()
    # filename = rep+"redescriptions.csv"
    filename = rep+"tid_test.queries"
    filep = open(filename, mode='r')
    reds = []
    rp.parseRedList(filep, data, reds)
    with open("/home/egalbrun/short/tmp_queries.txt", mode='w') as fp:
        # pdb.set_trace()
        fp.write(rp.printRedList(reds, missing=True))
        ## fp.write(rp.printTexRedList(reds, names = [data.getNames(0), data.getNames(1)], nblines=3, standalone=True))
        ## fields=[-1, "CUST:XX=q0:containsC:0", "Lnb_queryLHS", "Lset_queryLHS", "Lnb_queryRHS", "Lset_queryRHS", "containsAND_queryRHS", "containsOR_queryRHS"]
    exit()
    # rep = "/home/galbrun/TKTL/redescriptors/data/vaalikone/"
    # data = Data([rep+"vaalikone_profiles_test.csv", rep+"vaalikone_questions_test.csv", {}, "NA"], "csv")

    # reds = []
    # with codecs.open("../../bazar/queries.txt", encoding='utf-8', mode='r') as f:
    #     for line in f:
    #         if len(line.strip().split("\t")) >= 2:
    #             try:
    #                 tmpLHS = Query.parse(line.strip().split("\t")[0], data.getNames(0))
    #                 tmpRHS = Query.parse(line.strip().split("\t")[1], data.getNames(1))
    #             except:
    #                 continue
    #             r = Redescription.fromQueriesPair([tmpLHS, tmpRHS], data)
    #             reds.append(r)

    # with codecs.open("../../bazar/queries_list2.txt", encoding='utf-8', mode='w') as f:
    #     f.write(rp.printRedList(reds))

    # with codecs.open("../../bazar/queries_list2.txt", encoding='utf-8', mode='r') as f:
    #     reds, _ = rp.parseRedList(f, data)

    # for red in reds:
    #     print red.disp()
