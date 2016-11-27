#!/bin/bash

#####################################################################
SERIE=biosmall_missing
RES_REP=~/redescriptors/sandbox/synthe_res/${SERIE}/
ANALYSIS_REP=~/redescriptors/sandbox/synthe_res/

mkdir -p ${ANALYSIS_REP}
# cp ${RES_REP}*.compare ${ANALYSIS_REP}
# cp ${RES_REP}*_recomputed.queries ${ANALYSIS_REP}
# cp ${RES_REP}small.queries ${ANALYSIS_REP}

cut -f 3  ${RES_REP}small.queries | sed 's/^ *//g' | cut -f 1,2 -d ' ' > ${RES_REP}small.accuracies

for copy in $(ls ${RES_REP}*queryorg*_recomputed.queries ) 
do
    #echo "COPY " $copy
    TYPE=$( echo $copy | sed 's/^.*\/\([0-9]*pc[0-9]*\)queryorg.*$/\1/g' )
    echo "TYPE "$TYPE
    cut -f 3 $copy | sed 's/^ *//g' | cut -f 1,2 -d ' ' | paste -d ' ' ${RES_REP}small.accuracies - | sed "s/^\(.*\)$/${TYPE} BIOSMALL \1 # FULL/g" >>  ${ANALYSIS_REP}${SERIE}_queries.accuracies 
done


for copy in $(ls ${RES_REP}*.compare ) 
do
    #echo "COPY " $copy
    TYPE=$( echo $copy | sed 's/^.*\/\([0-9]*pc[0-9]*\)_.*$/\1/g' )
    echo "TYPE "$TYPE
    cut -f 3,4 $copy |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) .*# *\([0-1]\.[0-9]* [0-1].[0-9]*\) .*$/${TYPE} BIOSMALL \1 \2 # MISS/g" >>  ${ANALYSIS_REP}${SERIE}_queries.accuracies 
done
