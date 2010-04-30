#RES_PREF=~/redescriptors/sandbox/randomized/CURRENT/results/randomized
RES_PREF=${1}
TYPE=${2}
RULE_EXT=.rul
RES_MATCH=${RES_PREF}'_'${TYPE}*$RULE_EXT
ORG_RES=${RES_PREF}_0.*$RULE_EXT
RATIO=0.01
OUT=${RES_PREF}'_'${TYPE}'0.sign'$RULE_EXT

if [ -e $OUT ]; then
    rm $OUT
fi

awk -F'\t' '{ print $3 }' ${RES_MATCH} | sort -n -r > summup.tmp
NB_FILES=$(echo ${RES_MATCH} | wc -w )
NB_ACCS=$(wc -l summup.tmp | cut -f 1 -d ' ' )
if [ ${NB_ACCS} -eq 0 ]; then
    LINE_NB=0
    SIGN_ACC=0
    BEST_ACC=0
else
     LINE_NB=$(echo $NB_ACCS*$RATIO  | bc | cut -f 1 -d '.' )
     if [ ${#LINE_NB} -eq 0 ]; then
	 LINE_NB=1
     fi
     SIGN_ACC=$(head -n $LINE_NB summup.tmp | tail -1)
     BEST_ACC=$(head -n 1 summup.tmp )
fi
rm summup.tmp

echo -e "# Significant results: acc>= $SIGN_ACC line $NB_ACCS x $RATIO = $LINE_NB in $NB_FILES $TYPE copies, best found $BEST_ACC" > $OUT
AWK_SCRIPT='{ if ($3>='${SIGN_ACC}') print $0 ; else print $0 " # below significant accuracy !" }'
awk -F'\t' "${AWK_SCRIPT}" $ORG_RES >> $OUT