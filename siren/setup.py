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
import subprocess
import pdb

# Common info
APP = 'siren.py'
NAME="python-siren"
SHORT_NAME="Siren"
VERSION = '2.0.0'
DESCRIPTION="Interactive Geospatial Redescription Mining"
AUTHOR="Esther Galbrun and Pauli Miettinen"
AUTHOR_EMAIL="galbrun@cs.helsinki.fi"
URL="http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren/"
LICENSE="Apache_2.0"

########## SETUPTOOLS FILES
ST_RESOURCES=['help', 'commons', 'ABOUT', 'LICENSE',
              'ui_confdef.xml', 'reremi/miner_confdef.xml', 'reremi/inout_confdef.xml']
# N.B. You must include the icon files later
ST_FILES = ['DataWrapper.py', 'classGridTable.py', 'classMapView.py',
            'classPreferencesDialog.py', 'classSiren.py', 'miscDialogs.py']
ST_MORE_FILES=['ez_setup.py']
#ST_PACKAGES = ['wx', 'mpl_toolkits.basemap', 'reremi']
ST_PACKAGES = ['wx', 'mpl_toolkits', 'reremi']
MATPLOTLIB_BACKENDS = ['wxagg']

########## DISTUTILS FILES
DU_RESOURCES_SIREN=['icons/*', 'help/*', 'ABOUT', 'LICENSE',
              'ui_confdef.xml']
DU_RESOURCES_REREMI=['miner_confdef.xml', 'inout_confdef.xml']
DU_FILES = ['siren', 'DataWrapper', 'classGridTable', 'classMapView',
            'classPreferencesDialog', 'classSiren','miscDialogs']
DU_PACKAGES = ['reremi']

extra_options = dict(
    name=NAME,
    version=VERSION,
    description=(DESCRIPTION),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    )

# Get SVN revision -- works w/o awk/grep/sed
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


if sys.platform == 'darwin':
    ################ MAC SETUP
    # Bootstrap
    import ez_setup
    ez_setup.use_setuptools()
    
    from setuptools import setup

    # A custom plist to associate with .siren -files
    Plist = dict(CFBundleDocumentTypes = [dict(CFBundleTypeExtensions=['siren'],
                                               CFBundleTypeName='Siren data file',
                                               CFBundleTypeRole = 'Viewer',
                                               CFBundleTypeIconFile = 'siren_file_icon.icns'),
                                               ],
                CFBundleShortVersionString = VERSION,
                CFBundleVersion = svn_revision,
                CFBundleName = SHORT_NAME
        )

    ICONS = ['icons/siren_icon.icns', 'icons/siren_file_icon.icns', 'icons/siren_icon32x32.png', 'icons/siren_icon.ico', 'icons/usiren_icon.ico']
    LICENSES = ['LICENSE_basemap', 'LICENSE_matplotlib', 'LICENSE_python', 'LICENSE_wx']
    
    OPTIONS = {'argv_emulation': True,
    'iconfile': 'icons/siren_icon.icns',
    'packages': ST_PACKAGES,
    'matplotlib_backends': MATPLOTLIB_BACKENDS,
    #'includes': ['ui_confdef.xml'], 
    #'includes': ['reremi'],
    'resources': ST_RESOURCES+ICONS+LICENSES,
    'site_packages': True,
    #'semi-standalone': True, # depends on local Python
    'plist': Plist,
    }
    # Set extra options
    extra_options.update(dict(
        app=[APP],
        data_files=ST_FILES,
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
        subprocess.call('cp '+f+' dist/third-party-licenses/', shell=True)
    subprocess.call('cp README_mac.rtf dist/README.rtf', shell=True)
    subprocess.call('cp CHANGELOG dist/CHANGELOG', shell=True)
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
    subprocess.call('hdiutil detach tmp', shell=True)
    subprocess.call('rm -rf tmp', shell=True)
    subprocess.call('rm -f '+SHORT_NAME+'.dmg', shell=True)
    # Convert
    print "Converting the disk image to the final one"
    subprocess.call('hdiutil convert raw-'+SHORT_NAME+'.dmg -format UDZO -o '+SHORT_NAME+'.dmg', shell=True)
    # Clean
    subprocess.call('rm -rf dist build', shell=True)
    subprocess.call('rm -f raw-'+SHORT_NAME+'.dmg', shell=True)

    
elif sys.platform == 'win32':
    ################ WINDOWS SETUP
    ## Should this be 'win64'??
    from distutils.core import setup
    import py2exe
    import matplotlib, glob
    ICONS = [('icons', ['icons\\siren_icon.icns', 'icons\\siren_file_icon.icns', 'icons\\siren_icon32x32.png', 'icons\\siren_icon.ico', 'icons\\usiren_icon.ico'])]
    LICENSES = [('', ['ABOUT', 'LICENSE', 'LICENSE_basemap', 'LICENSE_matplotlib', 'LICENSE_python', 'LICENSE_wx'])]
    CONFIGS = [('', ['ui_confdef.xml']), ('reremi', ['reremi\\miner_confdef.xml', 'reremi\\inout_confdef.xml'])]
    MORE = [('help', glob.glob('help\\*')), ('commons', glob.glob('commons\\*'))]

    OPTIONS = {
    'packages': ST_PACKAGES,
    'dll_excludes': ['MSVCP90.dll'],
    'excludes': ['email', '_gtkagg', '_tkagg', '_ssl', 'nose', 'pygments', 'doctest'],
    }
    # Set extra options
    MPL = matplotlib.get_py2exe_datafiles()
    MTK = [('mpl_toolkits\\basemap\\data', glob.glob('C:\\Python27\\Lib\\site-packages\\mpl_toolkits\\basemap\\data\\*.*'))]
    extra_options.update(dict(
        windows=[APP],
        data_files=ICONS + LICENSES + CONFIGS + MPL + MTK,
        options={'py2exe': OPTIONS}))
    # Run setup
    setup(**extra_options)


else:
    ################ LINUX SETUP
    from distutils.core import setup

    extra_options.update(dict(
        packages=DU_PACKAGES,
        py_modules=DU_FILES,
        package_data={'': DU_RESOURCES_SIREN,
                      'reremi': DU_RESOURCES_REREMI},
        ))
    # Run setup
    setup(**extra_options)

