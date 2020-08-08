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
            'data_url': (cv["DATA_URL"]+"%s", "prepared dataset"),
            'gitlab_url': (cv["GITLAB_URL"]+"%s", "GitLab Inria"),
            'pdf_url': (cv["PDFS_URL"]+"%s", "pdf"),
            }


version, changes, ctime = getVersion()

#### also update help url in clired preference manager
home_eg = "https://members.loria.fr/EGalbrun/"
web_siren = home_eg+"siren/"
gitlab_siren = "https://gitlab.inria.fr/egalbrun/siren"

dependencies_clired = [("python-dateutil", "-python3-dateutil", "(>= 2.8.1)"),
                ("shapely", "-python3-shapely", "(>= 1.7.0)"),
                ("numpy", "python3-numpy", "(>= 1.13.0)"),
                ("scipy", "python3-scipy", "(>= 0.19.0)"),
                ("scikit-learn", "python3-sklearn", "(>= 0.19.0)")]
dependencies_siren = [("wxPython", "-python3-wxgtk4.0","(>= 4.0.0)"),
                ("matplotlib", "python3-matplotlib", "(>= 2.1.0)"),
                ("cartopy", "python3-cartopy", "(>= 0.14)")]

# "python-dateutil >= 2.8.1", "shapely >= 1.7.0" "numpy >= 1.13.0" "scipy >= 0.19.0" "scikit-learn >= 0.19.0"
# "wxPython >= 4.1.0" "matplotlib >= 2.1.0" "cartopy >= 0.14"

depclired_deb = []
depclired_pip = []
for pname, dname, v in dependencies_clired:
    depclired_pip.append("%s %s" % (pname, v))
    if dname[0] != "-":
        depclired_deb.append("%s %s" % (dname, v))
dependencies_deb = []
dependencies_pip = []
for pname, dname, v in dependencies_clired+dependencies_siren:
    dependencies_pip.append("%s %s" % (pname, v))
    if dname[0] != "-":
        dependencies_deb.append("%s %s" % (dname, v))

common_variables = {
    "PROJECT_NAME": "Siren",
    "PROJECT_NAMELOW": "siren",
    "PACKAGE_NAME": "python-siren",
    "MAIN_FILENAME": "exec_siren.py",
    "VERSION": version,
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
    "PROJECT_URL": web_siren,
    "DATA_URL": web_siren+"data/",
    "CODE_URL": web_siren+"code/",
    "GITLAB_URL": gitlab_siren,
    "PDFS_URL": home_eg+"resources/",
    "PROJECT_DESCRIPTION": "Interactive Redescription Mining",
    "PROJECT_DESCRIPTION_LINE": "Siren is an interactive tool for visual and interactive redescription mining.",
    "PROJECT_DESCRIPTION_LONG": """This provides the Siren interface for interactive mining and visualization of redescriptions. Once installed, Siren can be launched by calling the command 'exec_siren'.""",
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
    "PROJECT_DESCRIPTION_LONG": """This provides the Clired command-line tool for redescription mining including, in particular, the greedy ReReMi algorithm and tree-based algorithms. Once installed, Clired can be run by calling the command 'exec_clired'.""",})
