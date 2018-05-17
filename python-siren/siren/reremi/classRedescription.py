import re, string, numpy, codecs
from classQuery import  *
from classSParts import  SParts, tool_pValSupp, tool_pValOver
from classBatch import Batch
import toolRead
import pdb

ACTIVE_RSET_ID = "S0"
SIDE_CHARS = {0:"L", 1:"R", -1: "C"}
HAND_SIDE = {"qLHS": 0, "qRHS": 1, "q0": 0, "q1": 1, "qCOND": -1, "q-1": -1}
NUM_CHARS = dict([(numpy.base_repr(ii, base=25), "%s" % chr(ii+ord("a"))) for ii in range(25)])

def digit_to_char(n, pad=None):
    if pad is None:
        tmp = "".join([NUM_CHARS[t] for t in numpy.base_repr(n, base=25)])
    else:
        tmp = ("z"*pad+"".join([NUM_CHARS[t] for t in numpy.base_repr(n, base=25)]))[-pad:]
    # print "%s -> %s" % (n, tmp)
    return tmp

def side_ltx_cmd(sid, padss=None):
    if sid in SIDE_CHARS:
        schar = SIDE_CHARS[sid]
    else:
        schar = digit_to_char(sid, padss)
    return schar

def var_ltx_cmd(sid, vid, padsv=None, padss=None):
    schar = side_ltx_cmd(sid, padss)
    vchar = digit_to_char(vid, padsv)
    return "\\v%sHS%s" % (schar.upper(), vchar.lower())

def cust_eval(exp, loc):
    try:
        return eval(exp, {}, loc)
    except ZeroDivisionError:
        return float("Inf")
    except TypeError:
        return None

def prepareFmtString(nblines, nbstats, last_one, tex=False):
    nbc = "%d" % (nbstats+1)
    if nblines == 3:
        #### SPREAD ON THREE LINES            
        if tex:
            frmts = "%(rid)s & & %(stats)s \\\\ [.2em]\n & \\multicolumn{"+ nbc +"}{p{.9\\textwidth}}{ %(q0)s } \\\\ \n" + \
                    " & \\multicolumn{"+ nbc +"}{p{.9\\textwidth}}{ %(q1)s } \\\\"
            if not last_one:
                frmts +=  " [.32em] \cline{2-"+ nbc +"} \\\\ [-.88em]"
        else:
            frmts = "%(rid)s%(stats)s\n%(q0)s\n%(q1)s"
    elif nblines == 2:
        if tex:
            frmts = "%(rid)s & %(q0)s & & %(stats)s \\\\ \n & \\multicolumn{2}{r}{ %(q1)s } \\\\"
            if not last_one:
                frmts +=  " [.3em]"
        else:
            frmts = "%(rid)s%(q0)s\t%(q1)s\n%(stats)s"
    else:
        if tex:
            frmts = "%(rid)s & %(all)s \\\\"
        else:
            frmts = "%(rid)s%(all)s"
    return frmts

    
class Redescription(object):
    diff_score = Query.diff_length + 1
    namedsuff = "_named"
    splitssuff = "_splits"
    misssuff = "_missing"
    condsuff = "_cond"
    
    qry_infos = {"queryLHS": "self.prepareQueryLHS", "queryLHS"+namedsuff: "self.prepareQueryLHSNamed",
                 "queryRHS": "self.prepareQueryRHS", "queryRHS"+namedsuff: "self.prepareQueryRHSNamed",
                 "queryCOND": "self.prepareQueryCOND", "queryCOND"+namedsuff: "self.prepareQueryCONDNamed"}
    infos = {"track": "self.getTrack()", "status_enabled": "self.getStatus()"}
    match_prop = "(?P<prop>((?P<rset_id>(cond|learn|test|all|qLHS|qRHS|q0|q1)))?:(?P<what>\w+):(?P<which>\w+)?)"
    match_cust_prop = "CUST:(?P<name>[^=]+)=(?P<exp>.*)"
    
    ######################################
    ###   DEFINITIONS OF FIELDS REDS
    ######################################
    which_dets = {"I": "supp"}
    what_dets = {"acc": "J", "pval": "pV"}
    which_dets_tex = {"I": "\\supp"}
    what_dets_tex = {"pr0": "prLHS", "pr1": "prRHS"}
    rset_dets = {"all" : {"name": "", "exp": "all", "lbl_gui": "", "lbl_txt": "", "lbl_tex": "\\RSetAll"},
                 "cond" : {"name": "_cond", "exp": "cond", "lbl_gui": "C", "lbl_txt": "_cond", "lbl_tex": "\\SubCond"},
                 "learn" : {"name": "_learn", "exp": "learn", "lbl_gui": SYM.SYM_LEARN, "lbl_txt": "_learn", "lbl_tex": "_{\\RSetLearn}"},
                 "test" : {"name": "_test", "exp": "test", "lbl_gui": SYM.SYM_TEST, "lbl_txt": "_test", "lbl_tex": "_{\\RSetTest}"}}


    tex_fld_defs = {} ### to contain tex command definitions
    exp_details = {} ### to contain actual fields infos
    ### QUERY FIELDS
    ###################################
            
    ### SHARED TEX COMMAND DEFS
    tex_fld_stat = {"acc": "\\newcommand{\\PPacc}[1]{\\jacc#1} % Jacc\n",
                    "pval": "\\newcommand{\\PPpval}[1]{\\pValue#1} % pvalue\n",
                    "pr0": "\\newcommand{\\PPprLHS}[1]{\\pr(\\iLHS#1)} % proba\n",
                    "pr1": "\\newcommand{\\PPprRHS}[1]{\\pr(\\iRHS#1)} % proba\n",
                    "qlen": "\\newcommand{\\PPQlen}[1]{\\abs{#1}} % Nb. vars\n"}

    ### QUERY FIELDS, SIDE SPECIFIC
    ###################################
    #### QUERY 
    for what in qry_infos.keys():
        exp_details[what] = {"exp": ":%s:" % what, "fmt": "s",
                             "lbl_gui": what.split("_")[0], "lbl_txt": what.split("_")[0], "lbl_tex": "\\PP"+what.split("_")[0]}
        if re.search("LHS", what):
            tex_fld_defs[what] = "\\newcommand{\\PP%s}{q_\\iLHS} %% LHS query\n" % what.split("_")[0]
        if re.search("COND", what):
            tex_fld_defs[what] = "\\newcommand{\\PP%s}{q_\\iCOND} %% COND query\n" % what.split("_")[0]
        else:
            tex_fld_defs[what] = "\\newcommand{\\PP%s}{q_\\iRHS} %% RHS query\n" % what.split("_")[0]

    #### QUERY STATS        
    for what in Query.info_what.keys():
        for si, side in enumerate(["LHS", "RHS", "COND"]):
            fmt = "d"
            if re.search("set", what): fmt = "s"
            name = "%s_query%s" % (what, side)
            exp_details[name] =  {"exp": "q%d:%s:" % (si, what), "fmt": fmt,
                                  "lbl_gui": "%s query %s" % (what, side),
                                  "lbl_txt": name,
                                  "lbl_tex": "\\PPQ%s{q_\\i%s}" % (what, side)}
            if ("q"+what) in tex_fld_stat: 
                tex_fld_defs[name] = tex_fld_stat[("q"+what)]
            else:
                tex_fld_defs[name] = "\\newcommand{\\PPQ%s}[1]{\\text{%s} #1}\n" % (what, what)

    ### SUPP FIELDS, SPLITS SPECIFIC
    ###################################
    for rset_id in ["all", "learn", "test", "cond"]:

        # what = "meanJSuppI"
        # expJ = "%s:acc:" % rset_dets[rset_id]["exp"]
        # expSupp = "%s:prc:I" % rset_dets[rset_id]["exp"]
        # name = "%s%s" % (what, rset_dets[rset_id]["name"])
        # exp_details[name] =  {"exp": "2./((1./(%s))+(100./(%s)))" % (expJ, expSupp), "fmt": ".3f",
        #                       "lbl_gui": rset_dets[rset_id]["lbl_gui"]+what,
        #                       "lbl_txt": "%s%s" % (what, rset_dets[rset_id]["lbl_txt"]),
        #                       "lbl_tex": "%s%s" % (what, rset_dets[rset_id]["lbl_tex"])}
        # tex_fld_defs[name] = ""

        # what = "meanJSuppU"
        # expJ = "%s:acc:" % rset_dets[rset_id]["exp"]
        # expSupp = "%s:prc:U" % rset_dets[rset_id]["exp"]
        # name = "%s%s" % (what, rset_dets[rset_id]["name"])
        # exp_details[name] =  {"exp": "2./((1./(%s))+(100./(%s)))" % (expJ, expSupp), "fmt": ".3f",
        #                       "lbl_gui": rset_dets[rset_id]["lbl_gui"]+what,
        #                       "lbl_txt": "%s%s" % (what, rset_dets[rset_id]["lbl_txt"]),
        #                       "lbl_tex": "%s%s" % (what, rset_dets[rset_id]["lbl_tex"])}
        # tex_fld_defs[name] = ""

        
        ### COMMON STATS
        whts = ["acc", "pval"]
        if rset_id != "cond":
            whts.extend(["pr0", "pr1"])
        for what in whts:
            name = "%s%s" % (what, rset_dets[rset_id]["name"])
            exp_details[name] =  {"exp": "%s:%s:" % (rset_dets[rset_id]["exp"], what), "fmt": ".3f",
                                  "lbl_gui": rset_dets[rset_id]["lbl_gui"]+what_dets.get(what, what),
                                  "lbl_txt": "%s%s" % (what, rset_dets[rset_id]["lbl_txt"]),
                                  "lbl_tex": "\\PP%s{%s}" % (what_dets_tex.get(what, what), rset_dets[rset_id]["lbl_tex"])}
            tex_fld_defs[name] = tex_fld_stat[what]
        
        ### SUPP LEN, SUPP SET, SUPP PERCENTAGE 
        for which in SSetts.labels+list(SParts.sets_letters):
            ### len
            name = "len%s%s" % (which, rset_dets[rset_id]["name"])
            exp_details[name] =  {"exp": "%s:len:%s" % (rset_dets[rset_id]["exp"], which), "fmt": "d", 
                                  "lbl_gui": rset_dets[rset_id]["lbl_gui"]+("|%s|" % which_dets.get(which, which)),
                                  "lbl_txt": "card_%s%s" % (which, rset_dets[rset_id]["lbl_txt"]),
                                  "lbl_tex": "\\PPcard{%s%s}" % (which_dets_tex.get(which, which), rset_dets[rset_id]["lbl_tex"])}
            tex_fld_defs[name] = "\\newcommand{\\PPcard}[1]{\\abs{#1}} % support size\n"
            ### supp
            name = "%s%s" % (which, rset_dets[rset_id]["name"])
            exp_details[name] =  {"exp": "%s:supp:%s" % (rset_dets[rset_id]["exp"], which), "fmt": "s", "supp_set": True, "sep": ",",
                                  "lbl_gui": rset_dets[rset_id]["lbl_gui"]+("%s" % which_dets.get(which, which)),
                                  "lbl_txt": "%s%s" % (which, rset_dets[rset_id]["lbl_txt"]),
                                  "lbl_tex": "\\PPsupp{%s%s}" % (which_dets_tex.get(which, which), rset_dets[rset_id]["lbl_tex"])}
            exp_details[name+namedsuff] =  {"exp": "%s:supp:%s" % (rset_dets[rset_id]["exp"], which), "fmt": "s", "supp_set": True, "sep": ",",
                                  "lbl_gui": rset_dets[rset_id]["lbl_gui"]+("%s" % which_dets.get(which, which)),
                                  "lbl_txt": "%s%s" % (which, rset_dets[rset_id]["lbl_txt"]),
                                  "lbl_tex": "\\PPsupp{%s%s}" % (which_dets_tex.get(which, which), rset_dets[rset_id]["lbl_tex"])}
            tex_fld_defs[name] = "\\newcommand{\\PPsupp}[1]{#1} % support\n"
            tex_fld_defs[name+namedsuff] = "\\newcommand{\\PPsupp}[1]{#1} % support\n"

            ### prc
            name = "prc%s%s" % (which, rset_dets[rset_id]["name"])
            exp_details[name] =  {"exp": "%s:prc:%s" % (rset_dets[rset_id]["exp"], which), "fmt": ".2f",
                                  "lbl_gui": rset_dets[rset_id]["lbl_gui"]+("%%%s" % which_dets.get(which, which)),
                                  "lbl_txt": "prc_%s%s" % (which, rset_dets[rset_id]["lbl_txt"]),
                                  "lbl_tex": "\\PPprc{%s%s}" % (which_dets_tex.get(which, which), rset_dets[rset_id]["lbl_tex"])}
            tex_fld_defs[name] = "\\newcommand{\\PPprc}[1]{\\%#1} % support percent\n"


    ### FURTHER FIELDS
    ###################################
    for what in infos.keys():
        exp_details[what] = {"exp": ":%s:" % what, "fmt": "s",
                             "lbl_gui": what, "lbl_txt": what, "lbl_tex": "\\PP"+what}
        tex_fld_defs[what] = "\\newcommand{\\PP%s}{%s} %% other\n" % (what, what)
        
    exp_details["acc_ratioTL"] = {"exp": "test:acc:/learn:acc:", "fmt": ".3f",
                                  "lbl_gui": SYM.SYM_RATIO+what_dets.get("acc", "acc"),
                                  "lbl_txt": "acc_ratioTL", "lbl_tex": "\\PPaccRatioTL"}
    tex_fld_defs["acc_ratioTL"] = "\\newcommand{\\PPaccRatioTL}{\\jacc_{\\RSetTest/\\RSetLearn}} % support\n"
    exp_details["lenI_ratioTA"] = {"exp": "test:len:I/(1.*all:len:I)", "fmt": ".3f",
                                  "lbl_gui": SYM.SYM_RATIO+which_dets.get("I", "I"),
                                  "lbl_txt": "Exx_ratioTL", "lbl_tex": "\\PPlenIRatioTA"}
    tex_fld_defs["lenI_ratioTA"] = "\\newcommand{\\PPlenIRatioTA}{\\supp_{\\RSetTest/\\mathcal{A}}} % support\n"

        
    ### set rounding info where relevant
    for fk in exp_details.keys():
        mtc = re.search("\.(?P<rnd>[0-9]+)f", exp_details[fk].get("fmt", ""))
        if mtc is not None:
            exp_details[fk]["rnd"] = int(mtc.group("rnd"))

            
    ### FIELD LISTS FOR DIFFERENT PURPOSES
    ##########################################
    default_fields_parts = {}
    
    default_fields_parts["q"] = ["queryLHS", "queryRHS"]
    default_fields_parts["q"+namedsuff] = ["%s%s" % (f, namedsuff) for f in default_fields_parts["q"]]
    default_fields_parts["qCOND"] = ["queryCOND"]
    default_fields_parts["qCOND"+namedsuff] = ["%s%s" % (f, namedsuff) for f in default_fields_parts["qCOND"]]

    default_fields_parts["stats_basic"] = ["acc", "pval"]
    default_fields_parts["statsCOND_basic"] = ["lenI_cond", "acc_cond", "pval_cond"]
    default_fields_parts["stats_gui"] = ["acc", "lenI", "prcI", "pval"]
    default_fields_parts["stats_txt"] = ["acc", "lenI", "pval"]
    default_fields_parts["stats_tex"] = ["acc", "lenI", "prcI"] #, "acc_test", "prcI_test", "lenI_ratioTA"]
    width_mid = .5

    for ss in ["", condsuff]:
        default_fields_parts.update({"lens"+ss:[], "supps"+ss: [], "lens"+ss+misssuff: [], "supps"+ss+misssuff: []})
        for nname in SSetts.labels:
            if "m" in nname:
                default_fields_parts["lens"+ss+misssuff].append("len%s%s" % (nname, ss))
                default_fields_parts["supps"+ss+misssuff].append("%s%s" % (nname, ss))
            elif "xx" in nname:
                default_fields_parts["lens"+ss].append("len%s%s" % (nname, ss))
                default_fields_parts["lens"+ss+misssuff].append("len%s%s" % (nname, ss))
                default_fields_parts["supps"+ss+misssuff].append("%s%s" % (nname, ss))
            else:
                default_fields_parts["lens"+ss].append("len%s%s" % (nname, ss))
                default_fields_parts["supps"+ss].append("%s%s" % (nname, ss))
                default_fields_parts["lens"+ss+misssuff].append("len%s%s" % (nname, ss))
                default_fields_parts["supps"+ss+misssuff].append("%s%s" % (nname, ss))
            
    ######################################
    ######################################            
    field_lists = {}
    for named, nsuff in [(False, ""), (True, namedsuff)]:
        for wcond, csuff in [(False, ""), (True, condsuff)]:
            for wmiss, msuff in [(False, ""), (True, misssuff)]:
                bname = "basic"+nsuff+csuff+msuff
                qname = "q"+nsuff+csuff
                tname = "stats"+csuff
                sname = "supp"+msuff
                field_lists[qname] = list(default_fields_parts["q"+nsuff])
                field_lists[bname] = list(default_fields_parts["q"+nsuff])
                field_lists[tname] = []
                if wcond:
                    field_lists[qname].extend(default_fields_parts["qCOND"+nsuff])
                    field_lists[bname].extend(default_fields_parts["qCOND"+nsuff])
                    field_lists[bname].extend(default_fields_parts["statsCOND_basic"])
                    field_lists[tname].extend(default_fields_parts["statsCOND_basic"])
                field_lists[bname].extend(default_fields_parts["stats_basic"])
                field_lists[tname].extend(default_fields_parts["stats_basic"])
                field_lists[bname].extend(default_fields_parts["lens"+msuff])
                field_lists[sname] = list(default_fields_parts["supps"+msuff])

    for basis in ["gui"]:
        for wsplits, ssuff in [(0, ""), (1, splitssuff), (-1, condsuff)]:
            nf = "%s%s" % (basis, ssuff)
            field_lists[nf] = [] #list(default_fields_parts["q"])
            if wsplits == -1:
                field_lists[nf].extend(["queryCOND_named", "acc_cond"])
            if wsplits == 1:
                field_lists[nf].extend(["acc_ratioTL", "lenI_ratioTA"])
                for ff in default_fields_parts["stats_%s" % basis]:            
                    field_lists[nf].extend(["%s_%s" % (ff, split) for split in ["test", "learn"]])
            else:
                field_lists[nf].extend(default_fields_parts["stats_%s" % basis])
                
    for basis in ["txt", "tex"]:
        for named, nsuff in [(False, ""), (True, namedsuff)]:
            for wsplits, ssuff in [(0, ""), (1, splitssuff), (-1, condsuff)]:
                nf = "%s%s%s" % (basis, nsuff, ssuff)
                field_lists[nf] = list(default_fields_parts["q%s" % nsuff])
                field_lists[nf].extend(default_fields_parts["stats_%s" % basis])
                if wsplits == 1:
                    field_lists[nf].extend(["acc_ratioTL", "lenI_ratioTA"])
                    for split in ["test", "learn"]:
                        field_lists[nf].extend(["%s_%s" % (ff, split) for ff in default_fields_parts["stats_%s" % basis]])
                if wsplits == -1:
                    field_lists[nf].extend(["", "lenI_ratioTA"])
                    for split in ["cond"]:
                        field_lists[nf].extend(["%s_%s" % (ff, split) for ff in default_fields_parts["stats_%s" % basis]])


    @classmethod
    def getFSuff(tcl, named=False, wsplits=0, wmissing=False):
        kk = ""
        if named: kk += tcl.namedsuff
        if wsplits > 0: kk += tcl.splitssuff
        elif wsplits < 0: kk += tcl.condsuff            
        if wmissing: kk += tcl.misssuff
        return kk
    @classmethod
    def hasFieldsList(tcl, k="basic", named=False, wsplits=0, wmissing=False):
        return (k+tcl.getFSuff(named, wsplits, wmissing)) in tcl.field_lists

    @classmethod
    def getFieldsListCust(tcl, k="basic", named=False, wsplits=0, wmissing=False):
        kk = k+tcl.getFSuff(named, wsplits, wmissing)
        if Redescription.hasFieldsList("custom-"+kk):
            return Redescription.getFieldsList("custom-"+kk)
        else:
            return Redescription.getFieldsList(k, named, wsplits, wmissing)
        
    @classmethod
    def getFieldsList(tcl, k="basic", named=False, wsplits=0, wmissing=False):
        kk = k+tcl.getFSuff(named, wsplits)
        if wmissing and kk+tcl.misssuff in tcl.field_lists:
            return list(tcl.field_lists[kk+tcl.misssuff])
        if kk in tcl.field_lists:
            return list(tcl.field_lists[kk])
        return list(tcl.field_lists.get(k, []))
    @classmethod
    def setFieldsList(tcl, k, fields):
        tcl.field_lists[k] = fields

    @classmethod
    def getFieldsDet(tcl, fk, det, default=None):
        if fk in tcl.exp_details:
            if det == "name": return fk
            return tcl.exp_details[fk].get(det, default)
        else:
            m = re.match(tcl.match_cust_prop, fk)
            if m is not None:
                if re.match("lbl_", det) or det == "name":
                    return m.group("name")
                elif det == "exp":
                    return m.group("exp")            
        return default 
    @classmethod
    def getFieldsKeys(tcl):
        return tcl.exp_details.keys()
    
    @classmethod
    def collectTexCommands(tcl, list_fields):
        return sorted(set([tcl.tex_fld_defs[fk] for fk in list_fields]))
            
    @classmethod
    def map_field_name(tcl, fld):
        fldtmp = fld        
        for (sf, st) in [("query_", "query"), ("card_", "len"), ("alpha", "Exo"), ("beta", "Eox"), ("gamma", "Exx"), ("delta", "Eoo"), ("mua", "Exm"), ("mub", "Emx"), ("muaB", "Eom"), ("mubB", "Emo"), ("mud", "Emm"), ("status_disabled", "status_enabled")]:
            fld = fld.replace(sf, st)
        return fld
        
    @classmethod
    def getExpDict(tcl, list_fields):
        tmp = []
        for fk in list_fields:
            if fk in tcl.getFieldsKeys():
                tmp.append((fk, tcl.getFieldsDet(fk, "exp", "")))
            else:
                m = re.match(tcl.match_cust_prop, fk)
                if m is not None:
                    tmp.append((m.group("name"), m.group("exp")))
        return dict(tmp)
    
    def __init__(self, nqueryL=None, nqueryR=None, nsupps = None, nN = -1, nPrs = [-1,-1], ssetts=None):
        self.resetRestrictedSuppSets()
        self.queries = [nqueryL, nqueryR]
        if nsupps is not None:
            self.sParts = SParts(ssetts, nN, nsupps, nPrs)
            self.dict_supp_info = None
        else:
            self.sParts = None
            self.dict_supp_info = {}
        self.lAvailableCols = [None, None]
        self.vectorABCD = None
        self.status = 1
        self.track = []
        self.cache_evals = {}
        self.condition = None

    def fromInitialPair(initialPair, data, dt={}):
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

        r = Redescription(queries[0], queries[1], supps_miss, data.nbRows(), [len(supps_miss[0])/float(data.nbRows()),len(supps_miss[1])/float(data.nbRows())], data.getSSetts())
        r.track = [(-1, -1)]

        if dt.get("litC") is not None:
            litC = dt["litC"]
            if type(litC) is list:
                # if len(litC) > 1: pdb.set_trace()
                qC = Query(OR=False, buk=litC) 
            else:                
                qC = Query(buk=[litC])                
            supp_cond, miss_cond = qC.recompute(-1, data)
            r.setCondition(qC, supp_cond)
        if data.hasLT():
            r.setRestrictedSupp(data)
        return r
    fromInitialPair = staticmethod(fromInitialPair)

    def fromQueriesPair(queries, data):
        r = Redescription(queries[0].copy(), queries[1].copy())
        r.recompute(data)        
        r.track = [tuple([0] + sorted(r.queries[0].invCols())), tuple([1] + sorted(r.queries[1].invCols()))]
        if len(queries) > 2 and queries[2] is not None:
            qC = queries[2]
            supp_cond, miss_cond = qC.recompute(-1, data)
            r.setCondition(qC, supp_cond)            
        return r
    fromQueriesPair = staticmethod(fromQueriesPair)

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
        if len(redB.invColsSide(side) & self.invColsSide(side)) == 0:
            return 0
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

    def overlapRows(self, redB):
        if redB is not None:
            return len(redB.getSuppI() & self.getSuppI())/float(min(redB.getLenI(), self.getLenI()))
        return 0
    
    def oneSideIdentical(self, redescription):
        return self.queries[0] == redescription.queries[0] or self.queries[1] == redescription.queries[1]
    def bothSidesIdentical(self, redescription):
        return self.queries[0] == redescription.queries[0] and self.queries[1] == redescription.queries[1]

    def equivalent(self, y):
       return abs(self.compare(y)) < Query.diff_balance
        
    # def __hash__(self):
    #      return int(hash(self.queries[0])+ hash(self.queries[1])*100*self.score())
        
    def __len__(self):
        return self.length(0) + self.length(1)

    def usesOr(self, side=None):
        if side is not None:
            return self.queries[side].usesOr()
        return self.queries[0].usesOr() or self.queries[1].usesOr()

    def supp(self, side):
        return self.supports().supp(side)

    def miss(self, side):
        return self.supports().miss(side)
            
    def score(self):
        return self.getAcc()

    def supports(self):
        return self.sParts
    
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
        
    def availableColsSide(self, side, data=None, single_dataset=False):
        if self.lAvailableCols[side] is not None and self.length(1-side) != 0:
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
            self.supports().update(side, op.isOr(), suppX, missX)
            self.dict_supp_info = None
            if self.lAvailableCols[side] is not None:
                self.lAvailableCols[side].remove(literal.colId())
            self.track.append(((1-side) * 1-2*int(op.isOr()), literal.colId()))

    def setFull(self, max_var=None):
        if max_var is not None:
            for side in [0,1]:
                if self.length(side) >= max_var[side]:
                    self.lAvailableCols[side] = set()
                
    def kid(self, data, side= -1, op = None, literal= None, suppX= None, missX=None):
        kid = self.copy()        
        kid.update(data, side, op, literal, suppX, missX)
        return kid
            
    def copy(self):
        r = Redescription(self.queries[0].copy(), self.queries[1].copy(), \
                             self.supports().supparts(), self.supports().nbRows(), self.probas(), self.supports().getSSetts())
        for side in [0,1]:
            if self.lAvailableCols[side] is not None:
                r.lAvailableCols[side] = set(self.lAvailableCols[side])
        r.status = self.status
        r.track = list(self.track)
        r.restricted_sets = {}
        for sid, rst in self.restricted_sets.items():
            r.restricted_sets[sid] = {"sParts": rst["sParts"],
                                         "prs": [rst["prs"][0], rst["prs"][1]],
                                         "rids": set(rst["rids"])}

        return r

    def recomputeQuery(self, side, data= None, restrict=None):
        return self.queries[side].recompute(side, data, restrict)
    
    def invLiteralsSide(self, side):
        return self.queries[side].invLiterals()

    def invLiterals(self):
        return [self.invLiteralsSide(0), self.invLiteralsSide(1)]
    
    def invColsSide(self, side):
        return self.queries[side].invCols()

    def invCols(self):
        return [self.invColsSide(0), self.invColsSide(1)]
        
    def setRestrictedSupp(self, data):
        ### USED TO BE STORED IN: self.restrict_sub, self.restricted_sParts, self.restricted_prs = None, None, None
        self.setRestrictedSuppSets(data, supp_sets=None)
        
    def resetRestrictedSuppSets(self):
        self.restricted_sets = {}

    def setRestrictedSuppSets(self, data, supp_sets=None):
        self.dict_supp_info = None
        if supp_sets is None:
            if data.hasLT():
                supp_sets = data.getLT()
            else:
                supp_sets = {ACTIVE_RSET_ID: data.nonselectedRows()}
        for sid, sset in supp_sets.items():
            if len(sset) == 0:
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
        if data.hasLT():
            self.setRestrictedSupp(data)
        if self.hasCondition():
            qC = self.getQueryC()
            supp_cond, miss_cond = qC.recompute(-1, data)
            self.setCondition(qC, supp_cond)                        
        self.dict_supp_info = None

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
        return self.status
    def getEnabled(self):
        return self.status

    def flipEnabled(self):
        self.status = -self.status

    def setEnabled(self):
        self.status = 1
    def setDisabled(self):
        self.status = -1

    def setDiscarded(self):
        self.status = -2

    ##### GET FIELDS INFO INVOLVING ADDITIONAL DETAILS (PRIMARILY FOR SIREN)
    def getQueriesU(self, details=None):
        if details is not None and "names" in details:
            return self.queries[0].disp(details["names"][0], style="U") + "---" + self.queries[1].disp(details["names"][1], style="U")
        else:
            return self.queries[0].disp(style="U") + "---" + self.queries[1].disp(style="U")

    def getQueryLU(self, details=None):
        if details is not None and "names" in details:
            return self.queries[0].disp(details["names"][0], style="U") #, unicd=True)
        else:
            return self.queries[0].disp(style="U")

    def getQueryRU(self, details=None):
        if details is not None and "names" in details:
            return self.queries[1].disp(details["names"][1], style="U") #, unicd=True)
        else:
            return self.queries[1].disp(style="U")

    def getTrack(self, details=None):
        if details is not None and ( details.get("aim", None) == "list" or details.get("format", None) == "str"):
            return ";".join(["%s:%s" % (t[0], ",".join(map(str,t[1:]))) for t in self.track])
        else:
            return self.track

    def getSortAble(self, details=None):
        if details.get("aim") == "sort":
            return (self.status, details.get("id", "?"))
        return ""

    def getShortRid(self, details=None):
        return "R%s" % details.get("id", "?")

    def getEnabled(self, details=None):
        return 1*(self.status>0)

    def getTypeParts(self, details=None):
        return self.supports().getTypeParts()
    def getMethodPVal(self, details=None):
        return self.supports().getMethodPVal()    
        
    def getRSet(self, details=None):
        if type(details) is dict:
            rset_id = details.get("rset_id")
        else:
            rset_id = details
        if rset_id is not None:
            if rset_id == "all":
                return {"sParts": self.supports()}
            elif rset_id == "cond" and self.hasCondition():
                return {"sParts": self.getSupportsC()}
            elif rset_id in self.restricted_sets:
                return self.restricted_sets[rset_id]
            return None
        elif ACTIVE_RSET_ID in self.restricted_sets:
            return self.restricted_sets[ACTIVE_RSET_ID]
        else:            
            return {"sParts": self.supports()}
    def getRSetParts(self, details=None):
        rset = self.getRSet(details)
        if rset is not None:
            return rset.get("sParts")
    def getRSetIds(self, details=None):
        rset = self.getRSet(details)
        if rset is not None and "rids" in rset:
            return sorted(rset["rids"])
        return None
       
    def getRSetABCD(self, details=None):
        ssp = self.getRSetParts(details)
        if ssp is not None:
            return ssp.get("sParts").getVectorABCD(force_list=True, rest_ids=ssp.get("rids"))
        
    def getAccRatio(self, details=None):
        if details is not None and (details.get("rset_id_num") in self.restricted_sets \
               or details.get("rset_id_den") in self.restricted_sets):
            acc_num = self.getRSetParts(details.get("rset_id_num")).acc()
            acc_den = self.getRSetParts(details.get("rset_id_den")).acc()
            if acc_den == 0:
                return float('Inf')
            return acc_num/acc_den
        return 1.

    def getLenRatio(self, details=None):
        if details is not None and (details.get("rset_id_num") in self.restricted_sets \
               or details.get("rset_id_den") in self.restricted_sets):
            len_num = self.getRSetParts(details.get("rset_id_num")).lenI()
            len_den = self.getRSetParts(details.get("rset_id_den")).lenI()
            if len_den == 0:
                return float('Inf')
            return len_num/float(len_den)
        return 1.
    
    def getAcc(self, details=None):
        return self.getRSetParts(details).acc()
    def getPVal(self, details=None):
        return self.getRSetParts(details).pVal()

    def getLenP(self, details=None):
        if "part_id" in details:
            return self.getRSetParts(details).lenP(details["part_id"])
        return -1

    def getLenI(self, details=None):
        return self.getRSetParts(details).lenI()
    def getLenU(self, details=None):
        return self.getRSetParts(details).lenU()
    def getLenL(self, details=None):
        return self.getRSetParts(details).lenL()
    def getLenR(self, details=None):
        return self.getRSetParts(details).lenR()
    def getLenO(self, details=None):
        return self.getRSetParts(details).lenO()
    def getLenN(self, details=None):
        return self.getRSetParts(details).lenN()
    def getLenA(self, details=None):
        return self.getRSetParts(details).lenA()
    def getLenB(self, details=None):
        return self.getRSetParts(details).lenB()
    
    def getSuppI(self, details=None):
        return self.getRSetParts(details).suppI()
    def getSuppU(self, details=None):
        return self.getRSetParts(details).suppU()
    def getSuppL(self, details=None):
        return self.getRSetParts(details).suppL()
    def getSuppR(self, details=None):
        return self.getRSetParts(details).suppR()
    def getSuppO(self, details=None):
        return self.getRSetParts(details).suppO()
    def getSuppN(self, details=None):
        return self.getRSetParts(details).suppN()
    def getSuppA(self, details=None):
        return self.getRSetParts(details).suppA()
    def getSuppB(self, details=None):
        return self.getRSetParts(details).suppB()

    def getProp(self, what, which=None, rset_id=None, details=None):
        if Query.hasProp(what) and rset_id in HAND_SIDE:
            q = self.query(HAND_SIDE[rset_id])            
            if q is not None:
                return q.getProp(what, which, details)
            return None

        if rset_id is not None and which == "rids": ### ids details for split sets
            rset_ids = self.getRSetIds(rset_id)
            if rset_ids is None:
                return None
            if what == "len":
                return len(rset_ids)
            elif what == "supp":
                return rset_ids
            elif what == "prc":
                return (100.*len(rset_ids))/self.supports().nbRows()
        if what in SParts.props_what or what in SParts.infos: ### info from supp parts
            rset_parts = self.getRSetParts(rset_id)
            if rset_parts is None:
                return None
            return self.getRSetParts(rset_id).getProp(what, which)
        elif what in Redescription.qry_infos: ### other redescription info
            methode = eval(Redescription.qry_infos[what])
            if callable(methode):
                return methode(details)
        elif what in Redescription.infos: ### other redescription info
            return eval(Redescription.infos[what])
        
    def refreshEVals(self, exps, details=None):
        self.cache_evals = self.compEvals(exps, details)        
    def compEVal(self, exp, details=None):
        texp = exp
        Rd = {} 
        for mtch in list(re.finditer(Redescription.match_prop, exp))[::-1]:
            Rd[mtch.group("prop")] = self.getProp(mtch.group("what"), mtch.group("which"), mtch.group("rset_id"), details)
            texp = texp[:mtch.start()] + ('R["%s"]' % mtch.group("prop")) + texp[mtch.end():]
        return cust_eval(texp, loc={"R": Rd})        
    def compEVals(self, exps, details=None):
        props_collect = set()
        trans_exps = {}
        for eid, exp in exps.items():
            texp = exp
            for mtch in list(re.finditer(Redescription.match_prop, exp))[::-1]:
                props_collect.add(mtch)
                texp = texp[:mtch.start()] + ('R["%s"]' % mtch.group("prop")) + texp[mtch.end():]
            trans_exps[eid] = texp        
        Rd = {}
        for prop in props_collect:
            Rd[prop.group("prop")] = self.getProp(prop.group("what"), prop.group("which"), prop.group("rset_id"), details)
        props = {}
        for eid, exp in trans_exps.items():
            props[eid] = cust_eval(exp, loc={"R": Rd})
        return props
    def getEVal(self, k, exp=None, fresh=False, default=None, details=None):
        if (exp is not None) and (k not in self.cache_evals or fresh):
            self.cache_evals[k] = self.compEVal(exp, details)
        return self.cache_evals.get(k, default)
    def getEVals(self, exps, fresh=False, details=None):
        if fresh:
            revals = exps
        else:
            revals = dict([(k,v) for (k,v) in exps.items() if k not in self.cache_evals])
        if len(revals) > 0:            
            self.cache_evals.update(self.compEVals(revals, details))
        return dict([(k,self.cache_evals[k]) for k in exps.keys()])
    def getEValGUI(self, details):
        if "k" in details:
            tmp = self.getEVal(details["k"], details.get("exp"), details=details)
        ## print "getEValGUI", details["k"], details.get("exp"), details.get("rnd"), "->", tmp
        if details.get("rnd") is not None and tmp is not None:
            return round(tmp, details.get("rnd"))
        if tmp is None:
            return details.get('replace_none')
        return tmp

##### PRINTING AND PARSING METHODS
    #### FROM HERE ALL PRINTING AND READING
    def __str__(self):
        str_av = ["?", "?"]
        for side in [0,1]:
            if self.availableColsSide(side) is not None:
                str_av[side] = "%d" % len(self.availableColsSide(side))
        supps_cond = "-"
        if self.hasCondition():
            supps_cond = "COND"+str(self.getSupportsC())
        tmp = ('%s + %s terms:' % tuple(str_av)) + ('\t (%i): %s\t%s\t%s\t%s\t%s' % (len(self), self.dispQueries(with_fname=True), self.dispStats(sep=" ", with_fname=True), str(self.supports()), supps_cond, self.getTrack({"format":"str"})))
        return tmp
        
    def dispHeader(list_fields=None, style="", named=False, sep = None, missing=False):
        if list_fields is None:
            fstyle = "txt"
            if style == "tex":
                fstyle = "tex"
            list_fields = Redescription.getFieldsListCust(fstyle, named=named, wmissing=missing)
                
        if style == "tex":
            sepc = " & "
            lbls = ["$%s$" % Redescription.getFieldsDet(fk, "lbl_tex") for fk in list_fields]
        else:
            sepc = "\t"
            lbls = [Redescription.getFieldsDet(fk,"lbl_txt") for fk in list_fields]
        if sep is not None:
            sepc = sep
        return sepc.join(lbls)
    dispHeader = staticmethod(dispHeader)

    def prepareQuery(self, side, details={}, named=False):
        style=details.get("style", "")
        q = self.query(side)
        if q is None: return ""
        if named and "names" in details:
            return q.disp(names=details["names"][side], style=style)
        return q.disp(style=style)        
    def prepareQueryRHS(self, details):
        return self.prepareQuery(1, details)
    def prepareQueryLHS(self, details):
        return self.prepareQuery(0, details)
    def prepareQueryCOND(self, details):
        return self.prepareQuery(-1, details)
    def prepareQueryRHSNamed(self, details):
        return self.prepareQuery(1, details, named=True)
    def prepareQueryLHSNamed(self, details):
        return self.prepareQuery(0, details, named=True)
    def prepareQueryCONDNamed(self, details):
        return self.prepareQuery(-1, details, named=True)
    
    def disp(self, names= [None, None], list_fields=None, sep="\t", with_fname=False, rid="", nblines=1, delim="", style="", supp_names=None, last_one=False, missing=False):
        tex = False
        if style == "tex":            
            tex = True
            sep = " & "
        details = {"style": style}
        if names[0] is not None or names[1] is not None:
            details["names"] = names
        if list_fields is None:
            fstyle = "txt"
            if style == "tex":
                fstyle = "tex"
            named = False
            if "names" in details:
                named = True
            list_fields = Redescription.getFieldsListCust(fstyle, named=named, wmissing=missing)

        exp_dict = Redescription.getExpDict(list_fields)
        evals_dict = self.compEVals(exp_dict, details)

        if type(with_fname) == list and len(with_fname) == len(list_fields):
            lbls = with_fname
            with_fname = True
        elif with_fname:
            det = "lbl_txt"
            if tex:
                det = "lbl_tex"
            lbls = ["%s=" % Redescription.getFieldsDet(field,det) for field in list_fields]
            
        dts = {}
        entries = {"stats": [], "all": [], "q0": "", "q1": "", "rid": rid}
        for fid, field in enumerate(list_fields):
            entry = evals_dict[Redescription.getFieldsDet(field, "name", field)]
            fmt = Redescription.getFieldsDet(field, "fmt", "s")
            if entry is None:
                entry = "-"
                fmt = "s"
            else:
                if supp_names is not None and Redescription.getFieldsDet(field, "supp_set", False) and re.search(Redescription.getFSuff(named=True)+"$", field):
                    entry = [supp_names[i] for i in entry]
                if type(entry) in [list, set]:
                    entry = Redescription.getFieldsDet(field, "sep", ",").join(map(str, entry))
                elif Redescription.getFieldsDet(field, "rnd") is not None:
                    if style == "":
                        fmt = "f"
                    else:
                        entry = round(entry, Redescription.getFieldsDet(field, "rnd"))
                    
                        
            delim, lbl = ("", "")
            if tex and re.search("[df]$", Redescription.getFieldsDet(field, "fmt", "")):
                delim = "$"
            if with_fname:
                lbl = lbls[fid]
                if tex and not re.search("[df]$", Redescription.getFieldsDet(field, "fmt", "")):
                    lbl = "$"+lbl+"$"
            dts[field] = (delim+lbl+"%"+fmt+delim) % entry
            if re.search("queryLHS", field):
                entries["q0"] = dts[field]
            elif re.search("queryRHS", field):
                entries["q1"] = dts[field]
            else:
                entries["stats"].append(dts[field])
            entries["all"].append(dts[field])
        nbstats = len(entries["stats"])
        nball = len(entries["all"])
        entries["all"] = sep.join(entries["all"])
        entries["stats"] = sep.join(entries["stats"])
        frmts = prepareFmtString(nblines, nbstats, last_one, tex)
        return frmts % entries
    
    def dispQueries(self, names=[None,None], sep='\t', with_fname=False):
        named = False
        wcond = 0
        if names[0] is not None or names[1] is not None:
            named = True
        if self.hasCondition():
            wcond = -1
        list_fields = Redescription.getFieldsList("q", wsplits=wcond, named=named)
        return self.disp(list_fields=list_fields, sep=sep, names=names, with_fname=with_fname)

    def dispStats(self, sep='\t', with_fname=False):
        wcond = 0
        if self.hasCondition():
            wcond = -1
        list_fields = Redescription.getFieldsList("stats", wsplits=wcond)
        return self.disp(list_fields=list_fields, sep=sep, with_fname=with_fname)
        
    def dispSupp(self):
        if self.hasCondition():
            return self.getSupportsC().dispSupp()+self.supports().dispSupp()
        return self.supports().dispSupp()
    
    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def fromXML(self, node):
        self.queries = [None, None]
        dsi = {}
        for query_data in node.getElementsByTagName("query"):
            side = toolRead.getTagData(query_data, "side", int)
            if side not in [0,1]:
                print "Unknown side (%s)!" % side
            else:
                query_tmp = toolRead.getTagData(query_data, "ids_expression")
                self.queries[side] = Query.parseApd(query_tmp)
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
            self.sParts = None # SParts(None, dsi)
            self.dict_supp_info = dsi
        tmp_en = toolRead.getTagData(node, "status_enabled", int)
        if tmp_en is not None:
            self.status = tmp_en
    ################# END FOR BACKWARD COMPATIBILITY WITH XML
            
    def parseHeader(string, sep=None):
        default_queries_fields = Redescription.getFieldsList("q")
        if sep is None:
            seps = ["\t", ",", ";"]
        else:
            seps = [sep]
        for ss in seps:
            fields = [Redescription.map_field_name(s.strip()) for s in string.split(ss)]
            if all([len([f for f in fields if re.match("%s(%s)?" % (h, Redescription.getFSuff(named=True)), f)]) > 0 for h in default_queries_fields]):
                return fields, ss
        return None, None
    parseHeader = staticmethod(parseHeader)    

    def parseQueries(string, list_fields=None, sep="\t", names=[None, None]):
        if type(string) is str:
            string = codecs.decode(string, 'utf-8','replace')

        if list_fields is None:
            # list_fields = Redescription.getFieldsList("basic"+Redescription.getFSuff(wmissing=True))
            list_fields = Redescription.getFieldsList("basic", wmissing=True, wsplits=-1)
        default_queries_fields = [f for f in Redescription.getFieldsList("q_cond") if f in list_fields]
        poplist_fields = list(list_fields) ### to pop out the query fields...
        map_fields = dict([(v,k) for (k,v) in enumerate(list_fields)])
        
        queries = [None, None, None]
        lpartsList = {}

        parts = string.strip().rsplit(sep)
        for side, fldu in enumerate(default_queries_fields):
            try_parse = True
            flds = [(fldu, False)]
            if side < len(names) and names[side] is not None:
                fldn = "%s%s" % (fldu, Redescription.getFSuff(named=True))
                if fldn in map_fields:
                    flds.append((fldn, True))
            for (fld, named) in flds:
                poplist_fields[map_fields[fld]] = None
                if try_parse:
                    if map_fields[fld] >= len(parts):
                        raise Warning("Did not find expected query field for side %d (field %s expected at %d, found only %d fields)!" % (side, fld, map_fields[fld], len(parts)))
                    else:
                        try:
                            if named:
                                query = Query.parse(parts[map_fields[fld]], names[side])
                            else:
                                query = Query.parse(parts[map_fields[fld]])
                            if query is not None:
                                queries[side] = query
                                try_parse = False
                        except Exception as e:
                            raise Warning("Failed parsing query for side %d (field %s, string %s)!\n\t%s" % (side, fld, parts[map_fields[fld]], e))

        for pi, fk in enumerate(poplist_fields):
            if fk is not None and fk in Redescription.getFieldsKeys():
                vs = parts[pi]
                if vs == '-':
                    continue
                if Redescription.getFieldsDet(fk, "supp_set", False):
                    sep = Redescription.getFieldsDet(fk, "sep", ",")
                    vs = vs.strip().split(sep)
                    if not re.search(Redescription.getFSuff(named=True)+"$", fk):
                        vs = map(int, vs)
                if re.search("f$", Redescription.getFieldsDet(fk, "fmt", "")):
                    vs =float(vs)
                elif re.search("d$", Redescription.getFieldsDet(fk, "fmt", "")):
                    vs =int(vs)
                lpartsList[fk] = vs
                    
        for side in [0, 1]:
            if queries[side] is None:
                queries[side] =  Query()
        if queries[-1] is not None:
            lpartsList["queryCOND"] = queries[-1]
        return (queries[0], queries[1], lpartsList)
    parseQueries = staticmethod(parseQueries)
    
    def parse(stringQueries, stringSupport = None, data = None, list_fields=None, sep="\t"):
        if data is not None and data.hasNames():
            names = data.getNames()
        else:
            names = [None, None]
        (queryL, queryR, lpartsList) = Redescription.parseQueries(stringQueries, list_fields, sep, names)
        status_enabled = None
        if "status_enabled" in lpartsList:
            status_enabled = int(lpartsList.pop("status_enabled"))
        r = None
        if data is not None and stringSupport is not None and type(stringSupport) == str and re.search('\t', stringSupport) :
            supportsS = SParts.parseSupport(stringSupport, data.nbRows(), data.getSSetts())
            if supportsS is not None:
                r = Redescription(queryL, queryR, supportsS.supparts(), data.nbRows(), [set(),set()], [ queryL.proba(0, data), queryR.proba(1, data)], data.getSSetts())

                for key, v in lpartsList.items():
                    tv = r.getEVal(key)
                    if tv != v:
                        raise Warning("Something wrong in the supports ! (%s: %s ~ %s)\n" \
                                  % (key, v, tv))

        if r is None:
            r = Redescription(queryL, queryR)
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
            r.status = status_enabled
        return r
    parse = staticmethod(parse)
  
    def load(queriesFp, supportsFp = None, data= None):
        stringQueries = queriesFp.readline()
        if len(stringQueries) == 0:
            return (None, -1, -1)
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

def printTexRedList(reds, names=[None, None], list_fields=None, nblines=1, standalone=False):
    try:
        red_list = sorted(reds.items())
        last_ri = red_list[-1][0]
    except AttributeError:
        red_list = enumerate(reds)
        last_ri = len(reds)-1
    if list_fields is None:
        fstyle = "tex"
        named = False        
        if names[0] is not None or names[1] is not None:
            named = True
        list_fields = Redescription.getFieldsListCust(fstyle, named=named)

    macfld_commands = "".join(Redescription.collectTexCommands(list_fields))
    ####### prepare variable names    
    names_alts = []
    names_commands = ""
    numvs_commands = ""
    macvs_commands = ""
    padss = len(digit_to_char(len(names)-1))
    for i, ns in enumerate(names):
        if ns is not None:
            names_alts.append([])
            padsv = len(digit_to_char(len(ns)-1))
            sltx = side_ltx_cmd(i, padss)
            macvs_commands += "\\newcommand{\\varname%s}[1]{\\text{\\textcolor{%sHSclr}{#1}}} \n" % (sltx, sltx)
            for ni, n in enumerate(ns):
                vlc = var_ltx_cmd(i, ni, padsv, padss)
                names_alts[i].append("$"+vlc+"{}$")
                tmp = re.sub("#", "\#", re.sub("_", "\\_", re.sub("\\\\", "\\\\textbackslash{}", n)))
                names_commands += "\\newcommand{%s}{\\varname%s{%s}}\n" % (vlc, sltx, tmp)
                numvs_commands += "%% \\newcommand{%s}{\\varname%s{v%d}}\n" % (vlc, sltx, ni)
        else:
            names_alts.append(None)
    if standalone:
        str_out = "" + \
              "\\documentclass{article}\n"+ \
              "\\usepackage{amsmath}\n"+ \
              "\\usepackage{amsfonts}\n"+ \
              "\\usepackage{amssymb}\n"+ \
              "\\usepackage{booktabs}\n"+ \
              "\\usepackage[mathletters]{ucs}\n"+ \
              "\\usepackage[utf8x]{inputenc}\n"+ \
              "\\newcommand{\\iLHS}{\\mathbf{L}} % index for left hand side\n"+ \
              "\\newcommand{\\iRHS}{\\mathbf{R}} % index for right hand side\n"+ \
              "\\newcommand{\\iCOND}{\\mathbf{C}} % index for right hand side\n"+ \
              "\\newcommand{\\SubCond}{C} % index for learn subset\n"+ \
              "\\newcommand{\\RSetLearn}{\\mathcal{O}} % index for learn subset\n"+ \
              "\\newcommand{\\RSetTest}{\\mathcal{I}} % index for test subset\n"+ \
              "\\newcommand{\\RSetAll}{} % index for test subset\n"+ \
              "\\newcommand{\\abs}[1]{\\vert#1\\vert} % absolute value\n\n"+ \
              "\\usepackage{color}\n"+ \
              "\\definecolor{LHSclr}{rgb}{.855, .016, .078} %% medium red\n"+ \
              "% \\definecolor{LHSclr}{rgb}{.706, .012, .063} %% dark red\n"+ \
              "% \\definecolor{LHSclr}{rgb}{.988, .345, .392} %% light red\n"+ \
              "\\definecolor{RHSclr}{rgb}{.055, .365, .827} %% medium blue\n"+ \
              "% \\definecolor{RHSclr}{rgb}{.043, .298, .682} %% dark blue\n"+ \
              "% \\definecolor{RHSclr}{rgb}{.455, .659, .965} %% light blue\n"+ \
              "\\definecolor{LCclr}{rgb}{.50,.50,.50} %% medium gray\n"+ \
              "\\definecolor{RNclr}{rgb}{.40, .165, .553} %% medium purple\n"+ \
              macvs_commands + \
              "\\newcommand{\\RName}[1]{\\textcolor{RNclr}{R#1}} \n"+ \
              "%% \\renewcommand{\\land}{\\text{\\textcolor{LCclr}{~AND~}}} \n"+ \
              "%% \\renewcommand{\\lor}{\\text{\\textcolor{LCclr}{~OR~}}} \n\n"+ \
              "\\DeclareMathOperator*{\\pValue}{pV}\n"+ \
              "\\DeclareMathOperator*{\\jacc}{J}\n"+ \
              "\\DeclareMathOperator*{\\supp}{supp}\n"+ \
              "\\DeclareMathOperator*{\\pr}{p}\n"+ \
              names_commands+ \
              numvs_commands+ \
              macfld_commands+ \
              "\\begin{document}\n"+ \
              "\\begin{table}[h]\n"+ \
              "\\scriptsize\n"
    else:
        str_out = "\\scriptsize\n"
    
    # str_out = ""
    with_fname=False
    if nblines == 3:
        #### SPREAD ON THREE LINES
        str_out += "\\begin{tabular}{@{\\hspace*{1ex}}p{0.05\\textwidth}@{\\hspace*{3ex}}"+ ("p{%.3f\\textwidth}" % Redescription.width_mid)
        for i in range(len(list_fields)-2):
            str_out += "@{\\hspace*{2ex}}l"
        str_out += "@{\\hspace*{1ex}}}\n"
        str_out += "\\toprule\n"
        with_fname=True
        
    elif nblines == 2:
        #### SPREAD ON TWO LINES 
        str_out += "\\begin{tabular}{@{\\hspace*{1ex}}r@{\\hspace*{1ex}}p{0.67\\textwidth}@{}r"
        for i in range(len(list_fields)-2):
            str_out += "@{\\hspace*{2ex}}r"
        str_out += "@{\\hspace*{1ex}}}\n\\toprule\n"

        str_out += " & " + Redescription.dispHeader(list_fields, style="tex") + " \\\\\n"
        str_out += "%%% & " + Redescription.dispHeader(list_fields) + " \\\\\n"
        str_out += "\\midrule\n"

    else:
        #### SINGLE LINE
        str_out += "\\begin{tabular}{@{\\hspace*{1ex}}r@{\\hspace*{1ex}}p{0.35\\textwidth}@{\\hspace*{1em}}p{0.35\\textwidth}"
        for i in range(len(list_fields)-2):
            str_out += "@{\\hspace*{2ex}}r"
        str_out += "@{\\hspace*{1ex}}}\n\\toprule\n"

        str_out += " & " + Redescription.dispHeader(list_fields, style="tex") + " \\\\\n"
        str_out += "%%% & " + Redescription.dispHeader(list_fields) + " \\\\\n"
        str_out += "\\midrule\n"

    for ri, red in red_list:
        ridstr = "\RName{%s}" %ri
        str_out += red.disp(names_alts, list_fields, style="tex", sep=" & ", with_fname=with_fname, rid=ridstr, nblines=nblines, last_one=(ri == last_ri)) + "\n" 

    str_out += "" + \
        "\\bottomrule\n"+ \
        "\\end{tabular}\n"
    if standalone:
        str_out += "\\end{table}\n"+ \
          "\\end{document}"
        ### auctex vars
        str_out += "\n%%%%%% Local Variables:\n"+ \
          "%%%%%% mode: latex\n"+ \
          "%%%%%% TeX-master: t\n"+ \
          "%%%%%% End:\n"
    return str_out

def printRedList(reds, names=[None, None], fields=None, full_supp=False, supp_names=None, nblines=1, missing=False):
    try:
        red_list = sorted(reds.items())
    except AttributeError:
        red_list = list(enumerate(reds))

    wcond = 0
    if any([red[1].hasCondition() for red in red_list]):
        wcond = -1
    fstyle = "basic"
    named = False
    if names[0] is not None or names[1] is not None:
        named = True
    all_fields = Redescription.getFieldsListCust(fstyle, named=named, wsplits=wcond, wmissing=missing)

    if type(fields) is list and len(fields) > 0:
        if fields[0] == -1:
            all_fields.extend(fields[1:])
        else:
            all_fields = fields
    if full_supp:
        all_fields.extend(Redescription.getFieldsList("supp", wmissing=missing))
    str_out = Redescription.dispHeader(all_fields, sep="\t") 
    for ri, red in red_list:
        str_out += "\n" +red.disp(list_fields=all_fields, names=names, sep="\t", supp_names=supp_names, nblines=nblines)
    return str_out

def parseRedList(fp, data, reds=None):
    list_fields = None
    sep = None
    more = []
    if reds is None:
        reds = []
    lid = 0
    for line in fp:
        lid += 1
        if len(line.strip()) > 0 and not re.match("^[ \t]*#", line):
            if list_fields is None:
                list_fields, sep = Redescription.parseHeader(line)
            else:                    
                r = Redescription.parse(line, data=data, list_fields=list_fields, sep=sep)
                if r is not None:
                    reds.append(r)
                    more.append(line)
    return reds, {"fields": list_fields, "sep": sep, "lines": more}

if __name__ == '__main__':
    # print Redescription.exp_details.keys()
    from classData import Data
    from classQuery import Query
    import sys

    rep = "/home/egalbrun/short/vaalikone_FILES/"
    rep = "/home/egalbrun/short/raja_time/"
    data = Data([rep+"data_LHS_lngtid.csv", rep+"data_RHS_lngtid.csv", {}, "NA"], "csv")

    # filename = rep+"redescriptions.csv"
    filename = rep+"tid_test.queries"
    filep = open(filename, mode='r')
    reds = Batch([])
    parseRedList(filep, data, reds)
    with open("/home/egalbrun/short/tmp_queries.txt", mode='w') as fp:
        # pdb.set_trace()
        fp.write(printRedList(reds, missing=True))
        ## fp.write(printTexRedList(reds, names = [data.getNames(0), data.getNames(1)], nblines=3, standalone=True))
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
    #     f.write(printRedList(reds))

    # with codecs.open("../../bazar/queries_list2.txt", encoding='utf-8', mode='r') as f:
    #     reds, _ = parseRedList(f, data)

    # for red in reds:
    #     print red.disp()
