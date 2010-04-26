#!/bin/bash
CONFIG_PATH=~/redescriptors/sandbox/conf/
if [ -e $CONFIG_PATH${1}.conf ]; then
    CONFIG_FILE=$CONFIG_PATH${1}.conf
else
    echo "ERROR ! No config file ! $CONFIG_PATH${1}.conf"
    exit
fi

source $CONFIG_FILE

FIRST_COPY_SWAP=${2}
LAST_COPY_SWAP=${3}
FIRST_COPY_SWAPDISC=${4}
LAST_COPY_SWAPDISC=${5}
FIRST_COPY_PERM=${6}
LAST_COPY_PERM=${7}
FIRST_COPY_PERMSSYM=${8}
LAST_COPY_PERMSSYM=${9}

SUFF_ORG=_0
SUFF_SWAP=_swap
SUFF_SWAPDISC=_swapdisc
SUFF_PERM=_perm
SUFF_PERMSSYM=_permssym

MAT_PATH=~/redescriptors/sandbox/scripts/
METHOD_PATH=~/redescriptors/sandbox/swap/
MATLAB_BIN=/opt/matlab/bin/matlab

mkdir -p ${DATA_REP}
mkdir -p ${RES_REP}

if [ ! -e ${DATA_REP}${FILE_L}${SUFF_ORG}${EXT_L} ]; then
    echo "Original as copy 0"
    cp ${ORG_REP}${FILE_L}${EXT_L} ${DATA_REP}${FILE_L}${SUFF_ORG}${EXT_L}
    cp ${ORG_REP}${FILE_R}${EXT_R} ${DATA_REP}${FILE_R}${SUFF_ORG}${EXT_R}
fi

####### SCRIPT MATLAB RANDOM SWAP NO DISCRETIZE
SCRIPT_MATLAB_SWAP="
path(path,'${MAT_PATH}');
%path(path,'${METHOD_PATH}');
cd '${METHOD_PATH}';
XL = load_matrix('${DATA_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${DATA_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = ${FIRST_COPY_SWAP}:${LAST_COPY_SWAP}
    XL_r = swap(XL);
    XR_r = swap(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}${SUFF_SWAP}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}${SUFF_SWAP}' num2str(i)], '${EXT_R}');
end
" 

####### SCRIPT MATLAB RANDOM SWAP DISCRETIZE RIGHT
SCRIPT_MATLAB_SWAPDISC="
path(path,'${MAT_PATH}');
%path(path,'${METHOD_PATH}');
cd '${METHOD_PATH}';
XL = load_matrix('${DATA_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${DATA_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

SR = scale_data(XR);
DR = discretize(SR);

for i = ${FIRST_COPY_SWAPDISC}:${LAST_COPY_SWAPDISC}
    XL_r = swap(XL);
    DR_r = swap(DR);
    SR_r = undiscretize(DR_r, SR);
    XR_r = unscale_data(SR_r, XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}${SUFF_SWAPDISC}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}${SUFF_SWAPDISC}' num2str(i)], '${EXT_R}');
end
" 

####### SCRIPT MATLAB RANDOM PERMUTE
SCRIPT_MATLAB_PERM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${DATA_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${DATA_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = ${FIRST_COPY_PERM}:${LAST_COPY_PERM}
    XL_r = permute_mat(XL);
    XR_r = permute_mat(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}${SUFF_PERM}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}${SUFF_PERM}' num2str(i)], '${EXT_R}');
end
"

####### SCRIPT MATLAB RANDOM PERMUTE RIGHT SPARSE SYMMETRIC
SCRIPT_MATLAB_PERMSSYM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${DATA_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${DATA_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = ${FIRST_COPY_PERMSSYM}:${LAST_COPY_PERMSSYM}
    XL_r = permute_mat(XL);
    XR_r = permute_ssym(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}${SUFF_PERMSSYM}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}${SUFF_PERMSSYM}' num2str(i)], '${EXT_R}');
end
"
 
if [ "$LAST_COPY_SWAP" -ge "$FIRST_COPY_SWAP" ]; then
    echo "Generating ${FIRST_COPY_SWAP}...${LAST_COPY_SWAP} swap randomized copies..."
    echo "${SCRIPT_MATLAB_SWAP}" | $MATLAB_BIN > /dev/null
fi
if [ "$LAST_COPY_SWAPDISC" -ge "$FIRST_COPY_SWAPDISC" ]; then
    echo "Generating ${FIRST_COPY_SWAPDISC}...${LAST_COPY_SWAPDISC} swap discretize randomized copies..."
    echo "${SCRIPT_MATLAB_SWAPDISC}" | $MATLAB_BIN > /dev/null
fi
if [ "$LAST_COPY_PERM" -ge "$FIRST_COPY_PERM" ]; then
    echo "Generating ${FIRST_COPY_PERM}...${LAST_COPY_PERM}  perm randomized copies..."
    echo "${SCRIPT_MATLAB_PERM}" | $MATLAB_BIN > /dev/null
fi
if [ "$LAST_COPY_PERMSSYM" -ge "$FIRST_COPY_PERMSSYM" ]; then
    echo "Generating ${FIRST_COPY_PERMSSYM}...${LAST_COPY_PERMSSYM}  perm sparse sym randomized copies..."
    echo "${SCRIPT_MATLAB_PERMSSYM}" | $MATLAB_BIN > /dev/null
fi
