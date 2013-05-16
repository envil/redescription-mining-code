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

import pdb

from reremi.classRedescription import Redescription
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
    DATA_FILENAME = 'data.xml'
    REDESCRIPTIONS_FILENAME = 'redescriptions.xml'
    PREFERENCES_FILENAME = 'preferences.xml'
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'siren_package'

    pref_dir = os.path.dirname(__file__)
    conf_defs = [findFile('miner_confdef.xml', ['reremi', pref_dir+'/reremi']),
                 findFile('ui_confdef.xml', [pref_dir])]
    #conf_defs = ['miner_confdef.xml', 'ui_confdef.xml']
    # Stuff to write to plist
    FILETYPE_VERSION = 3
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

    def getNbRows(self):
        if self.data is not None:
            return self.data.nbRows()
        return 0

    def getDataCols(self, side):
        if self.data is not None:
            return self.data.cols[side]
        return []

    def getDataMatrix(self, sides=None, cols=None):
        if self.data is not None:
            return self.data.getMatrix(sides, cols)
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
            return [min(self.data.coords[0]), max(self.data.coords[0]), min(self.data.coords[1]), max(self.data.coords[1])]
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
        return "coords = " + str(self.coords) + "; " \
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
            #self.isChanged = True


#################### IMPORTS            
    def importDataFromCSVFiles(self, data_filenames):
        fnames = list(data_filenames[:2])
        self._startMessage('importing', fnames)        
        try:
            tmp_data = self._readDataFromCSVFiles(data_filenames)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "error", "DW")
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing data from CSV files!\n%s" %  sys.exc_info()[1], "error", "DW")
            raise
        else:
            self.data = tmp_data
            self.resetRedescriptions()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')

    def importDataFromMulFiles(self, data_filenames, names_filenames, coo_filename):
        fnames = list(data_filenames)
        if names_filenames is not None:
            fnames += names_filenames
        if coo_filename is not None:
            fnames += [coo_filename]
        self._startMessage('importing', fnames)
        
        try:
            tmp_data = self._readDataFromMulFiles(data_filenames, names_filenames, coo_filename)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "error", "DW")
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing data from separate files!\n%s" %  sys.exc_info()[1], "error", "DW")
            raise
        else:
            self.data = tmp_data
            self.resetRedescriptions()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')
        

    def importDataFromXMLFile(self, data_filename):
        self._startMessage('importing', data_filename)
        try:
            tmp_data = self._readDataFromXMLFile(data_filename)
        except DataError as details:
            self.logger.printL(1,"Problem reading files.\n%s" % details, "error", "DW")
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing data from file %s!\n%s" % (data_filename, sys.exc_info()[1]), "error", "DW")
            raise
        else:
            self.data = tmp_data
            self.resetRedescriptions()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')

    def importRedescriptionsFromFile(self, redescriptions_filename):
        """Loads new redescriptions from file"""
        self._startMessage('importing', redescriptions_filename)
        try:
            (pn, suffix) = os.path.splitext(os.path.basename(redescriptions_filename))
            if suffix == ".queries":
                tmp_reds, tmp_rshowids = self._readRedescriptionsTXTFromFile(redescriptions_filename)
            else:
                tmp_reds, tmp_rshowids = self._readRedescriptionsFromFile(redescriptions_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing redescriptions from file %s!\n%s" % (redescriptions_filename, sys.exc_info()[1]), "error", "DW")
            raise
        else:
            self.reds = tmp_reds
            self.rshowids = tmp_rshowids
            #self.isChanged = True
        finally:
            self._stopMessage('importing')

    def importRedescriptionsTXTFromFile(self, redescriptions_filename):
        """Loads new redescriptions from file"""
        self._startMessage('importing', redescriptions_filename)
        try:
            tmp_reds, tmp_rshowids = self._readRedescriptionsTXTFromFile(redescriptions_filename)
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing redescriptions from file %s!\n%s" % (redescriptions_filename, sys.exc_info()[1]), "error", "DW")
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
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing preferences from file %s!\n%s" % (preferences_filename, sys.exc_info()[1]), "error", "DW")
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
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open %s" % arg, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while importing package from file %s!\n%s" % (package_filename, sys.exc_info()[1]), "error", "DW")
            raise
        else:
            self.isChanged = False
            self.package_filename = package_filename
        finally:
            self._stopMessage('loading')

######################## READS
    def _readDataFromCSVFiles(self, data_filenames):
        ### WARNING THIS EXPECTS FILENAMES, NOT FILE POINTERS
        try:
            data = Data(data_filenames, "csv")
        except:
            raise
        return data

    def _readDataFromMulFiles(self, data_filenames, names_filenames, coo_filename):
        ### WARNING THIS EXPECTS FILENAMES, NOT FILE POINTERS
        try:
            
            filenames = list(data_filenames)
            if names_filenames is None:
                filenames.extend([None, None])
            else:
                filenames.extend(names_filenames)
            if coo_filename is not None:
                filenames.append(coo_filename)
            data = Data(filenames, "multiple")
        except:
            raise
        return data

    def _readDataFromXMLFile(self, filename):
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, 'r')
        return Data(filep, "xml")


    def _readRedescriptionsFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                raise Exception("Cannot load redescriptions if data is not loaded")
            else:
                data = self.data
        reds = Batch([])
        show_ids = None

        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, 'r')
        
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


    def _readRedescriptionsTXTFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                raise Exception("Cannot load redescriptions if data is not loaded")
            else:
                data = self.data
        reds = Batch([])
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            reds_fp = filename
        else:
            reds_fp = open(filename, 'r')

        for line in reds_fp:
            parts = line.strip().split('\t')
            if len(parts) > 1:
                queryL = Query.parse(parts[0])
                queryR = Query.parse(parts[1])
                red = Redescription.fromQueriesPair([queryL, queryR], data)
                if red is not None:
                    reds.append(red)
        rshowids = ICList(range(len(reds)), True)
        return reds, rshowids

    def _readPreferencesFromFile(self, filename):
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, 'r')

        return ICDict(PreferencesReader(self.pm).getParameters(filep))

    def _readPackageFromFile(self, filename):
        """Loads a package"""

        # TODO: Check that file exists
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
            except:
                raise

            # if plist['filetype_version'] > self.FILETYPE_VERSION:
            #     self.logger.printL(1,"Too new filetype", "error", "DW")
            #     raise Error('Too new filetype')
            if plist['filetype_version'] != self.FILETYPE_VERSION:
                self.logger.printL(1,"Filetype does not match current, reading might fail!", "error", "DW")

            package_name = plist['package_name']

            # Load data
            if 'data_filename' in plist:
                try:
                    fd = package.open(plist['data_filename'], 'r')
                    data = self._readDataFromXMLFile(fd)
                except:
                    raise
                finally:
                    fd.close()
                    
            # Load redescriptions
            if 'redescriptions_filename' in plist:
                try:
                    fd = package.open(plist['redescriptions_filename'], 'r')
                    reds, rshowids = self._readRedescriptionsFromFile(fd, data)
                except:
                    raise
                finally:
                    fd.close()

            # Load preferences
            if 'preferences_filename' in plist:
                try:
                    fd = package.open(plist['preferences_filename'], 'r')
                    preferences = self._readPreferencesFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
        except:
            raise
        finally:
            package.close()


        # Closes with ZipFile
        # Move data class variables
        self.package_name = package_name
        if 'data_filename' in plist:
            self.data = data
        else:
            self.data = None
        if 'redescriptions_filename' in plist:
            self.reds = reds
            self.rshowids = rshowids
        else:
            self.reds = Batch([])
            self.rshowids = ICList([], True)
        if 'preferences_filename' in plist:
            self.preferences = preferences
        else:
            self.preferences = self.pm.getDefaultTriplets()
        self.package_filename = os.path.abspath(filename)
        self.isChanged = False
        self.isFromPackage = True
##        print "Done Loading"


    def savePackageToFile(self, filename, suffix='.siren'):
        try:
            self._writePackageToFile(filename, suffix)
        except DataError as details:
            self.logger.printL(1,"Problem writing package.\n%s" % details, "error", "DW")
            raise
        except IOError as arg:
            self.logger.printL(1,"Cannot open file for package %s" % filename, "error", "DW")
            raise
        except:
            self.logger.printL(1,"Unexpected error while writing package!\n%s" % sys.exc_info()[1], "error", "DW")
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
            raise


        # Write data files
        try:
            if self.data is not None:
                self._writeData(os.path.join(tmp_dir, plist['data_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write redescriptions
        try:
            if self.reds is not None and len(self.reds) > 0:
                self._writeRedescriptions(os.path.join(tmp_dir, plist['redescriptions_filename']), named=False, toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write preferences
        try:
            if self.preferences is not None:
                self._writePreferences(os.path.join(tmp_dir, plist['preferences_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
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
                package.write(os.path.join(tmp_dir, plist['data_filename']),
                              arcname = os.path.join('.', plist['data_filename']),
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
        except:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
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


    def exportRedescriptions(self, filename, named=True):
        self._startMessage('exporting', filename)
        ### TODO select format
        (pn, suffix) = os.path.splitext(os.path.basename(filename))
        if suffix == ".tex":
            self._writeRedescriptionsTEX(filename, named)
        elif suffix == ".queries":
            self._writeRedescriptionsTXT(filename, named)
        else:
            self._writeRedescriptions(filename, named)
        self._stopMessage('exporting')

    def _writeRedescriptionsTXT(self, filename, named = False, toPackage = False):
        if named:
            names = self.data.getNames()
        else:
            names = [None, None]
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            for i in self.rshowids:
                if self.reds[i].getEnabled():
                    f.write(self.reds[i].dispU(names)+"\n")

    def _writeRedescriptionsTEX(self, filename, named = False, toPackage = False):
        if named:
            names = self.data.getNames()
        else:
            names = [None, None]
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            f.write(Redescription.dispTexPrelude()+"\n")
            for i in self.rshowids:
                if self.reds[i].getEnabled():
                    f.write(self.reds[i].dispTexLine(i, names)+"\n")
            f.write(Redescription.dispTexConc()+"\n")
            f.write("\n")

    def _writeRedescriptions(self, filename, named = False, toPackage = False):
        if named:
            names = self.data.getNames()
        else:
            names = [None, None]

        with open(filename, 'w') as f:
            f.write("<root>\n")
            f.write("\t<redescriptions>\n")
            for i in range(len(self.reds)):
                f.write(self.reds[i].toXML(False, names).replace("\n", "\n\t\t"))
            f.write("\t<showing_ids>\n")
            for i in self.rshowids:
                f.write("\t\t<value>%i</value>\n" % i)
            f.write("\t</showing_ids>\n")
            f.write("\t</redescriptions>\n")
            f.write("</root>\n")
            
    def _writePreferences(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            f.write(PreferencesReader(self.pm).dispParameters(self.preferences, True))

    def _writeData(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            self.data.writeXML(f)
    
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
            d['data_filename'] = self.DATA_FILENAME
                                
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

    def _stopMessage(self, action):
        "Removes the message if needed"
        if self.stopReadingFileCallback is not None:
            (fnc, args, kwargs) = self.stopReadingFileCallback
            fnc(action.capitalize()+' done', *args, **kwargs)
