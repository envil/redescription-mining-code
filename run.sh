#!/bin/bash

if [ -e ./conf/${1}.conf ]; then
    CONFIG_FILE=./conf/${1}.conf
else
    echo "ERROR ! No config file !"
    exit
fi

DATE_S=$(date +%y%m%d%H%M%S)
UNIQ_ID="_DATE_"
if [ "${2}" ]; then
    UNIQ_ID=${2}
fi

source $CONFIG_FILE

UNIQ_ID=$(echo $UNIQ_ID | sed 's/_DATE_/'${DATE_S}'/g')
echo "UNIQ_ID is ${UNIQ_ID}"
OUT_BASE=${1}'.'${UNIQ_ID}


DATAL=${DATA_REP}${FILE_L}${EXT_L}
DATAR=${DATA_REP}${FILE_R}${EXT_R}

LABELSL=${DATA_REP}${FILE_L}${LABELS_EXT_L}
LABELSR=${DATA_REP}${FILE_R}${LABELS_EXT_R}

RULES_EXT=.rul
SUPP_EXT=.supp
DENSESUPP_EXT=.dense_supp
NAMED_EXT=.names
LOG_EXT=.log

RULES_OUT=${RES_REP}${OUT_BASE}$RULES_EXT
NAMED_OUT=${RES_REP}${OUT_BASE}$NAMED_EXT
SUPPORT_OUT=${RES_REP}${OUT_BASE}$SUPP_EXT
DENSESUPPORT_OUT=${RES_REP}${OUT_BASE}$DENSESUPP_EXT
LOG_OUT=${RES_REP}${OUT_BASE}$LOG_EXT


if (( ${#RUN_ACTION} > 0 ))
then
COMM_LINE=$( echo  ./scripts/greedyRuleFinder6.py \
       --dataL=$DATAL --dataR=$DATAR --rules-out=$RULES_OUT --support-out=$SUPPORT_OUT \
       --nb-variables=$NB_VARIABLES --min-len=$MIN_LEN \
       --contribution=$CONTRIBUTION --itm-in=$ITM_IN --itm-out=$ITM_OUT --fin-in=$FIN_IN --fin-out=$FIN_OUT \
       --nb-rules=$NB_RULES --meth-sel=$METH_SEL --div-L=$DIV_L --div-R=$DIV_R --min-score=$MIN_SCORE \
       --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT \
       --min-improvement=$MIN_IMPROVEMENT --coeff-pvrule=$COEFF_PVRULE --coeff-pvred=$COEFF_PVRED \
       $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT \
       --verbosity=$VERBOSITY)

if [ "${RUN_ACTION}" = "log" ]
then         
    cat $CONFIG_FILE > $LOG_OUT
    $COMM_LINE >> $LOG_OUT
else
    $COMM_LINE
fi
fi

if (( ${#POST_ACTIONS} > 0 ))
then         
    ./scripts/postProcess.py $POST_ACTIONS \
    --dataL=$DATAL --dataR=$DATAR \
    --rules-in=$RULES_OUT  --support-in=$SUPPORT_OUT \
    --left-labels=$LABELSL --right-labels=$LABELSR \
    --rules-out=$NAMED_OUT --support-out=$DENSESUPPORT_OUT \
    --verbosity=$VERBOSITY  
fi