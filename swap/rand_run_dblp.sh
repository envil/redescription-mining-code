if [ -e ../conf/${1}.conf ]; then
    CONFIG_FILE=../conf/${1}.conf
else
    echo "ERROR ! No config file !"
    exit
fi

source $CONFIG_FILE

NB_PROCESSES=2
NB_COPIES=3
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

echo "Original as copy 0"
cp ${ORG_REP}${FILE_L}${SUFF_ORG}${EXT_L} ${DATA_REP}${FILE_L}${SUFF_ORG}${EXT_L}
cp ${ORG_REP}${FILE_R}${SUFF_ORG}${EXT_R} ${DATA_REP}${FILE_R}${SUFF_ORG}${EXT_R}
echo -e "0\t${RUN_PATH}run.sh $SERIE _0 $PROC_ID_PLACE_HOLDER" >> $TODO_LIST

${SCRI_PATH}sclaves.sh $NB_PROCESSES $TODO_LIST 

echo "Generating randomized copies..."
SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');

for i = 1:${NB_COPIES}
    XL_r = swap(XL);
    XR_r = swap(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_perm' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_perm' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _perm%i $PROC_ID_PLACE_HOLDER\n', i);
end
"
echo "${SCRIPT_MATLAB}" | $MATLAB_BIN > /dev/null

for (( i=1; i<=${NB_PROCESSES}; i++ ))
do
echo -e "0\texit" >> $TODO_LIST
done
