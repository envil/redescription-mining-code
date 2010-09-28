#!/bin/bash


CONF_FILE=../binning_exp/template.conf
NB_SL=3

for HOW in 'height' 'width' 'means'
do
    for N in 10 20 30 50 75 100 150
    do
	echo "0	./generate.sh $N $HOW $CONF_FILE" 
    done
done

for (( c=1; c<=$NB_SL; c++ ))
do
    echo '0	exit'
done