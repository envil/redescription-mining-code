
NB_COPIES_SWAP=25
NB_COPIES_PERM=25
SERIE=B

RAND_REP=~/redescriptors/sandbox/rand_rajapaja/${SERIE}/data/
RES_REP=~/redescriptors/sandbox/rand_rajapaja/${SERIE}/results/
ORG_REP=~/redescriptors/sandbox/rajapaja/
FILE_L=mammals
FILE_R=worldclim_tp
EXT_L=bdat
EXT_R=num
RULES_EXT=rul
SUPP_EXT=supp
OUT_BASE=random
LOG_FILE=${RES_REP}random.log
SUFF_PERM="_perm"
SUFF_SWAP="_swap"

########## MINING SETTINGS
NB_VARIABLES=4
MIN_LEN=2

CONTRIBUTION=3
ITM_IN=5
ITM_OUT=400
FIN_IN=5
FIN_OUT=400

NB_RULES=100
METH_SEL="alternate"
DIV_L=1
DIV_R=1
MIN_SCORE=0.2

DRAFT_CAPACITY=4
DRAFT_OUTPUT=1

MIN_IMPROVEMENT=0
COEFF_IMPACC=1
COEFF_RELIMPACC=0
COEFF_PVRULE=1
COEFF_PVRED=1

AMNESIC=""
MAX_SIDE_IDENTICAL=2
WITHOUT="--without-nots"

VERBOSITY=8

SCRI_PATH=~/redescriptors/sandbox/scripts/
MAT_PATH=~/redescriptors/sandbox/scripts/
METHOD_PATH=~/redescriptors/sandbox/swap/
MATLAB_BIN=/opt/matlab/bin/matlab

mkdir -p ${RAND_REP}
mkdir -p ${RES_REP}

echo "Original as copy 0"
cp ${ORG_REP}${FILE_L}.${EXT_L} ${RAND_REP}${FILE_L}_0.${EXT_L}
cp ${ORG_REP}${FILE_R}.${EXT_R} ${RAND_REP}${FILE_R}_0.${EXT_R}

function f_gen_swap {

   local NB_COPIES=${1}

   echo "Generating randomized swap copies..."
   SCRIPT_MATLAB_SWAP="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH_SWAP}');
XL = load_matrix('${ORG_REP}${FILE_L}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}', '${EXT_R}');

SR = scale_data(XR);
DR = discretize(SR);

%%IF NEEDED DISCRETIZE

for i = 1:${NB_COPIES}
    XL_r = swap(XL);
    DR_r = swap(DR);
    SR_r = undiscretize(DR_r, SR);
    XR_r = unscale_data(SR_r, XR);
    save_matrix(XL_r, ['${RAND_REP}${FILE_L}${SUFF_SWAP}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${RAND_REP}${FILE_R}${SUFF_SWAP}' num2str(i)], '${EXT_R}');
end
"
   echo "${SCRIPT_MATLAB_SWAP}" | $MATLAB_BIN > /dev/null
}

function f_gen_perm {

   local NB_COPIES=${1}

   echo "Generating randomized permutation copies..."
SCRIPT_MATLAB_PERM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH_PERM}');
XL = load_matrix('${ORG_REP}${FILE_L}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}', '${EXT_R}');

for i = 1:${NB_COPIES}
    XL_r = permute_mat(XL);
    XR_r = permute_mat(XR);
    save_matrix(XL_r, ['${RAND_REP}${FILE_L}${SUFF_PERM}' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${RAND_REP}${FILE_R}${SUFF_PERM}' num2str(i)], '${EXT_R}');
end
"
echo "${SCRIPT_MATLAB_PERM}" | $MATLAB_BIN > /dev/null
}

function f_process {

      local COPY_ID=${1}

      echo "Processing copy $COPY_ID"
   
   DATAL=${RAND_REP}${FILE_L}${COPY_ID}.${EXT_L}
   DATAR=${RAND_REP}${FILE_R}${COPY_ID}.${EXT_R}
   RULES_OUT=${RES_REP}${OUT_BASE}${COPY_ID}.$RULES_EXT
   SUPPORT_OUT=${RES_REP}${OUT_BASE}${COPY_ID}.$SUPP_EXT


   ${SCRI_PATH}/greedyRuleFinder6.py \
       --dataL=$DATAL --dataR=$DATAR \
       --rules-out=$RULES_OUT --support-out=$SUPPORT_OUT \
       --nb-variables=$NB_VARIABLES --min-len=$MIN_LEN \
       --contribution=$CONTRIBUTION --itm-in=$ITM_IN --itm-out=$ITM_OUT --fin-in=$FIN_IN --fin-out=$FIN_OUT \
       --nb-rules=$NB_RULES --meth-sel=$METH_SEL --div-L=$DIV_L --div-R=$DIV_R --min-score=$MIN_SCORE \
       --draft-capacity=$DRAFT_CAPACITY --draft-output=$DRAFT_OUTPUT \
       --min-improvement=$MIN_IMPROVEMENT --coeff-impacc=$COEFF_IMPACC --coeff-relimpacc=$COEFF_RELIMPACC  --coeff-pvrule=$COEFF_PVRULE --coeff-pvred=$COEFF_PVRED \
       $AMNESIC --max-side-identical=$MAX_SIDE_IDENTICAL $WITHOUT \
       --verbosity=$VERBOSITY >> $LOG_FILE
}


f_gen_swap $NB_COPIES_SWAP
f_gen_perm $NB_COPIES_PERM

f_process "_"$i

for (( i=0; i<=${NB_COPIES_SWAP}; i++ ))
do
   f_process $SUFF_SWAP$i
done

for (( i=0; i<=${NB_COPIES_PERM}; i++ ))
do
   f_process $SUFF_PERM$i
done