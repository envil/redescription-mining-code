#!/bin/bash
CONFIG_PATH=~/redescriptors/sandbox/conf/
SCRI_PATH=~/redescriptors/sandbox/scripts/

if [ -e $CONFIG_PATH${1}.conf ]; then
    CONFIG_FILE=$CONFIG_PATH${1}.conf
else
    echo "ERROR ! No config file ! $CONFIG_PATH${1}.conf"
    exit
fi
if [ "${2}" = "none" ]; then
    DATA_S=""
else
    DATA_S=${2}
fi


DATE_S=$(date +%y%m%d%H%M%S)
UNIQ_ID="_DATE_"
if [ "${3}" ]; then
    UNIQ_ID=${3}
fi

source $CONFIG_FILE

UNIQ_ID=$(echo $UNIQ_ID | sed 's/_DATE_/'${DATE_S}'/g')
#echo "UNIQ_ID is ${UNIQ_ID}"
OUT_BASE=${1}${DATA_S}'.'${UNIQ_ID}


DATAL=${DATA_REP}${FILE_L}${DATA_S}${EXT_L}
DATAR=${DATA_REP}${FILE_R}${DATA_S}${EXT_R}

LABELSL=${DATA_REP}${FILE_L}${LABELS_EXT_L}
LABELSR=${DATA_REP}${FILE_R}${LABELS_EXT_R}

RULES_EXT=.rul
SUPP_EXT=.supp
NAMED_EXT=.names
LOG_EXT=.log
CONF_EXT=.conf

RULES_OUT=${RES_REP}${OUT_BASE}$RULES_EXT
NAMED_OUT=${RES_REP}${OUT_BASE}$NAMED_EXT
SUPPORT_OUT=${RES_REP}${OUT_BASE}$SUPP_EXT
LOG_OUT=${RES_REP}${OUT_BASE}$LOG_EXT
CONF_OUT=${RES_REP}${OUT_BASE}$CONF_EXT


if (( ${#RUN_ACTION} > 0 ))
then
COMM_LINE=$( echo  ${SCRI_PATH}greedyRuleFinder6.py \
       --dataL=$DATAL --dataR=$DATAR --rules-out=$RULES_OUT --support-out=$SUPPORT_OUT \
       --nb-variables=$NB_VARIABLES --min-len=$MIN_LEN \
       --contribution=$CONTRIBUTION --itm-in=$ITM_IN --itm-out=$ITM_OUT --fin-in=$FIN_IN --fin-out=$FIN_OUT \
       --nb-rules=$NB_RULES --meth-sel=$METH_SEL --div-L=$DIV_L --div-R=$DIV_R --min-score=$MIN_SCORE \
       --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT \
    --min-improvement=$MIN_IMPROVEMENT --coeff-impacc=$COEFF_IMPACC --coeff-relimpacc=$COEFF_RELIMPACC  --coeff-pvrule=$COEFF_PVRULE --coeff-pvred=$COEFF_PVRED \
       $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT \
       --verbosity=$VERBOSITY)

cat $CONFIG_FILE > $CONF_OUT
if [ "${RUN_ACTION}" = "log" ]
then         
    $COMM_LINE > $LOG_OUT
else
    $COMM_LINE
fi
fi

if (( ${#POST_ACTIONS} > 0 ))
then         
    ${SCRI_PATH}postProcess.py $POST_ACTIONS \
    --dataL=$DATAL --dataR=$DATAR \
    --rules-in=$RULES_OUT  --support-in=$SUPPORT_OUT \
    --left-labels=$LABELSL --right-labels=$LABELSR \
    --base-out=${RES_REP}${OUT_BASE}  --verbosity=$VERBOSITY  
fi