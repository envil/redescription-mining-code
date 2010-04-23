FIRST_PROCESS=${1}
LAST_PROCESS=${2}
TODO_FILE=${3}
MASTER_ID=${4}

function f_run_sub {

      local PROC_ID=${1}
      local TODO_F=${2}
      echo "Starting" $PROC_ID $TODO_F
       while [ 1 ] 
       do
	   lockfile-create $TODO_F
	   COMM_ACTION=$(grep -m 1 '^0' $TODO_F | cut -f 2- | sed "s/__PROC_ID__/${PROC_ID}/g")
	   sed -i '0,/^0\t/s//1\t/1' $TODO_F
	   lockfile-remove $TODO_F
	   if (( ${#COMM_ACTION} > 0 )); then
	       $COMM_ACTION	  
	   else
	       sleep 180
	   fi
      done
      echo "$PROC_ID died..."
}


for (( i=${FIRST_PROCESS}; i<=${LAST_PROCESS}; i++ ))
do
    (f_run_sub $MASTER_ID$i $TODO_FILE)& 
    sleep 1
done

echo "Sclaves $HOSTNAME $MASTER_ID$FIRST_PROCESS $MASTER_ID$LAST_PROCESS" >> $TODO_FILE.sclaves
jobs -l >> $TODO_FILE.sclaves

echo "===================================================================="
echo "Sclaves $HOSTNAME $MASTER_ID$FIRST_PROCESS $MASTER_ID$LAST_PROCESS"
jobs -l
echo "===================================================================="
