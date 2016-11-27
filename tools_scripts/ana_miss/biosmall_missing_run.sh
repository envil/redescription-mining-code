#!/bin/bash

#####################################################################
SUFF_DATA=small
SUFF_MISS=smallmissing
ORG_REP=~/redescriptors/sandbox/rajapaja/
BASE_REP=~/redescriptors/sandbox/synthe/biosmall_missing/
DATA_REP=${BASE_REP}data/
RESULTS_REP=${BASE_REP}results/
DATA_L=mammals
EXT_L=.datbool
DATA_R=worldclim_tp
EXT_R=.densenum


SCRIPTS_PATH=~/redescriptors/sandbox/miss_scripts/
TOOLS_PATH=~/redescriptors/sandbox/tools_scripts/
MINE_SCRIPT=${SCRIPTS_PATH}greedyRedescriptions.py
POST_SCRIPT=${SCRIPTS_PATH}postProcess.py
MAT_PATH=${TOOLS_PATH}
METHOD_PATH=~/redescriptors/sandbox/synthe/
MATLAB_BIN=/opt/matlab/bin/matlab

EXT_RULES=.queries
EXT_INFO=.info
EXT_TIME=.time

MINE_CONF=~/redescriptors/sandbox/synthe/biosmall_missing_template.conf
GEN_LOG_INFO=${DATA_REP}${SUFF_DATA}${EXT_INFO} ## WARNING NAME REBUILT IN MATLAB, DO NOT MODIFY
RES_LOG_INFO=${BASE_REP}${SUFF_MISS}.results
STATS_LOG_INFO=${BASE_REP}${SUFF_MISS}.stats

mkdir -p ${DATA_REP}
mkdir -p ${RESULTS_REP}

OTHER_VAR_PARAMS='::DATA_REP::='$DATA_REP',::DATA_R::='$DATA_R',::DATA_L::='$DATA_L',::RESULTS_REP::='$RESULTS_REP',::EXT_RULES::='$EXT_RULES',::EXT_L::='$EXT_L',::EXT_R::='$EXT_R',::SUFF_DATA::='$SUFF_MISS
OTHER_VAR_PARAMS_POST='::DATA_REP::='$ORG_REP',::DATA_R::='$DATA_R',::DATA_L::='$DATA_L',::RESULTS_REP::='$RESULTS_REP',::EXT_RULES::='$EXT_RULES',::EXT_L::='$EXT_L',::EXT_R::='$EXT_R',::SUFF_DATA::='$SUFF_DATA',::SUFF_MISS::='$SUFF_MISS
TIME_FORMAT="%e %U %S\n%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k\n%Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"

	SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');

params = struct( 'directory_in', '${ORG_REP}', ...
        'directory_out', '${DATA_REP}', ...
        'suffix', '${SUFF_DATA}', ...
        'suffix_miss', '${SUFF_MISS}', ...
        'data_L', '${DATA_L}', ...        
        'data_R', '${DATA_R}', ...        
        'dat_ext_L', '${EXT_L}', ...
        'dat_ext_R', '${EXT_R}');

confs = struct( 'density', {0.01, 0.05, 0.1}, ... 
                'number', {10, 10, 10}, ...
		'label', {'1pc', '5pc', '10pc'});

[L, sym] = load_matrix([params.directory_in params.data_L '_' params.suffix], params.dat_ext_L);
[R, sym] = load_matrix([params.directory_in params.data_R '_' params.suffix], params.dat_ext_R);


for l = 1:length(confs)
     for i=1:confs(l).number
         n = full(sprand(size(L,1), size(L,2),confs(l).density) > 0);
	 L=L-L.*n-8005*n;
	 n = full(sprand(size(R,1), size(R,2),confs(l).density) > 0);
	 R=R-R.*n-8005*n;
         save_matrix(L, [params.directory_out params.data_L confs(l).label num2str(i) '_' params.suffix_miss], params.dat_ext_L);
         save_matrix(R, [params.directory_out params.data_R confs(l).label num2str(i) '_' params.suffix_miss], params.dat_ext_R);
     end
end
"

############ 

# echo "Generating synthetic matrices..."
# echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nosplash -nodesktop > /dev/null

# sed -i 's/-800[0-9]/m/g' ${DATA_REP}*_$SUFF_MISS*

for copy in $(ls ${DATA_REP}${DATA_L}*_$SUFF_MISS* ) 
do
    # echo "COPY " $copy
    TYPE=$( echo $copy | sed 's/^.*\/[a-z]*\([0-9]*pc[0-9]*\)_.*$/\1/g' )
    #TYPE='1pc1'
    OUT=${RESULTS_REP}${TYPE}_${SUFF_MISS}
    echo "Mining ${TYPE} ..." 1>&2
    echo /usr/bin/time -f "$TIME_FORMAT" -o ${OUT}$EXT_TIME  $MINE_SCRIPT $MINE_CONF '::TYPE::='$TYPE','$OTHER_VAR_PARAMS	
    #$POST_SCRIPT $MINE_CONF '::TYPE::='$TYPE','$OTHER_VAR_PARAMS_POST	
    #cut -f 3 ${RESULTS_REP}${TYPE}_${SUFF_MISS}_recomputed.queries | paste -d '#' ${RESULTS_REP}${TYPE}_${SUFF_MISS}.queries - | sed 's/#/ #/g' > ${RESULTS_REP}${TYPE}_${SUFF_MISS}.compare
    exit
done
