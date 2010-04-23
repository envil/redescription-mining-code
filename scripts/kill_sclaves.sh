TODO_FILE=${1}

COUNT_SCL=$(grep -c 'f_run_sub' $TODO_FILE.sclaves)

for (( i=1; i<=${COUNT_SCL}; i++ ))
do
    echo -e "0\texit" >> $TODO_FILE
done
