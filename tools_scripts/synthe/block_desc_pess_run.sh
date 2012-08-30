#!/bin/bash

#####################################################################
### CHANGING PARAMETERS :

# ## BOOL CONSERVATIVE
# ####################
# NB_COPIES=50
# SERIE=bool_conservative
# EXT_L=.datbool
# EXT_R=.datbool
# PRESERVING='3'
# GEN_MARGIN_R='1'

# ## BOOL DESTRUCTIVE
# ####################
NB_COPIES=50
SERIE=bool_destructive
EXT_L=.datbool
EXT_R=.datbool
PRESERVING='2'
GEN_MARGIN_R='1'

## REAL VALUED CONSERVATIVE
############################
# NB_COPIES=5
# SERIE=realvalued_conservative
# EXT_L=.datbool
# EXT_R=.densenum
# PRESERVING='3'
# GEN_MARGIN_R='0.3'

#####################################################################

SUFF_DATA=random
SUFF_MISS=block
BASE_REP=~/redescriptors/sandbox/synthe/${SERIE}/
DATA_REP=${BASE_REP}data/
RESULTS_REP=${BASE_REP}results_block_pess/

SCRIPTS_PATH=~/redescriptors/sandbox/pess_scripts/
TOOLS_PATH=~/redescriptors/sandbox/tools_scripts/
MINE_SCRIPT=${SCRIPTS_PATH}greedyRedescriptions.py
POST_SCRIPT=${SCRIPTS_PATH}postProcess.py
MAT_PATH=${TOOLS_PATH}
METHOD_PATH=~/redescriptors/sandbox/synthe/
MATLAB_BIN=/opt/matlab/bin/matlab

EXT_RULES=.queries
EXT_INFO=.info
EXT_TIME=.time

MINE_CONF=~/redescriptors/sandbox/synthe/synthe_template.conf
#GEN_LOG_INFO=${DATA_REP}${SUFF_DATA}${EXT_INFO} ## WARNING NAME REBUILT IN MATLAB, DO NOT MODIFY
GEN_LOG_INFO=${DATA_REP}${SUFF_DATA}${EXT_INFO}.block

RES_LOG_INFO=${BASE_REP}${SUFF_MISS}.results
STATS_LOG_INFO=${BASE_REP}${SUFF_MISS}.stats

########## GENERATION SETTINGS

gen_nb_rows='500' # total nb of rows
gen_nb_cols_L='10' # number of columns of the left hand side matrix
gen_nb_cols_R='10' # number of columns of the right hand side matrix
gen_supp_rows_L='50' # number of supporting rows of the left hand side matrix
gen_supp_rows_R='50' # number of supporting rows of the right hand side matrix
gen_nb_variables_L='3' # number of supporting variables of the left hand side matrix
gen_nb_variables_R='3' # number of supporting variables of the right hand side matrix
gen_contrib='3' # contribution
gen_offset='0' # offset before support of right hand side matrix
gen_preserving=$PRESERVING # boolean, is the original support of the rules perserved when adding noise
gen_margin_L='1' # margin left 1=boolean
gen_margin_R=$GEN_MARGIN_R # margin right 1=boolean
gen_density='0.01, 0.025, 0.05, 0.1' # noise density
gen_density_blurr_OR='1' # supporting columns blurr density
gen_density_blurr_AND='1' # supporting columns blurr density

mkdir -p ${DATA_REP}
mkdir -p ${RESULTS_REP}

if [[ $EXT_L == *bool ]]; then
    BOOL_LEFT=1
else
    BOOL_LEFT=0
fi
if [[ $EXT_R == *bool ]]; then
    BOOL_RIGHT=1
else
    BOOL_RIGHT=0
fi
FULL_BOOL=$(( $BOOL_RIGHT * $BOOL_LEFT ))

OTHER_VAR_PARAMS='::DATA_REP::='$DATA_REP',::RESULTS_REP::='$RESULTS_REP',::EXT_RULES::='$EXT_RULES',::EXT_L::='$EXT_L',::EXT_R::='$EXT_R',::SUFF_DATA::='$SUFF_MISS',::SUFF_MISS::='$SUFF_MISS',::MIN_IMPROV::='$(( $FULL_BOOL * -1 ))

OTHER_VAR_PARAMS_POST='::DATA_REP::='$DATA_REP',::RESULTS_REP::='$RESULTS_REP',::EXT_RULES::='$EXT_RULES',::EXT_L::='$EXT_L',::EXT_R::='$EXT_R',::SUFF_DATA::='$SUFF_DATA',::SUFF_MISS::='$SUFF_MISS',::MIN_IMPROV::='$(( $FULL_BOOL * -1 ))

TIME_FORMAT="%e %U %S\n%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k\n%Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"


############ 

function f_make_rule {

	local OR_P=${1}
	local NB_VAR=${2}
	local BOOL_S=${3}
	local CAR_OP_OR='|'
	local CAR_OP_AND='&'
	local LEN_INDEX=3

	if (( $OR_P == 1 )); then
	    CAR_OP=${CAR_OP_OR}
	else
	    CAR_OP=${CAR_OP_AND}
	fi
	if (( $BOOL_S == 1 )); then
	    CAR_BOUNDS=' '
	else
	    CAR_BOUNDS='[<>0-9\.]* '
	fi
	
	RULE_P=$(printf '  % '${LEN_INDEX}'i' 0)${CAR_BOUNDS}
	for i in $(seq 1 $((${NB_VAR}-1)) )
	do
	   RULE_P=${RULE_P}' '${CAR_OP}$(printf '  % '${LEN_INDEX}'i' $i)${CAR_BOUNDS} 
	done
	echo $RULE_P
}

function f_remove_point_float {
	local ACC=${1}
	if [[ "$ACC" =~ ^[0-9]\.[0-9]{6}$ ]]; then
	    echo ${ACC:0:1}${ACC:2}
	else
	    echo -1
	    echo 'Floating point number does not have expected format ! '$ACC 1>&2
	fi
}
############ 
## Input fields on each line: (first contains labels)
## 1:Mining_ok, 2:Found_planted, 3:nb_rules_acc_geq, 4:nb_total_rules, 5:elapsed_time, 6:user_time, 7:system_time, 8:conf_id, 9:rule_type_id, 10:serie_id, 11:out_name
## Output fields on each line: (first contains labels)
## 1:conf_id, 2:rule_type_id, 3:nb_found_planted, 4:nb_series, 5:nb_better, 6:nb_total, 7:ratio_found_planted, 8:ratio_better, 
## 9:avg_elapsed_time, 10:max_elapsed_time, 11:avg_user_time, 12:max_user_time, 13:avg_system_time, 14:max_system_time, 15:serie_name 

SCRIPT_RESULTS_AWK='
BEGIN {
    FS=" "
}
{
if (FNR != 1) {
   found_r[$8 " " $9]+=$2
   better_r[$8 " " $9]+=$3
   neither_fb[$8 " " $9]+=($2+$3)<=0
   total_r[$8 " " $9]+=$4   
   if ( $10 == 0) serie_name[$8 " " $9]=$11
   series[$8 " " $9]+=1

   elapsed_t[$8 " " $9]+=$5
   if (elapsed_max[$8 " " $9] < $5) elapsed_max[$8 " " $9]=$5
   user_t[$8 " " $9]+=$6
   if (user_max[$8 " " $9] < $6) user_max[$8 " " $9]=$6
   system_t[$8 " " $9]+=$7
   if (system_max[$8 " " $9] < $7) system_max[$8 " " $9]=$7
   }
} 
END {
     print "conf_id rule_type_id nb_found_planted nb_series nb_better nb_neither_fb nb_total ratio_found_planted ratio_better avg_elapsed_time max_elapsed_time avg_user_time max_user_time avg_system_time max_system_time"
     for (setts_type in series) 
         printf "%s %i %i %i %i %i %f %f %f %f %f %f %f %f %s\n", setts_type, found_r[setts_type], series[setts_type], better_r[setts_type], neither_fb[setts_type], total_r[setts_type], found_r[setts_type]/series[setts_type], better_r[setts_type]/total_r[setts_type], elapsed_t[setts_type]/series[setts_type], elapsed_max[setts_type], user_t[setts_type]/series[setts_type], user_max[setts_type], system_t[setts_type]/series[setts_type], system_max[setts_type], serie_name[setts_type]
}
	'
############ 

# echo "Generating synthetic matrices..."
# echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nosplash -nodesktop > /dev/null
 
#echo 'Mining_ok Found_planted nb_rules_acc_geq nb_total_rules elapsed_time user_time system_time conf_id rule_type_id serie_id out_name' > $RES_LOG_INFO
while read line
do
   ## fetch parameters
	ACC=$(echo $line | cut -d ' ' -f 5 )
	NACC=$(f_remove_point_float $ACC )
	if [ ${#NACC} == 0 ]; then
	    OK_F=0
	else
	    OK_F=1
	fi
	SERIES=$(echo $line | cut -d ' ' -f 1)
	NB_VAR_L=$(echo $line | cut -d ' ' -f 6)
	NB_VAR_R=$(echo $line | cut -d ' ' -f 7)
	OR_L=$(echo $line | cut -d ' ' -f 8)
	OR_R=$(echo $line | cut -d ' ' -f 9)
	MAX_K=$(echo $line | cut -d ' ' -f 14)
	RULE_L=$(f_make_rule ${OR_L} ${NB_VAR_L} ${BOOL_LEFT})
	RULE_R=$(f_make_rule ${OR_R} ${NB_VAR_R} ${BOOL_RIGHT})
	MATCH_RULE='^'${RULE_L}'[[:space:]]*'${RULE_R}'[[:space:]]*[^|&][[:space:]]'
	
	TIME_STAMP=$(date +%s)
	SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');

params = struct( 'directory_out', '${DATA_REP}', ...
        'suffix', '${SUFF_DATA}', ...
        'suffix_miss', '${SUFF_MISS}', ...
        'series', '${SERIES}', ...        
        'dat_ext_L', '${EXT_L}', ...
        'dat_ext_R', '${EXT_R}');

confs = struct( 'density', {0.01, 0.05, 0.1}, ... 
                'number', {1, 1, 1}, ...
		'label', {'1pc', '5pc', '10pc'});

[L, sym] = load_matrix([params.directory_out 'L' params.series '_' params.suffix], params.dat_ext_L);
[R, sym] = load_matrix([params.directory_out 'R' params.series '_' params.suffix], params.dat_ext_R);

ns2 = RandStream.create('mrg32k3a','NumStreams',3,'StreamIndices',2,'Seed',${TIME_STAMP});
RandStream.setDefaultStream(ns2);

for l = 1:length(confs)
     for i=1:confs(l).number
         nb_colsL=randi(3);
         nb_rowsL=round(confs(l).density*prod(size(L))/(nb_colsL+1));
         rowspL=randperm(size(L,1));
         L(rowspL(nb_rowsL),[1, 4:4+nb_colsL])=-8005;
         nb_colsR=randi(3);
         nb_rowsR=round(confs(l).density*prod(size(R))/(nb_colsR+1));
         rowspR=randperm(size(R,1));
         R(rowspR(nb_rowsR),[1, 4:4+nb_colsR])=-8005;
         save_matrix(L, [params.directory_out 'L' confs(l).label num2str(i) '_' params.series '_' params.suffix_miss], params.dat_ext_L);
         save_matrix(R, [params.directory_out 'R' confs(l).label num2str(i) '_' params.series '_' params.suffix_miss], params.dat_ext_R);
     end
end
"
 
 	# echo "Generating block ${SERIES} ..."
	# echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nosplash -nodesktop > /dev/null
	
	# sed -i 's/-800[0-9]/m/g' ${DATA_REP}L*_${SERIES}_${SUFF_MISS}*
	# sed -i 's/-800[0-9]/m/g' ${DATA_REP}R*_${SERIES}_${SUFF_MISS}*


	for copy in $(ls ${DATA_REP}L*_${SERIES}_${SUFF_MISS}* ) 
	do
#	    echo "COPY " $copy 
	   TYPE=$( echo $copy | sed 's/^.*\/L\([0-9]*pc[0-9]\)_.*$/\1/g' )
	   OUT=${RESULTS_REP}${TYPE}_${SERIES}_${SUFF_MISS}
	   LINE_OUT=$(echo $line | cut -d ' ' -f 2-4 )" "$OUT

	   echo "Mining ${TYPE}_${SERIES} ..." 1>&2
#	   echo "LINE_OUT" $LINE_OUT
 	   /usr/bin/time -f "$TIME_FORMAT" -o ${OUT}$EXT_TIME  $MINE_SCRIPT $MINE_CONF '::SERIES::='$TYPE'_'$SERIES',::TYPES_SERIES::='$TYPE'_'$SERIES','$OTHER_VAR_PARAMS

	   cp ${RESULTS_REP}${TYPE}_${SERIES}_${SUFF_MISS}${EXT_RULES} ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}${EXT_RULES} 
	   cp ${RESULTS_REP}${TYPE}_${SERIES}_${SUFF_MISS}${EXT_RULES} ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}${EXT_RULES}
	   
	   if [[ "$SERIES" =~ "AO" ]]; then
	       echo -e "0 & 1 & 2\t 0 | 1 | 2" >> ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}${EXT_RULES}
	       echo -e "0 & 1 & 2\t 0 | 1 | 2" >> ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}${EXT_RULES}
#	       echo "AO: "$SERIES
	   elif [[ "$SERIES" =~ "OA" ]]; then
	       echo -e "0 | 1 | 2\t 0 & 1 & 2" >> ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}${EXT_RULES}
	       echo -e "0 | 1 | 2\t 0 & 1 & 2" >> ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}${EXT_RULES}
#	       echo "OA: "$SERIES
	   elif [[ "$SERIES" =~ "OO" ]]; then
	       echo -e "0 | 1 | 2\t 0 | 1 | 2" >> ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}${EXT_RULES}
	       echo -e "0 | 1 | 2\t 0 | 1 | 2" >> ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}${EXT_RULES}
#	       echo "OO: "$SERIES
	   elif [[ "$SERIES" =~ "AA" ]]; then
	       echo -e "0 & 1 & 2\t 0 & 1 & 2" >> ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}${EXT_RULES}
	       echo -e "0 & 1 & 2\t 0 & 1 & 2" >> ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}${EXT_RULES}
#	       echo "AA: "$SERIES
	   else
	       echo "none: "$SERIES
	   fi
	  
	   $POST_SCRIPT $MINE_CONF '::SERIES::='$TYPE'_'$SERIES',::TYPES_SERIES::='$TYPE'test_'$SERIES','$OTHER_VAR_PARAMS
	   $POST_SCRIPT $MINE_CONF '::SERIES::='$SERIES',::TYPES_SERIES::='$TYPE'orgdata_'$SERIES','$OTHER_VAR_PARAMS_POST
	   cut -f 3 ${RESULTS_REP}${TYPE}orgdata_${SERIES}_${SUFF_MISS}_recomputed${EXT_RULES} | paste -d '#' ${RESULTS_REP}${TYPE}test_${SERIES}_${SUFF_MISS}_recomputed${EXT_RULES} - | sed 's/#/ #/g' > ${RESULTS_REP}${TYPE}_${SERIES}_${SUFF_MISS}.compare

	done

done < $GEN_LOG_INFO
