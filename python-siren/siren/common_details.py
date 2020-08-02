import os, re, time

CHANGELOG_FILE = os.path.split(os.path.dirname(__file__))[0]+"/CHANGELOG"

def getVersion():
    version = None
    changes = []
    if os.path.isfile(CHANGELOG_FILE):
        ctime = time.strftime("%a, %d %b %Y %T", time.localtime(os.path.getmtime(CHANGELOG_FILE)))
        with open(CHANGELOG_FILE) as fp:        
            for line in fp:
                tmp = re.match("^v(?P<version>[0-9\.]*)$", line)
                if tmp is not None:
                    if version is None:
                        version = tmp.group("version")
                    else:
                        return version, changes, ctime
                elif version is not None and len(line.strip("[\n\*\- ]")) > 0:
                    changes.append(line.strip("[\n\*\- ]"))
                    
    return "", [], time.strftime("%a, %d %b %Y %T", time.localtime())

def getExtLinks(cv):

    return {'contact_email': ("%s"+cv["MAINTAINER_EMAIL"], None) , #cv["MAINTAINER_EMAIL"]),
            'project_url': (cv["PROJECT_URL"]+"%s", cv["PROJECT_NAME"]),
            'code_url': (cv["CODE_URL"]+"%s", cv["PACKAGE_NAME"]),
            'pdf_link': (cv["PDFS_URL"]+"%s", "pdf"),
            'data_link': (cv["DATA_URL"]+"%s", "prepared dataset"),
            'src_release': (cv["DOWNLOAD_URL"]+"?loc="+cv["CODE_LOC"]+"&file="+cv["PACKAGE_NAME"]+"-"+cv["SPEC_RELEASE"]+"%s",
                            cv["PROJECT_NAME"]+" (v"+cv["SPEC_RELEASE"]+") "),
            'deb_release': (cv["DOWNLOAD_URL"]+"?loc="+cv["CODE_LOC"]+"&file="+cv["PACKAGE_NAME"]+"_"+cv["SPEC_RELEASE"]+"_all%s",
                            cv["PROJECT_NAME"]+" (v"+cv["SPEC_RELEASE"]+") "),
            'mac_release': (cv["DOWNLOAD_URL"]+"?loc="+cv["CODE_LOC"]+"&file="+cv["PROJECT_NAME"]+"_OSX10.12_"+cv["VERSION_OLD"]+"%s",
                            cv["PROJECT_NAME"]+" (v"+cv["VERSION_OLD"]+") "),
            'mac_cap_release': (cv["DOWNLOAD_URL"]+"?loc="+cv["CODE_LOC"]+"&file="+cv["PROJECT_NAME"]+"_OSX10.11_"+cv["VERSION_OLD"]+"%s",
                            cv["PROJECT_NAME"]+" (v"+cv["VERSION_OLD"]+") "),
            'win_release': (cv["DOWNLOAD_URL"]+"?loc="+cv["CODE_LOC"]+"&file=install_"+cv["PROJECT_NAMELOW"]+"_"+cv["VERSION_OLD"]+"%s",
                            cv["PROJECT_NAME"]+" (v"+cv["VERSION_OLD"]+") ")
            }


version, changes, ctime = getVersion()

home_eg = "https://members.loria.fr/EGalbrun/"
home_siren = "http://siren.gforge.inria.fr/"

dependencies_clired = [("python-dateutil", "python3-dateutil", "(>= 2.8.1)"),
                ("Shapely", "python3-shapely", "(>= 1.7.0)"),
                ("numpy", "python3-numpy", "(>= 1.13.0)"),
                ("scipy", "python3-scipy", "(>= 0.19.0)"),
                ("scikit-learn", "python3-sklearn", "(>= 0.19.0)")]
dependencies_siren = [("matplotlib", "python3-matplotlib", "(>= 2.1.0)"),
                ("cartopy", "python3-cartopy", "(>= 0.14)")]

# "python3-wxgtk4.0 (>= 4.0.0)",
depclired_deb = []
depclired_pip = []
for pname, dname, v in dependencies_clired:
    depclired_pip.append("%s %s" % (pname, v))
    depclired_deb.append("%s %s" % (dname, v))
dependencies_deb = []
dependencies_pip = []
for pname, dname, v in dependencies_clired+dependencies_siren:
    dependencies_pip.append("%s %s" % (pname, v))
    dependencies_deb.append("%s %s" % (dname, v))

common_variables = {
    "PROJECT_NAME": "Siren",
    "PROJECT_NAMELOW": "siren",
    "PACKAGE_NAME": "python-siren",
    "MAIN_FILENAME": "exec_siren.py",
    "VERSION": version,
    "VERSION_OLD": "4.3.0",
    "DEPENDENCIES_PIP_LIST": dependencies_pip,
    "DEPENDENCIES_PIP_STR": "* " + "\n* ".join(dependencies_pip),
    "DEPENDENCIES_DEB_LIST": dependencies_deb,
    "DEPENDENCIES_DEB_STR": ", ".join(dependencies_deb),
    "LAST_CHANGES_LIST": changes,
    "LAST_CHANGES_STR": "    * " + "\n    * ".join(changes),
    "LAST_CHANGES_DATE": ctime + " +0200",
    "PROJECT_AUTHORS": "Esther Galbrun and Pauli Miettinen",
    "MAINTAINER_NAME": "Esther Galbrun",
    "MAINTAINER_LOGIN": "egalbrun",
    "MAINTAINER_EMAIL": "esther.galbrun@inria.fr",
    "PDFS_URL": home_eg+"resources/",
    "DATA_URL": home_siren+"/data/",
    "PROJECT_URL": home_siren,
    "CODE_URL": home_siren+"/code/",
    "CODE_MAC_URL": "http://www.cs.helsinki.fi/u/pamietti/data/siren/",
    "DOWNLOAD_URL": home_siren+"php/download.php",
    "CODE_LOC": "1",
    "CODE_MAC_LOC": "2",
    "PROJECT_DESCRIPTION": "Interactive Redescription Mining",
    "PROJECT_DESCRIPTION_LINE": "Siren is an interactive tool for visual and interactive redescription mining.",
    "PROJECT_DESCRIPTION_LONG": """This provides the Siren interface for interactive mining and visualization of redescriptions.""",
    "COPYRIGHT_YEAR_FROM": "2012",
    "COPYRIGHT_YEAR_TO": "2020",
    "SPEC_RELEASE": ""} ### set in conf.py of sphinx projects 


clired_variables = dict(common_variables)
clired_variables.update({
    "PROJECT_NAME": "Clired",
    "PROJECT_NAMELOW": "clired",
    "PACKAGE_NAME": "python-clired",
    "MAIN_FILENAME": "exec_clired.py",
    "DEPENDENCIES_PIP_LIST": depclired_pip,
    "DEPENDENCIES_PIP_STR": "* " + "\n* ".join(depclired_pip),
    "DEPENDENCIES_DEB_LIST": depclired_deb,
    "DEPENDENCIES_DEB_STR": ", ".join(depclired_deb),
    "PROJECT_DESCRIPTION": "Command-line Redescription Mining",
    "PROJECT_DESCRIPTION_LINE": "clired is a command-line tool for redescription mining.",
    "PROJECT_DESCRIPTION_LONG": """This provides the Clired command-line tool for redescription mining including, in particular, the greedy ReReMi algorithm and tree-based algorithms.""",})

#    "DOWNLOAD_URL": "http://www.loria.fr/~egalbrun/log/download.php",

# cv = common_variables
# version = '.'.join(cv["VERSION"].split('.')[:-1])
# # The full version, including alpha/beta/rc tags.
# release = cv["VERSION"]

# cv["SPEC_RELEASE"] = release
# print(getExtLinks(cv))
