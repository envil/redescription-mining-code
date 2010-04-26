## rule file without rul ext 
## filtered / numbdm / ... 
## ext left
## ext right
REP=~/redescriptors/sandbox/

${REP}scripts/postProcess.py --disp-names  --dataL=${REP}dblp/conference_${2}.${3} --dataR=${REP}dblp/coauthor_${2}.${4} --rules-in=${1}.rul  --left-labels=${REP}dblp/conference_${2}.en.names --right-labels=${REP}dblp/coauthor_${2}.en.names --base-out=${1}.en --verbosity=8
