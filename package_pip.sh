#!/bin/bash

# ./package_deb.sh ./python-siren ./sphinx pa

# SRC_REP=${1}
# SPH_REP=${2}
## PASS=${3}

SRC_REP="./python-siren"
SPH_REP="./sphinx"
YAH=$(pwd) # YOU ARE HERE

#PACK_REP=${YAH}/${3}

PACK_REP=${YAH}/packaging_pip_$(date "+%Y%m%d%H%M%S")
ROOT_REP=${PACK_REP}"/python-siren"
SPHINX_REP=${PACK_REP}"/sphinx"
HELP_SRC_REP=${SPHINX_REP}"/siren-help/_build/html"
HELP_TRG_REP=${ROOT_REP}"/siren/data/help"
# GUIDE_PDF_SRC=${SPHINX_REP}"/siren-help/_build/latex/Siren.pdf"
# GUIDE_PDF_TRG=${HELP_TRG_REP}"/Siren-UserGuide.pdf"

# ### checkout the code itself
mkdir $PACK_REP
# # svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/siren ${SIREN_REP}
cp -r ${SRC_REP} ${ROOT_REP}
python ${ROOT_REP}/prepare_pck_files.py src

# ### checkout the sources for the help pages
mkdir ${SPHINX_REP}
# # svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/siren-help ${SPHINX_REP}/siren-help
# # svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_static ${SPHINX_REP}/_static
# # svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_figs ${SPHINX_REP}/_figs
# # svn co --password ${PASS}  https://vcs.hiit.fi/svn/redescriptors/sandbox/sphinx/_templates ${SPHINX_REP}/_templates
cp -r ${SPH_REP}/siren-help ${SPHINX_REP}/siren-help
cp -r ${SPH_REP}/_static ${SPHINX_REP}/_static
cp -r ${SPH_REP}/_figs ${SPHINX_REP}/_figs
cp -r ${SPH_REP}/_templates ${SPHINX_REP}/_templates

### COPY FILES FROM THE SOURCE CODE TO DOC
cp ${ROOT_REP}/siren/*/*confdef.xml ${SPHINX_REP}/_static/
sed -i 's:\./reremi/confdef:/confdef:' ${SPHINX_REP}/_static/*confdef.xml

cp ${ROOT_REP}/CHANGELOG ${SPHINX_REP}/_static/

### UPDATE THE IMPORT PATH FOR COMMON VARIABLES IN SPHINX CONF FILES
sed -i -e s:__SIREN_PYTHON_PATH__:${ROOT_REP}/siren:g ${SPHINX_REP}/*/conf.py

# ################################
# ### prepare the help pages
cd ${SPHINX_REP}/siren-help/
rm -rf _build
make html
#make latexpdf
#exit

rm -rf ${HELP_TRG_REP}
cp -R ${HELP_SRC_REP} ${HELP_TRG_REP}
## cp ${GUIDE_PDF_SRC} ${GUIDE_PDF_TRG}
cd ${HELP_TRG_REP}
mv $( cat *.html | sed -n -e 's:^.*href="\([^"]*_static/[^"]*\)".*$:\1:p' -e 's:^.*href="\([^"]*_images/[^"]*\)".*$:\1:p' -e 's:^.*src="\([^"]*_static/[^"]*\)".*$:\1:p' -e 's:^.*src="\([^"]*_images/[^"]*\)".*$:\1:p' | sed 's:\.\./::' | sort | uniq ) ./
mv _static/*.css ./
mv _static/confdef.xsl _static/*_confdef.xml ./
#sed -i '/Main Siren webpage/d' *.html
sed -i 's!../main/!http://siren.gforge.inria.fr/!g' *.html
sed -i '/As a PDF/d' *.html
sed -i 's:\([^/]\)_static/:\1:g' *.html
sed -i 's:\([^/]\)_images/:\1:g' *.html
sed -i 's:\.\./_static/::g' *.html
sed -i 's:\.\./_images/::g' *.html
rm -rf _static _images
rm .buildinfo objects.inv slidy*s
################################

rm -rf ${SPHINX_REP}

### ... and make the package
cd ${ROOT_REP}
python setup.py sdist bdist_wheel
# python -m twine upload dist/*
