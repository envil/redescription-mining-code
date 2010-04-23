RES_PREF=~/redescriptors/sandbox/rajapaja_rand/0.1_TP1/results/rajapaja_randTP1
TYPE=swap
RULE_EXT=.rul
RES_MATCH=${RES_PREF}'_'${TYPE}*$RULE_EXT
ORG_RES=${RES_PREF}_0.*$RULE_EXT
RATIO=0.01
OUT=${RES_PREF}'_'${TYPE}'0.sign'$RULE_EXT

awk -F'\t' '{ print $3 }' ${RES_MATCH} | sort -n -r > summup.tmp
NB_FILES=$(echo ${RES_MATCH} | wc -w )
NB_ACCS=$(wc -l summup.tmp | cut -f 1 -d ' ' )
LINE_NB=$(echo $NB_ACCS*$RATIO | bc | cut -f 1 -d '.' )
SIGN_ACC=$(head -n $LINE_NB summup.tmp | tail -1)
rm summup.tmp

echo -e "Significant results: acc>= $SIGN_ACC line $NB_ACCS x $RATIO = $LINE_NB in $NB_FILES copies" > $OUT
AWK_SCRIPT='{ if ($3>='${SIGN_ACC}') print $0 "\t" 1; else print $0 "\t" 1 }'
awk -F'\t' "${AWK_SCRIPT}" $ORG_RES >> $OUT