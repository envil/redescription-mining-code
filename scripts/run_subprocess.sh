
PROC_ID=${1}
TODO_F=${2}
echo $(date ) "Starting" $PROC_ID $TODO_F >> $TODO_F.log$PROC_ID
while [ 1 ] 
do
    lockfile-create $TODO_F
    COMM_ACTION=$(grep -m 1 '^0' $TODO_F | cut -f 2- | sed "s/__PROC_ID__/${PROC_ID}/g")
    sed -i '0,/^0\t/s//1\t/1' $TODO_F
    lockfile-remove $TODO_F
    if (( ${#COMM_ACTION} > 0 )); then
	echo $(date ) "$PROC_ID executing $COMM_ACTION ..." 
	echo $(date ) "$PROC_ID executing $COMM_ACTION ..." >> $TODO_F.log$PROC_ID
	$COMM_ACTION >> $TODO_F.log$PROC_ID
	echo $(date ) "$PROC_ID done with $COMM_ACTION ..." >> $TODO_F.log$PROC_ID
    else
	echo $(date ) "$PROC_ID waiting ..." >> $TODO_F.log$PROC_ID
	sleep 3
    fi
done
echo $(date ) "$PROC_ID died..." >> $TODO_F.log$PROC_ID
