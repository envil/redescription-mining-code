N=${1}
HOW=${2}
TEMPLATE_CONF=${3}

SUFF=_${N}${HOW}
OUT=out
BASE_REP=~/redescriptors/sandbox/binning_exp/
SCRIPT_REP=~/redescriptors/sandbox/NMscripts/
DATA=worldclim_tp
DENSENUM=densenum
DATBOOL=datbool
NAMES=names
BOUNDS=bounds
MATLAB_BIN=/opt/matlab/bin/matlab

NAME_BASE=${REP_BASE}/${DATA}${SUFF}


sed -e "s/__SUFF__/${SUFF}/g" ${TEMPLATE_CONF} > ${BASE_REP}${OUT}${SUFF}.conf

if [ -e ${BASE_REP}/${DATA}${SUFF}.${BOUNDS} ]
then
  echo "Removing old bounds file..."
  rm ${BASE_REP}/${DATA}${SUFF}.${BOUNDS}
fi


SCRIPT_MATLAB="
    path(path,'${SCRIPT_REP}');
    mat_real=load('${BASE_REP}/${DATA}.${DENSENUM}')';
    [mat_bin, bounds] = bin_matrix(mat_real, ${N}, '${HOW}');
    [i,j,s] = find(mat_bin);
    i = [size(mat_bin,1); i];
    j = [size(mat_bin,2); j];
    s = [0; s~=0];
    A = [i j s];
    dlmwrite('${BASE_REP}/${DATA}${SUFF}.${DATBOOL}', A, 'delimiter', '\t');
    for column=1:length(bounds)
        dlmwrite('${BASE_REP}/${DATA}${SUFF}.${BOUNDS}', bounds{column}', 'delimiter', '\t','-append');    
    end
"

    echo "Computing bins..."
    echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null	

    echo "Translating names..."
    awk -f ${SCRIPT_REP}bins_names.awk ${BASE_REP}/${DATA}.${NAMES} ${BASE_REP}/${DATA}${SUFF}.${BOUNDS} > ${BASE_REP}/${DATA}${SUFF}.${NAMES}


${SCRIPT_REP}greedyRedescriptions.py ${BASE_REP}${OUT}${SUFF}.conf
${SCRIPT_REP}postProcess.py ${BASE_REP}${OUT}${SUFF}.conf



