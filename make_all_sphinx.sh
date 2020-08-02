#!/bin/bash

##### THERE ARE A NUMBER OF BAD LINK WARNINGS IN THE COMPILATION, DUE TO SHARED FOLDERS
# ./make_all_sphinx.sh ./python-siren ./sphinx pa
#### To send
## rsync -rvv -e ssh main/ egalbrun@scm.gforge.inria.fr:/home/groups/siren/htdocs/main/

# SRC_REP=${1}
# SPH_REP=${2}
JUST_HELP=${1}

SRC_REP="./python-siren"
SPH_REP="./sphinx"
# JUST_HELP=1

YAH=$(pwd) # YOU ARE HERE

#PACK_REP=${YAH}/${3}

PACK_REP=${YAH}/packaging_sphinx_$(date "+%Y%m%d%H%M%S")
# PACK_REP=${YAH}/packaging_sphinx_current
rm -rf $PACK_REP
SPHINX_REP=${PACK_REP}"/sphinx"
OUT_REP=${PACK_REP}"/out"

mkdir -p ${PACK_REP}
mkdir ${OUT_REP}
cp -r ${SPH_REP} ${SPHINX_REP}

### COPY FILES FROM THE SOURCE CODE TO DOC
cp ${SRC_REP}/siren/*/*confdef.xml ${SPHINX_REP}/_static/
sed -i 's:\./clired/confdef:/confdef:' ${SPHINX_REP}/_static/*confdef.xml

cp ${SRC_REP}/CHANGELOG ${SPHINX_REP}/_static/

mkdir ${SPHINX_REP}/siren
cp ${SRC_REP}/CHANGELOG ${SPHINX_REP}/
cp ${SRC_REP}/siren/common_details.py ${SPHINX_REP}/siren/

### UPDATE THE IMPORT PATH FOR COMMON VARIABLES IN SPHINX CONF FILES
sed -i -e s:__SIREN_PYTHON_PATH__:${SPHINX_REP}/siren:g ${SPHINX_REP}/*/conf.py


if [ $JUST_HELP -gt 0 ]; then
    # #### MAKE HELP ONLY
    cd ${SPHINX_REP}/siren-help/
    rm -rf _build
    make html
    ## make latexpdf

    cp -r _build/html/* ${OUT_REP}
    cd ${OUT_REP}
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
    
else    
    # #### MAKE HELP
    cd ${SPHINX_REP}/siren-help/
    rm -rf _build
    make html
    make latexpdf
    cp -r _build/html ${OUT_REP}/help
    cp _build/latex/Siren.pdf ${OUT_REP}/help/Siren-UserGuide.pdf

    #### MAKE MAIN
    cd ${SPHINX_REP}/siren-web/
    rm -rf _build
    make html
    cp -r _build/html ${OUT_REP}/main

    # #### MAKE CONF SPECIFIC
    # for conf in "sigmod" "icdm"; do
    #     cd ${SPHINX_REP}/siren-${conf}/
    #     rm -rf _build
    #     make singlehtml
    #     make latexpdf
    #     cp -r _build/singlehtml ${OUT_REP}/${conf}
    #     cp _build/latex/Siren.pdf ${OUT_REP}/${conf}/Siren-$(echo ${conf} | tr 'a-z' 'A-Z' ).pdf
    # done


    cd ${OUT_REP}
    sed -i 's:\([^/]\)_static/:\1../_static/:g' */*.html
    sed -i 's:\([^/]\)_images/:\1../_images/:g' */*.html
    mkdir ./_static/ ./_images/
    # for fold in "help" "main" "sigmod" "icdm"; do
    for fold in "help" "main"; do
        mv ${fold}/_static/* ./_static/
        mv ${fold}/_images/* ./_images/
        rmdir ${fold}/_static ${fold}/_images
    done
    rm */objects.inv */.buildinfo
fi
    
# cd ${PACK_REP}
# tar -cvzf sphinx-siren-out.tar.gz out
