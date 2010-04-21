
NB_COPIES=25
SUFF_DATA=filtered
SERIE=${SUFF_DATA}_bn

RAND_REP=/fs-1/3/galbrun/redescriptors/sandbox/rand_dblp/${SERIE}/data/
RES_REP=/fs-1/3/galbrun/redescriptors/sandbox/rand_dblp/${SERIE}/results/
ORG_REP=/fs-1/3/galbrun/redescriptors/sandbox/dblp/
FILE_L=conference_${SUFF_DATA}
FILE_R=coauthor_${SUFF_DATA}
EXT_L=bdat
EXT_R=ndat
RULES_EXT=rul
SUPP_EXT=supp
OUT_BASE=random
LOG_FILE=${RES_REP}random.log

########## MINING SETTINGS
NB_VARIABLES=4
MIN_LEN=2

CONTRIBUTION=3
ITM_IN=3
ITM_OUT=3
FIN_IN=3
FIN_OUT=3

NB_RULES=100
METH_SEL="overall"
DIV_L=1
DIV_R=1
MIN_SCORE=0.01

DRAFT_CAPACITY=4
DRAFT_OUTPUT=1

MIN_IMPROVEMENT=0
COEFF_IMPACC=1
COEFF_RELIMPACC=0
COEFF_PVRULE=1
COEFF_PVRED=1

AMNESIC=""
MAX_SIDE_IDENTICAL=2
WITHOUT="--without-nots"

VERBOSITY=8

SCRI_PATH=/fs-1/3/galbrun/redescriptors/sandbox/scripts/
MAT_PATH=/fs-1/3/galbrun/redescriptors/sandbox/scripts/
METHOD_PATH=/fs-1/3/galbrun/redescriptors/sandbox/swap/
MATLAB_BIN=/opt/matlab/bin/matlab

mkdir -p ${RAND_REP}
mkdir -p ${RES_REP}

echo "Original as copy 0"
cp ${ORG_REP}${FILE_L}.${EXT_L} ${RAND_REP}${FILE_L}_0.${EXT_L}
cp ${ORG_REP}${FILE_R}.${EXT_R} ${RAND_REP}${FILE_R}_0.${EXT_R}

echo "Generating randomized copies..."
SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}', '${EXT_R}');

%%IF NEEDED DISCRETIZE

for i = 1:${NB_COPIES}
    XL_r = swap(XL);
    XR_r = swap(XR);
    save_matrix(XL_r, ['${RAND_REP}${FILE_L}_' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${RAND_REP}${FILE_R}_' num2str(i)], '${EXT_R}');
end
"
echo "${SCRIPT_MATLAB}" | $MATLAB_BIN > /dev/null


for (( i=0; i<=${NB_COPIES}; i++ ))
do
   echo "Processing copy $i"
   
   DATAL=${RAND_REP}${FILE_L}_${i}.${EXT_L}
   DATAR=${RAND_REP}${FILE_R}_${i}.${EXT_R}
   RULES_OUT=${RES_REP}${OUT_BASE}_${i}.$RULES_EXT
   SUPPORT_OUT=${RES_REP}${OUT_BASE}_${i}.$SUPP_EXT


   ${SCRI_PATH}/greedyRuleFinder6.py \
       --dataL=$DATAL --dataR=$DATAR \
       --rules-out=$RULES_OUT --support-out=$SUPPORT_OUT \
       --nb-variables=$NB_VARIABLES --min-len=$MIN_LEN \
       --contribution=$CONTRIBUTION --itm-in=$ITM_IN --itm-out=$ITM_OUT --fin-in=$FIN_IN --fin-out=$FIN_OUT \
       --nb-rules=$NB_RULES --meth-sel=$METH_SEL --div-L=$DIV_L --div-R=$DIV_R --min-score=$MIN_SCORE \
       --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT \
       --min-improvement=$MIN_IMPROVEMENT --coeff-impacc=$COEFF_IMPACC --coeff-relimpacc=$COEFF_RELIMPACC  --coeff-pvrule=$COEFF_PVRULE --coeff-pvred=$COEFF_PVRED \
       $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT \
       --verbosity=$VERBOSITY >> $LOG_FILE

done
