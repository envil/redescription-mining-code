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

# #### MAKE HELP
cd ${SPHINX_REP}/siren-help/
rm -rf _build
make html
make latexpdf
cp -r _build/html ${OUT_REP}/help
cp _build/latex/Siren.pdf ${OUT_REP}/help/Siren-UserGuide.pdf

# #### MAKE MAIN
cd ${SPHINX_REP}/siren-web/
rm -rf _build
make html
cp -r _build/html ${OUT_REP}/main

#### MAKE CONF SPECIFIC
for conf in "sigmod" "icdm"; do
    cd ${SPHINX_REP}/siren-${conf}/
    rm -rf _build
    make singlehtml
    make latexpdf
    cp -r _build/singlehtml ${OUT_REP}/${conf}
    cp _build/latex/Siren.pdf ${OUT_REP}/${conf}/Siren-$(echo ${conf} | tr 'a-z' 'A-Z' ).pdf
done

cd ${OUT_REP}
sed -i 's:\([^/]\)_static/:\1../_static/:g' */*.html
sed -i 's:\([^/]\)_images/:\1../_images/:g' */*.html
mkdir ./_static/ ./_images/
for fold in "help" "main" "sigmod" "icdm"; do
    mv ${fold}/_static/* ./_static/
    mv ${fold}/_images/* ./_images/
    rmdir ${fold}/_static ${fold}/_images
done
rm */objects.inv

# cd ${PACK_REP}
# tar -cvzf sphinx-siren-out.tar.gz out
