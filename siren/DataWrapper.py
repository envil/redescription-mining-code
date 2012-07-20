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

import pdb

from reremi.classRedescription import Redescription
from reremi.classData import Data, DataError
from reremi.classQuery import Query
from reremi.toolICList import ICList
from reremi.classBatch import Batch
from reremi.classPreferencesManager import PreferencesManager, PreferencesReader
import reremi.toolRead as toolRead

class DataWrapper(object):
    """Contains all the data
    """

    # CONSTANTS
    # Names of the files in the package
    DATA_FILENAME = 'data.xml'
    QUERIES_FILENAME = 'queries.xml'
    PREFERENCES_FILENAME = 'preferences.xml'
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'siren_package'

    pref_dir = os.path.dirname(__file__)
    conf_defs = [pref_dir + "/reremi/miner_confdef.xml", pref_dir + "/ui_confdef.xml"]
    # Stuff to write to plist
    FILETYPE_VERSION = 2
    CREATOR = 'DataWrapper'

    def __init__(self, package_filename = None):
        """Inits the class. Either package_filename or the others should be given.
        """

        #### [[idi, 1] for idi in range(len(self.data))]
        self.pm = PreferencesManager(self.conf_defs)
        self.resetData()
        self.preferences = self.pm.getDefaultTriplets()
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

    def resetData(self):
        self.data = None
        self.resetQueries()
        self.isChanged = True
        self.isFromPackage = False
        
    def resetQueries(self):
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

    def getData(self):
        return self.data

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
        if self.preferences is not None and self.preferences.has_key(param_id):
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
        if self.reds is not None:
            self._isChanged |= self.reds.isChanged
        if self.rshowids is not None:
            self._isChanged |= self.rshowids.isChanged
        return self._isChanged
    
    @isChanged.setter
    def isChanged(self, value):
        if isinstance(value, bool):
            if value is False:
                if self.reds is not None:
                    self.reds.isChanged = value
                if self.rshowids is not None:
                    self.rshowids.isChanged = value
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
        if type(params) == dict:
            self.preferences.update(params)
            self.isChanged = True


#################### IMPORTS            
    def importDataFromFiles(self, data_filenames, names_filenames, coo_filename):
        fnames = list(data_filenames)
        if names_filenames is not None:
            fnames += names_filenames
        if coo_filename is not None:
            fnames += [coo_filename]
        self._startMessage('importing', fnames)
        
        try:
            tmp_data = self._readDataFromFiles(data_filenames, names_filenames, coo_filename)

        except DataError as details:
            print "Problem reading files.", details
            raise
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.data = tmp_data
            self.resetQueries()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')
        

    def importDataFromFile(self, data_filename):
        self._startMessage('importing', data_filename)
        try:
            tmp_data = self._readDataFromFile(data_filename)
        except DataError as details:
            print "Problem reading files.", details
            raise
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.data = tmp_data
            self.resetQueries()
            self.isChanged = True
            self.isFromPackage = False
        finally:
            self._stopMessage('importing')

    def importQueriesFromFile(self, queries_filename):
        """Loads new queries from file"""
        self._startMessage('importing', queries_filename)
        try:
            (pn, suffix) = os.path.splitext(os.path.basename(queries_filename))
            if suffix == ".queries":
                tmp_reds, tmp_rshowids = self._readQueriesTXTFromFile(queries_filename)
            else:
                tmp_reds, tmp_rshowids = self._readQueriesFromFile(queries_filename)
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.reds = tmp_reds
            self.rshowids = tmp_rshowids
            self.isChanged = True
        finally:
            self._stopMessage('importing')

    def importQueriesTXTFromFile(self, queries_filename):
        """Loads new queries from file"""
        self._startMessage('importing', queries_filename)
        try:
            tmp_reds, tmp_rshowids = self._readQueriesTXTFromFile(queries_filename)
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.reds = tmp_reds
            self.rshowids = tmp_rshowids
            self.isChanged = True
        finally:
            self._stopMessage('importing')

    def importPreferencesFromFile(self, preferences_filename):
        """Imports mining preferences from file"""
        self._startMessage('importing', preferences_filename)
        try:
 
            tmp_preferences = self._readPreferencesFromFile(preferences_filename)
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.preferences = tmp_preferences
            self.isChanged = True
        finally:
            self._stopMessage('importing')
            
    def openPackage(self, package_filename):
        """Loads new data from a package"""
        self._startMessage('loading', [package_filename])
        try:
            self._readPackageFromFile(package_filename)
        except DataError as details:
            print "Problem reading files.", details
            raise
        except IOError as arg:
            print "Cannot open", arg
            raise
        else:
            self.isChanged = False
            self.package_filename = package_filename
        finally:
            self._stopMessage('loading')

######################## READS
    def _readDataFromFiles(self, data_filenames, names_filenames, coo_filename):
        ### WARNING THIS EXPECTS FILENAMES, NOT FILE POINTERS
        try:
            data = Data(data_filenames, names_filenames, coo_filename)
        except:
            raise
        return data

    def _readDataFromFile(self, filename):
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            filep = filename
        else:
            filep = open(filename, 'r')
        return Data(filep)


    def _readQueriesFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                raise Exception("Cannot load queries if data is not loaded")
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


    def _readQueriesTXTFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                raise Exception("Cannot load queries if data is not loaded")
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

        return PreferencesReader(self.pm).getParameters(filep)

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

            if plist['filetype_version'] > self.FILETYPE_VERSION:
                raise Error('Too new filetype')

            package_name = plist['package_name']

            # Load data
            if 'data_filename' in plist:
                try:
                    fd = package.open(plist['data_filename'], 'r')
                    data = self._readDataFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
                    
            # Load queries
            if 'queries_filename' in plist:
                try:
                    fd = package.open(plist['queries_filename'], 'r')
                    reds, rshowids = self._readQueriesFromFile(fd, data)
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
        if 'queries_filename' in plist:
            self.reds = reds
            self.rshowids = rshowids
        else:
            self.reds = None
            self.rshowids = None
        if 'preferences_filename' in plist:
            self.preferences = preferences
        else:
            self.preferences = self.pm.getDefaultTriplets()
        self.package_filename = os.path.abspath(filename)
        self.isChanged = False
        self.isFromPackage = True
##        print "Done Loading"

    ## The saving function
    def savePackageToFile(self, filename, suffix='.siren'):
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
            print "Cannot write to file", arg
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

        # Write queries
        try:
            if self.reds is not None:
                self._writeQueries(os.path.join(tmp_dir, plist['queries_filename']), named=False, toPackage = True)
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
            if self.reds is not None:
                package.write(os.path.join(tmp_dir, plist['queries_filename']),
                              arcname = os.path.join('.',
                                                     plist['queries_filename']),
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


    def exportQueries(self, filename, named=True):
        self._startMessage('exporting', filename)
        ### TODO select format
        (pn, suffix) = os.path.splitext(os.path.basename(filename))
        if suffix == ".tex":
            self._writeQueriesTEX(filename, named)
        elif suffix == ".queries":
            self._writeQueriesTXT(filename, named)
        else:
            self._writeQueries(filename, named)
        self._stopMessage('exporting')

    def _writeQueriesTXT(self, filename, named = False, toPackage = False):
        if named:
            names = self.data.getNames()
        else:
            names = [None, None]
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            for i in self.rshowids:
                if self.reds[i].getEnabled():
                    f.write(self.reds[i].dispU(names)+"\n")

    def _writeQueriesTEX(self, filename, named = False, toPackage = False):
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

    def _writeQueries(self, filename, named = False, toPackage = False):
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
                                
        if self.reds is not None:
            d['queries_filename'] = self.QUERIES_FILENAME

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
