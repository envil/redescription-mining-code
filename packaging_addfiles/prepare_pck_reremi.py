#!/usr/bin/env python

### usage: python prepare_pck_reremi.py win|src|clean

import sys, re, os.path, glob, subprocess

from common_details import reremi_variables

this_rep = os.path.dirname(os.path.abspath(__file__))

file_list = ['README.md']
if len(sys.argv) > 1:
    if sys.argv[1] == "clean":
        print("Cleaning up files...")
        for filename in file_list:
            if os.path.exists(this_rep+"/"+filename):
                print("- "+ this_rep+"/"+ filename)
                os.remove(this_rep+"/"+ filename)
        exit()
            
variables = {}
for entry, vals in reremi_variables.items():
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
######################### README
files_dest["README.md"]='''# __PROJECT_NAME__ --- __PROJECT_DESCRIPTION__

__PROJECT_DESCRIPTION_LINE__


### Installation

#### Dependencies
`python-reremi` requires several other Python utilities, including Numpy, Scipy, Scikit-learn.

__DEPENDENCIES_PIP_STR__

#### PIP
with pip, installation should be as easy as running 
`pip install python-reremi`

this should provide `exec_reremi` to run the command-line redescription mining algorithms

### More information
See __PROJECT_URL__

### License
__PROJECT_NAME__ is licensed under Apache License v2.0. See attached file "LICENSE".

(c) __PROJECT_AUTHORS__, __COPYRIGHT_YEAR_FROM__
'''


#print(files_dest.keys())
print("Generating files...")
for filename in file_list:
    print("+ "+this_rep+"/"+filename)
    with openMakeP(this_rep+"/"+filename, "w") as fp:
        fp.write(multiple_replace(variables, files_dest[filename]))
