#!/bin/bash

PASS=${2}
SRC_REP=${1}
YAH=$(pwd) # YOU ARE HERE

PACK_REP=${YAH}/packaging_current_$(date "+%Y%m%d%H%M%S")
# PACK_REP=${YAH}/packaging_current_0
mkdir $PACK_REP
ROOT_REP=${PACK_REP}"/python-siren"
SPHINX_REP=${ROOT_REP}"/sphinx"
HELP_SRC_REP=${SPHINX_REP}"/siren-help/_build/html"
HELP_TRG_REP=${ROOT_REP}"/help"
GUIDE_PDF_SRC=${SPHINX_REP}"/siren-help/_build/latex/Siren.pdf"
GUIDE_PDF_TRG=${HELP_TRG_REP}"/Siren-UserGuide.pdf"

### checkout the files for making the .deb package
# svn co --password ${PASS} https://vcs.hiit.fi/svn/redescriptors/sandbox/pck/deb ${ROOT_REP}

### checkout the code itself
# svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/siren ${SIREN_REP}
cp ${SRC_REP} ${ROOT_REP}

### checkout the sources for the help pages
mkdir ${SPHINX_REP}
svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/siren-help ${SPHINX_REP}/siren-help
svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_static ${SPHINX_REP}/_static
svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_figs ${SPHINX_REP}/_figs
svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_templates ${SPHINX_REP}/_templates

# ### Update version !!DOES NOT WORK!!
# sed -i "s/version = '[0-9.a-z]*'/version = '${VERSION}'/" ${SPHINX_REP}/siren-help/*.py

### COPY FILES FROM THE SOURCE CODE TO DOC
cp ${ROOT_REP}/siren/interface/*confdef.xml ${ROOT_REP}/siren/reremi/*confdef.xml ${SPHINX_REP}/_static/
cp ${ROOT_REP}/siren/reremi/redquery.ebnf ${SPHINX_REP}/_static/redquery_grammar.txt
cp ${ROOT_REP}/siren/common_details.py ${SPHINX_REP}/

### prepare the help pages
cd ${SPHINX_REP}"/siren-help/"
rm -rf _build
make html
make latexpdf

rm -rf ${HELP_TRG_REP}
cp -R ${HELP_SRC_REP} ${HELP_TRG_REP}
cp ${GUIDE_PDF_SRC} ${GUIDE_PDF_TRG}
cd ${HELP_TRG_REP}
rm .buildinfo objects.inv
sed -i -e 's:\([^/]\)../_static/:\1:g' -e 's:\([^/]\)_static/:\1:g' -e 's:\([^/]\)_images/:\1:g' -e 's!../main/!http://www.cs.helsinki.fi/u/galbrun/redescriptors/siren/!g' *.html
mv _static/* .
mv _images/* .
rm -rf _static _images
rm -rf ${SPHINX_REP}
rm slides_*.html drawing_*.svg slidy*s


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
