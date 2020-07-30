import os.path
import collections
import sys
import re

import time

import pdb

from ..clired.toolICList import ICList
from ..clired.toolICDict import ICDict
from ..clired.toolLog import Log
from ..clired.classContent import StoredRCollection

from ..clired.classCol import DataError, ColM
from ..clired.classData import Data

from ..clired.classQuery import Query, Literal
from ..clired.classRedescription import Redescription
from ..clired.classConstraints import Constraints

from ..clired.classPreferencesManager import PreferencesManager, PreferencesReader
from ..clired.classPackage import Package, IOTools


class DataWrapper(object):
    """Contains all the data
    """
    def __init__(self, logger=None, package_filename = None, conf_defs=[]):
        """Inits the class. Either package_filename or the others should be given.
        """

        #### [[idi, 1] for idi in range(len(self.data))]
        if logger is None:
            self.logger = Log()
        else:
            self.logger = logger
        self.pm = PreferencesManager(conf_defs)
        self.data = None
        self.reds = StoredRCollection()
        self.count_loaded_rlists = 0
        self.preferences = ICDict(self.pm.getDefaultTriplets())
        self.resetConstraints()
        self.setupFilterActs()
        self.package = None
        self._isChanged = False
        self._isFromPackage = False
        self.reloaded()
        # self._needsReload = False

        # (possible) function pointers to tell we've started and stopped reading
        # If these are not None, they have to be triples (fnc, *args, **kwargs)
        # See: self.registerStartReadingFileCallback and self.registerStopReadingFileCallback
        self.startReadingFileCallback = None
        self.stopReadingFileCallback = None

        if package_filename is not None:
            self.openPackage(package_filename)

    def clearRedescriptions(self):
        self.reds.clear()
    def hasRedsChanged(self, inc_hist=False, inc_buffer=False):
        return len(self.reds.getNonEmpyLids(check_changed=True, inc_hist=inc_hist, inc_buffer=inc_buffer)) > 0
    def hasRedsToExport(self, inc_hist=False, inc_buffer=False):
        return len(self.reds.getNonEmpyLids(check_changed=False, inc_hist=inc_hist, inc_buffer=inc_buffer)) > 0

    def getVarsOrRedsForInfo(self, info):
        if self.getData() is not None and info is not None:
            if info.get("tab_type") == "r":
                return [(iid, self.reds.getItem(iid)) for iid in info.get("iids", [])]
            elif info.get("tab_type") == "v" or info.get("tab_type") == "e":
                return [(iid, self.getData().getItem(iid)) for iid in info.get("iids", [])]
        return []
    def getItemsForInfo(self, info):
        if self.getData() is not None and info is not None:
            if info.get("tab_type") == "r":
                return [(iid, self.reds.getItem(iid)) for iid in info.get("iids", [])]
            elif info.get("tab_type") == "v":
                return [(iid, self.getData().getItem(iid)) for iid in info.get("iids", [])]
            elif info.get("tab_type") == "e":
                return [(i, self.data.getRow(i)) for i in info.get("row_ids", [])]
        return []
    def getItemsActiveLidForInfo(self, info):
        if self.getData() is not None and info is not None:
            if info.get("tab_type") == "r" and info.get("active_lid") is not None:
                return [(iid, self.reds.getItem(iid)) for iid in self.reds.getIidsList(info.get("active_lid"))]
            elif info.get("tab_type") == "v" and info.get("active_lid") is not None:
                return [(iid, self.getData().getItem(iid)) for iid in self.getData().getIidsList(info.get("active_lid"))]
            elif info.get("tab_type") == "e":
                return [(i, row) for i, row in enumerate(self.data.getRows())]
        return []

    def getContentInfo(self, info_in={}):
        info = {"pck_path": None, "tab_type": "r", "tab_id": None, "active_lid": None, "lids": None}
        info.update(info_in)
        if self.getData() is not None and self.isFromPackage and self.getPackageSaveFilename() is not None:
            info["pck_path"] = self.getPackageSaveFilename()
        if info["tab_type"] == "r":
            info.update(self.reds.getContentInfo(info["lids"], info["iids"]))
        elif info["tab_type"] == "v" and self.getData() is not None:
            info.update(self.getData().getContentInfo(info["lids"], info["iids"]))
        elif info["tab_type"] == "e" and self.getData() is not None:
            info.update(self.getData().getContentInfo(None, info["iids"]))
        if "lid" not in info: ### fill default
            info.update(self.reds.getContentInfo(None, []))
        return info
    def getColNames(self):
        if self.data is not None:
            return self.data.getNames()
        return [[],[]]

    def dataHasMissing(self):
        if self.data is not None:
            return self.data.hasMissing()
        return False

    def getNbRows(self):
        if self.data is not None:
            return self.data.nbRows()
        return 0

    def getAllCols(self):
        if self.data is not None:
            return [(iid, self.data.getItem(iid)) for iid in self.data.getIids()]
        return []
    def getDataCols(self, side):
        if self.data is not None:
            return self.data.colsSide(side)
        return []

    def getDataRows(self):
        if self.data is not None:
            return self.data.getRows()
        return []

    def getData(self):
        return self.data

    def isGeospatial(self):
        if self.data is not None and self.data.isGeospatial():
            return True
        else:
            return False
    def getTypeD(self):
        if self.data is not None:
            return self.data.getTypeD()
        else:
            return {}
    def getExtensionKeys(self):
        if self.data is not None:
            return self.data.getActiveExtensionKeys()
        else:
            return []

    def getCoords(self):
        if self.data is not None and self.data.isGeospatial():
            return self.data.getCoords()
    def getCoordPoints(self):
        if self.data is not None and self.data.isGeospatial():
            return self.data.getCoordPoints()
        
    def getCoordsExtrema(self):
        if self.data is not None and self.data.isGeospatial():
            return self.data.getCoordsExtrema()
        return None

    def getAllReds(self):
        return [(iid, self.reds.getItem(iid)) for iid in self.reds.getIids()]
    def getRedLists(self):
        return self.reds
    def getReds(self, lid=None):
        return self.reds.getItems(lid)
    def getRed(self, iid=None):
        return self.reds.getItem(iid)
    def getNbReds(self, lid=None):
        if lid is None:
            return self.reds.nbItems()
        return self.reds.getLen(lid)

    def getPreferencesManager(self):
        return self.pm
             
    def getPreferences(self):
        return self.preferences
    def getActionsRegistry(self):
        return self.constraints.getActionsRegistry()
    def getPreference(self, param_id):
        if self.preferences is not None and param_id in self.preferences:
            return self.preferences[param_id]["data"]
        else:
            return False
    def registerStartReadingFileCallback(self, fnc, *args, **kwargs):
        """Registers the function DataWrapper calls when it starts to read a file (to tell that it
        starts reading the file). Parameters: fnc, [*args,] [**kwargs],
        where fnc is a function with prototype
        fnc(msg, [short_msg], [*args], [**kwargs])"""
        self.startReadingFileCallback = (fnc, args, kwargs)

    def registerStopReadingFileCallback(self, fnc, *args, **kwargs):
        """Registers the function DataWrapper calls when it stops reading a file.
        Parameters: fnc, [*args,] [**kwargs],
        where fnc is a function with prototype
        fnc([msg], [*args], [**kwargs])"""
        self.stopReadingFileCallback = (fnc, args, kwargs)

    def __str__(self):
        return "coords = " + str(self.getCoords()) + "; " \
            + "data = " + str(self.data) + "; " \
            + "preferences = " + str(len(self.preferences)) + "; " \
            + "package = " + str(self.package) + "; " \
            + "isChanged = " + str(self.isChanged) + "; " \
            + "isFromPackage = " + str(self.isFromPackage) + "; " \
            + "reds = " + str(self.reds) 

    ## Setters
    @property
    def isChanged(self):
        """The property tracking if dw has changed"""
        isChanged = self._isChanged
        # if self.reds is not None:
        #     isChanged |= self.reds.isChanged
        if self.preferences is not None:
            isChanged |= self.preferences.isChanged
        return isChanged
    
    @isChanged.setter
    def isChanged(self, value):
        if isinstance(value, bool):
            if value is False:
                # if self.reds is not None:
                #     self.reds.isChanged = value
                if self.preferences is not None:
                    self.preferences.isChanged = value
            self._isChanged = value
        else:
            raise TypeError("The isChanged property accepts only Boolean attributes")

                #isChanged = property(_get_isChanged, _set_isChanged)
    
    @property
    def isFromPackage(self):
        """The property tracking if dw was loaded from a package"""
        return self._isFromPackage

    @isFromPackage.setter
    def isFromPackage(self, value):
        if isinstance(value, bool):
            self._isFromPackage = value
        else:
            raise TypeError("The isFromPackage property accepts only Boolean attributes")

        
    def updatePreferencesDict(self, params):
        #if type(params) == dict:
        if isinstance(params, collections.MutableMapping):
            params_l = PreferencesReader.paramsToDict(params)
            dtv = [item_id for (item_id, trip) in params_l.items() if trip != self.getPreference(item_id)]
            self.preferences.update(params)
            self.resetConstraints(dtv=dtv)
            
    def loadExtension(self, ek, filenames={}):
        if len(filenames) == 0 and ek in self.getExtensionKeys():
            self.data.getExtension(ek).setParams(self.getPreferences())        
        else:
            self.data.initExtension(ek, filenames, self.getPreferences())
            params_l = self.data.getExtension(ek).getParams()
            if len(params_l) > 0:
                params = PreferencesReader(self.pm).readParametersDict(params_l)
                self.updatePreferencesDict(params)            
        self.addReloadRecompute()
        self.addReloadData("v")

    def addVecCol(self, vec, name, side=1, force_type=None):
        self.getData().addVecCol(vec, name, side, force_type)
        self.addReloadData("v")
        self.addReloadFields("r")
    ### HANDLING FOLDS
    def addFoldsCol(self):
        self.getData().addFoldsCol()
        self.addReloadData("v")
    def extractFolds(self, side, colid):
        self.getData().extractFolds(side, colid)
    def assignLT(self, ids_learn=None, ids_test=None):
        if ids_learn is None or ids_test is None:
            self.getData().dropLT()
        else:
            self.getData().assignLT(ids_learn, ids_test)
        self.addReloadRecompute()
    def setData(self, data):
        self.data = data
        self.constraints.resetDataDependent(data, self.getPreferences())
        self.addReloadAll()

    def applyVarsMask(self, pdict):
        if self.data is not None:
            return self.data.applyDisableMasks(pdict.get("mask_vars_LHS"),
                                        pdict.get("mask_vars_RHS"),
                                        pdict.get("mask_rows"))
    def resetConstraints(self, AR=None, dtv=None):
        if dtv is None:
            self.constraints = Constraints(self.getPreferences(), data=self.getData(), AR=AR)
            changed = {"reset_all": True}
        else:
            changed = self.constraints.reset(self.getPreferences(), data=self.getData(), AR=AR, dtv=dtv)
        self.addReloadFromDict(changed)
        return changed
        
    def recompute(self):
        self.doneReloadRecompute()
        self.recomputeReds()
        self.recomputeVars()

    def recomputeVars(self):
        data = self.getData()
        if data is not None:
            data.recomputeCols()
            self.addReloadData("v")
            self.addReloadFields("v")        
        
    def recomputeReds(self):
        data = self.getData()
        if data is not None:
            for rid in self.reds.getIids():
                self.reds.getItem(rid).recompute(data)
            self.addReloadData("r")
            self.addReloadFields("r")        
            self.addReloadData("z")
        
################################################################
    def loadRedescriptionsFromFile(self, redescriptions_filename):
        """Loads new redescriptions from file"""
        tmp_reds = None
        self._startMessage('importing', redescriptions_filename)
        try:
            tmp_reds = self._readRedescriptionsFromFile(redescriptions_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open: %s" % arg, "dw_error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing redescriptions from file %s!\n%s" % (redescriptions_filename, sys.exc_info()[1]), "dw_error", "DW")
            self._stopMessage()
            raise
        finally:            
            self._stopMessage('importing')
            
        trg_lid, iids, newl = (None, [], False)
        if tmp_reds is not None:
            src=('file', redescriptions_filename, 0)
            trg_lid, iids, newl = self.appendRedsToSrc(tmp_reds, src, recompute=False, set_changed=False)
            if newl:
                self.addReloadSwitchTab("r")
                self.addReloadSwitchList(trg_lid, "r")
        return trg_lid, iids, newl

    def importTracks(self, tracks, source=None):
        self.reds.importTracks(tracks, source)
    
    def appendRedsToSrc(self, reds, src, recompute=True, set_changed=None):
        iids = []
        org_lid = self.reds.getUidForSrc(src)
        for r in reds:
            if recompute and self.getData() is not None:
                r.recompute(self.getData())
            if not self.reds.hasIid(r.getUid()):
                if src[0] == "run":
                    r.appendTrack((src[1], "W"), 0)
                else:
                    r.appendTrack((src[0][0],), 0)
            else:
                r.setDisabled()
            iids.append(self.reds.appendItemSrc(r, trg_src=src))
        trg_lid = self.reds.getUidForSrc(src)
        if set_changed is not None:
            self.reds.getList(trg_lid).isChanged = set_changed
        if len(iids) > 0:
            self.addReloadListContent(trg_lid, "r", new_lid=org_lid is None)
        return trg_lid, iids, org_lid is None

    def prepareRedsPackage(self):
        rtp = []
        for lid in self.reds.getLids():
            if self.reds.isListToPack(lid):
                rtp.append({"items": self.reds.getItems(lid), "src": self.reds.getList(lid).getSrc()})
                self.reds.getList(lid).isChanged = False
        return rtp
    
    def substituteRed(self, iid, red, backup=True):
        old_red = self.reds.substituteItem(iid, red, backup)
        self.addReloadListContent(self.reds.getHistLid(), "r", [])
        self.addReloadItem(iid, "r")
        self.addReloadItem(iid, "z")
        return old_red

    def addItemToHist(self, red):
        self.reds.addItemToHist(red)
        self.addReloadListContent(self.reds.getHistLid(), "r", [])

    def moveIids(self, tab_type, src_lid, iids=None, trg_lid=None, trg_pos=-1):
        if tab_type == "r":
            self.reds.moveIids(src_lid, iids=iids, trg_lid=trg_lid, trg_pos=trg_pos)
            if self.reds.showingLid(src_lid):
                self.addReloadListContent(src_lid, "r", iids)
            if src_lid != trg_lid and self.reds.showingLid(trg_lid):
                self.addReloadListContent(trg_lid, "r", iids)
                
    def process(self, actions, lid, iids):
        if lid is not None and iids is not None and len(iids) > 0:
            before_iids = self.reds.getIidsListAbove(lid, iids[0])
            if len(iids) == 1:
                compare_iids = self.reds.getIidsListBelow(lid, iids[0])
                after_iids = []
            else:
                compare_iids = iids
                after_iids = [iid for iid in self.reds.getIidsListBelow(lid, iids[0]) if iid not in iids]
                
            current_iids = [i for i in compare_iids if self.reds.getItem(i).isEnabled()]
            bottom_iids = [i for i in compare_iids if not self.reds.getItem(i).isEnabled()]

            selected_iids = self.reds.selected(actions, current_iids, data=self.getData())
            middle_iids = []
            for i in current_iids:
                if i not in selected_iids:
                    self.reds.getItem(i).setDisabled()
                    middle_iids.append(i)
            return before_iids, selected_iids, middle_iids, bottom_iids, after_iids
        return iids, None, None, None, None
            
#################### IMPORTS
    def loadDefsFromFile(self, path, fld_type="fields_rdefs"):
        if fld_type == "fields_vdefs":
            ColM.extendRP([path])
            self.addReloadFields("v")
        elif fld_type == "fields_rdefs":
            Redescription.extendRP([path])
            self.addReloadFields("r")
        elif fld_type == "actions_rdefs":
            AR = self.getActionsRegistry()
            AR.extend([path])
            self.resetConstraints(AR, [])
            
    def importDataFromCSVFiles(self, data_filenames):
        fnames = list(data_filenames[:2])
        self._startMessage('importing', fnames)        
        try:
            tmp_data = self._readDataFromCSVFiles(data_filenames)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "dw_error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open: %s" % arg, "dw_error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing data from CSV files!\n%s" %  sys.exc_info()[1], "dw_error", "DW")
            self._stopMessage()
            raise
        else:
            self.setData(tmp_data)
            self.clearRedescriptions()
            self._isChanged = True
            self._isFromPackage = False
        finally:
            self.addReloadAll()
            self._stopMessage('importing')

    def importPreferencesFromFile(self, preferences_filename):
        """Imports mining preferences from file"""
        self._startMessage('importing', preferences_filename)
        try:
 
            tmp_preferences = self._readPreferencesFromFile(preferences_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open: %s" % arg, "dw_error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing preferences from file %s!\n%s" % (preferences_filename, sys.exc_info()[1]), "dw_error", "DW")
            self._stopMessage()
            raise
        else:
            self.preferences = tmp_preferences
            self.preferences.isChanged = True
            self.resetConstraints()
        finally:
            self.addReloadAll()
            self._stopMessage('importing')
            
    def openPackage(self, package_filename):
        """Loads new data from a package"""
        self._startMessage('loading', [package_filename])
        try:
            self._readPackageFromFile(package_filename)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "dw_error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open: %s" % arg, "dw_error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing package from file %s!\n%s" % (package_filename, sys.exc_info()[1]), "dw_error", "DW")
            self._stopMessage()
            raise
        finally:
            self.addReloadAll()
            self._stopMessage('loading')

######################## READS
    def _readDataFromCSVFiles(self, data_filenames):
        try:
            data = Data(data_filenames, "csv")
        except Exception:
            self._stopMessage()
            raise
        return data

    def _readRedescriptionsFromFile(self, filename, data=None):
        sid = ("%s" % (self.count_loaded_rlists + 1))[::-1]
        reds = []
        if data is None:
            if self.data is None:
                raise Exception("Cannot load redescriptions if data is not loaded")
            else:
                data = self.data
        if os.path.isfile(filename):
            rp = Redescription.getRP()
            filep = open(filename, mode='r')
            rp.parseRedList(filep, data, reds, sid=sid)
        if len(reds) > 0:
            self.count_loaded_rlists += 1
        return reds

    def _readPreferencesFromFile(self, filename):
        filep = open(filename, mode='r')
        return ICDict(PreferencesReader(self.pm).getParameters(filep))

    def _readPackageFromFile(self, filename):
        package = Package(filename, self._stopMessage)
        elements_read = package.read(self.pm)
        self.data = None
        self.clearRedescriptions()
        
        self.package_name = package.getPackagename()
        AR = None
        if elements_read.get("preferences"):
            preferences = elements_read.get("preferences")
            if "AR" in preferences:
                AR = preferences.pop("AR")
            self.preferences = ICDict(preferences)
        else:
            self.preferences = ICDict(self.pm.getDefaultTriplets())
        self.resetConstraints(AR)
            
        if elements_read.get("data") is not None:
            self.setData(elements_read.get("data"))

        if elements_read.get("reds") is not None:            
            for rlist in elements_read.get("reds"):
                self.appendRedsToSrc(rlist["items"], rlist["src"], recompute=False, set_changed=False)
                
        self.package = package
        self._isChanged = False
        self._isFromPackage = True

    def prepareContentPackage(self):
        contents = {}
        if self.data is not None:
            contents['data'] = self.data
        rtp = self.prepareRedsPackage()
        if len(rtp) > 0:
            contents['redescriptions'] = rtp
        if self.preferences is not None:
            contents['preferences'] = self.preferences
            contents['pm'] = self.pm

        ### definitions
        vdefs = ColM.getRP().fieldsToStr()
        if len(vdefs) > 0:
            contents['fields_vdefs'] = vdefs
        rdefs = Redescription.getRP().fieldsToStr()
        if len(rdefs) > 0:
            contents['fields_rdefs'] = rdefs
        AR = self.getActionsRegistry()
        if AR is not None:
            adefs = AR.actionsToStr()
            if len(adefs) > 0:
                contents['actions_rdefs'] = adefs
        return contents


    def savePackageToFile(self, filename, suffix=Package.DEFAULT_EXT):
        try:
            if self.package is None:
                self.package = Package(None, self._stopMessage, mode="w")
            self._writePackageToFile(filename, suffix)
        except DataError as details:
            self.logger.printL(1,"Problem writing package.\n%s" % details, "dw_error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open file for package %s" % filename, "dw_error", "DW")
            self._stopMessage()
            raise
        # except Exception:
        #     self.logger.printL(1,"Unexpected error while writing package!\n%s" % sys.exc_info()[1], "dw_error", "DW")
        #     self._stopMessage()
        #     raise
        for lid in self.reds.getOrdLids():
            self.addReloadList(lid, "r")

    ## The saving function
    def _writePackageToFile(self, filename, suffix=Package.DEFAULT_EXT):
        """Saves all information to a new file"""
        if suffix is None:
            (filename, suffix) = os.path.splitext(filename)
        else:
            (fn, sf) = os.path.splitext(filename)
            if sf == suffix:
                filename = fn

        # Tell everybody
        self._startMessage('saving', filename+suffix)
        # Test that we can write to filename
        try:
            f = open(os.path.abspath(filename+suffix), 'a+')
        except IOError as arg:
            self.logger.printL(1,"Cannot open: %s" % arg, "dw_error", "DW")
            self._stopMessage()
            return
        else:
            f.close()
            
        self.package.writeToFile(filename+suffix, self.prepareContentPackage())
        # self._isChanged = False
        self.isChanged = False
        self._isFromPackage = True

        # Tell others we're done
        self._stopMessage('saving')
        ## END THE SAVING FUNCTION

    def getPackageSaveFilename(self):
        if self.package is not None:
            return self.package.getSaveFilename()
        return None
    
    def savePackage(self):
        """Saves to known package"""
        if self.package is None:
            raise ValueError('Cannot save if package_filename is None, use savePackageToFile instead')
        else:
            self.savePackageToFile(self.package.getSaveFilename(), None)

    def exportPreferences(self, filename, inc_def=False, conf_def=None):
        pm = self.pm
        prefs = self.preferences
        core = False        
        ## prefs = pm.getDefaultTriplets()
        if conf_def is not None:
            pm = PreferencesManager(conf_def)           
            core = not inc_def

        self._startMessage('exporting prefs', filename)
        try:
            IOTools.writePreferences(prefs, pm, filename, False, inc_def, core)
        except Exception:
            self._stopMessage()
            raise
        self._stopMessage('exporting prefs')

    def exportRedescriptions(self, filename, iids=None, lid=None):
        if iids is not None and len(iids) > 0:
            reds = [self.reds.getItem(iid) for iid in iids]
        else:
            return
        self._startMessage('exporting', filename)
        params = IOTools.getPrintParams(filename, self.data)
        rp = Redescription.getRP()
        params["modifiers"] = rp.getModifiersForData(self.data)
        try:
            IOTools.writeRedescriptions(reds, filename, **params)
        except Exception:
            self._stopMessage()
            raise
        self._stopMessage('exporting')
        if lid is not None:
            self.reds.getList(lid).isChanged = False
            self.addReloadList(lid, "r")

        
    def exportFigs(self, parent, filename, items, dims=(600,600), fmt_details={}):        
        self._startMessage('saving figures', filename)
        with_disabled = fmt_details.get("with_disabled", False)
        viewT = fmt_details.get("viewT")
        fmt = fmt_details.get("format", None)
        stamp = fmt_details.get("stamp", False)
        
        if not re.search("%s", filename):
            parts = filename.split(".")
            if len(parts) > 1:
                filename = ".".join(parts[:-1])+"_%s."+parts[-1]
            else:
                filename += "_%s"
        try:
            for iid, item in items:
                if not with_disabled and not item.isEnabled():
                    continue
                mapV = parent.viewOpen(item, iid=iid, viewT=viewT)
                mapV.lastStepInit(blocking=True)
                mapV.getLayH().getFrame().SetClientSize(dims[0], dims[1])
                mapV.addStamp(viewT, force=stamp)
                mapV.getLayH().savefig(filename % str(iid), format=fmt)
                mapV.getLayH().OnKil()
                
        except Exception:
            self._stopMessage()
            raise
        self._stopMessage('saving figures')
        
#### WARNING HERE DISABLED FILE LOAD MESSAGES 
    # def _startMessage(self, action, filenames):
    #     "Shows the message if needed"
    #     if self.startReadingFileCallback is not None:
    #         (fnc, args, kwargs) = self.startReadingFileCallback
    #         msg = 'Please wait. ' + action.capitalize() + ' file'
    #         short_msg = action.capitalize() + ' file'
    #         if len(filenames) <= 1:
    #             msg += ' '
    #         else:
    #             msg += 's '
    #             short_msg += 's'

    #         if isinstance(filenames, basestring):
    #             # In Python 3, test has to be isinstance(filenames, str)
    #             filenames = [filenames]
    #         msg += ' '.join(map(os.path.basename, filenames))
    #         # filename can be a list of filenames with full paths, hence map()
    #         fnc(msg, short_msg, *args, **kwargs)

    # def _stopMessage(self, action=None):
    #     "Removes the message if needed"
    #     if self.stopReadingFileCallback is not None:
    #         (fnc, args, kwargs) = self.stopReadingFileCallback
    #         if action is None:
    #             mess = "An error occurred"
    #         else:
    #             mess = action.capitalize()+' done'
    #         fnc(mess, *args, **kwargs)

    def _startMessage(self, action, filenames):
        pass
    def _stopMessage(self, action=None):
        pass

    ##### RELOAD/REFRESH INFO
    def getNeedsReload(self):
        return self._needsReload
    def reloaded(self):
        self._needsReload = {"reset_all": False}
        # self._needsReload = {"reset_all": True}
    def getNeedsReloadDone(self):
        rneeds = self.getNeedsReload()
        if not rneeds.get("recompute"):
            self.reloaded()
        return rneeds    
    def addReloadItem(self, ii, tab_type="r"):
        if tab_type not in "rvez":
            return
        if tab_type not in self._needsReload:
            self._needsReload[tab_type] = {}
        if "items" not in self._needsReload[tab_type]:
            self._needsReload[tab_type]["items"] = []
        self._needsReload[tab_type]["items"].append(ii)
    def addReloadList(self, lid, tab_type="r"):
        if tab_type == "e" or (tab_type in "rv" and lid is not None):
            if tab_type not in self._needsReload:
                self._needsReload[tab_type] = {}
            if "lists" not in self._needsReload[tab_type]:
                self._needsReload[tab_type]["lists"] = []
            self._needsReload[tab_type]["lists"].append(lid)
    def addReloadListContent(self, lid, tab_type="r", selected_iids=None, new_lid=False):
        if tab_type in "erv":
            if tab_type not in self._needsReload:
                self._needsReload[tab_type] = {}
            if "lists_content" not in self._needsReload[tab_type]:
                self._needsReload[tab_type]["lists_content"] = []
            self._needsReload[tab_type]["lists_content"].append((lid, selected_iids, new_lid))
    def addReloadFields(self, tab_type="r"):
        if tab_type not in "rvez":
            return
        if tab_type not in self._needsReload:
            self._needsReload[tab_type] = {}
        self._needsReload[tab_type]["fields"] = True
    def addReloadData(self, tab_type="r"):
        if tab_type not in "rvez":
            return
        if tab_type not in self._needsReload:
            self._needsReload[tab_type] = {}
        self._needsReload[tab_type]["data"] = True
    def addReloadSwitchList(self, lid, tab_type="r"):
        if tab_type in "rv":
            if tab_type not in self._needsReload:
                self._needsReload[tab_type] = {}
            self._needsReload[tab_type]["switch"] = lid 
    def addReloadSwitchTab(self, tab_type="r"):
        if tab_type not in "rve":
            return
        self._needsReload["switch"] = tab_type
    def addReloadFilters(self):
        self._needsReload["actions_filters"] = True
    def addReloadRecompute(self):
        self._needsReload["recompute"] = True
    def doneReloadRecompute(self):
        self._needsReload["recompute"] = False
    def addReloadAll(self):
        self._needsReload["reset_all"] = True
    def addReloadFromDict(self, rdict):
        try:
            for k, v in rdict.items():
                if v:
                    self._needsReload[k] = v
        except AttributeError:
            pass
                
        
    ################ SPECIFYING ACTION FUNCTIONS START
    #####################################################
    acts_list = []    
    ## ENABLING
    def actFlipEnabled(self, info):
        for ii, item in self.getItemsForInfo(info):
            if item is not None:
                item.flipEnabled()
                self.addReloadItem(ii, info.get("tab_type"))
                if info.get("tab_type") == "e":
                    self.addReloadRecompute()
                    self.addReloadData("v")
    acts_list.append({"key": "FlipEnabled", "group": "able", "method": actFlipEnabled,                          
                      "label": "E&nable/Disable\tCtrl+G", "legend": "Enable/Disable current item."})
    def actEnableAll(self, info):
        items = []
        rld = False
        if info["nb"] > 1:
            items = self.getItemsForInfo(info)
        else:
            items = self.getItemsActiveLidForInfo(info)
        for ii, item in items:
            if item is not None:
                item.setEnabled()
                rld = True
        if rld:
            self.addReloadListContent(info.get("active_lid"), info.get("tab_type"))
            if info.get("tab_type") == "e":
                self.addReloadRecompute()
                self.addReloadData("v")
    acts_list.append({"key": "EnabledAll", "group": "able", "method": actEnableAll,
                      "label": "Ena&ble all\tCtrl+B", "legend": "Enable all items."})
    def actDisableAll(self, info):
        items = []
        rld = False
        if info["nb"] > 1:
            items = self.getItemsForInfo(info)
        else:
            items = self.getItemsActiveLidForInfo(info)
        for ii, item in items:
            if item is not None:
                item.setDisabled()
                rld = True
        if rld:
            self.addReloadListContent(info.get("active_lid"), info.get("tab_type"))
            if info.get("tab_type") == "e":
                self.addReloadData("v")
                self.addReloadData("r")
                self.addReloadData("z")
    acts_list.append({"key": "DisabledAll", "group": "able", "method": actDisableAll,
                      "label": "Disable all\tShift+Ctrl+B", "legend": "Disable all items."})   
    def actDeleteDisAll(self, info):
        if info["tab_type"] != "r":
            return
        items = []
        rld = False
        non_deleted_iids = []
        if info["nb"] > 1:
            items = self.getItemsForInfo(info)
        else:
            items = self.getItemsActiveLidForInfo(info)
        for ii, item in items:
            if item is not None and not item.isEnabled():
                self.reds.deleteItem(ii) 
                rld = True
            else:
                non_deleted_iids.append(ii)
        if rld:
            if info["nb"] <= 1:
                non_deleted_iids = []
            self.addReloadListContent(info.get("active_lid"), info.get("tab_type"), non_deleted_iids)
    acts_list.append({"key": "DeleteDisAll", "group": "able", "method": actDeleteDisAll,
                      "label": "Delete disabled\tShift+Ctrl+D", "legend": "Delete all disabled items."})

    ## COPY, CUT AND PASTE
    def actDelete(self, info):
        if info["tab_type"] == "r":
            if info.get("lid") is not None:
                self.reds.deleteList(info.get("lid"))
                self.addReloadSwitchList(None, "r")
                active_lid = None
            else:
                for iid in info.get("iids", []):
                    self.reds.deleteItem(iid)
                active_lid = info.get("active_lid")
            self.addReloadListContent(active_lid, info.get("tab_type"), [])
    acts_list.append({"key": "Delete", "group": "redCCP", "method": actDelete,
                      "label": "&Delete\tCtrl+D", "legend": "Delete current redescription."})
    def actCut(self, info):
        if info["tab_type"] == "r":
            if info["active_lid"] is not None and info["nb"] > 0:
                self.reds.cutIids(src_lid=info["active_lid"], iids=info["iids"]) 
                self.addReloadListContent(info.get("active_lid"), info.get("tab_type"), [])
    acts_list.append({"key": "Cut", "group": "redCCP", "method": actCut,
                      "label": "Cu&t\tCtrl+X", "legend": "Cut current redescription."})
    def actCopy(self, info):
        if info["tab_type"] == "r":
            if info["active_lid"] is not None and info["nb"] > 0:
                self.reds.copyToBufferIids(src_lid=info["active_lid"], iids=info["iids"]) 
    acts_list.append({"key": "Copy", "group": "redCCP", "method": actCopy,
                      "label": "&Copy\tCtrl+C", "legend": "Copy current redescription."})
    def actPaste(self, info):
        if info["tab_type"] == "r":
            lid = None
            if info.get("lid", -1) is None and info.get("lids") is not None and len(info["lids"]) == 0:
                lid = self.reds.newList()
                new_lid = True
                # self.addReloadSwitchList(lid, "r")
            elif info["active_lid"] is not None:
                lid = info["active_lid"]
                new_lid = False

            if lid is not None:
                trg_pos = None
                if info["nb"] == 1:
                    trg_pos = self.reds.getPosForLidIid(lid, info["iids"][0])
                if trg_pos is None:
                    trg_pos = -1
                pos = self.reds.pasteIids(trg_lid=lid, trg_pos=trg_pos)
                iids = [self.reds.getIidForLidPos(lid, p) for p in pos]
                self.addReloadListContent(lid, info.get("tab_type"), iids, new_lid)
    acts_list.append({"key": "Paste", "group": "redCCP", "method": actPaste,
                      "label": "&Paste\tCtrl+V", "legend": "Paste current redescription."})

    ## ACT ON SINGLE RED
    # def actNormalize(self, info):
    #     if info["tab_type"] == "r" and len(info.get("iids", [])) > 0:
    #         for iid in info["iids"]:
    #             item  = self.reds.getItem(iid)
    #             if item is not None:
    #                 itemn, changed = item.getNormalized(self.getData())
    #                 if changed:
    #                     self.substituteRed(iid, itemn, backup=True) ### rneeds done inside
    # acts_list.append({"key": "Normalize", "group": "redMod", "method": actNormalize,
    #                   "label": "Normalize", "legend": "Normalize current redescription."})
    # def actPrune(self, info):
    #     if info["tab_type"] == "r" and len(info.get("iids", [])) > 0:
    #         for iid in info["iids"]:
    #             item  = self.reds.getItem(iid)
    #             if item is not None:
    #                 itemn, changed = item.prune(self.getData())
    #                 if changed:
    #                     self.substituteRed(iid, itemn, backup=True) ### rneeds done inside
    # acts_list.append({"key": "Prune", "group": "redMod", "method": actPrune,
    #                   "label": "Prune", "legend": "Prune current redescription."})

    ## FILTER REDS
    def actFilter(self, info, action_key="redundant_area", action_substitute=None):
        if info["tab_type"] == "r" and info["active_lid"] is not None and info["nb"] > 0:
            if info["nb"] == 1:
                compare_iids = self.reds.getIidsListBelow(info["active_lid"], info["iids"][0])
            else:
                compare_iids = info["iids"]
            actions = self.constraints.getActionsList(action_key, action_substitute)            
            disable_iids = self.reds.doActions(actions, compare_iids, complement=True)
            if len(disable_iids) > 0:
                for iid in disable_iids:
                    self.reds.getItem(iid).setDisabled()                
                self.addReloadListContent(info.get("active_lid"), info.get("tab_type"), info["iids"])
    def actProcess(self, info, action_key="process"):
        if info["tab_type"] == "r" and info["active_lid"] is not None and info["nb"] > 0:
            actions = self.constraints.getActionsList(action_key)
            before_iids, selected_iids, middle_iids, bottom_iids, after_iids = self.process(actions, info["active_lid"], info["iids"])
            if selected_iids is not None:
                self.reds.setIids(info["active_lid"], before_iids+selected_iids+middle_iids+bottom_iids+after_iids)
                self.addReloadListContent(info.get("active_lid"), info.get("tab_type"), selected_iids)
    def actApply(self, info, action_key="prune"):
        if info["tab_type"] == "r" and info["active_lid"] is not None and info["nb"] > 0:
            actions = self.constraints.getActionsList(action_key)
            if len(actions) == 1:
                action = actions[0]
                action["data"] = self.getData()
                for iid in info["iids"]:
                    itemn, changed = self.reds.applyAct(iid, action)
                    if changed:
                        self.substituteRed(iid, itemn, backup=True) ### rneeds done inside
                    else:
                        self.reds.getItem(iid).setDisabled()                
            self.addReloadListContent(info.get("active_lid"), info.get("tab_type"), info["iids"])
            
    ## FILTER EXTRAS
    def actExtraAddDelListToPack(self, info):
        if info["tab_type"] == "r" and info.get("lid") is not None:                
            self.reds.addDelListToPack(info["lid"])
    acts_list.append({"key": "AddDelListToPack", "group": "extra", "method": actExtraAddDelListToPack,
                      "label": "Add to package", 
                      "legend": "Add/Remove package list."})
    def actExtraNewList(self, info):
        if info["tab_type"] == "r":
            nlid = self.reds.newList()
            self.addReloadSwitchList(nlid, "r")
            self.addReloadListContent(nlid, "r")
    acts_list.append({"key": "NewList", "group": "extra", "method": actExtraNewList,
                      "label": "New &list\tCtrl+N",
                      "legend": "New list."})

    ################ SPECIFYING ACTION FUNCTIONS ENDS
    #####################################################

    acts_meths_dict = dict([(c["key"], c["method"]) for c in acts_list])
    acts_params_dict = {}
    acts_groups = {}
    acts_extras = {}
    for c in acts_list:
        cgroup = c.get("group")
        if cgroup == "extra":
            acts_extras[c["key"]] = {"key": c["key"], "label": c["label"], "legend": c["legend"]}
        else:
            if cgroup not in acts_groups:
                acts_groups[cgroup] = []
            acts_groups[cgroup].append({"key": c["key"], "label": c["label"], "legend": c["legend"]})

    def setupFilterActs(self):
        prev_acts = self.acts_groups.pop("redsFilter", [])
        for act in prev_acts:
            self.acts_meths_dict.pop(act["key"])
            self.acts_params_dict.pop(act["key"])
        AR = self.getActionsRegistry()

        acts_mod = []        
        #######################
        for apply_act in AR.getActionsKeysSimple(patt="apply"):
            name = re.sub("_", " ", apply_act)
            key = "Apply:%s" % apply_act
            acts_mod.append({"key": key, 
                             "label": "%s" % name.capitalize(), 
                             "legend": "%s the redescriptions." % name.capitalize() })            
            self.acts_meths_dict[key] = self.actApply
            self.acts_params_dict[key] = {"action_key": apply_act}
        self.acts_groups["redsMod"] = acts_mod
        
        acts_filter = []        
        for filter_single in AR.getActionsKeysSimple(patt="filterSingle"):
            name = re.sub("_", " ", filter_single)
            key = "FilterSingle:%s" % filter_single
            acts_filter.append({"key": key, 
                                "label": "Filter %s" % name, 
                                "legend": "Filters redescriptions individually according to criteria '%s'." % name })            
            self.acts_meths_dict[key] = self.actFilter
            self.acts_params_dict[key] = {"action_key": filter_single}

        for filter_pairs in AR.getActionsKeysSimple(patt="filterPairs"):
            name = re.sub("_", " ", filter_pairs)
            key = "FilterToFirst:%s" % filter_pairs
            acts_filter.append({"key": key, 
                                "label": "Filter %s to first" % name, 
                                "legend": "Filter redescriptions comparing to first selected according to criteria '%s'." % name })            
            self.acts_meths_dict[key] = self.actFilter
            self.acts_params_dict[key] = {"action_key": filter_pairs,
                                     "action_substitute": ("filterPairs", "filterToFirst")}
            key = "FilterAll:%s" % filter_pairs
            acts_filter.append({"key": key, 
                                "label": "Filter %s pairwise" % name, 
                                "legend": "Filter redescriptions pairwise according to criteria '%s'." % name })            
            self.acts_meths_dict[key] = self.actFilter
            self.acts_params_dict[key] = {"action_key": filter_pairs}
            
        for process in AR.getActionsKeysMulti():
            name = re.sub("_", " ", process)
            key = "ProcessAll:%s" % process
            acts_filter.append({"key": key, 
                                "label": "Do %s" % name, 
                                "legend": "Sort and filter current redescription list according to criteria '%s'." % name })            
            self.acts_meths_dict[key] = self.actProcess
            self.acts_params_dict[key] = {"action_key": process}
        #######################            
        self.acts_groups["redsFilter"] = acts_filter

    def getGroupActs(self, group=None):
        return self.acts_groups.get(group, [])
    def getExtraAct(self, key):
        return self.acts_extras.get(key)        
    
    def OnActContent(self, event, info):
        if event in self.acts_meths_dict:
            if event in self.acts_params_dict: ### those methods are bound
                self.acts_meths_dict[event](info, **self.acts_params_dict[event])
            else:
                self.acts_meths_dict[event](self, info)
