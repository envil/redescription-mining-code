TODO_FILE=${1}

echo "Killed so far" >> $TODO_FILE.slaves
COUNT_SCL=$(grep -c 'Running' $TODO_FILE.slaves)

for (( i=1; i<=${COUNT_SCL}; i++ ))
do
    echo -e "0\texit" >> $TODO_FILE
done
