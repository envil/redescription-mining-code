FIRST_PROCESS=${1}
LAST_PROCESS=${2}
TODO_FILE=${3}
MASTER_ID=${4}
echo "Sclaves $HOSTNAME ${MASTER_ID}_$FIRST_PROCESS ${MASTER_ID}_$LAST_PROCESS $TODO_FILE"
echo "Sclaves $HOSTNAME ${MASTER_ID}_$FIRST_PROCESS ${MASTER_ID}_$LAST_PROCESS $TODO_FILE" >> $TODO_FILE.logmasters


for (( i=${FIRST_PROCESS}; i<=${LAST_PROCESS}; i++ ))
do
    echo "$HOSTNAME starting ${MASTER_ID}_$i $TODO_FILE"
    echo "$HOSTNAME starting ${MASTER_ID}_$i $TODO_FILE" >> $TODO_FILE.logmasters
    (~/redescriptors/sandbox/scripts/run_subprocess.sh ${MASTER_ID}_$i $TODO_FILE)& 
    sleep 1
done

echo "Sclaves $HOSTNAME ${MASTER_ID}_$FIRST_PROCESS ${MASTER_ID}_$LAST_PROCESS" >> $TODO_FILE.sclaves
jobs -l >> $TODO_FILE.sclaves

echo "===================================================================="
echo "Sclaves $HOSTNAME ${MASTER_ID}_$FIRST_PROCESS ${MASTER_ID}_$LAST_PROCESS"
jobs -l
echo "===================================================================="
