#!/bin/bash

SRC_REP="./python-siren"
ADD_REP="./packaging_addfiles"
YAH=$(pwd) # YOU ARE HERE

PACK_REP=${YAH}/packaging_pip-clired_$(date "+%Y%m%d%H%M%S")
ROOT_REP=${PACK_REP}/python-clired/

# ### checkout the code itself
mkdir -p ${ROOT_REP}
cp -r ${SRC_REP}/siren/clired ${ROOT_REP}
cp ${SRC_REP}/CHANGELOG ${ROOT_REP}/
grep -v -e "siren/[^rw]" ${SRC_REP}/MANIFEST.in | sed 's:siren/::;s:work/::' > ${ROOT_REP}/MANIFEST.in
head -n -3 ${SRC_REP}/LICENSE > ${ROOT_REP}/LICENSE
sed 's:os.path.split(os.path.dirname(__file__))\[0\]:os.path.dirname(__file__):' ${SRC_REP}/siren/common_details.py > ${ROOT_REP}/common_details.py
cp ${ADD_REP}/setup_clired.py ${ROOT_REP}/setup.py
cp ${ADD_REP}/prepare_pck_clired.py ${ROOT_REP}/
python ${ROOT_REP}/prepare_pck_clired.py src
rm ${ROOT_REP}/prepare_pck_clired.py

### ... and make the package
cd ${ROOT_REP}
python setup.py sdist bdist_wheel
# python -m twine upload dist/*
