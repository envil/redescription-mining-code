import tempfile
import os.path
import plistlib
import shutil
import zipfile
import re
import io
import sys

import pdb

try:
    from toolLog import Log
    from classCol import ColM
    from classRedescription import Redescription
    from classData import Data
    from classQuery import Query
    from classConstraints import Constraints, ActionsRegistry
    from classPreferencesManager import PreferencesReader, getPM, getUsage, processHelpArgs
except ModuleNotFoundError:
    from .toolLog import Log
    from .classCol import ColM
    from .classRedescription import Redescription
    from .classData import Data
    from .classQuery import Query
    from .classConstraints import Constraints, ActionsRegistry
    from .classPreferencesManager import PreferencesReader, getPM, getUsage, processHelpArgs

    
class Package(object):
    """Class to handle the zip packages that contain data, preferences, results, etc. for redescription mining.
    """

    # CONSTANTS
    # Names of the files in the package
    DATA_FILENAMES = ['data_LHS.csv',
                     'data_RHS.csv']

    REDESCRIPTIONS_FILENAME = 'redescriptions.csv'
    PREFERENCES_FILENAME = 'preferences.xml'
    FDEFS_FILENAME = {'fields_vdefs': 'fields_vdefs_custom.txt',
                      'fields_rdefs': 'fields_rdefs_custom.txt',
                      'actions_rdefs': 'actions_rdefs_custom.txt'}
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'siren_package'

    FILETYPE_VERSION = 6
    XML_FILETYPE_VERSION = 3

    RED_FN_SEP = ";"

    CREATOR = "Clired/Siren Package"
    DEFAULT_EXT = ".siren"
    DEFAULT_TMP = "siren"

    def __init__(self, filename, callback_mess=None, mode="r"):
        if filename is not None:
            filename = os.path.abspath(filename)
            if mode !="w" and not os.path.isfile(filename):
                raise IOError('File does not exist')
            if mode !="w" and not zipfile.is_zipfile(filename):
                raise IOError('File is of wrong type')
        self.filename = filename
        self.callback_mess = callback_mess
        self.plist = dict(creator = self.CREATOR,
                          filetype_version = self.FILETYPE_VERSION)

    def __str__(self):
        return "PACKAGE: %s" % self.filename

    def raiseMess(self):
        if self.callback_mess is not None:
            self.callback_mess()

    def getFilename(self):
        return self.filename

    def getPackagename(self):
        return self.plist.get('package_name')

    def getFormatV(self):
        return self.plist.get('filetype_version', -1)
    def isOldXMLFormat(self):
        return self.getFormatV() <= self.XML_FILETYPE_VERSION
    def isLatestFormat(self):
        return self.getFormatV() == self.FILETYPE_VERSION

    def getSaveFilename(self):
        svfilename = self.filename
        if self.isOldXMLFormat():
            parts = self.filename.split(".")
            if len(parts) == 1:
                svfilename += "_new"
            elif len(parts) > 1:
                svfilename = ".".join(parts[:-1]) + "_new."+ parts[-1]
        return svfilename

    def getNamelist(self):
        return self.package.namelist()

    def closePack(self):
        if self.package is not None:
            self.package.close()
            self.package = None
            
    def openPack(self):
        try:
            self.package = zipfile.ZipFile(self.filename, 'r')
            # plist_fd = self.package.open(self.PLIST_FILE, 'r')
            # self.plist = plistlib.readPlist(plist_fd)
            plist_ffd = self.package.read(self.PLIST_FILE)
            self.plist = plistlib.loads(plist_ffd)
        except Exception:
            self.package = None
            self.plist = {}
            self.raiseMess()
            raise

######### READING ELEMENTS
##########################

    def read(self, pm, options_args=None):
        elements_read = {}
        self.openPack()
        try:
            preferences = self.readPreferences(pm, options_args)
            if preferences is not None:
                elements_read["preferences"] = preferences
                
            if 'actions_rdefs' in self.plist:
                ar_fns = []
                for f in self.plist["actions_rdefs"].split(";"):
                    ff = f.strip()
                    if len(ff) > 0:
                        ar_fns.append(self.package.open(ff))
                if len(ar_fns) > 0:
                    AR = ActionsRegistry(ar_fns)
                    if "preferences" in elements_read:
                        elements_read["preferences"]["AR"] = AR
                    else:
                        elements_read["preferences"] = {"AR": AR}
                for fn in ar_fns:
                    fn.close()                   
                    
            if 'fields_vdefs' in self.plist:
                fields_fns = []
                for f in self.plist['fields_vdefs'].split(";"):
                    ff = f.strip()
                    if len(ff) > 0:
                        fields_fns.append(self.package.open(ff))                    
                ColM.extendRP(fields_fns)
                for fn in fields_fns:
                    fn.close()
                    
            if 'fields_rdefs' in self.plist:
                fields_fns = []
                for f in self.plist['fields_rdefs'].split(";"):
                    ff = f.strip()
                    if len(ff) > 0:
                        fields_fns.append(self.package.open(ff))
                Redescription.extendRP(fields_fns)
                for fn in fields_fns:
                    fn.close()

            params_l = PreferencesReader.paramsToDict(preferences)
            add_info = IOTools.getDataAddInfo(params_l, plist=self.plist, version=self.getFormatV())  
            data = self.readData(add_info)
            if data is not None:
                if 'ext_keys' in self.plist:
                    ext_keys = self.plist['ext_keys'].strip().split(";")
                    params_l = data.loadExtensions(ext_keys=ext_keys, filenames=self.plist, params=preferences, details={"package": self.package})
                    if len(params_l) > 0:
                        params = PreferencesReader(pm).readParametersDict(params_l)
                        preferences.update(params)
                    data.recomputeCols()
                elements_read["data"] = data
                reds = self.readRedescriptions(data)
                if reds is not None and len(reds) > 0:
                    elements_read["reds"] = reds
        finally:
            self.closePack()
        return elements_read

    def readPreferences(self, pm, options_args=None):
        # Load preferences
        preferences = None
        if 'preferences_filename' in self.plist:
            fd = None
            try:
                fd = self.package.open(self.plist['preferences_filename'], 'r')
                preferences = PreferencesReader(pm).getParameters(fd, options_args)
            except Exception:
                self.raiseMess()
                raise
            finally:
                if fd is not None:
                    fd.close()
        return preferences


    def readData(self, add_info):
        data = None
        if add_info is None:
            add_info = [{}, Data.NA_str]
        # Load data
        if 'data_LHS_filename' in self.plist:
            try:
                fdLHS = io.TextIOWrapper(io.BytesIO(self.package.read(self.plist['data_LHS_filename'])))
                if self.plist.get('data_RHS_filename', self.plist['data_LHS_filename']) != self.plist['data_LHS_filename']:
                    fdRHS = io.TextIOWrapper(io.BytesIO(self.package.read(self.plist['data_RHS_filename'])))
                else:
                    fdRHS = None                    
                data = Data([fdLHS, fdRHS]+add_info, "csv")
            except Exception:
                data = None
                self.raiseMess()
                raise
            finally:
                fdLHS.close()
                if fdRHS is not None: 
                    fdRHS.close()                    
        return data

    def readRedescriptions(self, data):
        reds = []
        # Load redescriptions
        rp = Redescription.getRP()
        if 'redescriptions_filename' in self.plist:
            for file_red in self.plist['redescriptions_filename'].split(self.RED_FN_SEP):
                sid = ("%s" % (len(reds) + 1))[::-1]
                try:
                    fd = io.TextIOWrapper(io.BytesIO(self.package.read(file_red)))
                    # fd = self.package.open(file_red, 'r')
                    rs = []
                    rp.parseRedList(fd, data, rs, sid=sid)
                except Exception:
                    self.raiseMess()
                    raise
                finally:
                    fd.close()
                reds.append({"items": rs, "src": ('file', file_red, 1)})
        return reds

######### WRITING ELEMENTS
##########################
    def getTmpDir(self):
        return tempfile.mkdtemp(prefix=self.DEFAULT_TMP)
            
    ## The saving function
    def writeToFile(self, filename, contents):
        # Store old package_filename
        old_package_filename = self.filename
        self.filename = os.path.abspath(filename)
        # Get a temp folder
        tmp_dir = self.getTmpDir()
        #package_dir = os.path.join(tmp_dir, filename)
        #os.mkdir(package_dir)

        # Write plist
        plist, filens = self.makePlistDict(contents)
        try:
            plistlib.writePlist(plist, os.path.join(tmp_dir, self.PLIST_FILE))
        except IOError:
            shutil.rmtree(tmp_dir)
            self.filename = old_package_filename
            self.raiseMess()
            raise

        # Write data files
        if "data" in contents:
            try:
                filenames = [os.path.join(tmp_dir, plist['data_LHS_filename']), None]
                if plist.get('data_RHS_filename', plist['data_LHS_filename']) != plist['data_LHS_filename']:
                    filenames[1] = os.path.join(tmp_dir, plist['data_RHS_filename'])
                IOTools.writeData(contents["data"], filenames, toPackage = True)
                IOTools.writeDataExtensions(contents["data"], plist, tmp_dir)
            except IOError:
                shutil.rmtree(tmp_dir)
                self.filename = old_package_filename
                self.raiseMess()
                raise

        # Write redescriptions
        if "redescriptions" in contents:
            for rs in contents["redescriptions"]:            
                try:
                    IOTools.writeRedescriptions(rs.get("items", []), os.path.join(tmp_dir, os.path.basename(rs["src"][1])),
                                        names=False, with_disabled=True, toPackage=True)
                except IOError:
                    shutil.rmtree(tmp_dir)
                    self.filename = old_package_filename
                    self.raiseMess()
                    raise

        # Write preferences
        if "preferences" in contents:
            try:
                IOTools.writePreferences(contents["preferences"], contents["pm"],
                                 os.path.join(tmp_dir, plist['preferences_filename']), toPackage = True)
            except IOError:
                shutil.rmtree(tmp_dir)
                self.filename = old_package_filename
                self.raiseMess()
                raise

        for k in self.FDEFS_FILENAME.keys():
            if k in contents:
                fn  = os.path.join(tmp_dir, plist[k])
                try:
                    with open(fn, 'w') as f:
                        f.write(contents[k])
                except IOError:
                    shutil.rmtree(tmp_dir)
                    self.filename = old_package_filename
                    self.raiseMess()
                    raise
            
        # All's there, so pack
        try:
            package = zipfile.ZipFile(self.filename, 'w')
            package.write(os.path.join(tmp_dir, self.PLIST_FILE),
                          arcname = os.path.join('.', self.PLIST_FILE))
            for eln, element in filens.items():                
                package.write(os.path.join(tmp_dir, element),
                              arcname = os.path.join('.', element),
                              compress_type = zipfile.ZIP_DEFLATED)
        except Exception:
            shutil.rmtree(tmp_dir)
            self.filename = old_package_filename
            self.raiseMess()
            raise
        finally:
            package.close()

        # All's done, delete temp file
        shutil.rmtree(tmp_dir)

    
    def makePlistDict(self, contents):
        """Makes a dict to write to plist."""
        d = dict(creator = self.CREATOR,
            filetype_version = self.FILETYPE_VERSION)
        
        if self.filename is None:
            d['package_name'] = self.PACKAGE_NAME
        else:
            (pn, suffix) = os.path.splitext(os.path.basename(self.filename))
            if len(pn) > 0:
                d['package_name'] = pn
            else:
                d['package_name'] = self.PACKAGE_NAME

        fns = {}              
        if "data" in contents:
            d['NA_str'] = contents["data"].NA_str
            fns['data_LHS_filename'] = self.DATA_FILENAMES[0]
            if not contents["data"].isSingleD():
                fns['data_RHS_filename'] = self.DATA_FILENAMES[1]
            ext_keys = contents["data"].getActiveExtensionKeys()
            if len(ext_keys) > 0:
                d['ext_keys'] = ";".join(ext_keys)
            fns.update(contents["data"].getExtensionsActiveFilesDict())    
                                
        if "preferences" in contents:
            fns['preferences_filename'] = self.PREFERENCES_FILENAME
        for k, fn in self.FDEFS_FILENAME.items():
            if k in contents:
                fns[k] = fn
        d.update(fns)
        
        if "redescriptions" in contents and len(contents["redescriptions"]) > 0:
            base_names = [os.path.basename(c["src"][1]) for c in contents["redescriptions"]]
            d['redescriptions_filename'] = self.RED_FN_SEP.join(base_names)
            for ci, c in enumerate(base_names):
                fns['redescriptions_filename_%d' %ci] = c
        return d, fns

class IOTools:
    NA_FILETYPE_VERSION = 4
    map_data_params = [{"trg": 0, "from": "delim_in", "to": "delimiter",
                        "vmap": {"(auto)": None, "TAB": '\t', "SPC": ' '}},
                        {"trg": 1, "from": "NA_str", "to": "NA_str"},
                       {"trg": 1, "from": "time_dayfirst", "to": "time_dayfirst",
                        "vmap": {"(auto)": None, "yes": True, "no": False}},
                       {"trg": 1, "from": "time_yearfirst", "to": "time_yearfirst",
                        "vmap": {"(auto)": None, "yes": True, "no": False}}]
    @classmethod
    def getDataAddInfo(tcl, params_l={}, plist={}, version=None, add_info=None):
        if add_info is None:
            add_info = [{}, {'NA_str': Data.NA_str_def}]

        for p in tcl.map_data_params:
            for src in [params_l, plist]:
                if p["from"] in src:
                    val = src[p["from"]]
                    if "vmap" in p:
                        val = p["vmap"].get(val, val)
                        if val is not None:
                            add_info[p["trg"]][p["to"]] = val
                    else:
                        add_info[p["trg"]][p["to"]] = val
        if add_info[1]['NA_str'] is None and (version is not None and version <= tcl.NA_FILETYPE_VERSION):
            add_info[1]['NA_str'] = Data.NA_str_def
        # print("ADD_INFO", add_info)
        return add_info
    
    @classmethod
    def writeRedescriptions(tcl, reds, filename, names = [None, None], with_disabled=False, toPackage = False, style="", full_supp=False, nblines=1, supp_names=None, modifiers={}, fmts=[None, None, None]):
        if names is False:
            names = [None, None]
        red_list = [red for red in reds if red.isEnabled() or with_disabled]
        if toPackage:
            fields_supp = [-1, ":extra:status"]
        else:
            fields_supp = None
        with open(filename, mode='w') as f:
            rp = Redescription.getRP()
            if style == "tex":
                f.write(rp.printTexRedList(red_list, names, fields_supp, nblines=nblines, modifiers=modifiers, fmts=fmts))
            else:
                f.write(rp.printRedList(red_list, names, fields_supp, full_supp=full_supp, supp_names=supp_names, nblines=nblines, modifiers=modifiers, fmts=fmts))

    @classmethod
    def writePreferences(tcl, preferences, pm, filename, toPackage=False, inc_def=False, core=False):
        sections = False
        helps = False
        # if toPackage:
        if preferences is None or inc_def or core:
            helps = True
        if preferences is None or inc_def:
            sections = True
        print("PARAMS", sections, helps, inc_def, core)
        with open(filename, 'w') as f:
            f.write(PreferencesReader(pm).dispParameters(preferences, sections, helps, inc_def, core))

    @classmethod
    def writeData(tcl, data, filenames, toPackage = False):        
        data.writeCSV(filenames)
    @classmethod
    def writeDataExtensions(tcl, data, plist=None, tmp_dir="./"):
        if plist is not None:
            data.saveExtensions(plist, {"tmp_dir": tmp_dir})
    @classmethod
    def saveAsPackage(tcl, filename, data, preferences=None, pm=None, reds=None, AR=None):
        package = Package(None, None, mode="w")
    
        (filename, suffix) = os.path.splitext(filename)
        contents = {}
        if data is not None:
            contents['data'] = data                                
        if reds is not None and len(reds) > 0:
            contents['redescriptions'] = (self.REDESCRIPTIONS_FILENAME, reds, range(len(reds)))
        if preferences is not None:
            if pm is None:
                pm = getPM()
            contents['preferences'] = preferences
            contents['pm'] = pm
    
        ### definitions
        vdefs = ColM.getRP().fieldsToStr()
        if len(vdefs) > 0:
            contents['fields_vdefs'] = vdefs
        rdefs = Redescription.getRP().fieldsToStr()
        if len(rdefs) > 0:
            contents['fields_rdefs'] = rdefs
        if AR is not None:
            adefs = AR.actionsToStr()
            if len(adefs) > 0:
                contents['actions_rdefs'] = adefs
            
        package.writeToFile(filename+suffix, contents)
    
    @classmethod
    def getPrintParams(tcl, filename, data=None):
        params = {"with_disabled": False, "style": "", "full_supp":False, "nblines":1,
                  "names": [None, None], "supp_names": None}
    
        named = re.search("[^a-zA-Z0-9]named[^a-zA-Z0-9]", filename) is not None
        supp_names = ( re.search("[^a-zA-Z0-9]suppnames[^a-zA-Z0-9]", filename) is not None ) or \
                     ( re.search("[^a-zA-Z0-9]suppids[^a-zA-Z0-9]", filename) is not None )
    
        params["with_disabled"] = re.search("[^a-zA-Z0-9]all[^a-zA-Z0-9]", filename) is not None
        params["full_supp"] = ( re.search("[^a-zA-Z0-9]support[^a-zA-Z0-9]", filename) is not None ) or supp_names
                
        if re.search(".tex$", filename):
            params["style"] = "tex"
    
        tmp = re.search("[^a-zA-Z0-9](?P<nbl>[1-3]).[a-z]*$", filename)
        if tmp is not None:
            params["nblines"] = int(tmp.group("nbl"))
    
        if named and data is not None:
            params["names"] = data.getNames()
            params["fmts"] = data.getFmts()       
        if supp_names:
            params["supp_names"] = data.getRNames()
        return params

    @classmethod
    def prepareFilenames(tcl, params_l, tmp_dir=None, src_folder=None):
        filenames = {"queries": "-",
                     "style_data": "csv",
                     "add_info": tcl.getDataAddInfo(params_l)
                     }
        
        for p in ['result_rep', 'data_rep', 'extensions_rep']:
            if p not in params_l:
                params_l[p] = ""
            if sys.platform != 'win32':
                if src_folder is not None and re.match("./", params_l[p]):
                    params_l[p] = src_folder+params_l[p][1:]
                elif params_l[p] == "__TMP_DIR__":
                    if tmp_dir is None:
                        tmp_dir = tempfile.mkdtemp(prefix='clired')
                    params_l[p] = tmp_dir + "/"
                elif sys.platform != 'darwin':
                    params_l[p] = re.sub("~", os.path.expanduser("~"), params_l[p])
    
        ### Make data file names
        filenames["LHS_data"] = ""
        if len(params_l.get("LHS_data", "")) != 0:
            filenames["LHS_data"] = params_l['LHS_data']
        elif len(params_l.get('data_l', "")) != 0:
            filenames["LHS_data"] = params_l['data_rep']+params_l['data_l']+params_l.get('ext_l', "")
                      
        filenames["RHS_data"] = ""
        if len(params_l.get("RHS_data", "")) != 0 :
            filenames["RHS_data"] = params_l['RHS_data']
        elif len(params_l.get('data_r', "")) != 0:
            filenames["RHS_data"] = params_l['data_rep']+params_l['data_r']+params_l.get('ext_r', "")
    
        if len(params_l.get("trait_data", "")) != 0 :
            filenames["traits_data"] = params_l['traits_data']
        elif len(params_l.get('data_t', "")) != 0:
            filenames["traits_data"] = params_l['data_rep']+params_l['data_t']+params_l.get('ext_t', "")    
            
        if os.path.splitext(filenames["LHS_data"])[1] != ".csv" or os.path.splitext(filenames["RHS_data"])[1] != ".csv":
            filenames["style_data"] = "multiple"
            filenames["add_info"] = []
    
        if len(params_l.get("extensions_names", "")) != 0:
            filenames["extensions"] = {}
            extkf = params_l.get("extensions_names", "")
            for blck in extkf.strip().split(";"):
                parts = [p.strip() for p in blck.split("=")]
                if len(parts) == 2:
                    filenames["extensions"]["extf_"+parts[0]] = params_l["extensions_rep"] + parts[1]
    
            
        ### Make queries file names
        if len(params_l.get("queries_file", "")) != 0 :
            filenames["queries"] = params_l["queries_file"]
        elif params_l.get('out_base', "-") != "-"  and len(params_l['out_base']) > 0 and len(params_l.get('ext_queries', ".queries")) > 0:
            filenames["queries"] = params_l['result_rep']+params_l['out_base']+params_l.get('ext_queries', ".queries")
    
        if filenames["queries"] != "-":
            if not os.path.isfile(filenames["queries"]):
                try:
                    tfs = open(filenames["queries"], "a")
                    tfs.close()
                    os.remove(filenames["queries"])
                except IOError:
                    print("Queries output file not writable, using stdout instead...")
                    filenames["queries"] = "-"
        parts = filenames["queries"].split(".")
        basis = ".".join(parts[:-1])
        filenames["basis"] = basis
    
        ### Make named queries file name
        if filenames["queries"] != "-" and params_l.get("queries_named_file", "") == "+":
            filenames["queries_named"] = basis+"_named."+parts[-1]
        elif len(params_l.get("queries_named_file", "")) > 0:
            filenames["queries_named"] = params_l["queries_named_file"]
    
        ### Make support file name
        if filenames["queries"] != "-" and params_l.get("support_file", "") == "+" and len(params_l.get('ext_support', "")) > 0:
            filenames["support"] = basis+params_l['ext_support']
        elif len(params_l.get("support_file", "")) > 0:
            filenames["support"] = params_l["support_file"]
    
        ### Make log file name
        if filenames["queries"] != "-" and params_l.get('logfile', "") == "+" and len(params_l.get('ext_log', "")) > 0:
            filenames["logfile"] = basis+params_l['ext_log']
        elif len(params_l.get('logfile', "")) > 0:
            filenames["logfile"] = params_l['logfile']
    
        if len(params_l.get("series_id", "")) > 0:
            for k in filenames.keys():
                if type(filenames[k]) is str:
                    filenames[k] = filenames[k].replace("__SID__", params_l["series_id"])

        if src_folder is not None and re.match("/", src_folder):
            ks = list(filenames.keys()) + list(filenames.get("extensions", {}).keys())
            for k in ks:
                if k not in ["style_data", "add_info", "extensions"] \
                    and len(filenames[k]) > 0 and filenames[k]!="-" and not re.match("/", filenames[k]):
                    filenames[k] = src_folder+"/"+filenames[k]
                        
        return filenames
    @classmethod
    def outputResults(tcl, filenames, results, data=None, with_headers=True, mode="w", data_recompute=None):
        rp = Redescription.getRP()
        modifiers, modifiers_recompute = {}, {}
        if data is not None:
            modifiers = rp.getModifiersForData(data)
        if data_recompute is not None:
            modifiers_recompute = rp.getModifiersForData(data_recompute)
        fstyle = "basic"
        
        header_recompute = ""
        if data_recompute is not None:
            fields_recompute = rp.getListFields("stats", modifiers_recompute)
            header_recompute = rp.dispHeaderFields(fields_recompute) + "\tacc_diff"
    
        filesfp = {"queries": None, "queries_named": None, "support": None}
        if filenames["queries"] == "-":
            filesfp["queries"] = sys.stdout
        else:
            filesfp["queries"] = open(filenames["queries"], mode)
        all_fields = rp.getListFields(fstyle, modifiers)
        if with_headers:
            filesfp["queries"].write(rp.dispHeaderFields(all_fields)+"\t"+header_recompute+"\n")
    
        names = None
        if data is not None and data.hasNames() and "queries_named" in filenames:
            names = data.getNames()
            filesfp["queries_named"] = open(filenames["queries_named"], mode)
            if with_headers:
                filesfp["queries_named"].write(rp.dispHeaderFields(all_fields)+"\t"+header_recompute+"\n")
        
        if "support" in filenames:
            filesfp["support"] = open(filenames["support"], mode)
            
        #### TO DEBUG: output all shown in siren, i.e. no filtering
        addto = ""
        for org in results:            
            if data_recompute is not None:
                red = org.copy()
                red.recompute(data_recompute)
                acc_diff = (red.getAcc()-org.getAcc())/org.getAcc()
                addto = "\t"+red.disp(list_fields=fields_recompute)+"\t%f" % acc_diff
            filesfp["queries"].write(org.disp(list_fields=all_fields)+addto+'\n')
            if filesfp["queries_named"] is not None:
                filesfp["queries_named"].write(org.disp(names, list_fields=all_fields)+addto+'\n')
            if filesfp["support"] is not None:
                filesfp["support"].write(org.dispSupp()+'\n')
    
        for (ffi, ffp) in filesfp.items():
            if ffp is not None and filenames.get(ffi, "") != "-":
                ffp.close()
    @classmethod
    def loadAll(tcl, arguments=[], conf_defs=None):
        pm = getPM(conf_defs)
        pr = PreferencesReader(pm)
        
        exec_folder = os.path.dirname(os.path.abspath(__file__))
        src_folder = exec_folder
    
        package = None
        pack_filename = None
        config_filename = None
        tmp_dir = None
        params = None
        reds = None
        params = None
        queries_second = None
        
        proceed = processHelpArgs(arguments, pr)
        if proceed:
            if os.path.isfile(arguments[1]):
                if os.path.splitext(arguments[1])[1] == Package.DEFAULT_EXT:
                    pack_filename = arguments[1]
                    if len(arguments) > 2 and os.path.isfile(arguments[2]):
                        config_filename = arguments[2]
                        options_args = arguments[3:]
                    else:
                        options_args = arguments[2:]
                else:
                    config_filename = arguments[1]
                    options_args = arguments[2:]
            else:
                options_args = arguments[1:]
                    
            if pack_filename is not None:
                src_folder = os.path.dirname(os.path.abspath(pack_filename))
                package = Package(pack_filename)
                elements_read = package.read(pm)        
                data = elements_read.get("data", None)
                reds = elements_read.get("reds", None)
                params = elements_read.get("preferences", None)
                tmp_dir = package.getTmpDir()
            
            elif config_filename is not None:
                src_folder = os.path.dirname(os.path.abspath(config_filename))
    
            if options_args is not None:
                try:
                    params = pr.getParameters(config_filename, options_args, params)        
                except AttributeError:
                    queries_second = config_filename
                    
        if params is None:
            print(getUsage(arguments[0]))
            sys.exit(2)
    
        params_l = PreferencesReader.paramsToDict(params)
        filenames = tcl.prepareFilenames(params_l, tmp_dir, src_folder)
        if queries_second is not None:
            filenames["queries_second"] = queries_second
        logger = Log(verbosity=params_l['verbosity'], output=filenames["logfile"])
    
        if pack_filename is None:
            data = Data([filenames["LHS_data"], filenames["RHS_data"]]+filenames["add_info"], filenames["style_data"])
            data.loadExtensions(ext_keys=params_l.get("activated_extensions", []), filenames=filenames.get("extensions"), params=params_l)
        logger.printL(2, data, "log")
    
        if pack_filename is not None:
            filenames["package"] = os.path.abspath(pack_filename)
        print(filenames)
        return {"params": params, "data": data, "logger": logger,
                "filenames": filenames, "reds": reds, "pm": pm, "package": package}
