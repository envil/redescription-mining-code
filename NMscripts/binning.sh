#!/bin/sh

DATA_REP=~/redescriptors/sandbox/binning
DATA=worldclim_tp
DENSENUM=densenum
DATBOOL=datbool
NAMES=names
BOUNDS=bounds
MAT_PATH=~/redescriptors/sandbox/binning
MATLAB_BIN=/opt/matlab/bin/matlab

N=${1}
HOW=${2}

SUFF=_${N}${HOW}

if [ -e ${DATA_REP}/${DATA}${SUFF}.${BOUNDS} ]
then
  echo "Removing old bounds file..."
  rm ${DATA_REP}/${DATA}${SUFF}.${BOUNDS}
fi


SCRIPT_MATLAB="
    path(path,'${MAT_PATH}/');
    mat_real=load('${DATA_REP}/${DATA}.${DENSENUM}')';
    [mat_bin, bounds] = bin_matrix(mat_real, ${N}, '${HOW}');
    [i,j,s] = find(mat_bin);
    i = [size(mat_bin,1); i];
    j = [size(mat_bin,2); j];
    s = [0; s~=0];
    A = [i j s];
    dlmwrite('${DATA_REP}/${DATA}${SUFF}.${DATBOOL}', A, 'delimiter', '\t');
    for column=1:length(bounds)
        dlmwrite('${DATA_REP}/${DATA}${SUFF}.${BOUNDS}', bounds{column}, 'delimiter', '\t','-append');    
    end
"

    echo "Computing bins..."
    echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null	

    echo "Translating names..."
    awk -f bins_names.awk ${DATA_REP}/${DATA}.${NAMES} ${DATA_REP}/${DATA}${SUFF}.${BOUNDS} > ${DATA_REP}/${DATA}${SUFF}.${NAMES}
