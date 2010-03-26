#!/bin/bash
TIMED="time --append -o time_log "


DATAL=../data/DBLP_spqrcx/conference_filtered
DATAR=../data/DBLP_spqrcx/coauthor_filtered

OUT=full
DAT_EXT=.dat
NAMES_EXT=_cut.names
NB=TEST


RULES_EXT=.rul
SUPP_EXT=.supp
GRAPH_EXT=.graph
LOG_EXT=.log

OUTPUT=${OUT}_$NB$RULES_EXT
SUPPORT_OUTPUT=${OUT}_$NB$SUPP_EXT

NB_VARIABLES=5
NB_RULES=20
LIMIT_SUPPORT=1
MIN_CONTRIBUTION=3
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
    --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT --min-improvement=$MIN_IMPROVEMENT $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT --verbosity=$VERBOSITY

#./scripts/display_graph_rules.py --dataL=$DATAL$DAT_EXT --dataR=$DATAR$DAT_EXT  -o ${OUT}_$NB$RULES_EXT -O compare_named$GRAPH_EXT -l $DATAL$NAMES_EXT -r $DATAR$NAMES_EXT
#./scripts/sanityChecker.py --dataL=$DATAL$DAT_EXT --dataR=$DATAR$DAT_EXT  -O ${OUT}_$NB$SUPP_EXT -o ${OUT}_$NB$RULES_EXT
