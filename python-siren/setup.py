import sys, subprocess
import setuptools

import pdb

from siren.common_details import common_variables

# Common info
APP = common_variables["MAIN_FILENAME"]
NAME = common_variables["PACKAGE_NAME"]
SHORT_NAME = common_variables["PROJECT_NAME"]
VERSION = common_variables["VERSION"]
DESCRIPTION = common_variables["PROJECT_DESCRIPTION"]
DESCRIPTION_LONG = common_variables["PROJECT_DESCRIPTION_LONG"]
DEPENDENCIES = common_variables["DEPENDENCIES_PIP_LIST"]
AUTHOR = common_variables["PROJECT_AUTHORS"]
AUTHOR_EMAIL = common_variables["MAINTAINER_EMAIL"]
URL = common_variables["PROJECT_URL"]
LICENSE="Apache_2.0"
COPYRIGHT=u'\u00A9 '+common_variables["COPYRIGHT_YEAR_FROM"]+'-' \
               +common_variables["COPYRIGHT_YEAR_FROM"]+' ' \
               +common_variables["PROJECT_AUTHORS"]
DU_FILES = [APP[:-3], "server_siren", "exec_clired"]
# setuptools.find_packages()
DU_PACKAGES = ['siren', 'siren.clired', 'siren.interface', 'siren.work', 'siren.views', 'siren.clired.grako']
PACKAGE_DATA = {'siren.clired': ['miner_confdef.xml', 'inout_confdef.xml', '*defs*.txt'],
                'siren.views': ['views_confdef.xml'],
                'siren.interface': ['ui_confdef.xml'],
                'siren': ['data/icons/*.png', 'data/icons/*.ico', 'data/help/*', 'data/licenses/LICENSE*']}

def get_git_hash():
    git_hash = '-1'
    try:
        git_hash = subprocess.check_output('git rev-parse HEAD', shell=True)
    except (subprocess.CalledProcessError, OSError):
        print("No GIT found, using default git revision (-1) instead")
    return git_hash.strip()

setuptools.setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=DESCRIPTION_LONG,
    long_description_content_type="text/markdown",
    license=LICENSE,
    url=URL,
    packages=DU_PACKAGES,
    package_data=PACKAGE_DATA,
    py_modules=DU_FILES,
    install_requires=DEPENDENCIES,
    # other arguments here...
    entry_points={
        'console_scripts': [
            'server_siren = server_siren:main',
            'exec_clired = siren.clired.exec_clired:main',
        ],
        'gui_scripts': [
            'exec_siren = exec_siren:main',
        ],        
    },
    python_requires='>=3',
    classifiers=[
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
    "Topic :: Scientific/Engineering",
    ],
)
