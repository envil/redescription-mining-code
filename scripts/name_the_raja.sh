## rule file without rul ext 
## tp / bio
## en / fi / fr
REP=~/redescriptors/sandbox/

${REP}scripts/postProcess.py --disp-names --dataL=${REP}rajapaja/mammals.bdat --dataR=${REP}rajapaja/worldclim_${2}.num --rules-in=${1}.rul  --left-labels=${REP}rajapaja/mammals.${3}.names --right-labels=${REP}rajapaja/worldclim_${2}.names --base-out=${1}.${3} --verbosity=8
