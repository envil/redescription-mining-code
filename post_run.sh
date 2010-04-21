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

RULES_IN=${RES_REP}${OUT_BASE}$RULES_EXT
SUPPORT_IN=${RES_REP}${OUT_BASE}$SUPP_EXT

./scripts/postProcess.py ${3} \
    --dataL=$DATAL --dataR=$DATAR \
    --rules-in=$RULES_IN  --support-in=$SUPPORT_IN \
    --left-labels=$LABELSL --right-labels=$LABELSR \
    --base-out=${RES_REP}${OUT_BASE} --verbosity=$VERBOSITY  