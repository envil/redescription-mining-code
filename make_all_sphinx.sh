#!/bin/bash

##### THERE ARE A NUMBER OF BAD LINK WARNINGS IN THE COMPILATION, DUE TO SHARED FOLDERS
# ./make_all_sphinx.sh ./python-siren ./sphinx pa

SRC_REP=${1}
SPH_REP=${2}
PASS=${3}
YAH=$(pwd) # YOU ARE HERE

#PACK_REP=${YAH}/${3}

PACK_REP=${YAH}/sphinx_current_$(date "+%Y%m%d%H%M%S")
SPHINX_REP=${PACK_REP}"/sphinx"
OUT_REP=${PACK_REP}"/out"

mkdir -p ${PACK_REP}
mkdir ${OUT_REP}
cp -r ${SPH_REP} ${SPHINX_REP}

### COPY FILES FROM THE SOURCE CODE TO DOC
# svn export --force https://vcs.hiit.fi/svn/redescriptors/sandbox/siren/CHANGELOG  _static/
# svn export --force https://vcs.hiit.fi/svn/redescriptors/sandbox/siren/ui_confdef.xml  _static/
# svn export --force https://vcs.hiit.fi/svn/redescriptors/sandbox/siren/reremi/inout_confdef.xml  _static/
# svn export --force https://vcs.hiit.fi/svn/redescriptors/sandbox/siren/reremi/miner_confdef.xml  _static/
cp ${SRC_REP}/siren/interface/*confdef.xml ${SRC_REP}/siren/reremi/*confdef.xml ${SPHINX_REP}/_static/
sed -i 's:\./reremi/confdef:/confdef:' ${SPHINX_REP}/_static/*confdef.xml

cp ${SRC_REP}/CHANGELOG ${SPHINX_REP}/_static/

mkdir ${SPHINX_REP}/siren
cp ${SRC_REP}/CHANGELOG ${SPHINX_REP}/
cp ${SRC_REP}/siren/common_details.py ${SPHINX_REP}/siren/

### UPDATE THE IMPORT PATH FOR COMMON VARIABLES IN SPHINX CONF FILES
sed -i -e s:__SIREN_PYTHON_PATH__:${SPHINX_REP}/siren:g ${SPHINX_REP}/*/conf.py

cd ${SPHINX_REP}/siren-help/
rm -rf _build
make html
make latexpdf
cp -r _build/html ${OUT_REP}/help
cp _build/latex/Siren.pdf ${OUT_REP}/help/Siren-UserGuide.pdf

cd ${SPHINX_REP}/siren-web/
rm -rf _build
make html
cp -r _build/html ${OUT_REP}/main

cd ${SPHINX_REP}/siren-sigmod/
rm -rf _build
make singlehtml
make latexpdf
cp -r _build/singlehtml ${OUT_REP}/sigmod
cp _build/latex/Siren.pdf ${OUT_REP}/sigmod/Siren-SIGMOD.pdf

cd ${SPHINX_REP}/siren-icdm/
rm -rf _build
make singlehtml
make latexpdf
cp -r _build/singlehtml ${OUT_REP}/icdm
cp _build/latex/Siren.pdf ${OUT_REP}/icdm/Siren-ICDM.pdf


cd ${OUT_REP}
sed -i 's:\([^/]\)_static/:\1../_static/:g' */*.html
sed -i 's:\([^/]\)_images/:\1../_images/:g' */*.html
mv help/_static ./
mv help/_images ./
mv main/_static/* ./_static/
mv main/_images/* ./_images/
mv sigmod/_static/* ./_static/
mv sigmod/_images/* ./_images/
mv icdm/_static/* ./_static/
mv icdm/_images/* ./_images/
rm */objects.inv
rmdir main/_images main/_static sigmod/_images sigmod/_static icdm/_images icdm/_static

cd ${PACK_REP}
tar -cvzf sphinx-siren-out.tar.gz out
