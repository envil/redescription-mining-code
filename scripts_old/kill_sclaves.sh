TODO_FILE=${1}

echo "Killed so far" >> $TODO_FILE.sclaves
COUNT_SCL=$(grep -c 'Running' $TODO_FILE.sclaves)

for (( i=1; i<=${COUNT_SCL}; i++ ))
do
    echo -e "0\texit" >> $TODO_FILE
done
