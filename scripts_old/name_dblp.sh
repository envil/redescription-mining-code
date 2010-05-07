## rule file without rul ext 
## filtered / numbdm / ... 
## ext left
## ext right
## action to perform
REP=~/redescriptors/sandbox/

${REP}scripts/postProcess.py ${5} --base-out=${1} --verbosity=8 --dataL=${REP}dblp/conference_${2}.${3} --dataR=${REP}dblp/coauthor_${2}.${4} --rules-in=${1}.rul  --left-labels=${REP}dblp/conference_${2}.en.names --right-labels=${REP}dblp/coauthor_${2}.en.names 
