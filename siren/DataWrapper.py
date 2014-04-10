import numpy as np
import tempfile
import time
import os
import os.path
import plistlib
import shutil
import zipfile
import cPickle
import codecs
import collections
import sys
import re

import pdb

from reremi.classRedescription import Redescription, printTexRedList, printRedList, parseRedList
from reremi.classData import Data, DataError
from reremi.classQuery import Query
from reremi.toolICList import ICList
from reremi.toolICDict import ICDict
from reremi.toolLog import Log
from reremi.classBatch import Batch
from reremi.classPreferencesManager import PreferencesManager, PreferencesReader
import reremi.toolRead as toolRead

#from findFiles import findFile

def findFile(fname, path=[]):
    """Finds file from path (always including the current working directory) and returns
    its path or 'None' if the file does not exist.
    If path is not given or an empty list, only checks if the file is present locally.

    On Windows, this also chagnges forward slashes to backward slashes in the path."""
    if os.path.exists(fname):
        return fname

    for p in path:
        testpath = os.path.join(os.path.normpath(p), fname)
        if os.path.exists(testpath):
            return testpath

    return None


class DataWrapper(object):
    """Contains all the data
    """

    # CONSTANTS
    # Names of the files in the package
    DATA_LHS_FILENAME = 'data_LHS.csv'
    DATA_RHS_FILENAME = 'data_RHS.csv'
    REDESCRIPTIONS_FILENAME = 'redescriptions.csv'
    PREFERENCES_FILENAME = 'preferences.xml'
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'siren_package'

    pref_dir = os.path.dirname(__file__)
    conf_defs = [findFile('miner_confdef.xml', ['reremi', pref_dir+'/reremi']),
                 findFile('ui_confdef.xml', [pref_dir])]
    #conf_defs = ['miner_confdef.xml', 'ui_confdef.xml']
    # Stuff to write to plist
    FILETYPE_VERSION = 4
    XML_FILETYPE_VERSION = 3
    CREATOR = 'DataWrapper'

    def __init__(self, logger=None, package_filename = None):
        """Inits the class. Either package_filename or the others should be given.
        """

        #### [[idi, 1] for idi in range(len(self.data))]
        if logger is None:
            self.logger = Log()
        else:
            self.logger = logger
        self.pm = PreferencesManager(self.conf_defs)
        self.data = None
        self.polys = None
        self.pdp = None
        self.resetRedescriptions()
        self.preferences = ICDict(self.pm.getDefaultTriplets())
        self.package_filename = None
        self._isChanged = False
        self._isFromPackage = False

        # (possible) function pointers to tell we've started and stopped reading
        # If these are not None, they have to be triples (fnc, *args, **kwargs)
        # See: self.registerStartReadingFileCallback and self.registerStopReadingFileCallback
        self.startReadingFileCallback = None
        self.stopReadingFileCallback = None

        if package_filename is not None:
            self.openPackage(package_filename)
        
    def resetRedescriptions(self):
        self.reds = Batch([])
        self.rshowids = ICList([], True)

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

    def getDataCols(self, side):
        if self.data is not None:
            return self.data.cols[side]
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

    def getCoords(self):
        if self.data is not None and self.data.isGeospatial():
            return self.data.coords
        
    def getCoordsExtrema(self):
        if self.data is not None and self.data.isGeospatial():
            return self.data.getCoordsExtrema()
        return None

    def getReds(self):
        if self.reds is not None:
            return self.reds
        return []

    def getShowIds(self):
        if self.rshowids is not None:
            return self.rshowids
        return []

    def getPreferencesManager(self):
        return self.pm
             
    def getPreferences(self):
        return self.preferences

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
            + "#reds = " + str(len(self.reds)) + "; " \
            + "rshowids = " + str(self.rshowids) + "; " \
            + "preferences = " + str(self.preferences) + "; " \
            + "package_name = " + str(self.package_name) + "; " \
            + "isChanged = " + str(self.isChanged) + "; " \
            + "isFromPackage = " + str(self.isFromPackage)

    ## Setters
    @property
    def isChanged(self):
        """The property tracking if dw (incl. reds and rshowids) has changed"""
        isChanged = self._isChanged
        if self.reds is not None:
            isChanged |= self.reds.isChanged
        if self.rshowids is not None:
            isChanged |= self.rshowids.isChanged
        if self.preferences is not None:
            isChanged |= self.preferences.isChanged 
        return isChanged
    
    @isChanged.setter
    def isChanged(self, value):
        if isinstance(value, bool):
            if value is False:
                if self.reds is not None:
                    self.reds.isChanged = value
                if self.rshowids is not None:
                    self.rshowids.isChanged = value
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
            self.preferences.update(params)
            self.resetSSetts()
            #self.isChanged = True

    def setData(self, data):
        self.data = data
        self.resetSSetts()

    def resetSSetts(self):
        if self.getData() is not None:
            if self.getData().hasMissing() is False:
                parts_type = "grounded"
            else:
                parts_type = self.preferences.get("parts_type", {"data": None})["data"]
            pval_meth = self.preferences.get("method_pval", {"data": None})["data"]
            self.getData().getSSetts().reset(parts_type, pval_meth)


#################### IMPORTS            
    def importDataFromCSVFiles(self, data_filenames):
        fnames = list(data_filenames[:2])
        self._startMessage('importing', fnames)        
        try:
            tmp_data = self._readDataFromCSVFiles(data_filenames)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing data from CSV files!\n%s" %  sys.exc_info()[1], "error", "DW")
            self._stopMessage()
            raise
        else:
            self.setData(tmp_data)
            self.resetRedescriptions()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')

    def importRedescriptionsFromFile(self, redescriptions_filename):
        """Loads new redescriptions from file"""
        self._startMessage('importing', redescriptions_filename)
        try:
            tmp_reds, tmp_rshowids = self._readRedescriptionsFromFile(redescriptions_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing redescriptions from file %s!\n%s" % (redescriptions_filename, sys.exc_info()[1]), "error", "DW")
            self._stopMessage()
            raise
        else:
            self.reds = tmp_reds
            self.rshowids = tmp_rshowids
            #self.isChanged = True
        finally:
            self._stopMessage('importing')

    def importPreferencesFromFile(self, preferences_filename):
        """Imports mining preferences from file"""
        self._startMessage('importing', preferences_filename)
        try:
 
            tmp_preferences = self._readPreferencesFromFile(preferences_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing preferences from file %s!\n%s" % (preferences_filename, sys.exc_info()[1]), "error", "DW")
            self._stopMessage()
            raise
        else:
            self.preferences = tmp_preferences
            self.preferences.isChanged = True 
        finally:
            self._stopMessage('importing')
            
    def openPackage(self, package_filename):
        """Loads new data from a package"""
        self._startMessage('loading', [package_filename])
        try:
            self._readPackageFromFile(package_filename)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while importing package from file %s!\n%s" % (package_filename, sys.exc_info()[1]), "error", "DW")
            self._stopMessage()
            raise
        finally:
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
        if data is None:
            if self.data is None:
                self._stopMessage()
                raise Exception("Cannot load redescriptions if data is not loaded")
            else:
                data = self.data
        reds = Batch([])
        show_ids = None

        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, mode='r')
        parseRedList(filep, data, reds)
        rshowids = ICList(range(len(reds)), True)
        return reds, rshowids

    def _readPreferencesFromFile(self, filename):
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, mode='r')

        return ICDict(PreferencesReader(self.pm).getParameters(filep))

    def _readPackageFromFile(self, filename):
        """Loads a package"""
        # TODO: Check that file exists
        ischanged = False
        if not zipfile.is_zipfile(filename):
            raise IOError('File is of wrong type')

        # Remove the with-statement from reading
        try:
            #with zipfile.ZipFile(filename, 'r') as package:
            package = zipfile.ZipFile(filename, 'r')
            files = package.namelist()
            
            # Read info.plist
            plist_fd = package.open(self.PLIST_FILE, 'r')
            try:
                plist = plistlib.readPlist(plist_fd)
            except Exception:
                self._stopMessage()
                raise

            # if plist['filetype_version'] > self.FILETYPE_VERSION:
            #     self.logger.printL(1,"Too new filetype", "error", "DW")
            #     raise Error('Too new filetype')

            ################# START FOR BACKWARD COMPATIBILITY WITH XML
            if plist['filetype_version'] <= self.XML_FILETYPE_VERSION:
                old_filename = filename
                parts = filename.split(".")
                if len(parts) == 1:
                    filename += "_new"
                elif len(parts) > 1:
                    filename = ".".join(parts[:-1]) + "_new."+ parts[-1]
                print filename
                self.logger.printL(1,"Deprecated filetype, will be saved in current filetype as %s instead of %s!" % (filename, old_filename), "error", "DW")
                package_name = plist['package_name']
                ischanged = True
                data, reds, rshowids, preferences = self.loadElementsPackageOLD(package, plist)
            ################# END FOR BACKWARD COMPATIBILITY WITH XML
            else:
                if plist['filetype_version'] != self.FILETYPE_VERSION:
                    self.logger.printL(1,"Filetype does not match current, reading might fail!", "error", "DW")
                package_name = plist['package_name']
                data, reds, rshowids, preferences = self.loadElementsPackage(package, plist)
        except Exception:
            self._stopMessage()
            raise
        finally:
            package.close()

        # Closes with ZipFile
        # Move data class variables
        self.package_name = package_name
        if data is not None:
            self.setData(data)
        else:
            self.data = None
        if reds is not None:
            self.reds = reds
            self.rshowids = rshowids
        else:
            self.reds = Batch([])
            self.rshowids = ICList([], True)
        if preferences:
            self.preferences = preferences
        else:
            self.preferences = self.pm.getDefaultTriplets()
        self.package_filename = os.path.abspath(filename)
        self.isChanged = ischanged
        self.isFromPackage = True
##        print "Done Loading"

    def loadElementsPackage(self, package, plist):
        data, reds, rshowids, preferences = None, None, None, None
        # Load data
        if 'data_LHS_filename' in plist and 'data_RHS_filename' in plist:
            try:
                fdLHS = package.open(plist['data_LHS_filename'], 'r')
                fdRHS = package.open(plist['data_RHS_filename'], 'r')
                data = self._readDataFromCSVFiles([fdLHS, fdRHS])
            except Exception as e:
                print e
                self._stopMessage()
                raise
            finally:
                fdLHS.close()
                fdRHS.close()

        # Load redescriptions
        if 'redescriptions_filename' in plist:
            try:
                fd = package.open(plist['redescriptions_filename'], 'r')
                reds, rshowids = self._readRedescriptionsFromFile(fd, data)
            except Exception:
                self._stopMessage()
                raise
            finally:
                fd.close()

        # Load preferences
        if 'preferences_filename' in plist:
            try:
                fd = package.open(plist['preferences_filename'], 'r')
                preferences = self._readPreferencesFromFile(fd)
            except Exception:
                self._stopMessage()
                raise
            finally:
                fd.close()
        return data, reds, rshowids, preferences


    ################# START FOR BACKWARD COMPATIBILITY WITH XML
    def loadElementsPackageOLD(self, package, plist):
        data, reds, rshowids, preferences = None, None, None, None
        # Load data
        if 'data_filename' in plist:
            try:
                fd = package.open(plist['data_filename'], 'r')
                data = self._readDataFromXMLFile(fd)
            except Exception as e:
                print e
                self._stopMessage()
                raise
            finally:
                fd.close()

        # Load redescriptions
        if 'redescriptions_filename' in plist:
            try:
                fd = package.open(plist['redescriptions_filename'], 'r')
                reds, rshowids = self._readRedescriptionsFromXML(fd, data)
            except Exception:
                self._stopMessage()
                raise
            finally:
                fd.close()

        # Load preferences
        if 'preferences_filename' in plist:
            try:
                fd = package.open(plist['preferences_filename'], 'r')
                preferences = self._readPreferencesFromFile(fd)
            except Exception:
                self._stopMessage()
                raise
            finally:
                fd.close()
        return data, reds, rshowids, preferences


    def _readDataFromXMLFile(self, filename):
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, mode='r')
        return Data.readDataFromXMLFile(filep)


    def _readRedescriptionsFromXML(self, filename, data=None):
        if data is None:
            if self.data is None:
                self._stopMessage()
                raise Exception("Cannot load redescriptions if data is not loaded")
            else:
                data = self.data
        reds = Batch([])
        show_ids = None

        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, mode='r')

        doc = toolRead.parseXML(filep)
        if doc is not None:
            tmpreds = doc.getElementsByTagName("redescriptions")
            if len(tmpreds) == 1:
                reds_node = tmpreds[0]
                for redx in reds_node.getElementsByTagName("redescription"):
                    tmp = Redescription()
                    tmp.fromXML(redx)
                    tmp.recompute(data)
                    reds.append(tmp)
                tmpsi = reds_node.getElementsByTagName("showing_ids")
                if len(tmpsi) == 1:
                    show_ids = toolRead.getValues(tmpsi[0], int)
                    if len(show_ids) == 0 or min(show_ids) < 0 or max(show_ids) >= len(reds):
                        show_ids = None
        if show_ids is None:
            show_ids = range(len(reds))
        rshowids = ICList(show_ids, True)
        return reds, rshowids
    ################# END FOR BACKWARD COMPATIBILITY WITH XML

    def savePackageToFile(self, filename, suffix='.siren'):
        try:
            self._writePackageToFile(filename, suffix)
        except DataError as details:
            self.logger.printL(1,"Problem writing package.\n%s" % details, "error", "DW")
            self._stopMessage()
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open file for package %s" % filename, "error", "DW")
            self._stopMessage()
            raise
        except Exception:
            self.logger.printL(1,"Unexpected error while writing package!\n%s" % sys.exc_info()[1], "error", "DW")
            self._stopMessage()
            raise


            
    ## The saving function
    def _writePackageToFile(self, filename, suffix='.siren'):
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
            f = open(os.path.abspath(filename + suffix), 'w')
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            self._stopMessage()
            return
        else:
            f.close()

        # Store old package_filename
        old_package_filename = self.package_filename
        self.package_filename = os.path.abspath(filename + suffix)
        # Get a temp folder
        tmp_dir = tempfile.mkdtemp(prefix='siren')
        #package_dir = os.path.join(tmp_dir, filename)
        #os.mkdir(package_dir)

        # Write plist
        plist = self._makePlistDict()
        try:
            plistlib.writePlist(plist, os.path.join(tmp_dir, self.PLIST_FILE))
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            self._stopMessage()
            raise


        # Write data files
        try:
            if self.data is not None:
                self._writeData([os.path.join(tmp_dir, plist['data_LHS_filename']),
                                 os.path.join(tmp_dir, plist['data_RHS_filename'])], toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            self._stopMessage()
            raise

        # Write redescriptions
        try:
            if self.reds is not None and len(self.reds) > 0:
                self._writeRedescriptions(os.path.join(tmp_dir, plist['redescriptions_filename']), named=False, with_disabled=True, toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            self._stopMessage()
            raise

        # Write preferences
        try:
            if self.preferences is not None:
                self._writePreferences(os.path.join(tmp_dir, plist['preferences_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            self._stopMessage()
            raise

        # All's there, so pack
        try:
            # DEBUG
            #print 'Writing to', ''.join((filename, '.', suffix))
            # Remove with zipfile... for compliance with Python 2.6
            package = zipfile.ZipFile(filename + suffix, 'w')
            #with zipfile.ZipFile(filename + suffix, 'w') as package:
            package.write(os.path.join(tmp_dir, self.PLIST_FILE),
                          arcname = os.path.join('.', self.PLIST_FILE))
            if self.data is not None:
                package.write(os.path.join(tmp_dir, plist['data_LHS_filename']),
                              arcname = os.path.join('.', plist['data_LHS_filename']),
                              compress_type = zipfile.ZIP_DEFLATED)
                package.write(os.path.join(tmp_dir, plist['data_RHS_filename']),
                              arcname = os.path.join('.', plist['data_RHS_filename']),
                              compress_type = zipfile.ZIP_DEFLATED)

            if self.reds is not None and len(self.reds) > 0:
                package.write(os.path.join(tmp_dir, plist['redescriptions_filename']),
                              arcname = os.path.join('.',
                                                     plist['redescriptions_filename']),
                    compress_type = zipfile.ZIP_DEFLATED)
            if self.preferences is not None:
                package.write(os.path.join(tmp_dir, plist['preferences_filename']),
                              arcname = os.path.join('.', plist['preferences_filename']),
                    compress_type = zipfile.ZIP_DEFLATED)
        except Exception:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            self._stopMessage()
            raise
        finally:
            package.close()

        # All's done, delete temp file
        shutil.rmtree(tmp_dir)
        self.isChanged = False
        self.isFromPackage = True

        # Tell others we're done
        self._stopMessage('saving')

        ## END THE SAVING FUNCTION

    def savePackage(self):
        """Saves to known package"""
        if self.package_filename is None:
            raise ValueError('Cannot save if package_filename is None, use savePackageToFile instead')
        else:
            self.savePackageToFile(self.package_filename, None)


    def exportRedescriptions(self, filename):
        self._startMessage('exporting', filename)
        named = re.search("[^a-zA-Z0-9]named[^a-zA-Z0-9]", filename) is not None
        with_disabled = re.search("[^a-zA-Z0-9]all[^a-zA-Z0-9]", filename) is not None
        style = ""
        if re.search("\.tex$", filename):
            style = "tex"
        try:
            self._writeRedescriptions(filename, named=named, with_disabled=with_disabled, style=style)
        except Exception:
            self._stopMessage()
            raise
        self._stopMessage('exporting')

    def _writeRedescriptions(self, filename, named = False, with_disabled=False, toPackage = False, style=""):
        if named:
            names = self.data.getNames()
        else:
            names = [None, None]
        red_list = [self.reds[i] for i in self.rshowids if self.reds[i].getEnabled() or with_disabled]
        if toPackage:
            fields_supp = [-1, "status_disabled"]
        else:
            fields_supp = None
        # with codecs.open(filename, encoding='utf-8', mode='w') as f:
        with open(filename, mode='w') as f:
            if style == "tex":
                f.write(printTexRedList(red_list, names, fields_supp))
            else:
                f.write(printRedList(red_list, names, fields_supp))
            
    def _writePreferences(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            f.write(PreferencesReader(self.pm).dispParameters(self.preferences, True))

    def _writeData(self, filenames, toPackage = False):
        self.data.writeCSV(filenames)
    
    def _makePlistDict(self):
        """Makes a dict to write to plist."""
        d = dict(creator = self.CREATOR,
            filetype_version = self.FILETYPE_VERSION)
        
        if self.package_filename is None:
            d['package_name'] = self.PACKAGE_NAME
        else:
            (pn, suffix) = os.path.splitext(os.path.basename(self.package_filename))
            if len(pn) > 0:
                d['package_name'] = pn
            else:
                d['package_name'] = self.PACKAGE_NAME

                            
        if self.data is not None:
            d['data_LHS_filename'] = self.DATA_LHS_FILENAME
            d['data_RHS_filename'] = self.DATA_RHS_FILENAME
                                
        if self.reds is not None and len(self.reds) > 0:
            d['redescriptions_filename'] = self.REDESCRIPTIONS_FILENAME

        if self.preferences is not None:
            d['preferences_filename'] = self.PREFERENCES_FILENAME
            
        return d

    def _startMessage(self, action, filenames):
        "Shows the message if needed"
        if self.startReadingFileCallback is not None:
            (fnc, args, kwargs) = self.startReadingFileCallback
            msg = 'Please wait. ' + action.capitalize() + ' file'
            short_msg = action.capitalize() + ' file'
            if len(filenames) <= 1:
                msg += ' '
            else:
                msg += 's '
                short_msg += 's'

            if isinstance(filenames, basestring):
                # In Python 3, test has to be isinstance(filenames, str)
                filenames = [filenames]
            msg += ' '.join(map(os.path.basename, filenames))
            # filename can be a list of filenames with full paths, hence map()
            fnc(msg, short_msg, *args, **kwargs)
            #time.sleep(1) ## give time to process the message?

    def _stopMessage(self, action=None):
        "Removes the message if needed"
        if self.stopReadingFileCallback is not None:
            (fnc, args, kwargs) = self.stopReadingFileCallback
            if action is None:
                mess = "An error occurred"
            else:
                mess = action.capitalize()+' done'
            fnc(mess, *args, **kwargs)

    # def getPolys(self, pdp, boundaries):
    #     if pdp is not None and self.pdp != pdp:
    #         self.pdp = pdp
    #         try:
    #             self.polys = make_polys.makePolys(self.pdp, boundaries)
    #         except Exception as e:
    #             self.logger.printL(1,"Failed drawing polygons.\nFall back to dots...", "error", "DW")
    #             self.polys = None
    #     return self.polys


# def main():
#     # print "UNCOMMENT"
#     # pdb.set_trace()
#     dw = DataWrapper(None,"/home/galbrun/TKTL/redescriptors/sandbox/runs/rajapaja_basic/rajapaja.siren")
#     dw.savePackage()
#     dw_new = DataWrapper(None,"/home/galbrun/TKTL/redescriptors/sandbox/runs/rajapaja_basic/rajapaja_new.siren")
#     for red in dw_new.reds:
#         print red

# if __name__ == '__main__':
#     main()
