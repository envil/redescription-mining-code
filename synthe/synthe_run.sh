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
# NB_COPIES=50
# SERIE=bool_destructive
# EXT_L=.datbool
# EXT_R=.datbool
# PRESERVING='2'
# GEN_MARGIN_R='1'

## REAL VALUED CONSERVATIVE
############################
NB_COPIES=5
SERIE=realvalued_conservative
EXT_L=.datbool
EXT_R=.densenum
PRESERVING='3'
GEN_MARGIN_R='0.3'

#####################################################################

SUFF_DATA=random
BASE_REP=~/redescriptors/sandbox/synthe/${SERIE}/
DATA_REP=${BASE_REP}data/
RESULTS_REP=${BASE_REP}results/

SCRIPTS_PATH=~/redescriptors/sandbox/NMscripts/
MINE_SCRIPT=${SCRIPTS_PATH}greedyRedescriptions.py
MAT_PATH=${SCRIPTS_PATH}
METHOD_PATH=~/redescriptors/sandbox/synthe/
MATLAB_BIN=/opt/matlab/bin/matlab

EXT_RULES=.rul
EXT_INFO=.info
EXT_TIME=.time

MINE_CONF=~/redescriptors/sandbox/synthe/synthe_template.conf
GEN_LOG_INFO=${DATA_REP}${SUFF_DATA}${EXT_INFO} ## WARNING NAME REBUILT IN MATLAB, DO NOT MODIFY
RES_LOG_INFO=${BASE_REP}${SUFF_DATA}.results
STATS_LOG_INFO=${BASE_REP}${SUFF_DATA}.stats

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

OTHER_VAR_PARAMS='::DATA_REP::='$DATA_REP',::RESULTS_REP::='$RESULTS_REP',::EXT_RULES::='$EXT_RULES',::EXT_L::='$EXT_L',::EXT_R::='$EXT_R',::SUFF_DATA::='$SUFF_DATA',::CONTRIBUTION::='$CONTRIBUTION',::MIN_IMPROV::='$(( $FULL_BOOL * -1 ))
TIME_FORMAT="%e %U %S\n%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k\n%Iinputs+%Ooutputs (%Fmajor+%Rminor)pagefaults %Wswaps"


SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');

params = struct( 'directory_out', '${DATA_REP}', ...
        'suffix', '${SUFF_DATA}', ...
        'differents', ${NB_COPIES}, ...
        'disp', false, ...
        'log_to_file', true, ...
        'dat_ext_L', '${EXT_L}', ...
        'dat_ext_R', '${EXT_R}', ...
        'info_ext', '${EXT_INFO}');

setts = struct( 'nb_rows', {$gen_nb_rows}, ... % total nb of rows
            'nb_cols_L', {$gen_nb_cols_L}, ... % number of columns of the left hand side matrix
            'nb_cols_R', {$gen_nb_cols_R}, ... % number of columns of the right hand side matrix
            'supp_rows_L', {$gen_supp_rows_L}, ... % number of supporting rows of the left hand side matrix
            'supp_rows_R', {$gen_supp_rows_R}, ... % number of supporting rows of the right hand side matrix
            'nb_variables_L', {$gen_nb_variables_L}, ... % number of supporting variables of the left hand side matrix
            'nb_variables_R', {$gen_nb_variables_R}, ... % number of supporting variables of the right hand side matrix
            'contrib', {$gen_contrib}, ... % contribution
            'offset', {$gen_offset}, ... % offset before support of right hand side matrix
            'preserving', {$gen_preserving} , ... % boolean, is the original support of the rules perserved when adding noise
            'margin_L', {$gen_margin_L}, ... % margin left 1=boolean data
            'margin_R', {$gen_margin_R}, ... % margin right 1=boolean data
            'density', {$gen_density}, ... % noise density
            'density_blurr_OR', {$gen_density_blurr_OR}, ... % supporting columns blurr density OR
            'density_blurr_AND', {$gen_density_blurr_AND}); % supporting columns blurr density AND

confs = struct( 'OR_L', {true, true, false, false}, ... 
                'OR_R', {true, false, true, false}, ... 
                'label', {'OO', 'OA', 'AO', 'AA'});
       
[log_info] = synthetic_data(params, setts, confs );
"

# confs = struct( 'OR_L', {false}, ... 
#                 'OR_R', {false}, ... 
#                 'label', {'AA'});


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

echo "Generating synthetic matrices..."
echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nosplash -nodesktop > /dev/null
 
echo 'Mining_ok Found_planted nb_rules_acc_geq nb_total_rules elapsed_time user_time system_time conf_id rule_type_id serie_id out_name' > $RES_LOG_INFO
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
	OUT=${RESULTS_REP}${SERIES}_${SUFF_DATA}
	NB_VAR_L=$(echo $line | cut -d ' ' -f 6)
	NB_VAR_R=$(echo $line | cut -d ' ' -f 7)
	OR_L=$(echo $line | cut -d ' ' -f 8)
	OR_R=$(echo $line | cut -d ' ' -f 9)
	MAX_K=$(echo $line | cut -d ' ' -f 14)
	RULE_L=$(f_make_rule ${OR_L} ${NB_VAR_L} ${BOOL_LEFT})
	RULE_R=$(f_make_rule ${OR_R} ${NB_VAR_R} ${BOOL_RIGHT})
	MATCH_RULE='^'${RULE_L}'[[:space:]]*'${RULE_R}'[[:space:]]*[^|&][[:space:]]'
	LINE_OUT=$(echo $line | cut -d ' ' -f 2-4 )" "$OUT


 	echo "Mining ${SERIES} ..." 1>&2
 	/usr/bin/time -f "$TIME_FORMAT" -o ${OUT}$EXT_TIME  $MINE_SCRIPT $MINE_CONF '::SERIES::='$SERIES','$OTHER_VAR_PARAMS	
	LINE_TIME=$(head -1 ${OUT}$EXT_TIME )
	found_p=0
	for found_acc in $(grep "$MATCH_RULE" ${OUT}$EXT_RULES | cut -f 3 | cut -d ' ' -f 1)
	do
	    if (( $FULL_BOOL == 0 )); then
		let found_p++
	    elif [ "$(f_remove_point_float $found_acc )" == "$NACC" ]; then 
		if [ "$found_p" != "0" ]; then 
		    echo 'Same formula occurred several times !' 1>&2
		    OK_F=0
		fi
		let found_p++
	    else
		echo 'Found acc ('$ACC') is not as expected ('$found_acc') !' 1>&2
		OK_F=0
	    fi
	done
	
	better=0
	total=0
	for curr_acc in $(cut -f 3 ${OUT}$EXT_RULES | cut -f 1 -d ' ')
	do
	    ncurr_acc=$(f_remove_point_float $curr_acc )
	    if [ ${#ncurr_acc} == 0 ]; then
		echo 'Trouble with floating point '$ncurr_acc' '$curr_acc 1>&2
		OK_F=0
	    else
		let total++
		if [ $ncurr_acc -ge $NACC ]; then 
 		    let better++
		fi
	    fi
	    
	done
	better=$(( better - found_p ))
	echo "$OK_F $found_p $better $total $LINE_TIME $LINE_OUT" >> $RES_LOG_INFO
	
done < $GEN_LOG_INFO
 
ERR_C=$(grep -c '^0' $RES_LOG_INFO)
if [ $ERR_C -gt 0 ]; then
    echo 'Errors in the results, not doing stats !'  1>&2
else
    awk "$SCRIPT_RESULTS_AWK" < $RES_LOG_INFO  > $STATS_LOG_INFO
fi
