"""
This is a setup.py script generated by py2applet

Usage (OS X):
    python setup.py py2app

Usage (Windows):
    python setup.py py2exe
    

Edits by Pauli
"""

import sys
import os
import os.path
import re
import subprocess
import pdb
import glob
import time

from siren.common_details import common_variables

# Common info
APP = common_variables["MAIN_FILENAME"]
NAME = common_variables["PACKAGE_NAME"]
SHORT_NAME = common_variables["PROJECT_NAME"]
VERSION = common_variables["VERSION"]
DESCRIPTION = common_variables["PROJECT_DESCRIPTION"]
DESCRIPTION_LONG = common_variables["PROJECT_DESCRIPTION_LONG"]
AUTHOR = common_variables["PROJECT_AUTHORS"]
AUTHOR_EMAIL = common_variables["MAINTAINER_EMAIL"]
URL = common_variables["PROJECT_URL"]
LICENSE="Apache_2.0"
COPYRIGHT=u'\u00A9 '+common_variables["COPYRIGHT_YEAR_FROM"]+'-' \
               +common_variables["COPYRIGHT_YEAR_FROM"]+' ' \
               +common_variables["PROJECT_AUTHORS"]
HELP_PACKAGE_FILENAME = 'help.tar.gz'
HELP_PACKAGE_URL = URL+HELP_PACKAGE_FILENAME
HELP_UNPACK_CMD = 'tar xfz '+HELP_PACKAGE_FILENAME # command to unpack the help file to folder help/

########## SETUPTOOLS FILES
LICENSES = ['licenses'] #'LICENSE_basemap', 'LICENSE_matplotlib', 'LICENSE_python', 'LICENSE_wx', 'LICENSE_grako']
#ST_RESOURCES=['help', 'commons', 'screenshots', 'ABOUT', 'LICENSE',
ST_RESOURCES=['help', 'LICENSE', 'CHANGELOG',
              'siren/interface/ui_confdef.xml', 'siren/reremi/miner_confdef.xml', 'siren/reremi/inout_confdef.xml']
# N.B. You must include the icon files later
ST_FILES = [common_variables["MAIN_FILENAME"]]

ST_MORE_FILES=['ez_setup.py']
ST_PACKAGES = ['wx',  'sklearn', 'mpl_toolkits']
MATPLOTLIB_BACKENDS = ['wxagg']

extra_options = dict(
    name=NAME,
    version=VERSION,
    description=(DESCRIPTION),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    )

def get_svnrevision():
    svn_revision = '-1'
    try:
        p = subprocess.check_output(['svn', 'info'])
    except (subprocess.CalledProcessError, OSError):
        print "No SVN found, using default svn revision (-1) instead"
    else:
        for line in p.splitlines():
            l = line.split()
            if l[0] == 'Revision:':
                svn_revision = l[1]
                break
    return svn_revision

def get_git_hash():
    git_hash = '-1'
    try:
        git_hash = subprocess.check_output(['git', 'rev-parse HEAD'])
    except (subprocess.CalledProcessError, OSError):
        print "No GIT found, using default git revision (-1) instead"
    return git_hash

def load_help_files():
    try:
        subprocess.check_call('curl "'+HELP_PACKAGE_URL+'" -o"'+HELP_PACKAGE_FILENAME+'"', shell=True)
    except CalledProcessError as e:
        sys.stderr.write('Downloading the help package failed, aborting:\n'+str(e))
        sys.exit(e.returncode)
    try:
        subprocess.check_call(HELP_UNPACK_CMD, shell=True)
    except CalledProcessError as e:
        sys.stderr.write('Unpacking the help package failed, aborting:\n'+str(e))
        sys.exit(e.returncode)

def clean_help_files():
    subprocess.call('rm -rf help/', shell=True)
    subprocess.call('rm -rf '+HELP_PACKAGE_FILENAME, shell=True)
    
if sys.platform == 'darwin':

    ################ MAC SETUP    
    # Bootstrap
    import ez_setup
    ez_setup.use_setuptools()
    
    from setuptools import setup

    # Get help files
    load_help_files()

    # Rename exec_siren.py as Siren.py
    subprocess.call('cp '+APP+' Siren.py', shell=True)
    
    # A custom plist to associate with .siren -files
    Plist = dict(CFBundleDocumentTypes = [dict(CFBundleTypeExtensions=['siren'],
                                               CFBundleTypeName='Siren data file',
                                               CFBundleTypeRole = 'Viewer',
                                               CFBundleTypeIconFile = 'siren_file_icon.icns'),
                                        dict(CFBundleTypeName   = 'fi.helsinki.cs.siren.csv',
                                             CFBundleTypeRole   = 'Viewer',
                                             LSHandlerRank      = 'Alternate',
                                             LSItemContentTypes = ['public.comma-separated-values-text'])
                                               ],
                CFBundleShortVersionString = VERSION,
                CFBundleVersion = get_git_hash(),
                CFBundleName = SHORT_NAME,
                CFBundleIdentifier = "fi.helsinki.cs.siren",
                NSHumanReadableCopyright = COPYRIGHT
        )

    ICONS = ['icons/siren_icon.icns', 'icons/siren_file_icon.icns', 'icons/siren_icon32x32.png', 'icons/siren_icon.ico', 'icons/usiren_icon.ico']
    
    OPTIONS = {'argv_emulation': True,
    'iconfile': 'icons/siren_icon.icns',
    'packages': ST_PACKAGES,
    #'matplotlib_backends': MATPLOTLIB_BACKENDS,
    #'includes': ['ui_confdef.xml'], 
    #'includes': ['reremi'],
    'resources': ST_RESOURCES+ICONS+LICENSES,
    'site_packages': True,
    'includes': ['server_siren.py'],
    #'semi-standalone': True, # depends on local Python
    'plist': Plist,
    }
    # Set extra options
    extra_options.update(dict(
        app=['Siren.py'],
        #data_files=ST_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
        ))
    # Run setup
    setup(**extra_options)

    # Post setup
    # Copy files
    print "Copying files..."
    subprocess.call('cp LICENSE dist/', shell=True)
    subprocess.call('mkdir dist/third-party-licenses/', shell=True)
    for f in LICENSES:
        subprocess.call('cp '+f+'/LICENSE* dist/third-party-licenses/', shell=True)
    subprocess.call('cp licenses/README_mac.rtf dist/README.rtf', shell=True)
    subprocess.call('cp CHANGELOG dist/CHANGELOG', shell=True)
    subprocess.call('cp help/Siren-UserGuide.pdf dist/UserGuide.pdf', shell=True)
    subprocess.call('ln -s /Applications dist/', shell=True)
    subprocess.call('cp icons/siren_dmg_icon.icns dist/.VolumeIcon.icns', shell=True)
    # Set VolumeIcon's creator
    subprocess.call('SetFile -c icnC dist/.VolumeIcon.icns', shell=True)
    # Make read/write tmp disk image
    print "Creating initial disk image"
    subprocess.call('hdiutil create -srcfolder dist/ -volname '+SHORT_NAME+' -format UDRW -ov raw-'+SHORT_NAME+'.dmg', shell=True)
    # Attach the disk image
    subprocess.call('mkdir tmp', shell=True)
    subprocess.call('hdiutil attach raw-'+SHORT_NAME+'.dmg -mountpoint tmp', shell=True)
    # Set custom icon
    subprocess.call('SetFile -a C tmp', shell=True)
    # Detach
    print "Detaching"
    time.sleep(2)
    subprocess.call('hdiutil detach tmp', shell=True)
    subprocess.call('rm -rf tmp', shell=True)
    subprocess.call('rm -f '+SHORT_NAME+'.dmg', shell=True)
    # Convert
    print "Converting the disk image to the final one"
    time.sleep(1)
    subprocess.call('hdiutil convert raw-'+SHORT_NAME+'.dmg -format UDZO -o '+SHORT_NAME+'.dmg', shell=True)
    # Clean
    subprocess.call('rm -rf dist build', shell=True)
    subprocess.call('rm -f raw-'+SHORT_NAME+'.dmg', shell=True)

    # Clean help files
    print "Cleaning help files"
    clean_help_files()

    
elif sys.platform == 'win32':
    ################ WINDOWS SETUP
    ## Should this be 'win64'??
    from distutils.core import setup
    import py2exe
    import matplotlib


    WICONS = [('icons', glob.glob('icons\\*.ico') + glob.glob('icons\\*.png'))]
    WLICENSES = [('licenses', ['LICENSE']+glob.glob('licenses\\LICENSE*'))]
    #WCONFIGS = [('siren.interface', ['siren\\interface\\ui_confdef.xml']),
    #            ('siren.reremi', ['siren\\reremi\\miner_confdef.xml', 'siren\\reremi\\inout_confdef.xml'])]
    WCONFIGS = [('confs', ['siren\\interface\\ui_confdef.xml','siren\\reremi\\miner_confdef.xml', 'siren\\reremi\\inout_confdef.xml'])]
    WMORE = [('help', glob.glob('help\\*')),
             ('', ['LICENSE'])]

    OPTIONS = {
    'packages': ST_PACKAGES,
    'dll_excludes': ['MSVCP90.dll'],
    'includes' : ['scipy.sparse.csgraph._validation','scipy.special._ufuncs_cxx','matplotlib.backends.backend_tkagg'],
    'excludes': ['email', '_gtkagg', '_tkagg', '_ssl', 'nose', 'pygments', 'doctest'],
    }
    # Set extra options
    MPL = matplotlib.get_py2exe_datafiles()
    MTK = [('mpl_toolkits\\basemap\\data', glob.glob('C:\\Python27\\Lib\\site-packages\\mpl_toolkits\\basemap\\data\\*'))]
    extra_options.update(dict(
        windows=[{"script": APP, "icon_resources": [(1, "icons\\siren_icon.ico")]}],
        data_files= WICONS + WLICENSES + WCONFIGS + WMORE + MPL + MTK,
        options={'py2exe': OPTIONS})
        )
    # Run setup
    setup(**extra_options)


else:
    ################ LINUX SETUP
    from distutils.core import setup
    
    patterns = [('siren.reremi.grako', []),
                ('siren.reremi', ['siren/reremi/miner_confdef.xml', 'siren/reremi/inout_confdef.xml']),
                ('siren.interface', ['siren/interface/ui_confdef.xml']),
                ('siren.work', []),
                ('siren.views', []),
                ('', ['LICENSE', 'CHANGELOG']),
                ('help', ['help/*']),
                ('icons', ['icons/*.png', 'icons/*.ico']),
                ('licenses', ['licenses/LICENSE*'])]
                  
    
    DU_FILES = [f[:-3] for f in ST_FILES]
    PACKAGE_DATA = {'siren': []}
    DU_PACKAGES = ['siren']
    PREFF_DOT = ""
    PREFF_SLASH = ""

    for pack, pattern in patterns:
        DU_PACKAGES.append(PREFF_DOT+pack)
        PACKAGE_DATA[PREFF_DOT+pack] = []
        for p in pattern:
            PACKAGE_DATA[PREFF_DOT+pack].extend([f.split('/')[-1] for f in glob.glob(PREFF_SLASH+p) if os.path.isfile(f)])

    extra_options.update(dict(
        platforms="UNIX",
        description=DESCRIPTION,
        long_description=DESCRIPTION_LONG,
        package_data=PACKAGE_DATA,
        packages=DU_PACKAGES,
        py_modules=DU_FILES
        ))
    # Run setup
    setup(**extra_options)

