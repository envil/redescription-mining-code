
import numpy as np
import tempfile
import os
import os.path
import plistlib
import shutil
import zipfile
import cPickle
import pdb
import codecs

from classRedescription import Redescription
from classData import Data
from classQuery import Query
from ICList import ICList
from classSettings import Settings


class DataWrapper(object):
    """Contains all the data
    """

    # CONSTANTS
    # Names of the files in the package
    COO_FILENAME = 'coordinates.txt'
    DATA_PICKLEFILENAME = "data.pickle"
    NAMES_PICKLEFILENAME = "names.pickle"
    DATA_FILENAMES_PREFIX = 'data-'
    DATA_FILENAMES_SUFFIX = '.txt'
    NAME_FILENAMES_SUFFIX = '.names'
    QUERIES_FILENAME = 'queries.txt'
    RSHOWIDS_FILENAME = 'rshowids.txt'
    SETTINGS_FILENAME = 'settings.conf'
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'sirene_package'

    # Stuff to write to plist
    FILETYPE_VERSION = 2
    CREATOR = 'DataWrapper'

    def __init__(self, coo_filename = None, data_filenames = None, queries_filename = None, settings_filename = None, package_filename = None):
        """Inits the class. Either package_filename or the others should be given.
        """

        #### [[idi, 1] for idi in range(len(self.data))]
        self.coord = None
        self.coo_filename = None
        self.data = None
        self.data_filenames = None
        self.number_of_datafiles = 0
        self.names = None
        self.reds = None
        self.rshowids = None
        self.minesettings = None
        self.uisettings = None
        self.queries_filename = None
        self.package_filename = None
        self.settings_filename = None
        self.package_name = None
        self._isChanged = False
        self._isFromPackage = False

        if package_filename is not None:
            self._initWithPackage(package_filename)
        else:
            self._initWithFiles(coo_filename, data_filenames, queries_filename, settings_filename)

    def _initWithPackage(self, package_filename):
        """Loads everything from a package"""
        try:
            self._readPackageFromFile(package_filename)
        except IOError, ValueError:
            print 'Cannot open'
            self.package_filename = None
            raise
            ## TODO exception handling
            #self.package_filename = package_filename
            #self.isFromPackage = True



    def _initWithFiles(self, coo_filename, data_filenames, queries_filename, settings_filename):
        """Loads from files"""

        self.coo_filename = coo_filename
        self.data_filenames = data_filenames
        self.queries_filename = queries_filename
        self.settings_filename = settings_filename
        try:
            if coo_filename is not None:
                self.coord = self._readCoordFromFile(coo_filename)
            if data_filenames is not None:
                self.data = self._readDataFromFiles(data_filenames)
                self.updateNames()
                #self.names = self.data.getNames(data_filenames)
            if queries_filename is not None:
                self.reds = self._readQueriesFromFile(queries_filename)
            if settings_filename is not None:
                self.minesettings = self._readSettingsFromFile(settings_filename)
        except IOError, ValueError:
            print "Cannot open"
            self.coo_filename = None
            self.data_filenames = None
            self.number_of_datafiles = 0
            self.names = None
            self.queries_filename = None
            self.settings_filename = None
            raise
            
        if data_filenames is not None:
            self.number_of_datafiles = len(data_filenames)
        self.isFromPackage = False
        if coo_filename is not None or data_filenames is not None or queries_filename is not None or settings_filename is not None:
            self.rshowids = ICList([[idi, 1] for idi in range(len(self.reds))], True)
            self.isChanged = True
             


    def __str__(self):
        return "coord = " + str(self.coord) + "; " \
            + "coo_filename = " + str(self.coo_filename) + "; " \
            + "data = " + str(self.data) + "; " \
            + "data_filenames = " + str(self.data_filenames) + "; " \
            + "number_of_datafiles = " + str(self.number_of_datafiles) + "; " \
            + "names = " + str(self.names) + "; " \
            + "#reds = " + str(len(self.reds)) + "; " \
            + "rshowids = " + str(self.rshowids) + "; " \
            + "minesettings = " + str(self.minesettings) + "; " \
            + "uisettings = " + str(self.uisettings) + "; " \
            + "queries_filename = " + str(self.queries_filename) + "; " \
            + "package_filename = " + str(self.package_filename) + "; " \
            + "settings_filename = " + str(self.settings_filename) + "; " \
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
        
        
    def importCoordFromFile(self, coo_filename):
        """Loads new coordinates from file"""
        old_coord = self.coord
        old_coo_filename = self.coo_filename
            
        try:
            self.coord = self._readCoordFromFile(coo_filename)
        except IOError as details:
            print "Cannot open:", details
            self.coord = old_coord
        except:
            self.coord = old_coord
            raise
        else:
            self.coo_filename = coo_filename
            self.isChanged = True

    def importDataFromFiles(self, data_filenames):
        """Loads new data from files"""
        old_data = self.data
        try:
            self.data = self._readDataFromFiles(data_filenames)
        except IOError as arg:
            print "Cannot open:", arg
            self.data = old_data
        except:
            self.data = old_data
            raise
        else:
            self.data_filenames = data_filenames
            self.number_of_datafiles = len(data_filenames)
            self.reds = ICList()
            self.coord = None
            self.isChanged = True
            self.isFromPackage = False

    def updateNames(self):
        """Update names to match those of data"""
        if self.data_filenames is None: return
        old_names = self.names
        try:
            self.names = self.data.getNames(self.data_filenames)
        except:
            print "Cannot update names"
            self.names = old_names
            raise
        else:
            self.isChanged = True
            self.isFromPackage = False

    def importQueriesFromFile(self, queries_filename):
        """Loads new queries from file"""
        old_reds = self.reds
        try:
            self.reds = self._readQueriesFromFile(queries_filename)
        except IOError as arg:
            print "Cannot open", arg
            self.reds = old_reds
            raise
        except:
            self.reds = old_reds
            raise
        else:
            self.queries_filename = queries_filename
            self.rshowids = ICList([[idi, 1] for idi in range(len(self.reds))], True)
            self.isChanged = True

    def importSettingsFromFile(self, settings_filename):
        """Imports mining settings from file"""
        old_settings = self.minesettings
        try:
            self.minesettings = self._readSettingsFromFile(settings_filename)
        except IOError as arg:
            print "Cannot open", arg
            self.minesettings = old_settings
            raise
        except:
            self.minesettings = old_settings
            raise
        else:
            self.settings_filename = settings_filename
            self.isChanged = True
            

    def reloadCoord(self):
        """Re-reads coordinates"""
        try:
            self.importCoordFromFile(self.coo_filename)
        except:
            raise

    def reloadQueries(self):
        """Re-reads queries"""
        try:
            self.importQueriesFromFile(self.queries_filename)
        except:
            raise

    def reloadSettings(self):
        """Re-read settings"""
        try:
            self.importSettingsFromFile(self.settings_filename)
        except:
            raise

    def openPackage(self, package_filename):
        """Loads new data from a package"""
        try:
            self._readPackageFromFile(package_filename)
        except IOError as arg:
            print "Cannot open", arg
            raise
        except:
            raise
        else:
            self.isChanged = False
            self.package_filename = package_filename

    ## The readers
    def _readCoordFromFile(self, filename):
        try:
            coord = np.loadtxt(filename, unpack=True, usecols=(1,0))
        except:
            raise
        return coord

    def _readDataFromFiles(self, filenames):
        try:
            data = Data(filenames)
        except:
            raise
        return data

    def _readPickledDataFromFile(self, f):
        """Requires a file pointer to a picle file"""
        try:
            data = cPickle.load(f)
        except cPickle.UnpicklingError as e:
            raise ValueError(e.args)
        except:
            raise
        return data

    def _readNamesFromFiles(self, filenames):
        try:
            names = self.data.getNames(filenames)
        except:
            raise
        return names

    def _readPickledNamesFromFile(self, f):
        """Requires a file pointer to a picle file"""
        try:
            names = cPickle.load(f)
        except cPickle.UnpicklingError as e:
            raise ValueError(e.args)
        except:
            raise
        return names
    
    def _readQueriesFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                raise Exception("Cannot load queries if data is not loaded")
            else:
                data = self.data
        reds = ICList([])
        if isinstance(filename, file) or isinstance(filename, zipfile.ZipExtFile):
            reds_fp = filename
        else:
            try:
                reds_fp = open(filename, 'r')
            except:
                raise

        for line in reds_fp:
            parts = line.strip().split('\t')
            if len(parts) > 1:
                queryL = Query.parse(parts[0])
                queryR = Query.parse(parts[1])
                red = Redescription.fromQueriesPair([queryL, queryR], data)
                if red != None:
                    reds.append(red)
        return reds

    def _readRshowidsFromFile(self, file):
        if not hasattr(file, 'readline'):
            try:
                fp = open(file)
            except:
                raise
        else:
            fp = file

        rshowids = ICList()
        for line in fp:
            rshowids.append(int(line))

        if not hasattr(file, 'readline'):
            fp.close()

        return rshowids

    def _readSettingsFromFile(self, filename):
        try:
            minesettings = Settings('mine', ['part_run_gui', filename])
            minesettings.getParams()
        except:
            raise
        else:
            return minesettings

    def _readPackageFromFile(self, filename):
        """Loads a package"""

        # TODO: Check that file exists
        if not zipfile.is_zipfile(filename):
            raise IOError('File is of wrong type')

        
        with zipfile.ZipFile(filename, 'r') as package:
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
            if 'data_picklefilename' in plist:
                try:
                    fd = package.open(plist['data_picklefilename'], 'r')
                    data = self._readPickledDataFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
  
            # Load names
            if 'name_picklefilename' in plist:
                try:
                    fd = package.open(plist['name_picklefilename'], 'r')
                    names = self._readPickledNamesFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()

            # Load coordinates
            if 'coo_filename' in plist:
                try:
                    fd = package.open(plist['coo_filename'], 'r')
                    coord = self._readCoordFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
                    
            # Load queries
            if 'queries_filename' in plist:
                try:
                    fd = package.open(plist['queries_filename'], 'r')
                    reds = self._readQueriesFromFile(fd, data)
                    fd2 = package.open(plist['rshowids_filename'], 'r')
                    rshowids = self._readRshowidsFromFile(fd2)
                except:
                    raise
                finally:
                    fd.close()
                    fd2.close()

            # Load settings
            if 'settings_filename' in plist:
                try:
                    fd = package.open(plist['settings_filename'], 'r')
                    minesettings = self._readSettingsFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()


        # Closes with ZipFile
        # Move data class variables
        self.package_name = package_name
        if 'data_picklefilename' in plist:
            self.data = data
            self.data_filenames = plist['data_filenames']
            self.number_of_datafiles = len(plist['data_filenames'])
        else:
            self.data = None
            self.data_filenames = None
            self.number_of_datafiles = 0
        if 'name_picklefilename' in plist:
            self.names = names
        else:
            self.names = None
        if 'coo_filename' in plist:
            self.coord = coord
            self.coo_filename = plist['coo_filename']
        else:
            self.coord = None
            self.coo_filename = None
        if 'queries_filename' in plist:
            self.reds = reds
            self.rshowids = rshowids
            self.queries_filename = plist['queries_filename']
        else:
            self.reds = None
            self.rshowids = None
            self.queries_filename = None
        if 'settings_filename' in plist:
            self.minesettings = minesettings
            self.settings_filename = plist['settings_filename']
        else:
            self.minesettings = None
            self.settings_filename = None
        self.package_filename = os.path.abspath(filename)
        self.isChanged = False
        self.isFromPackage = True


    ## The saving function
    def savePackageToFile(self, filename, suffix='.siren'):
        """Saves all information to a new file"""

        if suffix is None:
            (filename, suffix) = os.path.splitext(filename)
        else:
            (fn, sf) = os.path.splitext(filename)
            if sf == suffix:
                filename = fn

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

        # Write coordinates
        try:
            if self.coord is not None:
                self._writeCoordinates(os.path.join(tmp_dir, plist['coo_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write data files
        try:
            if self.data is not None:
                self._pickleDatafiles(os.path.join(tmp_dir, plist['data_picklefilename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write name files
        try:
            if self.names is not None:
                self._pickleNamefiles(os.path.join(tmp_dir, plist['name_picklefilename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write queries
        try:
            if self.reds is not None:
                self._writeQueries(os.path.join(tmp_dir, plist['queries_filename']), toPackage = True)
                self._writeRshowids(os.path.join(tmp_dir, plist['rshowids_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write settings
        try:
            if self.minesettings is not None:
                self._writeSettings(os.path.join(tmp_dir, plist['settings_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # All's there, so pack
        try:
            # DEBUG
            #print 'Writing to', ''.join((filename, '.', suffix))
            with zipfile.ZipFile(filename + suffix, 'w') as package:
                package.write(os.path.join(tmp_dir, self.PLIST_FILE),
                              arcname = os.path.join('.', self.PLIST_FILE))
                if self.coord is not None:
                    package.write(os.path.join(tmp_dir, plist['coo_filename']),
                                  arcname = os.path.join('.', plist['coo_filename']),
                        compress_type = zipfile.ZIP_DEFLATED)
                if self.data is not None:
                    package.write(os.path.join(tmp_dir, plist['data_picklefilename']),
                                  arcname = os.path.join('.', plist['data_picklefilename']),
                        compress_type = zipfile.ZIP_DEFLATED)
                if self.names is not None:
                    package.write(os.path.join(tmp_dir, plist['name_picklefilename']),
                                  arcname = os.path.join('.', plist['name_picklefilename']),
                        compress_type = zipfile.ZIP_DEFLATED)
                if self.reds is not None:
                    package.write(os.path.join(tmp_dir, plist['queries_filename']),
                                  arcname = os.path.join('.',
                                                         plist['queries_filename']),
                        compress_type = zipfile.ZIP_DEFLATED)
                    package.write(os.path.join(tmp_dir, plist['rshowids_filename']),
                                  arcname = os.path.join('.',
                                                         plist['rshowids_filename']),
                        compress_type = zipfile.ZIP_DEFLATED)
                if self.minesettings is not None:
                    package.write(os.path.join(tmp_dir, plist['settings_filename']),
                                  arcname = os.path.join('.', plist['settings_filename']),
                                  compress_type = zipfile.ZIP_DEFLATED)
        except:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # All's done, delete temp file
        shutil.rmtree(tmp_dir)
        self.isChanged = False
        self.isFromPackage = True

        ## END THE SAVING FUNCTION

    def savePackage(self):
        """Saves to known package"""
        if self.package_filename is None:
            raise ValueError('Cannot save if package_filename is None, use savePackageToFile instead')
        else:
            self.savePackageToFile(self.package_filename, None)

    def _writeCoordinates(self, filename, toPackage = False):
        c = np.vstack((self.coord[1,:], self.coord[0,:]))
        try:
            np.savetxt(filename, c.transpose())
        except:
            raise
        if not toPackage:
            self.coo_filename = filename


    def _pickleDatafiles(self, filename, toPackage = True):
        with open(filename, 'w') as f:
            try:
                cPickle.dump(self.data, f, 0)
            except cPickle.PicklingError as e:
                raise ValueError(e.args)
            except:
                raise


    def _pickleNamefiles(self, filename, toPackage = True):
        with open(filename, 'w') as f:
            try:
                cPickle.dump(self.names, f, 0)
            except cPickle.PicklingError as e:
                raise ValueError(e.args)
            except:
                raise

    def exportQueries(self, filename, named = False, toPackage = False):
        if named:
            names = self.names
        else:
            names = [None, None]
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            for i, show in self.rshowids:
                if show:
                    f.write(self.reds[i].dispU(names)+"\n")

    def exportQueriesLatex(self, filename, named = False, toPackage = False):
        if named:
            names = self.names
        else:
            names = [None, None]
        with codecs.open(filename, encoding='utf-8', mode='w') as f:
            f.write(Redescription.dispTexPrelude()+"\n")
            for i, show in self.rshowids:
                if show:
                    f.write(self.reds[i].dispTexLine(i, names)+"\n")
            f.write(Redescription.dispTexConc()+"\n")
            f.write("\n")

    def _writeQueries(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            for i in range(len(self.reds)):
                self.reds[i].write(f, None)

    def _writeRshowids(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            for i in range(len(self.rshowids)):
                f.write(str(self.rshowids[i])+'\n')

    def _writeSettings(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            f.write(self.minesettings.dispParams())
    

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
            
        if self.coord is not None:
            if self.coo_filename is not None:
                d['coo_filename'] = os.path.basename(self.coo_filename)
            else:
                d['coo_filename'] = self.COO_FILENAME
                
        if self.data is not None:
            if self.data_filenames is not None:
                d['data_filenames'] = [os.path.basename(df) for df in self.data_filenames]
            else:
                d['data_filenames'] = [''.join([self.DATA_FILENAMES_PREFIX, str(i), self.DATA_FILENAMES_SUFFIX]) for i in range(self.numberOfDataFiles)]
            d['data_picklefilename'] = self.DATA_PICKLEFILENAME
                
        if self.names is not None:
            if self.data_filenames is not None:
                name_filenames = []
                for i in range(len(self.data_filenames)):
                    (nf, ext) = os.path.splitext(os.path.basename(self.data_filenames[i]))
                    name_filenames.append(str(nf) + str(self.NAME_FILENAMES_SUFFIX))
                d['name_filenames'] = name_filenames
            else:
                d['name_filenames'] = [''.join([self.DATA_FILENAMES_PREFIX, str(i), self.NAME_FILENAMES_SUFFIX]) for i in range(self.numberOfDataFiles)]
            d['name_picklefilename'] = self.NAMES_PICKLEFILENAME
                
        if self.reds is not None:
            if self.queries_filename is not None:
                d['queries_filename'] = os.path.basename(self.queries_filename)
            else:
                d['queries_filename'] = self.QUERIES_FILENAME
            d['rshowids_filename'] = self.RSHOWIDS_FILENAME

        if self.minesettings is not None:
            if self.settings_filename is not None:
                d['settings_filename'] = os.path.basename(self.settings_filename)
            else:
                d['settings_filename'] = self.SETTINGS_FILENAME
            
        return d
            


            
