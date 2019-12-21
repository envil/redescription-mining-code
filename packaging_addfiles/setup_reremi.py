import sys, subprocess
import setuptools

import pdb

from common_details import reremi_variables

# Common info
APP = reremi_variables["MAIN_FILENAME"]
NAME = reremi_variables["PACKAGE_NAME"]
SHORT_NAME = reremi_variables["PROJECT_NAME"]
VERSION = reremi_variables["VERSION"]
DESCRIPTION = reremi_variables["PROJECT_DESCRIPTION"]
DESCRIPTION_LONG = reremi_variables["PROJECT_DESCRIPTION_LONG"]
DEPENDENCIES = reremi_variables["DEPENDENCIES_PIP_LIST"]
AUTHOR = reremi_variables["PROJECT_AUTHORS"]
AUTHOR_EMAIL = reremi_variables["MAINTAINER_EMAIL"]
URL = reremi_variables["PROJECT_URL"]
LICENSE="Apache_2.0"
COPYRIGHT=u'\u00A9 '+reremi_variables["COPYRIGHT_YEAR_FROM"]+'-' \
               +reremi_variables["COPYRIGHT_YEAR_FROM"]+' ' \
               +reremi_variables["PROJECT_AUTHORS"]
DU_FILES = [APP[:-3]]
# setuptools.find_packages()
DU_PACKAGES = ['reremi', 'reremi.grako']
PACKAGE_DATA = {'reremi': ['miner_confdef.xml', 'inout_confdef.xml', '*defs*.txt', 'LICENSE*']}

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
            'exec_reremi = reremi.mainReReMi:main',
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
