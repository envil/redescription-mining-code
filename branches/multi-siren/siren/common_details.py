import os, re

CHANGELOG_FILE = os.path.split(os.path.dirname(__file__))[0]+"/CHANGELOG"

def getVersion():
    version = None
    changes = []
    if os.path.isfile(CHANGELOG_FILE):
        with open(CHANGELOG_FILE) as fp:        
            for line in fp:
                tmp = re.match("^v(?P<version>[0-9\.]*)$", line)
                if tmp is not None:
                    if version is None:
                        version = tmp.group("version")
                    else:
                        return version, changes
                elif version is not None and len(line.strip("[\n\*\- ]")) > 0:
                    changes.append(line.strip("[\n\*\- ]"))
                    
    return "0", []

version, changes = getVersion()

common_variables = {
    "PROJECT_NAME": "Siren",
    "PROJECT_NAMELOW": "siren",
    "PACKAGE_NAME": "python-siren",
    "MAIN_FILENAME": "exec_siren.py",
    "VERSION": version,
    "VERSION_MAC": "3.0.0",
    "VERSION_MAC_UNDERSC": "",
    "LAST_CHANGES_LIST": changes,
    "LAST_CHANGES_STR": "    * " + "\n    * ".join(changes),
    "LAST_CHANGES_DATE": "Tue, 15 Dec 2015 11:29:53 +0100",
    "PROJECT_AUTHORS": "Esther Galbrun and Pauli Miettinen",
    "MAINTAINER_NAME": "Esther Galbrun",
    "MAINTAINER_LOGIN": "galbrun",
    "MAINTAINER_EMAIL": "galbrun@cs.helsinki.fi",
    "PROJECT_URL": "http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren/",
    "CODE_URL": "http://www.cs.helsinki.fi/u/galbrun/redescriptors/code/siren/",
    "CODE_MAC_URL": "http://www.cs.helsinki.fi/u/pamietti/data/siren/",
    "PROJECT_DESCRIPTION": "Interactive Redescription Mining",
    "PROJECT_DESCRIPTION_LINE": "Siren is an interactive tool for visual and interactive redescription mining.",
    "PROJECT_DESCRIPTION_LONG": """This provides the ReReMi redescription mining algorithm and the Siren interface for interactive mining and visualization of redescriptions.""",
    "COPYRIGHT_YEAR_FROM": "2012",
    "COPYRIGHT_YEAR_TO": "2015"}
