#!/usr/bin/env python

# usage: python prepare_pck_files.py win|src|clean

import sys
import re
import os.path
import glob
import subprocess

from blocks.common_details import common_variables

this_rep = os.path.dirname(os.path.abspath(__file__))

deb_file_list = ['README', 'Makefile', 'debian/copyright', 'debian/control', 'debian/rules', 'debian/changelog', 'debian/compat', 'x-siren.xml', 'siren_desktop',  'x-siren_desktop']
src_file_list = ['README.md']
win_file_list = ['setup.nsi']

file_list = src_file_list
if len(sys.argv) > 1:
    if sys.argv[1] == "win":
        file_list = win_file_list
    elif sys.argv[1] == "deb":
        file_list = deb_file_list
    elif sys.argv[1] == "clean":
        print("Cleaning up files...")
        for filename in deb_file_list+src_file_list+win_file_list:
            if os.path.exists(this_rep+"/"+filename):
                print("- " + this_rep+"/" + filename)
                os.remove(this_rep+"/" + filename)
        if os.path.isdir('debian'):
            print("- REP debian")
            subprocess.check_call("rm -rf "+this_rep+"/debian", shell=True)

        exit()

variables = {}
for entry, vals in common_variables.items():
    variables["__"+entry+"__"] = vals
variables.update({"__PYTHON_SRC__": sys.executable})
variables.update({"__MAIN_FILEPREFF__": re.sub(".py", "", variables["__MAIN_FILENAME__"])})


def openMakeP(filename, mode="w"):
    d = os.path.dirname(filename)
    if len(d) > 0 and not os.path.isdir(d):
        os.makedirs(d)
    return open(filename, mode)


def multiple_replace(dict, text):
    """ Replace in 'text' all occurences of any key in the given
    dictionary by its corresponding value.  Returns the new tring."""

    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)


files_dest = {}
# README
files_dest["README.md"] = '''# __PROJECT_NAME__ --- __PROJECT_DESCRIPTION__

__PROJECT_DESCRIPTION_LINE__


### Installation

#### Dependencies
`python-siren` requires several other Python utilities, including wxPython Phoenix (for the GUI), Numpy, Scipy, Scikit-learn, Matplotlib, and Cartopy.

__DEPENDENCIES_PIP_STR__

#### PIP
with pip, installation should be as easy as running 
`pip install python-siren`

this should provide the following commands:

* `exec_siren` to launch the interface for interactively mining and visualizing redescriptions
* `exec_clired` to run the command-line redescription mining algorithms
* `exec_server` to launch the server for off-loading computations
* `exec_client` to run the command-line client allowing to send computations to server

### More information
See __PROJECT_URL__

### License
__PROJECT_NAME__ is licensed under Apache License v2.0. See attached file "LICENSE".

(c) __PROJECT_AUTHORS__, __COPYRIGHT_YEAR_FROM__
'''


files_dest["README"] = '''# __PROJECT_NAME__ --- __PROJECT_DESCRIPTION__

__PROJECT_DESCRIPTION_LINE__


### Installation
python-siren requires several other python utilities, including wxPython Phoenix (GUI), Numpy, Scipy, Scikit-learn, and Matplotlib (+Cartopy).

With a debian-based distribution run the following commands as root to install:
dpkg -i the_latest___PROJECT_NAMELOW___deb_package.deb

Afterward, you might need to run, to fix dependencies, i.e., install missing required packages 
sudo apt-get -f install

If everything went fine, you should find a __PROJECT_NAME__ entry in your Applications menu.

### More information
See __PROJECT_URL__

### License
__PROJECT_NAME__ is licensed under Apache License v2.0. See attached file "LICENSE".

(c) __PROJECT_AUTHORS__, __COPYRIGHT_YEAR_FROM__
'''

# Makefile
files_dest["Makefile"] = '''PYTHON=__PYTHON_SRC__
DESTDIR=/
BUILDIR=$(CURDIR)/debian/__PROJECT_NAMELOW__
PROJECT=__PROJECT_NAME__
VERSION=__VERSION__

SIREN_DATA=siren/data

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

	mkdir -p $(DESTDIR)/usr/share/icons/hicolor/32x32/apps/
	cp $(SIREN_DATA)/icons/siren_icon32x32.png $(DESTDIR)/usr/share/icons/hicolor/32x32/apps/siren.png

	mkdir -p $(DESTDIR)/usr/share/applications/
	cp siren_desktop $(DESTDIR)/usr/share/applications/siren.desktop

	mkdir -p $(DESTDIR)/usr/share/mime/x-content/
	cp x-siren.xml $(DESTDIR)/usr/share/mime/x-content/	

	mkdir -p $(DESTDIR)/usr/share/mimelnk/x-content/
	cp x-siren_desktop $(DESTDIR)/usr/share/mimelnk/x-content/x-siren.desktop	

	mkdir -p $(DESTDIR)/usr/bin
	cp __MAIN_FILENAME__ $(DESTDIR)/usr/bin
	chmod a+x $(DESTDIR)/usr/bin/__MAIN_FILENAME__

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)-$$1\.orig\.tar\.gz/' ../*
	# build the package
	dpkg-buildpackage -rfakeroot

clean:
	$(PYTHON) setup.py clean
	#$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete'''

# debian/compat
files_dest["debian/compat"] = "7"

# debian/control
files_dest["debian/control"] = '''Source: __PACKAGE_NAME__
Section: science
Priority: extra
Maintainer: __MAINTAINER_NAME__ <__MAINTAINER_EMAIL__>
Build-Depends: __DEPENDENCIES_DEB_STR__
Standards-Version: 3.8.4

Package: __PACKAGE_NAME__
Architecture: all
Homepage: __PROJECT_URL__
Depends: python (>= 3), __DEPENDENCIES_DEB_STR__
Description: __PROJECT_NAME__ __PROJECT_DESCRIPTION__
 __PROJECT_DESCRIPTION_LONG__
'''

# debian/copyright
files_dest["debian/copyright"] = '''Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/

Files: *
Copyright: Copyright __COPYRIGHT_YEAR_FROM__ __MAINTAINER_NAME__ <__MAINTAINER_EMAIL__>
License: Apache-2.0
   Copyright __COPYRIGHT_YEAR_FROM__ __MAINTAINER_LOGIN__

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   On Debian systems, the complete text of the Apache License Version 2.0 can be found in `/usr/share/common-licenses/Apache-2.0'.
'''

# debian/rules
files_dest["debian/rules"] = '''#!/usr/bin/make -f
# -*- makefile -*-

%:
	dh $@

override_dh_usrlocal:
'''

# debian/changelog
files_dest["debian/changelog"] = '''__PACKAGE_NAME__ (__VERSION__) UNSTABLE; urgency=low

__LAST_CHANGES_STR__

 -- __MAINTAINER_NAME__ <__MAINTAINER_EMAIL__>  __LAST_CHANGES_DATE__
'''

# x-siren_desktop
files_dest["x-siren_desktop"] = '''[Desktop Entry]
Comment=__PROJECT_NAME__ File

Icon=__PACKAGE_NAMELOW__
Type=MimeType
MimeType=x-content/x-siren
Patterns=*.siren;
'''

# x-siren.xml
files_dest["x-siren.xml"] = '''<?xml version="1.0"?>
<mime-info xmlns='http://www.freedesktop.org/standards/shared-mime-info'>
  <mime-type type="x-content/x-siren">
    <comment>__PROJECT_NAME__ __PROJECT_DESCRIPTION__ package</comment>
    <glob pattern="*.siren"/>
  </mime-type>
</mime-info>
'''

# siren_desktop
files_dest["siren_desktop"] = '''[Desktop Entry]
Name=__PROJECT_NAME__
Comment=__PROJECT_DESCRIPTION__

Icon=siren

Type=Application
Categories=Education;Math;Science;
MimeType=application/x-siren

Exec=__MAIN_FILENAME__
StartupNotify=false
Terminal=false
'''

# print(files_dest.keys())
print("Generating files...")
for filename in file_list:
    print("+ "+this_rep+"/"+filename)
    with openMakeP(this_rep+"/"+filename, "w") as fp:
        fp.write(multiple_replace(variables, files_dest[filename]))
