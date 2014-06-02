For windows packaging:
=======================
_init_.py and pyproj.py belong to the site-packages\mpl_toolkits\basemap folder, edited so that they can find their data
# Switch to non unicode (classQuery.py) and exclude sklearn (classProj.py, setup.py)
run python setup.py py2exe in the siren folder, then compile the setup.nsi script using NSIS (Nullsoft Scriptable Install System)

COPY the siren folder into the packaging folder, remove useless stuff like this file...
Update the setup.py also in the packaging folder

For Linux:
===========
run package_deb.sh

* tar: run python setup.py sdist from the siren folder
* deb: run make builddeb from the packaging folder

Remember to edit setup.py and Manifest.in to include new files and update version number

scp python-siren-2.0.3.tar.gz  python-siren_2.0.3_all.deb  install_siren.exe CHANGELOG melkki.cs.helsinki.fi:~/public_html/redescriptors/code/siren/
