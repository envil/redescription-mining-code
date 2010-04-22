NB_PROCESSES=2
TODO_FILE=todo.list

function f_run_sub {

      local PROC_ID=${1}
      local TODO_F=${2}
      echo "Starting" $PROC_ID $TODO_F
       while [ 1 ] 
       do
	  if [ $(grep -c '^-1' $TODO_F) -eq 0 ]; then
	      
	      sed '0,/^0\t/s//-1\t/1' $TODO_F > $TODO_F.${PROC_ID}tmp 
	      mv $TODO_F.${PROC_ID}tmp $TODO_F
	      COMM_ACTION=$(grep -m 1 '^-1' $TODO_F | cut -f 2- | sed "s/__PROC_ID__/${PROC_ID}/g")
	      if (( ${#COMM_ACTION} > 0 )); then
		  sed '0,/^-1\t/s//1\t/1' $TODO_F > $TODO_F.${PROC_ID}tmp 
 		  mv $TODO_F.${PROC_ID}tmp $TODO_F
		  $COMM_ACTION	  
	      else
		  sleep 10
	      fi
	  else
	      sleep 0.2
	  fi 
      done
}


for (( i=1; i<=${NB_PROCESSES}; i++ ))
do
    (f_run_sub $i $TODO_FILE)& 
    sleep 1
done

jobs -l
