#!/bin/bash
CONFIG_PATH=~/redescriptors/sandbox/conf/
if [ -e $CONFIG_PATH${1}.conf ]; then
    CONFIG_FILE=$CONFIG_PATH${1}.conf
else
    echo "ERROR ! No config file ! $CONFIG_PATH${1}.conf"
    exit
fi

source $CONFIG_FILE

CONF=${1}
TODO_F=${2}
RULES_EXT="\.rul"
DELAY_MIN=30
RUN_SCRIPT=~/redescriptors/sandbox/scripts/run.sh
PID_PLACH="__PROC_ID__"

if [ -e flush.tmp ]; then
    echo "flush.tmp already exists ! Not doing anything ..."
    exit
fi


for file_gen in ${DATA_REP}${FILE_R}*${EXT_R}
do
    SUFF=$(echo "$file_gen" | sed -e "s/^.*"${FILE_R}"//" -e "s/"${EXT_R}"//" )
    #echo SUFF $SUFF
    let FOUND=$(find ${RES_REP} -maxdepth 1 -name ${CONF}${SUFF}\.\*${RULES_EXT} | wc -l )+$(grep -c $CONF' '$SUFF' '$PID_PLACH $TODO_F)
     
    if [[ "$FOUND" -eq "0" ]]; then
	last_mod=$(stat -c '%Z' $file_gen )
 	if [ -n "$last_mod" ]; then let delay_mod=$(date +%s)-${last_mod}; else let delay_mod=0; fi
	if [[ "$delay_mod" -gt "$DELAY_MIN" ]]; then
 	    echo -e "0\t$RUN_SCRIPT $CONF $SUFF $PID_PLACH" >> flush.tmp
 	fi
    fi
done
if [ -e flush.tmp ]; then
#     lockfile-create $TODO_F
#     cat flush.tmp >> $TODO_F
     echo "TO BE ADDED:"$(wc -l flush.tmp)
#     cat flush.tmp
#     rm flush.tmp
#     lockfile-remove $TODO_F
else
    echo "NONE ADDED"
fi
