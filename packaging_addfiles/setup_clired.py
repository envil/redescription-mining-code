import sys
import subprocess
import setuptools

import pdb

from blocks.common_details import clired_variables

# Common info
APP = clired_variables["MAIN_FILENAME"]
NAME = clired_variables["PACKAGE_NAME"]
SHORT_NAME = clired_variables["PROJECT_NAME"]
VERSION = clired_variables["VERSION"]
DESCRIPTION = clired_variables["PROJECT_DESCRIPTION"]
DESCRIPTION_LONG = clired_variables["PROJECT_DESCRIPTION_LONG"]
DEPENDENCIES = clired_variables["DEPENDENCIES_PIP_LIST"]
AUTHOR = clired_variables["PROJECT_AUTHORS"]
AUTHOR_EMAIL = clired_variables["MAINTAINER_EMAIL"]
URL = clired_variables["PROJECT_URL"]
LICENSE = "Apache_2.0"
COPYRIGHT = u'\u00A9 '+clired_variables["COPYRIGHT_YEAR_FROM"]+'-' \
    + clired_variables["COPYRIGHT_YEAR_FROM"]+' ' \
    + clired_variables["PROJECT_AUTHORS"]
DU_FILES = ["exec_server", "exec_client"]
# setuptools.find_packages()
DU_PACKAGES = ['blocks', 'blocks.mine', 'blocks.mine.grako', 'blocks.work']
PACKAGE_DATA = {'blocks.mine': ['*_confdef.xml', '*defs*.txt'],
                'blocks.work': ['network_confdef.xml']}


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
            'exec_clired = blocks.mine.exec_clired:main',
            'exec_server = exec_server:main',
            'exec_client = exec_client:main',
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
