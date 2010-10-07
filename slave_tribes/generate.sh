TEMPLATE_CONF=${1}

OUT=out
BASE_REP=~/redescriptors/sandbox/CART_exp/
SCRIPT_REP=~/redescriptors/sandbox/NMscripts/
DATA=worldclim_tp_small
DENSENUM=densenum
DATBOOL=datbool
NAMES=names
BOUNDS=bounds
MATLAB_BIN=/opt/matlab/bin/matlab

for HOW in 'height' 'width' 'segments'
do
    for N in 10 20 30 50 75 100 150
    do
       SUFF=_${N}${HOW}
       NAME_BASE=${REP_BASE}/${DATA}${SUFF}
       echo "Doing $SUFF"
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

    done
done

#${SCRIPT_REP}greedyRedescriptions.py ${BASE_REP}${OUT}${SUFF}.conf
#${SCRIPT_REP}postProcess.py ${BASE_REP}${OUT}${SUFF}.conf



