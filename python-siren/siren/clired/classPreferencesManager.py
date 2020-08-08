import getopt, re, os.path, sys
try:
    import toolXML, toolICDict
except ModuleNotFoundError:
    from . import toolXML, toolICDict
import pdb

### EACH parameter is a triplet (text, data, value)
### text is the raw text
### data is the text casted into the type of the parameter
### in case of option parameters value is the index of the option among available ones
### otherwise it is equal to data

### for color parameter, both data and value are the integer triplets representation

USAGE_DEF_HEADER = "Clired redescription mining"
USAGE_DEF_URL_HELP = "https://members.loria.fr/EGalbrun/siren/help/"

class CParameter(object):
    type_id = "X"
    type_str = "X"
    value_types = {"text": str, "boolean": bool, "integer": int, "float": float, "color": str}

    def __init__(self,  name=None, label=None, default=None, value_type=None, legend=None):
        self._name = name
        self._label = label
        self._default = default
        self._legend = legend
        self._value_type = value_type
        self._pfr = None

    def getCardinality(self):
        return "unique"

    def isDefault(self, triplet):
        return triplet.get("value") == self._default
    
    def isCore(self):
        return re.match("CORE", self._legend) is not None
    
    def getPathFromRoot(self):
        return self._prf

    def setPathFromRoot(self, pfr):
        self._prf = tuple(pfr)

    def getId(self):
        return self._name

    def getTypeDets(self):
        return self.type_str

    def getName(self):
        return self._name

    def getLegend(self):
        return re.sub("CORE *", "", self._legend)

    def getInfo(self):
        return "%s (%s)" % ( self.getLegend(), self.getTypeDets() ) 

    def getDefaultValue(self):
        return self._default

    def getDefaultData(self):
        return self._default

    def getDefaultText(self):
        return str(self._default)

    def getDefaultTriplet(self):
        return {"value": self.getDefaultValue(), "data": self.getDefaultData(), "text": self.getDefaultText()}

    def getLabel(self):
        return self._label

    def parseNode(self, node):
        self._name = toolXML.getTagData(node, "name")
        self._legend = toolXML.getTagData(node, "legend")
        if self._name is None:
            raise Exception("Name for param undefined!")
        self._label = toolXML.getTagData(node, "label")
        if self._label is None:
            raise Exception("Label for param %s undefined!"% self._name)
        tmp_vt = toolXML.getTagData(node, "value_type")
        if tmp_vt in self.value_types:
            self._value_type = self.value_types[tmp_vt]
        if self._value_type is None:
            raise Exception("Value type for param %s undefined!"% self._name)

    def __str__(self):
        return "Parameter (%s): %s" % (self.type_id, self._name)

    def getParamValue(self, raw_value):
        return toolXML.parseToType(raw_value, self._value_type)

    def getParamData(self, raw_value):
        return self.getParamValue(raw_value)

    def getParamText(self, raw_value):
        tmp = toolXML.parseToType(raw_value, self._value_type)
        if tmp is not None:
            return str(tmp)
        return None
        
    def getParamTriplet(self, raw_value):
        tmp = toolXML.parseToType(raw_value, self._value_type)
        if tmp is not None:
            return {"value": tmp, "data": tmp, "text": str(tmp)}
        else:
            return None

class OpenCParameter(CParameter):
    type_id = "open"
    type_str = "open text"
    
    def __init__(self, name=None, label=None, default=None, value_type=None, length=None, legend=None):
        CParameter.__init__(self, name, label, default, value_type, legend)
        self._length = length

    def parseNode(self, node):
        CParameter.parseNode(self, node)
        self._length = toolXML.getTagData(node, "length", int)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            self._default = toolXML.getValue(et[0], self._value_type)
        if self._default is None:
            raise Exception("Default value for param %s undefined!"% self._name)

class RangeCParameter(CParameter):
    type_id = "range"
    type_str = "range"
    
    def __init__(self, name=None, label=None, default=None, value_type=None, range_min=None, range_max=None, legend=None):
        CParameter.__init__(self, name, label, default, value_type, legend)
        self._range_min = range_min
        self._range_max = range_max

    def parseNode(self, node):
        CParameter.parseNode(self, node)
        self._range_min = toolXML.getTagData(node, "range_min", self._value_type)
        self._range_max = toolXML.getTagData(node, "range_max", self._value_type)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            self._default = toolXML.getValue(et[0], self._value_type)
        if self._default is None or self._range_min is None or self._range_max is None \
               or self._default < self._range_min or self._default > self._range_max:
            raise Exception("Default value for param %s not in range!"% self._name)

    def getTypeDets(self):
        return "%s in [%s, %s]" % (self.type_str, self._range_min, self._range_max)

    def getParamValue(self, raw_value):
        tmp =  toolXML.parseToType(raw_value, self._value_type)
        if tmp is not None and tmp >= self._range_min and tmp <= self._range_max:
            return tmp
        return None

    def getParamData(self, raw_value):
        return self.getParamValue(raw_value)

    def getParamText(self, raw_value):
        tmp = toolXML.parseToType(raw_value, self._value_type)
        if tmp is not None and tmp >= self._range_min and tmp <= self._range_max:
            return str(tmp)
        return None
        
    def getParamTriplet(self, raw_value):
        tmp = toolXML.parseToType(raw_value, self._value_type)
        if tmp is not None and tmp >= self._range_min and tmp <= self._range_max:
            return {"value": tmp, "data": tmp, "text": str(tmp)}
        else:
            return None

class SingleOptionsCParameter(CParameter):
    type_id = "single_options"
    type_str = "single option"

    def __init__(self, name=None, label=None, default=None, value_type=None, options=None, legend=None):
        CParameter.__init__(self, name, label, default, value_type, legend)
        self._options = options

    def parseNode(self, node):
        CParameter.parseNode(self, node)
        et = node.getElementsByTagName("options")
        if len(et) > 0:
            self._options = toolXML.getValues(et[0], self._value_type)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            self._default = toolXML.getValue(et[0], int)
        if self._default is None or self._default < 0 or self._default >= len(self._options):
            raise Exception("Default value for param %s not among options!"% self._name)

    def getTypeDets(self):
        return "%s in {%s}" % (self.type_str, ",".join( self.getOptionsText()))

    def getParamValue(self, raw_value, index=False):
        if index:
            tmp =  toolXML.parseToType(raw_value, int)
            if tmp is not None and tmp >= 0 and tmp < len(self._options):
                return tmp
        else:
            tmp =  toolXML.parseToType(raw_value, self._value_type)
            if tmp is not None and tmp in self._options:
                return self._options.index(tmp)
        return None

    def getParamData(self, raw_value, index=False):
        if index:
            tmp =  toolXML.parseToType(raw_value, int)
            if tmp is not None and tmp >= 0 and tmp < len(self._options):
                return self._options[tmp]
        else:
            tmp =  toolXML.parseToType(raw_value, self._value_type)
            if tmp is not None and tmp in self._options:
                return tmp
        return None

    def getParamText(self, raw_value, index=False):
        tmp = self.getParamData(raw_value, index)
        if tmp is not None:
            return str(tmp)
        return None
        
    def getParamTriplet(self, raw_value, index=False):
        tmp = self.getParamValue(raw_value, index)
        if tmp is not None:
            return {"value": tmp, "data": self._options[tmp], "text": str(self._options[tmp])}
        else:
            return None

    def getOptionsText(self):
        return list(map(str, self._options))

    def getDefaultText(self):
        return str(self._options[self._default])

    def getDefaultData(self):
        return self._options[self._default]


class BooleanCParameter(SingleOptionsCParameter):
    type_id = "boolean"
    type_str = "yes/no"
    opts_data = [False, True]   
    map_str = {"yes": True, "no": False,
               "true": True, "false": False,
               "t": True, "f": False,
               "1": True, "0": False}
    inv_str = {True: "yes", False: "no"}
    
    def __init__(self, name=None, label=None, default=None, value_type=bool, options=None, legend=None):
        CParameter.__init__(self, name, label, default, value_type, legend)
        self._options = self.opts_data

    def parseNode(self, node):        
        CParameter.parseNode(self, node)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            self._default = toolXML.getValue(et[0], bool)
        if self._default is None:
            raise Exception("Default value for param %s not among options!"% self._name)

    def getParamValue(self, raw_value, index=False):
        if index:
            tmp =  toolXML.parseToType(raw_value, int)
            if tmp is not None and tmp >= 0 and tmp < len(self._options):
                return tmp
        else:
            try:
                return int(self.map_str[raw_value.lower()])
            except (KeyError, AttributeError):
                return None
        return None

    def getParamData(self, raw_value, index=False):
        if index:
            tmp =  toolXML.parseToType(raw_value, int)
            if tmp is not None and tmp >= 0 and tmp < len(self._options):
                return self._options[tmp]
        return self.map_str.get(raw_value)

    def getParamText(self, raw_value, index=False):
        tmp = self.getParamData(raw_value, index)
        if tmp is not None:
            return self.inv_str.get(tmp)
        return None
        
    def getParamTriplet(self, raw_value, index=False):
        tmp = self.getParamValue(raw_value, index)
        if tmp is not None:
            return {"value": tmp, "data": self._options[tmp], "text": self.inv_str[self._options[tmp]]}
        else:
            return None
        
    def getTypeDets(self):
        return self.type_str
        
    def getDefaultValue(self):
        return int(self._default)
        
    def getDefaultText(self):
        return self.inv_str[self._default]

    def getDefaultData(self):
        return self._default
        
    def getOptionsText(self):
        return [self.inv_str[o] for o in self._options]

        
class MultipleOptionsCParameter(SingleOptionsCParameter):
    type_id = "multiple_options"
    type_str = "multiple options"

    def parseNode(self, node):
        CParameter.parseNode(self, node)
        et = node.getElementsByTagName("options")
        if len(et) > 0:
            self._options = toolXML.getValues(et[0], self._value_type)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            self._default = toolXML.getValues(et[0], int)
        if self._default is None or ( len(self._default) > 0 and (min(self._default) < 0 or max(self._default) >= len(self._options) ) ):
            raise Exception("Some default value for param %s not among options!"% self._name)        
    def getEmptyTriplet(self):
        return {"value": [], "data": [], "text": []}

    def getDefaultData(self):
        return [self._options[i] for i in self._default]
    
    def getDefaultText(self):
        return [str(self._options[i]) for i in self._default]

    def getCardinality(self):
        return "multiple"

class ColorCParameter(CParameter):
    type_id = "color_pick"
    type_str = "color #RRGGBB"
    match_p = "^#(?P<rr>[0-9A-Fa-f][0-9A-Fa-f])(?P<gg>[0-9A-Fa-f][0-9A-Fa-f])(?P<bb>[0-9A-Fa-f][0-9A-Fa-f])$"
    
    def parseNode(self, node):
        CParameter.parseNode(self, node)
        et = node.getElementsByTagName("default")
        if len(et) > 0:
            tmp = toolXML.getValue(et[0], self._value_type)
            self._default = self.txtToCol(tmp)

        if self._default is None:
            raise Exception("Default value for param %s not correct!"% self._name)

    def getParamValue(self, raw_value):
        tmp =  toolXML.parseToType(raw_value, self._value_type)
        return self.txtToCol(tmp)

    def getParamData(self, raw_value):
        return self.getParamValue(raw_value)

    def getParamText(self, raw_value):
        if type(raw_value) is tuple:
            return self.colToTxt(raw_value)
        else:
            tmp =  toolXML.parseToType(raw_value, self._value_type)
            if tmp is not None and re.match(self.match_p, tmp):
                return tmp
        return None
        
    def getParamTriplet(self, raw_value):
        if type(raw_value) is tuple:
            v = raw_value
            tmp = self.colToTxt(raw_value)
        else:
            tmp = toolXML.parseToType(raw_value, self._value_type)
            v = self.txtToCol(tmp)
        if tmp is not None and v is not None:
            return {"value": v, "data": v, "text": tmp}
        return None

    def colToTxt(self, tuple_value):
        return "#"+"".join([ v.replace("x", "")[-2:] for v in map(hex, tuple_value)])

    def txtToCol(self, txt_value):
        if txt_value is not None:
            g = re.match(self.match_p, txt_value)
            if g is not None:
                try:
                    return (int(g.group("rr"), 16), int(g.group("gg"), 16), int(g.group("bb"), 16))
                except:
                    raise Warning("Could not parse color %s!" % txt_value)
        return None
        

class PreferencesManager(object):
    parameter_types = {"open": OpenCParameter,
               "range": RangeCParameter,               
               "single_options": SingleOptionsCParameter,
               "boolean": BooleanCParameter,
               "multiple_options": MultipleOptionsCParameter,
               "color_pick": ColorCParameter}
    MTCH_ST = "^(?P<basis>[^0-9]*)((_s(?P<side>[01])_(?P<typ>[0-9]))|(_s(?P<oside>[01]))|(_(?P<otyp>[0-9])))$"

    def __init__(self, filenames):
        self.subsections = []
        self.pdict = {}
        
        if type(filenames) == str:
            filenames = [filenames]
        for filename in filenames:
             if filename is not None:
                doc = toolXML.parseXML(filename)
                if doc is not None:
                    params = self.processDom(doc.documentElement)
                    if type(params) == dict and len(params) == 1 and "subsections" in params:
                               self.subsections.extend(params["subsections"])

    def __str__(self):
        strd = "Preferences manager:\n"
        for sec in self.getTopSections():
            strd += self.dispSection(sec)
        return strd

    def getTopSections(self):
        return self.subsections
    def getSectionByName(self, name):
        tmp = [(ti, t) for (ti, t) in enumerate(self.getTopSections()) if t["name"] == name]
        if len(tmp) == 1:
            return tmp[0]
        else:
            return (None, None)

        
    def dispSection(self, parameters, level=0):
        strs = ("\t"*level)+("[%s]\n" % parameters.get("name", ""))
        for k in self.parameter_types.keys():
            if len(parameters[k]) > 0:
                strs += ("\t"*level)+("   * %s:\n" % k)
            for item_id in parameters[k]:
                item = self.pdict[item_id]
                tmp_str = str(item)
                tmp_str.replace("\n", "\n"+("\t"*(level+1)))
                strs += ("\t"*(level+1))+tmp_str+"\n"
        if len(parameters["subsections"]) > 0:
            strs += ("\t"*level)+("   * subsections:\n")
        for k in parameters["subsections"]:
            strs += self.dispSection(k, level+1)
        return strs

    def getItem(self, item_id):
        return self.pdict.get(item_id, None)

    def getNameSidesTypes(self, name):
        tmp = re.match(self.MTCH_ST, name)
        if tmp is not None:
           return (tmp.group("basis"),
                       int(tmp.group("side") or tmp.group("oside") or -1),
                       int(tmp.group("typ") or tmp.group("otyp") or -1))
        return (name, -1, -1)
       
    def getItemsSidesTypes(self):
        dd = {}
        for k in self.pdict.keys():
            tmp = self.getNameSidesTypes(k)
            if tmp[1] != -1 or tmp[2] != -1:
                dd[k] = tmp
        return dd
    
    def getDefaultTriplets(self):
        return dict([(item_id, item.getDefaultTriplet())
                 for (item_id, item) in self.pdict.items()])

    def getListOptions(self):
        return [item.getName()+"=" for (item_id, item) in self.pdict.items()]

    def processDom(self, current, sects=[]):
        parameters = None
        name = None
        if toolXML.isElementNode(current):
            if toolXML.tagName(current) in ["root", "section"]:
                parameters = {"subsections": []}
                if toolXML.tagName(current) == "section":
                    parameters["name"] = toolXML.getTagData(current, "name")
                    for k in self.parameter_types.keys():
                        parameters[k] = []
                    sects = list(sects + [parameters["name"]])
                for child in toolXML.children(current):
                    tmp = self.processDom(child, sects)
                    if tmp is not None:
                        if type(tmp) == dict:
                            parameters["subsections"].append(tmp)
                        elif tmp.type_id in parameters.keys():
                            tmp_id = tmp.getId()
                            if tmp_id in self.pdict:
                                raise Exception("Encountered two parameters with same id %s!" % tmp_id)
                            else:
                                self.pdict[tmp_id] = tmp  
                                parameters[tmp.type_id].append(tmp_id)
            if toolXML.tagName(current) == "parameter":
                name = toolXML.getTagData(current, "name")
                parameter_type = toolXML.getTagData(current, "parameter_type")
                if parameter_type in self.parameter_types.keys():
                    parameters = self.parameter_types[parameter_type]()
                    parameters.parseNode(current)
                    parameters.setPathFromRoot(sects)
        if parameters is not None:
            return parameters


class PreferencesReader(object):
    def __init__(self, pm):
        self.pm = pm

    @classmethod
    def paramsToDict(tcl, params, with_num=False):
        params_l = {}
        if type(params) in [dict, toolICDict.ICDict]:
            for k, v in params.items():
                if type(v) is dict and "data" in v:
                    params_l[k] = v["data"]
                    if with_num and "value" in v and v["data"] != v["value"]:
                        params_l[k+":NUM"] = v["value"]                
        return params_l
        
    def getParametersDict(self, filename=None, arguments=None, pv=None):
        return self.paramsToDict(self.getParameters(filename, arguments, pv), with_num=True)
    
    def getParameters(self, filename=None, arguments=None, pv=None):
        if pv is None:
            pv = self.pm.getDefaultTriplets()
        if filename is not None:
            tmp = self.readParametersDict(self.readParametersFromFile(filename))
            pv.update(tmp)
        if arguments is not None:
            tmp = self.readParametersDict(self.readParametersFromArguments(arguments))
            pv.update(tmp)
        return pv

    def readParametersFromArguments(self, arguments):
        options, args = getopt.getopt(arguments, "", self.pm.getListOptions())
        tmp = {}
        for (option, vals) in options:
            tmp[option.strip(" -")] = vals.strip().split(",")
        return tmp
            
    def readParametersFromFile(self, filename):
        tmp = {}
        if filename is not None:
            try:
                doc = toolXML.parseXML(filename)
            except Exception as inst:
                print("%s is not a valid configuration file! (%s)" % (filename, inst))
            else:
                for current in doc.documentElement.getElementsByTagName("parameter"):
                    name = toolXML.getTagData(current, "name")
                    values = toolXML.getValues(current)
                    tmp[name] = values
        return tmp
    
    def readParametersDict(self, params_dict):
        pv = {}
        non_matched = {}
        tt = self.pm.getItemsSidesTypes()
        bb_matched = {}
        for tk, t in tt.items():
            if not t[0] in bb_matched:
                bb_matched[t[0]] = []
            bb_matched[t[0]].append((tk, t[1], t[2]))

        for name, values in params_dict.items():
            item = self.pm.getItem(name)
            if item is not None:
                self.prepareItemVal(pv, item, name, values)
            else:
                tmp = self.pm.getNameSidesTypes(name)
                if tmp[0] in bb_matched:
                    non_matched[name] = tmp
        if len(non_matched):
            fill_matched = {}
            kk = sorted(non_matched.keys())
            for k in kk:
                cbasis, cside, ctyp = non_matched[k]
                for elem in bb_matched[cbasis]:
                    if (elem[1] == cside or elem[1] == -1 or -1 == cside) and (elem[2] == ctyp or elem[2] == -1 or -1 == ctyp):
                        fill_matched[elem[0]] = k
            # print("fill_matched", fill_matched)
            for name, nn in fill_matched.items():
                values = params_dict[nn]
                item = self.pm.getItem(name)
                if item is not None:
                    self.prepareItemVal(pv, item, name, values)
        return pv

    def prepareItemVal(self, pv, item, name, values):
        try:
            len(values)
        except TypeError:
            values = [values]
        if len(values) == 1 and item.getCardinality()=="unique":
            value = item.getParamTriplet(values[0])
            if value is not None:
                pv[name] = value
        elif item.getCardinality()=="multiple":
            tmp_opts = []
            tmp_ok = True
            for tmp_s in values:
                tmp = item.getParamTriplet(tmp_s)
                if tmp is not None:
                    tmp_opts.append(tmp)
                else:
                    tmp_ok = False
            if tmp_ok:
                # if name == 'map_elem_circ' or name == 'rhs_neg_query_2':
                #     pdb.set_trace()
        
                values = {}
                if len(tmp_opts) > 0:
                    for k in tmp_opts[0].keys():
                        values[k] = []
                        for t in tmp_opts:
                            values[k].append(t[k])
                else:
                    values = {'text': [], 'data': [], 'value': []}
                pv[name] = values

    def dispParametersRec(self, parameters, pv, level=0, sections=True, helps=False, defaults=False, core=False):
        indents = ""
        strd, header, footer = ("", "", "")
        if sections:
            indents = "\t"*(level+1)
            header = ("\t"*level)+"<section>\n"+indents+("<name>%s</name>\n" % parameters.get("name", ""))
            footer = ("\t"*level)+"</section>\n"
        
        for k in self.pm.parameter_types.keys():
            for item_id in parameters[k]:
                item = self.pm.getItem(item_id)
                if pv is None or item_id not in pv:
                    vs = item.getDefaultTriplet()
                else:
                    vs = pv[item_id]
                if item is not None and ((core and item.isCore()) or (defaults or not item.isDefault(vs))):
                    strd += indents+"<parameter>\n"
                    strd += indents+"\t<name>"+ item.getName() +"</name>\n"
                    if sections:
                        strd += indents+"\t<label>"+ item.getLabel() +"</label>\n"
                    if helps:
                        strd += indents+"\t<info>"+ item.getInfo() +"</info>\n"
                    if type(vs["text"]) == list:
                        for v in vs["text"]:
                            strd += indents+"\t<value>"+ v +"</value>\n"
                    else:
                        strd += indents+"\t<value>"+ vs["text"] +"</value>\n"
                    strd += indents+"</parameter>\n"

        for k in parameters["subsections"]:
            strd += self.dispParametersRec(k, pv, level+1, sections, helps, defaults, core)
        if len(strd) > 0:
            return header + strd + footer
        else:
            return ""


    def dispParameters(self, pv=None, sections=True, helps=False, defaults=False, core=False):            
        strd = ""
        for subsection in self.pm.subsections:
            ## print("---SUBSECTION:", subsection.get("name"))
            strd += self.dispParametersRec(subsection, pv, 0, sections, helps, defaults, core)
        if len(strd) == 0:
            strd = "<!-- Using only default parameters --> "
        return "<root>\n"+strd+"</root>"

# def rdictStr(rdict, level=0):
#     strd = ""
#     for k, v in rdict.items():
#         strd += ("\t"*level)+"["+str(k)+"]\n"
#         if type(v) == dict:
#             strd += rdictStr(v, level+1)
#         else:
#             tmp_str = str(v)
#             tmp_str.replace("\n", "\n"+("\t"*(level+1)))
#             strd += ("\t"*(level+1))+tmp_str+"\n"
#     return strd

def getUsage(arg_zero, header=None, footer=None):
    if header is None:
        header = USAGE_DEF_HEADER +"\n"
    if footer is None:
        footer = "\nFor more details see "+USAGE_DEF_URL_HELP+"formats.html and "+USAGE_DEF_URL_HELP+"preferences.html#mining-parameters"

    exec_name = arg_zero.split("/")[-1].replace(".py", "")
    return (
        f'{header}'
        f'usage: "{exec_name} [config_file] [additional_parameters]"\n'
        f'       Type "{exec_name} --config" to generate a default configuration file\n'
        f'         or "{exec_name} --template" to generate a basic configuration template{footer}'
        )

def processHelpArgs(arguments, pr):
    if len(arguments) > 1:
        if arguments[1] == "--help" or arguments[1] == "-h":
            return False
        elif arguments[1] == "--template":
            print(pr.dispParameters(pv=None, sections=False, helps=True, defaults=False, core=True))
            sys.exit(2)
        elif arguments[1] == "--config":
            print(pr.dispParameters(pv=None, sections=True, helps=True, defaults=True, core=False))
            sys.exit(2)
        return True
    return False
    

def getParams(arguments, conf_defs):
    pm = PreferencesManager(conf_defs)
    pr = PreferencesReader(pm)
    config_filename = None
    params = None

    proceed = processHelpArgs(arguments, pr)
    if proceed:
        if os.path.isfile(arguments[1]):
            config_filename = arguments[1]
            options_args = arguments[2:]
        else:
            options_args = arguments[1:]
        params = pr.getParametersDict(config_filename, options_args)
        
    if params is None:
        print(getUsage(arguments[0]))
        sys.exit(2)

    return params


conf_names = {"miner": 0, "inout": 0, "dataext": 1, "rnd": 1}
def getPM(conf_defs=None):
    if conf_defs is None:
        conf_defs = [k for (k,v) in conf_names.items() if v == 0]
    pref_dir = os.path.dirname(os.path.abspath(__file__))
    conf_files = ["%s/%s_confdef.xml" % (pref_dir, c) if c in conf_names else c for c in conf_defs]
    return PreferencesManager(conf_files)

if __name__ == "__main__":
    import glob, os.path, sys
    pref_dir = os.path.dirname(os.path.abspath(__file__))
    conf_defs = glob.glob(pref_dir + "/*_confdef.xml")
    params = getParams(sys.argv, conf_defs)
    print(params)
