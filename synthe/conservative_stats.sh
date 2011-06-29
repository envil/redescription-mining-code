#!/bin/bash

echo "noise level & accuracy type & OO & OA & AO & AA \\\\"

for noise in 'conservative' #'destructive'
do
for density in '1' '5' '10'
do
echo '\midrule'
for type in 'pess' 'ground' 'opt'
do
for serie in 'OO' 'OA' 'AO' 'AA'
do
coun=$(grep -c "${density}pc.*${serie}.*# 1 MATCH" bool_${noise}_${type}_queries.accuracies )
COUNTS=$COUNTS" & $"$((coun/2))"$"
done
echo "$ $density $ & $type $COUNTS \\\\"
COUNTS="" 
done
done
done