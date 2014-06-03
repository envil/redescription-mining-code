#!/bin/bash

YAH=$(pwd) # YOU ARE HERE

PACK_REP=${YAH}/packaging_current_$(date "+%Y%m%d%H%M%S")
# PACK_REP=${YAH}/packaging_current_0
mkdir $PACK_REP
ROOT_REP=${PACK_REP}"/python-siren"
SIREN_REP=${ROOT_REP}"/siren"
SPHINX_REP=${ROOT_REP}"/sphinx"
HELP_SRC_REP=${SPHINX_REP}"/siren-help/_build/html"
HELP_TRG_REP=${SIREN_REP}"/help"
GUIDE_PDF_SRC=${SPHINX_REP}"/siren-help/_build/latex/Siren.pdf"
GUIDE_PDF_TRG=${HELP_TRG_REP}"/Siren-UserGuide.pdf"

### checkout the files for making the .deb package
svn co  https://vcs.hiit.fi/svn/redescriptors/sandbox/pck/deb ${ROOT_REP}

### checkout the code itself
svn co  https://vcs.hiit.fi/svn/redescriptors/sandbox/siren ${SIREN_REP}

### checkout the sources for the help pages
mkdir ${SPHINX_REP}
svn co  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/siren-help ${SPHINX_REP}/siren-help
svn co  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_static ${SPHINX_REP}/_static
svn co  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_templates ${SPHINX_REP}/_templates

# ### Update version (almost) everywhere !!DOES NOT WORK!!
# # VERSION=$(grep "VERSION = '[0-9.a-z]*'" ${SIREN_REP}/setup.py | sed "s/VERSION *= *.\([0-9.a-z]*\)'/\1/" )
# # sed -i "s/version = '[0-9.a-z]*'/version = '${VERSION}'/" ${SIREN_REP}/classSiren.py
# # #### sed -n "s/M_VERSION \".*\"/M_VERSION \"${VERSION}\"/p" ${SIREN_REP}/setup.nsi
# # sed -i "s/version = '[0-9.a-z]*'/version = '${VERSION}'/" ${ROOT_REP}/Makefile
# # VERSION=${VERSION%.*}
# # sed -i "s/version = '[0-9.a-z]*'/version = '${VERSION}'/" ${SPHINX_REP}/siren-help/*.py

### prepare the help pages
cd ${SPHINX_REP}"/siren-help/"
rm -rf _build
make html
make latexpdf

rm -rf ${HELP_TRG_REP}
mv ${HELP_SRC_REP} ${HELP_TRG_REP}
cp ${GUIDE_PDF_SRC} ${GUIDE_PDF_TRG}
cd ${HELP_TRG_REP}
rm .buildinfo objects.inv
for file in $( grep "_static" *.html | sed -e 's/^.*src="\(_static[^"]*\)".*$/\1/' -e 's/^.*href="\(_static[^"]*\)".*$/\1/' | sort | uniq ); do
	mv $file "${file##[a-z_]*/}"
done
mv _static/*.css .
sed -i -e 's!../main/!http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren/!g' -e 's!_static/!!g' -e 's!screenshots/!!g' *.html
rm -rf _static
rm -rf ${SPHINX_REP}

# ### add the __init__.py files
echo "" > ${SIREN_REP}/icons/__init__.py
echo "" > ${HELP_TRG_REP}/__init__.py
# echo "" > ${HELP_TRG_REP}/_static/__init__.py
# echo "" > ${HELP_TRG_REP}/_static/screenshots/__init__.py

### Final files preparations
cd ${ROOT_REP}
sed 's: : siren/:' ${SIREN_REP}/MANIFEST.in > MANIFEST.in 
echo "include MANIFEST.in"  >> MANIFEST.in 
sed 's/INSIDE_SETUP = True/INSIDE_SETUP = False/' ${SIREN_REP}/setup.py > setup.py

# ### ... and make the package
make builddeb
