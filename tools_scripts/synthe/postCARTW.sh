#!/bin/bash

BASE_REP=~/redescriptors/sandbox/synthe/
TEMPLATE_CONF=${BASE_REP}templateCARTW.conf
SCRIPT_REP=~/redescriptors/sandbox/NMscripts/
OUT_BASE=${BASE_REP}results_CARTW/random_CARTW_1-

mkdir -p ${BASE_REP}results_CARTW

for HOW in 'OO' # 'height' 'width'
do
    for N in 1 # 25 50 75 100 150
    do
	
        SERIES=${N}${HOW}
	RAW=${BASE_REP}proc_CARTW/${SERIES}/out.txt
	OUT=${OUT_BASE}${SERIES}.rul
	
	grep 'REDESC' ${RAW} | sed -e 's/<=>/\t/g' -e 's/REDESC *: *//g' -e 's/[LR]//g' -e 's/~and~/ \& /g' -e 's/exc-/! /g'  -e 's/={or}=/) \| (/g' -e 's/\(.*\)\t\(.*\)/(\2)\t(\1)/g' > ${OUT}
	${SCRIPT_REP}postProcess.py ${TEMPLATE_CONF} ::SERIES::=${SERIES},::BASE_REP::=${BASE_REP}
	sort -nr -k 2 -t '.' ${OUT_BASE}${SERIES}_filtrated.rul > ${OUT_BASE}${SERIES}_sorted.rul
    done
done
