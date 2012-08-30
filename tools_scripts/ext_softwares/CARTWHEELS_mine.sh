#!/bin/bash

### DIRECTORIES
###############
UTILS_REP=~/redescriptors/sandbox/NMscripts/
ORGALG_REP=~/redescriptors/existing/VT/CARTwheels/
RESULTS_REP=~/redescriptors/sandbox/others/binning/
LOG_REP=~/redescriptors/sandbox/others/binning/

mkdir -p $RESULTS_REP
mkdir -p $LOG_REP 


### DATA
########
ORG_REP=~/redescriptors/sandbox/binning_exp/
DATA_REP=~/redescriptors/sandbox/others/binning/
FILE_L=mammals_small
FILE_R=worldclim_tp_small_10segments
EXT_ORG=.datbool
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
$PROG_CONVERT -i $ORG_REP$FILE_L$EXT_ORG -o $DATA_REP$FILE_L$EXT_IN -l L --classes
#$PROG_CONVERT -i $ORG_REP$FILE_R$EXT_ORG -o $DATA_REP$FILE_R$EXT_IN -l R
#cp $DATA_REP$FILE_L$EXT_IN.classes class.txt
#cp $DATA_REP$FILE_L$EXT_IN init1.txt
#cp $DATA_REP$FILE_R$EXT_IN init2.txt
#$PROG > $LOG
# echo "
# " | cat ${ORGALG_REP}class.txt - >  $LOG_INIT
# echo "
# " | cat ${ORGALG_REP}init1.txt - ${ORGALG_REP}init2.txt >>  $LOG_INIT
# #rm  ${ORGALG_REP}class.txt ${ORGALG_REP}init1.txt ${ORGALG_REP}init2.txt
# mv ${ORGALG_REP}out.txt $OUTPUT
