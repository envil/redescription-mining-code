
import numpy as np
import tempfile
import os
import os.path
import plistlib
import shutil
import zipfile

from classRedescription import Redescription
from classData import Data
from classQuery import Query

class DataWrapper():
    """Contains all the data
    """

    # CONSTANTS
    # Names of the files in the package
    COO_FILENAME = 'coordinates.txt'
    DATA_FILENAMES_PREFIX = 'data-'
    DATA_FILENAMES_SUFFIX = '.txt'
    NAME_FILENAMES_SUFFIX = '.names'
    QUERIES_FILENAME = 'queries.txt'
    PLIST_FILE = 'info.plist'

    # Stuff to write to plist
    FILETYPE_VERSION = 1
    CREATOR = 'DataWrapper'

    def __init__(self, coo_filename = None, data_filenames = None, queries_filename = None, package_filename = None):
        """Inits the class. Either package_filename or the others should be given.
        """
        self.coord = None
        self.coo_filename = None
        self.data = None
        self.lines = None # ??
        self.data_filenames = None
        self.number_of_datafiles = 0
        self.names = None
        self.reds = None
        self.queries_filename = None
        self.package_filename = None
        self.isChanged = False
        self.isFromPackage = False

        if package_filename is not None:
            self.__initWithPackage(package_filename)
        else:
            self.__initWithFiles(coo_filename, data_filenames, queries_filename)

    def __initWithPackage(self, package_filename):
        """Loads everything from a package"""
        try:
            self.loadPackageFromFile(package_filename)
        except IOError, ValueError:
            print 'Cannot open'
            self.package_filename = None
            raise
            ## TODO exception handling
        self.package_filename = package_filename
        self.isFromPackage = True



    def __initWithFiles(self, coo_filename, data_filenames, queries_filename):
        """Loads from files"""

        try:
            if coo_filename is not None:
                self.coord = self.loadCoordFromFile(coo_filename)
            if data_filenames is not None:
                self.data = self.loadDataFromFiles(data_filenames)
                self.updateNames()
                #self.names = self.data.getNames(data_filenames)
            if queries_filename is not None:
                self.reds = self.loadQueriesFromFile(queries_filename)
        except IOError, ValueError:
            print "Cannot open"
            self.coo_filename = None
            self.data_filenames = None
            self.number_of_datafiles = 0
            self.names = None
            self.queries_filename = None
            raise
            ## TODO exception handling

        self.coo_filename = coo_filename
        self.data_filenames = data_filenames
        self.queries_filename = queries_filename
        if data_filenames is not None:
            self.number_of_datafiles = len(data_filenames)
        self.isFromPackage = False
        if coo_filename is not None or data_filenames is not None or queries_filename is not None:
            self.isChanged = True
             



    ## Setters
    def setChanged(self, value=True):
        self.isChanged = value

    def setFromPackage(self, value=True):
        self.isFromPackage = value
        
    def setCoordFromFile(self, coo_filename):
        """Loads new coordinates from file"""
        old_coord = self.coord
        old_coo_filename = self.coo_filename
            
        try:
            self.coord = self.loadCoordFromFile(coo_filename)
        except IOError as details:
            print "Cannot open:", details
            self.coord = old_coord
        except:
            self.coord = old_coord
            raise
        else:
            self.coo_filename = coo_filename
            self.isChanged = True

    def setDataFromFile(self, data_filenames):
        """Loads new data from files"""
        old_data = self.data
        try:
            self.data = self.loadDataFromFiles(data_filenames)
        except IOError as arg:
            print "Cannot open:", arg
            self.data = old_data
        except:
            self.data = old_data
            raise
        else:
            self.data_filenames = data_filenames
            self.number_of_datafiles = len(data_filenames)
            self.isChanged = True

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

    def setQueriesFromFile(self, queries_filename):
        """Loads new queries from file"""
        old_reds = self.reds
        try:
            self.reds = self.loadQueriesFromFile(queries_filename)
        except IOError as arg:
            print "Cannot open", arg
            self.reds = old_reds
        except:
            self.reds = old_reds
            raise
        else:
            self.queries_filename = queries_filename
            self.isChanged = True

    def loadNewPackage(self, package_filename):
        """Loads new data from a package"""
        try:
            self.loadPackageFromFile(package_filename)
        except IOError as arg:
            print "Cannot open", arg
        except:
            raise
        else:
            self.isChanged = False
            self.package_filename = package_filename

    ## The loaders
    def loadCoordFromFile(self, filename):
        try:
            coord = np.loadtxt(self.coo_filename, unpack=True, usecols=(1,0))
        except:
            raise
        return coord

    def loadDataFromFiles(self, filenames):
        try:
            data = Data(filenames)
        except:
            raise
        return data

    def loadQueriesFromFile(self, filename):
        if self.data is None:
            return None
        reds = []
        if isinstance(filename, file):
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
                red = Redescription.fromQueriesPar([queryL, queryR], self.data)
                if red != None:
                    reds.append(red)
        return reds

    def loadPackageFromFile(self, filename):
        """Loads a package"""

        if not zipfile.is_zipfile(filename):
            raise IOError('File is of wrong type')

        
        with zipfile.ZipFile(filename, 'r') as package:
            files = package.namelist()
            (package_name, foo) = os.path.split(files[0])

            # Read info.plist
            plist_fd = package.open(os.path.join(package_name, self.PLIST_FILE), 'r')
            plist = plistlib.readPlist(plist_fd)

            if plist['filetype_version'] > self.FILETYPE_VERSION:
                raise Error('Too new filetype')

            ## TODO ##
        


    ## The saving function
    def savePackageToFile(self, filename, suffix='sirene'):
        """Saves all information to a new file"""

        # Test that we can write to filename
        try:
            f = open(''.join([filename, '.', suffix]), 'w')
        except IOError as arg:
            print "Cannot write to file", arg
            return
        else:
            f.close()

        # Get a temp folder
        tmp_dir = tempfile.mkdtemp(prefix='siren')
        package_dir = os.path.join(tmp_dir, filename)
        os.mkdir(package_dir)

        # Write plist
        plist = self.__makePlistDict()
        try:
            plistlib.writePlist(plist, os.path.join(package_dir, self.PLIST_FILE))
        except IOError:
            shutil.rmtree(tmp_dir)
            raise

        # Write coordinates
        try:
            if self.coord is not None:
                self.saveCoordinates(os.path.join(package_dir, self.COO_FILENAME), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            raise

        # Write data files
        try:
            if self.data is not None:
                self.saveDatafiles([os.path.join(package_dir, file) for file in plist['data_filenames']], toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            raise

        # Write name files
        try:
            if self.names is not None:
                self.saveNamefiles([os.path.join(package_dir, file) for file in plist['name_filenames']], toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            raise

        # Write queries
        try:
            if self.reds is not None:
                self.saveQueries(self.QUERIES_FILENAME, toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            raise

        # All's there, so pack
        try:
            # DEBUG
            #print 'Writing to', ''.join((filename, '.', suffix))
            with zipfile.ZipFile(''.join((filename, '.', suffix)), 'w') as package:
                package.write(os.path.join(package_dir, self.PLIST_FILE),
                              arcname = os.path.join(filename, self.PLIST_FILE))
                if self.coord is not None:
                    package.write(os.path.join(package_dir, self.COO_FILENAME),
                                  arcname = os.path.join(filename, self.COO_FILENAME),
                        compress_type = zipfile.ZIP_DEFLATED)
                if self.data is not None:
                    tmp_data_filenames = plist['data_filenames']
                else:
                    tmp_data_filenames = []
                if self.names is not None:
                    tmp_name_filenames = plist['name_filenames']
                for i in range(len(tmp_data_filenames)):
                    package.write(os.path.join(package_dir, tmp_data_filenames[i]),
                                  arcname = os.path.join(filename, tmp_data_filenames[i]),
                        compress_type = zipfile.ZIP_DEFLATED)
                    if self.names is not None:
                        package.write(os.path.join(package_dir, tmp_name_filenames[i]),
                                      arcname = os.path.join(filename, tmp_name_filenames[i]),
                            compress_type = zipfile.ZIP_DEFLATED)
                if self.reds is not None:
                    package.write(os.path.join(package_dir, self.QUERIES_FILENAME),
                                  arcname = os.path.join(filename,
                                                         self.QUERIES_FILENAME),
                        compress_type = zipfile.ZIP_DEFLATED)
        except:
            shutil.rmtree(tmp_dir)
            raise

        # All's done, delete temp file
        shutil.rmtree(tmp_dir)
        self.isChanged = False
        self.isFromPackage = True

        ## END THE SAVING FUNCTION

    def saveCoordinates(self, filename, toPackage = False):
        pass

    def saveDatafiles(self, filename, toPackage = False):
        pass

    def saveNamefiles(self, filename, toPackage = False):
        pass

    def saveQueries(self, filename, toPackage = False):
        pass
    

    def __makePlistDict(self):
        """Makes a dict to write to plist."""
        d = dict(creator = self.CREATOR,
            filetype_version = self.FILETYPE_VERSION)
            
        if self.coord is not None:
            d['coo_filename'] = self.COO_FILENAME
        if self.data is not None:
            d['data_filenames'] = [''.join([self.DATA_FILENAMES_PREFIX, str(i), self.DATA_FILENAMES_SUFFIX]) for i in range(self.numberOfDataFiles)]
        if self.names is not None:
            d['name_filenames'] = [''.join([self.DATA_FILENAMES_PREFIX, str(i), self.NAME_FILENAMES_SUFFIX]) for i in range(self.numberOfDataFiles)]
        if self.reds is not None:
            d['queries_filename'] = self.QUERIES_FILENAME
            
        return d
            

    ## The loaders
    def loadCoordFromFile(self, filename):
        pass

    def loadDataFromFiles(self, filenames):
        pass

    def loadQueriesFromFile(self, filename):
        pass

            
