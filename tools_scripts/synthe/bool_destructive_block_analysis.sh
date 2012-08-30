#!/bin/bash

#####################################################################
#SERIE=bool_conservative
SERIE=bool_destructive
B=block
ACC_T=ground
RES_REP=~/redescriptors/sandbox/synthe/${SERIE}/results_${B}_${ACC_T}/
ANALYSIS_REP=~/redescriptors/sandbox/synthe/analysis/
OUT=${ANALYSIS_REP}${SERIE}_${B}_${ACC_T}_queries.accuracies

mkdir -p ${ANALYSIS_REP}
# cp ${RES_REP}*.compare ${ANALYSIS_REP}
# cp ${RES_REP}*_recomputed.queries ${ANALYSIS_REP}
# cp ${RES_REP}small.queries ${ANALYSIS_REP}


for copy in $(ls ${RES_REP}*_${B}.compare ) 
do
    #echo "COPY " $copy
    TYPE=$( echo $copy | sed 's/^.*\/\([0-9]*pc[0-9]*\)_\([0-9][AO][AO]-[0-9]*\)_.*$/\1/g' )
    SERIES=$( echo $copy | sed 's/^.*\/\([0-9]*pc[0-9]*\)_\([0-9][AO][AO]-[0-9]*\)_.*$/\2/g' )
    echo "TYPE "$TYPE "SERIES "$SERIES
    ORG_QUERY=$( tail -1 ${RES_REP}${TYPE}_${SERIES}_${B}.compare )
    ORG_MATCH=$( sed '$d' ${RES_REP}${TYPE}_${SERIES}_${B}.compare | grep "$ORG_QUERY" - )
    if [ -n "$ORG_MATCH" ]; then
	echo "MATCH---"
	MATCH=1
    else
	echo "NO MATCH---"
	MATCH=0
    fi
    echo $ORG_QUERY | cut -f 11- -d ' ' |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) .*# *\([0-1]\.[0-9]* [0-1].[0-9]*\) .*$/${TYPE} ${SERIES} \1 \2 # ${MATCH} MATCH /g" >>  ${OUT} 
    sed '$d' ${RES_REP}${TYPE}_${SERIES}_${B}.compare | cut -f 3,4 |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) .*# *\([0-1]\.[0-9]* [0-1].[0-9]*\) .*$/${TYPE} ${SERIES} \1 \2/g" >>  ${OUT}
done
