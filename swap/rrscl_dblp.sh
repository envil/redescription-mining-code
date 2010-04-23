if [ -e ../conf/${1}.conf ]; then
    CONFIG_FILE=../conf/${1}.conf
else
    echo "ERROR ! No config file !"
    exit
fi

source $CONFIG_FILE

FIRST_PROCESS=1
LAST_PROCESS=2
MASTER_ID=a
NB_COPIES_SWAP=3
NB_COPIES_PERM=3
SERIE=${1}
SUFF_ORG=_0
TODO_LIST=${DATA_REP}todo.list

SCRI_PATH=~/redescriptors/sandbox/scripts/
RUN_PATH=~/redescriptors/sandbox/
MAT_PATH=~/redescriptors/sandbox/scripts/
METHOD_PATH=~/redescriptors/sandbox/swap/
MATLAB_BIN=/opt/matlab/bin/matlab
PROC_ID_PLACE_HOLDER="__PROC_ID__"

mkdir -p ${DATA_REP}
mkdir -p ${RES_REP}

if [ ! -e ${DATA_REP}${FILE_L}${SUFF_ORG}${EXT_L} ]; then
    echo "Original as copy 0"
    cp ${ORG_REP}${FILE_L}${SUFF_ORG}${EXT_L} ${DATA_REP}${FILE_L}${SUFF_ORG}${EXT_L}
    cp ${ORG_REP}${FILE_R}${SUFF_ORG}${EXT_R} ${DATA_REP}${FILE_R}${SUFF_ORG}${EXT_R}
    echo -e "0\t${RUN_PATH}run.sh $SERIE _0 $PROC_ID_PLACE_HOLDER" >> $TODO_LIST
fi

echo ${SCRI_PATH}sclaves.sh $FIRST_PROCESS $LAST_PROCESS $TODO_LIST $MASTER_ID
${SCRI_PATH}sclaves.sh $FIRST_PROCESS $LAST_PROCESS $TODO_LIST $MASTER_ID

SCRIPT_MATLAB_SWAP="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = 1:${NB_COPIES_SWAP}
    XL_r = swap(XL);
    XR_r = swap(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_swap' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_swap' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _swap%i $PROC_ID_PLACE_HOLDER\n', i);
end
" 
SCRIPT_MATLAB_PERM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = 1:${NB_COPIES_PERM}
    XL_r = permute_mat(XL);
    XR_r = permute_mat(XR);

    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_perm' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_perm' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _perm%i $PROC_ID_PLACE_HOLDER\n', i);
end
"


if [ "$NB_COPIES_SWAP" > 0 ]; then
    echo "Generating ${NB_COPIES_SWAP} swap randomized copies..."
    echo "${SCRIPT_MATLAB_SWAP}" | $MATLAB_BIN > /dev/null
fi
if [ "$NB_COPIES_PERM" > 0 ]; then
    echo "Generating ${NB_COPIES_PERM} perm randomized copies..."
    echo "${SCRIPT_MATLAB_PERM}" | $MATLAB_BIN > /dev/null
fi

for (( i=${FIRST_PROCESS}; i<=${LAST_PROCESS}; i++ ))
do
echo -e "0\texit" >> $TODO_LIST
done
