#!/bin/bash

for type in 'pess' 'ground' 'opt'
do
cut -f 1,2,5,7 -d ' ' bool_destructive_${type}_queries.accuracies | sort -n | grep -A 1 '#' | sed '/--/d' | cut -f 1,2 -d ' ' | uniq -u > ${type}_uniq
done

echo "noise level & accuracy type & OO & OA & AO & AA \\\\"

for density in '1' '5' '10'
do
echo '\midrule'
for type in 'pess' 'ground' 'opt'
do
for serie in 'OO' 'OA' 'AO' 'AA'
do
coun=$(grep -c "${density}pc.*${serie}-" ${type}_uniq)
COUNTS=$COUNTS" & $"$(( (200-coun)/2))"$"
done
echo "$ $density $ & $type $COUNTS \\\\"
COUNTS="" 
done
done