#!/bin/bash

SRC_REP="./python-siren"
ADD_REP="./packaging_addfiles"
YAH=$(pwd) # YOU ARE HERE

# PACK_REP=${YAH}/packaging_pip-clired_$(date "+%Y%m%d%H%M%S")
PACK_REP=${YAH}/packaging_current
ROOT_REP=${PACK_REP}/python-clired

# ### checkout the code itself
mkdir -p ${ROOT_REP}/blocks
cp -r ${SRC_REP}/blocks/mine ${ROOT_REP}/blocks/
cp -r ${SRC_REP}/blocks/work ${ROOT_REP}/blocks/
cp -r ${SRC_REP}/blocks/*.py ${ROOT_REP}/blocks/
rm -rf ${ROOT_REP}/blocks/*/__pycache__
cp ${SRC_REP}/CHANGELOG ${ROOT_REP}/
grep -v -e "blocks/[^mw]" ${SRC_REP}/MANIFEST.in > ${ROOT_REP}/MANIFEST.in
head -n -3 ${SRC_REP}/LICENSE > ${ROOT_REP}/LICENSE
# sed 's:os.path.split(os.path.dirname(__file__))\[0\]:os.path.dirname(__file__):' ${SRC_REP}/siren/common_details.py > ${ROOT_REP}/common_details.py
cp ${SRC_REP}/exec_server.py ${SRC_REP}/exec_client.py ${ROOT_REP}/
cp ${ADD_REP}/setup_clired.py ${ROOT_REP}/setup.py
cp ${ADD_REP}/prepare_pck_clired.py ${ROOT_REP}/
python ${ROOT_REP}/prepare_pck_clired.py src
rm ${ROOT_REP}/prepare_pck_clired.py

### ... and make the package
cd ${ROOT_REP}
python setup.py sdist bdist_wheel
### python -m twine upload dist/*
