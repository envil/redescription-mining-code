GENERATE_ACTION="gen"
RUN_ACTION="run"

NB_COPIES=3
SERIE=CURRENT
SUFF_DATA=random

#RAND_REP=~/redescriptors/sandbox/synthe/${SERIE}/data/
#RES_REP=~/redescriptors/sandbox/synthe/${SERIE}/results/

RAND_REP=~/redescriptors/sandbox/others/${SERIE}/data/
RES_REP=~/redescriptors/sandbox/others/${SERIE}/results/

EXT_L=.bdat
EXT_R=.bdat
RULES_EXT=.rul
SUPP_EXT=.supp
LOG_EXT=.log
INFO_EXT=.info
GEN_LOG_INFO=${RAND_REP}${SUFF_DATA}${INFO_EXT} ## WARNING NAME REBUILT IN MATLAB, DO NOT MODIFY
CONF_LOG_INFO=${RES_REP}${SUFF_DATA}${INFO_EXT} ## WARNING NAME REBUILT IN MATLAB, DO NOT MODIFY
SIDE_PLACE_HOLDER='::SIDE::'

########## GENERATION SETTINGS

gen_nb_rows='50' # total nb of rows
gen_nb_cols_L='100' # number of columns of the left hand side matrix
gen_nb_cols_R='100' # number of columns of the right hand side matrix
gen_supp_rows_L='10' # number of supporting rows of the left hand side matrix
gen_supp_rows_R='10' # number of supporting rows of the right hand side matrix
gen_nb_variables_L='2' # number of supporting variables of the left hand side matrix
gen_nb_variables_R='2' # number of supporting variables of the right hand side matrix
gen_c='4' # contribution
gen_offset='0' # offset before support of right hand side matrix
gen_preserving='3' # boolean, is the original support of the rules perserved when adding noise
gen_margin_L='1' # margin left 1=boolean
gen_margin_R='1' # margin right 1=boolean
gen_density='0.01' # noise density
gen_density_blurr_OR='0.5' # supporting columns blurr density
gen_density_blurr_AND='0.5' # supporting columns blurr density

# gen_nb_rows='100' # total nb of rows
# gen_nb_cols_L='20' # number of columns of the left hand side matrix
# gen_nb_cols_R='20' # number of columns of the right hand side matrix
# gen_supp_rows_L='25' # number of supporting rows of the left hand side matrix
# gen_supp_rows_R='25' # number of supporting rows of the right hand side matrix
# gen_nb_variables_L='5' # number of supporting variables of the left hand side matrix
# gen_nb_variables_R='5' # number of supporting variables of the right hand side matrix
# gen_offset='0' # offset before support of right hand side matrix
# gen_preserving='true, false'$(printf ', true%.0s' {1..4} )$(printf ', false%.0s' {1..4} ) # boolean, is the original support of the rules perserved when adding noise
# gen_margin_L='1' # margin left 1=boolean
# gen_margin_R='0.5' # margin right 1=boolean
# gen_density='0.01' # noise density
# gen_density_blurr_OR='0, 0, 0.25,0.5,0.75,0.9, 0.5,0.75,0.8,0.9' # supporting columns blurr density
# gen_density_blurr_AND='0, 0, 0.6,0.75,0.8,0.9, 0.25,0.33,0.45,0.5' # supporting columns blurr density


########## MINING SETTINGS
NB_VARIABLES=4
MIN_LEN=2

CONTRIBUTION=3
ITM_IN=3
ITM_OUT=3
FIN_IN=5
FIN_OUT=5

NB_RULES=30
METH_SEL="overall"
DIV_L=1
DIV_R=1
MIN_SCORE=0.01

DRAFT_CAPACITY=4
DRAFT_OUTPUT=1

MIN_IMPROVEMENT=0
COEFF_IMPACC=1
COEFF_RELIMPACC=0
COEFF_PVRULE=0
COEFF_PVRED=0

AMNESIC=""
MAX_SIDE_IDENTICAL=2
WITHOUT="--without-nots"

VERBOSITY=8

NB_lines_conf=$LINENO

SCRI_PATH=~/redescriptors/sandbox/scripts/
MAT_PATH=~/redescriptors/sandbox/scripts/
METHOD_PATH=~/redescriptors/sandbox/synthe/
MATLAB_BIN=/opt/matlab/bin/matlab
 
mkdir -p ${RAND_REP}
mkdir -p ${RES_REP}

SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');

params = struct( 'directory_out', '${RAND_REP}', ...
        'suffix', '${SUFF_DATA}', ...
        'differents', ${NB_COPIES}, ...
        'disp', false, ...
        'log_to_file', true, ...
        'side_place_holder', '${SIDE_PLACE_HOLDER}', ...
        'dat_ext_L', '${EXT_L}', ...
        'dat_ext_R', '${EXT_R}', ...
        'info_ext', '${INFO_EXT}');

setts = struct( 'nb_rows', {$gen_nb_rows}, ... % total nb of rows
            'nb_cols_L', {$gen_nb_cols_L}, ... % number of columns of the left hand side matrix
            'nb_cols_R', {$gen_nb_cols_R}, ... % number of columns of the right hand side matrix
            'supp_rows_L', {$gen_supp_rows_L}, ... % number of supporting rows of the left hand side matrix
            'supp_rows_R', {$gen_supp_rows_R}, ... % number of supporting rows of the right hand side matrix
            'nb_variables_L', {$gen_nb_variables_L}, ... % number of supporting variables of the left hand side matrix
            'nb_variables_R', {$gen_nb_variables_R}, ... % number of supporting variables of the right hand side matrix
            'c', {$gen_c}, ... % contribution
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

head -n $((NB_lines_conf -1 )) $0 > $CONF_LOG_INFO

if (( ${#GENERATE_ACTION} > 0 ))
then         
    echo "Generating synthetic matrices..."
    echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nosplash -nodesktop > /dev/null
fi

if (( ${#RUN_ACTION} > 0 ))
then         

while read line
    do
   ## fetch parameters
   FILE_L=$(echo $line | cut -d ' ' -f 1 | sed 's/'${SIDE_PLACE_HOLDER}'/L/')
   FILE_R=$(echo $line | cut -d ' ' -f 1 | sed 's/'${SIDE_PLACE_HOLDER}'/R/')
   OUT_BASE=$(echo $line | cut -d ' ' -f 1 | sed 's/'${SIDE_PLACE_HOLDER}'/O/')


   DATAL=${RAND_REP}${FILE_L}${EXT_L}
   DATAR=${RAND_REP}${FILE_R}${EXT_R}
   RULES_OUT=${RES_REP}${OUT_BASE}$RULES_EXT
   SUPPORT_OUT=${RES_REP}${OUT_BASE}$SUPP_EXT
   LOG_OUT=${RES_REP}${OUT_BASE}$LOG_EXT

   echo "Processing $OUT_BASE ..."

   echo ${SCRI_PATH}greedyRuleFinder6.py \
       --dataL=$DATAL --dataR=$DATAR \
       --rules-out=$RULES_OUT --support-out=$SUPPORT_OUT \
       --nb-variables=$NB_VARIABLES --min-len=$MIN_LEN \
       --contribution=$CONTRIBUTION --itm-in=$ITM_IN --itm-out=$ITM_OUT --fin-in=$FIN_IN --fin-out=$FIN_OUT \
       --nb-rules=$NB_RULES --meth-sel=$METH_SEL --div-L=$DIV_L --div-R=$DIV_R --min-score=$MIN_SCORE \
       --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT \
       --min-improvement=$MIN_IMPROVEMENT --coeff-impacc=$COEFF_IMPACC --coeff-relimpacc=$COEFF_RELIMPACC  --coeff-pvrule=$COEFF_PVRULE --coeff-pvred=$COEFF_PVRED \
       $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT \
       --verbosity=$VERBOSITY >> $LOG_OUT	
done < $GEN_LOG_INFO

fi
