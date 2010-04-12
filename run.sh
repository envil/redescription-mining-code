#!/bin/bash
TIMED="time --append -o time_log "
OUT=spqrcx_100_25 
NB=A

DATA_REP=../data/dblp/${OUT}/
DATAL=${DATA_REP}conference_selected
DATAR=${DATA_REP}coauthor_selected

DAT_EXT=.dat
NAMES_EXT=.cut_names

RULES_EXT=.rul
SUPP_EXT=.supp
GRAPH_EXT=.graph
LOG_EXT=.log

RES_REP=./results/
OUTPUT=${RES_REP}${OUT}_$NB$RULES_EXT
SUPPORT_OUTPUT=${RES_REP}${OUT}_$NB$SUPP_EXT
LOG_OUTPUT=${RES_REP}${OUT}_$NB$LOG_EXT
GRAPH_OUTPUT=${RES_REP}${OUT}_$NB$GRAPH_EXT

NB_VARIABLES=5
NB_RULES=100
LIMIT_SUPPORT=3
MIN_CONTRIBUTION=5
SCORE_FORMULA="suppI[i]/suppU[i]"
DRAFT_CAPACITY=8
DRAFT_OUTPUT=1
MIN_IMPROVEMENT=0
AMNESIC='' 
MAX_SIDE_IDENTICAL=2
WITHOUT="--without-nots"

VERBOSITY=3

./scripts/greedyRuleFinder6.py --dataL=$DATAL$DAT_EXT --dataR=$DATAR$DAT_EXT --output=$OUTPUT --support-output=$SUPPORT_OUTPUT \
    --nb-variables=$NB_VARIABLES --nb-rules=$NB_RULES --limit-support=$LIMIT_SUPPORT --min-contribution=$MIN_CONTRIBUTION --score-formula=$SCORE_FORMULA \
    --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT --min-improvement=$MIN_IMPROVEMENT $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT --verbosity=$VERBOSITY #> ${OUT}_$NB$LOG_EXT

#./scripts/display_graph_rules.py --dataL=$DATAL$DAT_EXT --dataR=$DATAR$DAT_EXT  -o ${OUT}_$NB$RULES_EXT -O compare_named$GRAPH_EXT -l $DATAL$NAMES_EXT -r $DATAR$NAMES_EXT
#./scripts/sanityChecker.py --dataL=$DATAL$DAT_EXT --dataR=$DATAR$DAT_EXT  -O ${OUT}_$NB$SUPP_EXT -o ${OUT}_$NB$RULES_EXT
