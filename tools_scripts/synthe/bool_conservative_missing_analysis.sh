#!/bin/bash

#####################################################################
#SERIE=bool_conservative
SERIE=bool_destructive
ACC_T=ground
RES_REP=~/redescriptors/sandbox/synthe/${SERIE}/results_missing_${ACC_T}/
ANALYSIS_REP=~/redescriptors/sandbox/synthe/analysis/
OUT=${ANALYSIS_REP}${SERIE}_${ACC_T}_queries.accuracies

mkdir -p ${ANALYSIS_REP}
# cp ${RES_REP}*.compare ${ANALYSIS_REP}
# cp ${RES_REP}*_recomputed.queries ${ANALYSIS_REP}
# cp ${RES_REP}small.queries ${ANALYSIS_REP}


for copy in $(ls ${RES_REP}*test*_missing_recomputed.queries ) 
do
    
    # echo "COPY " $copy
    TYPE=$( echo $copy | sed 's/^.*\/\([0-9]*pc[0-9]*\)test.*$/\1/g' )
    SERIES=$( echo $copy | sed 's/^.*test_\([0-9AO\-]*\)_missing_recomputed.*$/\1/g' )
    echo "TYPE "$TYPE "SERIES "$SERIES
    ORG_QUERY=$( tail -1 ${RES_REP}${TYPE}test_${SERIES}_missing_recomputed.queries )
    ORG_MATCH=$( grep "$ORG_QUERY" ${RES_REP}${TYPE}_${SERIES}_missing.compare)
    if [ -n "$ORG_MATCH" ]; then
	# echo "MATCH---"
	# echo $ORG_QUERY
	echo $ORG_MATCH | cut -f 11- -d ' ' |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) .*# *\([0-1]\.[0-9]* [0-1].[0-9]*\) .*$/${TYPE} ${SERIES} \1 \2 # 1 MATCH /g" >>  ${OUT} 
    else
	# echo "NO MATCH---"
	# echo $ORG_QUERY
	echo $ORG_QUERY | cut -f 11- -d ' ' |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) [0-9 ]*$/${TYPE} ${SERIES} \1 1 0 # 0 MATCH/g" >>  ${OUT} 
    fi
    cut -f 3,4 ${RES_REP}${TYPE}_${SERIES}_missing.compare |  sed "s/^ *\([0-1].[0-9]* [0-1].[0-9]*\) .*# *\([0-1]\.[0-9]* [0-1].[0-9]*\) .*$/${TYPE} ${SERIES} \1 \2/g" >>  ${OUT} 
done
