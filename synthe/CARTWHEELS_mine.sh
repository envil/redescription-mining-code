#!/bin/bash
HOW=${1}
N=${2}

SERIES=${N}${HOW}

### DATA
########
ORG_REP=~/redescriptors/sandbox/synthe/bool_conservative/data/
DATA_REP=~/redescriptors/sandbox/synthe/data_CARTW/
FILE_L=L${SERIES}-1_random
FILE_R=R${SERIES}-1_random
EXT_ORG=.datbool
EXT_IN=.cart

### DIRECTORIES
###############
UTILS_REP=~/redescriptors/sandbox/NMscripts/
ORGALG_REP=~/redescriptors/existing/VT/CARTwheels/
SCRIPT_REP=~/redescriptors/sandbox/NMscripts/
MATLAB_BIN=/opt/matlab/bin/matlab

### SCRIPTS
###########
PROG_CONVERT=${UTILS_REP}utilsIO.py
PROG=${ORGALG_REP}Redesc


### LOGS
########
LOG=cartwheels_log.txt

### COMMANDS
############
SCRIPT_MATLAB="
path(path,'${SCRIPT_REP}');
A = load_matrix('${ORG_REP}${FILE_L}','${EXT_ORG}');
C = load_matrix('${ORG_REP}${FILE_R}','${EXT_ORG}');
ids = find(sum(A,2).*sum(C,2)==0);
A(ids,:)=0;
C(ids,:)=0;
save_matrix(A,'${DATA_REP}${FILE_L}_zeros','${EXT_ORG}');
save_matrix(C,'${DATA_REP}${FILE_R}_zeros','${EXT_ORG}');
"

echo "Temporary removing zeros..."
echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null	

echo "Converting..."
$PROG_CONVERT -i $ORG_REP$FILE_L$EXT_ORG -o $DATA_REP$FILE_L$EXT_IN -l L
$PROG_CONVERT -i $ORG_REP$FILE_R$EXT_ORG -o $DATA_REP$FILE_R$EXT_IN -l R
cp $DATA_REP$FILE_L$EXT_IN init1.txt
cp $DATA_REP$FILE_R$EXT_IN init2.txt

echo "Mining..."
$PROG > $LOG
