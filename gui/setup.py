"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app

Edits by Pauli
"""

from setuptools import setup

# A custom plist to associate with .siren -files
Plist = dict(CFBundleDocumentTypes = [dict(CFBundleTypeExtensions=['siren'],
                                           CFBundleTypeName='Siren data file',
                                           CFBundleTypeRole = 'Viewer',
                                           CFBundleTypeIconFiles = 'siren_files.icns'),
                                           ]
    )

APP = ['siren.py']
DATA_FILES = ['DataWrapper.py',
 'ICList.py',
 'classBestsDraft.py',
 'classConstraints.py',
 'classData.py',
 'classLog.py',
 'classQuery.py',
 'classRedescription.py',
 'classRedescriptionsDraft.py',
 'classSParts.py',
 'classSettings.py',
 'classSouvenirs.py',
 'greedyRedescriptions.py',
 'utilsStats.py',
 'utilsTools.py']
OPTIONS = {'argv_emulation': True,
 'iconfile': '/Users/pamietti/Documents/tyo/redescriptors gui/siren.icns',
 'packages': ['wx', 'mpl_toolkits'],
 'site_packages': True,
 'plist': Plist,
 }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)