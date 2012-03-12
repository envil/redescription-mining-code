
import numpy as np
import tempfile
import os
import os.path
import plistlib
import shutil
import zipfile
import cPickle

from classRedescription import Redescription
from classData import Data
from classQuery import Query

class Redescriptions(list):
    """A list-like object to keep track of the changes"""
    def __init__(self, data=[], isChanged = False):
        list.__init__(self, data)
        self._isChanged = isChanged

    @property
    def isChanged(self):
        """Has the list changed"""
        return self._isChanged

    @isChanged.setter
    def isChanged(self, value):
        if isinstance(value, bool):
            self._isChanged = value
        else:
            raise TypeError('The value of isChanged must be Boolean, is '+str(type(value)))

    # Container-type methods
    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self._isChanged = True

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self._isChanged = True
        
    def __setslice__(self, i, j, sequence):
        list.__setslice__(self, i, j, sequence)
        self._isChanged = True

    def __delslice__(self, i, j):
        list.__delslice__(self, i, j)
        self._isChanged = True

    # "Numeric" operations for concatenation and repetition
    def __add__(self, other):
        return Redescriptions(list.__add__(self, other), True)

    def __radd__(self, other):
        return Redescriptions(list.__radd__(self, other), True)
    
    def __iadd__(self, other):
        list.__iadd__(self, other)
        self._isChanged = True
        return self

    def __mul__(self, other):
        return Redescriptions(list.__mul__(self, other), True)

    def __rmull__(self, other):
        return Redescriptions(list.__rmul__(self, other), True)

    def __imul__(self, other):
        list.__imul__(self, other)
        self._isChanged = True
        return self

    # Public methods for list
    def append(self, val):
        list.append(self, val)
        self._isChanged = True

    def extend(self, L):
        list.extend(self, L)
        self._isChanged = True

    def insert(self, i, x):
        list.insert(self, i, x)
        self._isChanged = True

    def remove(self, x):
        list.remove(self, x)
        self._isChanged = True

    def pop(self, i = None):
        list.pop(self, i)
        self._isChanged = True

    def sort(self):
        list.sort(self)
        self._isChanged = True

    def reverse(self):
        list.reverse(self)
        self._isChanged = True

class DataWrapper():
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
    PLIST_FILE = 'info.plist'
    PACKAGE_NAME = 'sirene_package'

    # Stuff to write to plist
    FILETYPE_VERSION = 2
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
        self.package_name = None
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
            #self.package_filename = package_filename
            #self.isFromPackage = True



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
            coord = np.loadtxt(filename, unpack=True, usecols=(1,0))
        except:
            raise
        return coord

    def loadDataFromFiles(self, filenames):
        try:
            data = Data(filenames)
        except:
            raise
        return data

    def _loadPickledDataFromFile(self, f):
        """Requires a file pointer to a picle file"""
        try:
            data = cPickle.load(f)
        except cPickle.UnpicklingError as e:
            raise ValueError(e.args)
        except:
            raise
        return data

    def loadNamesFromFiles(self, filenames):
        try:
            names = self.data.getNames(filenames)
        except:
            raise
        return names

    def _loadPickeldNamesFromFile(self, f):
        """Requires a file pointer to a picle file"""
        try:
            names = cPickle.load(f)
        except cPickle.UnpicklingError as e:
            raise ValueError(e.args)
        except:
            raise
        return names
    
    def loadQueriesFromFile(self, filename, data=None):
        if data is None:
            if self.data is None:
                return None
            else:
                data = self.data
        reds = []
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

    def loadPackageFromFile(self, filename):
        """Loads a package"""

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
                    data = self._loadPickledDataFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
  
            # Load names
            if 'name_picklefilename' in plist:
                try:
                    fd = package.open(plist['name_picklefilename'], 'r')
                    names = self._loadPickledNamesFromFiles(fd)
                except:
                    raise
                finally:
                    fd.close()

            # Load coordinates
            if 'coo_filename' in plist:
                try:
                    fd = package.open(plist['coo_filename'], 'r')
                    coord = self.loadCoordFromFile(fd)
                except:
                    raise
                finally:
                    fd.close()
                    
            # Load queries
            if 'queries_filename' in plist:
                try:
                    fd = package.open(plist['queries_filename'], 'r')
                    reds = self.loadQueriesFromFile(fd, data)
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
            self.queries_filename = plist['queries_filename']
        else:
            self.reds = None
            self.queries_filename = None
        self.package_filename = os.path.abspath(filename)
        self.isChanged = False
        self.isFromPackage = True


    ## The saving function
    def savePackageToFile(self, filename, suffix='siren'):
        """Saves all information to a new file"""

        # Test that we can write to filename
        try:
            f = open(os.path.abspath(''.join([filename, '.', suffix])), 'w')
        except IOError as arg:
            print "Cannot write to file", arg
            return
        else:
            f.close()

        # Store old package_filename
        old_package_filename = self.package_filename
        self.package_filename = os.path.abspath(''.join([filename, '.', suffix]))
        # Get a temp folder
        tmp_dir = tempfile.mkdtemp(prefix='siren')
        #package_dir = os.path.join(tmp_dir, filename)
        #os.mkdir(package_dir)

        # Write plist
        plist = self.__makePlistDict()
        try:
            plistlib.writePlist(plist, os.path.join(tmp_dir, self.PLIST_FILE))
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # Write coordinates
        try:
            if self.coord is not None:
                self.saveCoordinates(os.path.join(tmp_dir, plist['coo_filename']), toPackage = True)
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
                self.saveQueries(os.path.join(tmp_dir, plist['queries_filename']), toPackage = True)
        except IOError:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # All's there, so pack
        try:
            # DEBUG
            #print 'Writing to', ''.join((filename, '.', suffix))
            with zipfile.ZipFile(''.join((filename, '.', suffix)), 'w') as package:
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
        except:
            shutil.rmtree(tmp_dir)
            self.package_filename = old_package_filename
            raise

        # All's done, delete temp file
        shutil.rmtree(tmp_dir)
        self.isChanged = False
        self.isFromPackage = True

        ## END THE SAVING FUNCTION

    def saveCoordinates(self, filename, toPackage = False):
        c = np.vstack((self.coord[1,:], self.coord[0,:]))
        try:
            np.savetxt(filename, c.transpose())
        except:
            raise
        if not toPackage:
            self.coo_filename = filename

    def saveDatafiles(self, filename, toPackage = False):
        pass

    def _pickleDatafiles(self, filename, toPackage = True):
        with open(filename, 'w') as f:
            try:
                cPickle.dump(self.data, f, 0)
            except cPickle.PicklingError as e:
                raise ValueError(e.args)
            except:
                raise

    def saveNamefiles(self, filename, toPackage = False):
        pass

    def _pickeNamefiles(self, filename, toPackage = True):
        with open(filename, 'w') as f:
            try:
                cPickle.dump(self.names, f, 0)
            except cPickle.PicklingError as e:
                raise ValueError(e.args)
            except:
                raise

    def saveQueries(self, filename, toPackage = False):
        with open(filename, 'w') as f:
            for i in range(len(self.reds)):
                self.reds[i].write(f, None)
    

    def __makePlistDict(self):
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
            
        return d
            


            
