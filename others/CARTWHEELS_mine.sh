#!/bin/bash

### DIRECTORIES
###############
UTILS_REP=~/redescriptors/sandbox/scripts/
ORGALG_REP=~/redescriptors/existing/VT/CARTwheels/
RESULTS_REP=~/redescriptors/sandbox/others/results/
LOG_REP=~/redescriptors/sandbox/others/logs/

mkdir -p $RESULTS_REP
mkdir -p $LOG_REP 


### DATA
########
DATA_REP=~/redescriptors/sandbox/others/data/
FILE_L=conference_picked
FILE_R=coauthor_picked
EXT_ORG=.bdat
EXT_IN=.cart

### PARAMETERS
##############
EXPID="0.1"

### SCRIPTS
###########
PROG_CONVERT=${UTILS_REP}utilsIO.py
PROG=${ORGALG_REP}Redesc

### RESULTS
###########
OUTPUT=${RESULTS_REP}cartwheels_${EXPID}.txt

### LOGS
########
LOG=${LOG_REP}cartwheels_log_${EXPID}.txt
LOG_INIT=${LOG_REP}cartwheels_init_${EXPID}.txt

### COMMANDS
############
$PROG_CONVERT -i $DATA_REP$FILE_L$EXT_ORG -o $DATA_REP$FILE_L$EXT_IN -l L --classes
$PROG_CONVERT -i $DATA_REP$FILE_R$EXT_ORG -o $DATA_REP$FILE_R$EXT_IN -l R
mv $DATA_REP$FILE_L$EXT_IN.classes class.txt
mv $DATA_REP$FILE_L$EXT_IN init1.txt
mv $DATA_REP$FILE_R$EXT_IN init2.txt
$PROG > $LOG
# echo "
# " | cat ${ORGALG_REP}class.txt - >  $LOG_INIT
# echo "
# " | cat ${ORGALG_REP}init1.txt - ${ORGALG_REP}init2.txt >>  $LOG_INIT
# #rm  ${ORGALG_REP}class.txt ${ORGALG_REP}init1.txt ${ORGALG_REP}init2.txt
# mv ${ORGALG_REP}out.txt $OUTPUT
