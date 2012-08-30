#!/bin/bash
HOW=${1}
N=${2}

SERIES=${N}${HOW}

mkdir -p proc_CARTW/${SERIES}
cp CARTWHEELS_mine.sh proc_CARTW/${SERIES}/
cd proc_CARTW/${SERIES}/
nice -n 1 ./CARTWHEELS_mine.sh ${HOW} ${N}
