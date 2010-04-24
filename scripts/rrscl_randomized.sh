#!/bin/bash
CONFIG_PATH=~/redescriptors/sandbox/conf/
SCRI_PATH=~/redescriptors/sandbox/scripts/

if [ -e $CONFIG_PATH${1}.conf ]; then
    CONFIG_FILE=$CONFIG_PATH${1}.conf
else
    echo "ERROR ! No config file ! $CONFIG_PATH${1}.conf"
    exit
fi

source $CONFIG_FILE

SERIE=${1}
SUFF_ORG=_0
TODO_LIST=${DATA_REP}todo.list

SCRI_PATH=~/redescriptors/sandbox/scripts/
RUN_PATH=~/redescriptors/sandbox/scripts/
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
    #echo -e "0\t${RUN_PATH}run.sh $SERIE _0 $PROC_ID_PLACE_HOLDER" >> $TODO_LIST
    echo -e "0\tsleep 15" >> $TODO_LIST
fi

echo "Commands for the sclaves also in  $TODO_LIST.commands:"
echo "========================================================" 
H_id=1
echo ${SCRI_PATH}sclaves.sh $FIRST_SCLAVE_MASTER $LAST_SCLAVE_MASTER $TODO_LIST $H_id
echo ${SCRI_PATH}sclaves.sh $FIRST_SCLAVE_MASTER $LAST_SCLAVE_MASTER $TODO_LIST $H_id > $TODO_LIST.commands 
for scl_host in $SCLAVE_HOSTS
do
    let H_id++
    echo ssh $scl_host ${SCRI_PATH}sclaves.sh $FIRST_SCLAVE_HOSTS $LAST_SCLAVE_HOSTS $TODO_LIST $H_id
    echo ssh $scl_host ${SCRI_PATH}sclaves.sh $FIRST_SCLAVE_HOSTS $LAST_SCLAVE_HOSTS $TODO_LIST $H_id >> $TODO_LIST.commands
done
echo "========================================================"


####### SCRIPT MATLAB RANDOM SWAP NO DISCRETIZE
SCRIPT_MATLAB_SWAP="
path(path,'${MAT_PATH}');
%path(path,'${METHOD_PATH}');
cd '${METHOD_PATH}';
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');
fidco = fopen('${TODO_LIST}.swap', 'a');

for i = ${FIRST_COPY_SWAP}:${FIRST_COPY_SWAP}+${NB_COPIES_SWAP}-1
    XL_r = swap(XL);
    XR_r = swap(XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_swap' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_swap' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _swap%i $PROC_ID_PLACE_HOLDER\n', i);
    fclose(fid);
    fprintf(fidco, '0\t${RUN_PATH}run.sh $SERIE _swap%i $PROC_ID_PLACE_HOLDER\n', i);
end
fclose(fidco);
" 

####### SCRIPT MATLAB RANDOM SWAP DISCRETIZE RIGHT
SCRIPT_MATLAB_SWAP_DISC="
path(path,'${MAT_PATH}');
%path(path,'${METHOD_PATH}');
cd '${METHOD_PATH}';
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');
fidco = fopen('${TODO_LIST}.swapdisc', 'a');

SR = scale_data(XR);
DR = discretize(SR);

for i = ${FIRST_COPY_SWAP_DISC}:${FIRST_COPY_SWAP_DISC}+${NB_COPIES_SWAP_DISC}-1
    XL_r = swap(XL);
    DR_r = swap(DR);
    SR_r = undiscretize(DR_r, SR);
    XR_r = unscale_data(SR_r, XR);
    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_swapdisc' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_swapdisc' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _swapdisc%i $PROC_ID_PLACE_HOLDER\n', i);
    fclose(fid);
    fprintf(fidco, '0\t${RUN_PATH}run.sh $SERIE _swapdisc%i $PROC_ID_PLACE_HOLDER\n', i);
end
fclose(fidco);
" 

####### SCRIPT MATLAB RANDOM PERMUTE
SCRIPT_MATLAB_PERM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');
fidco = fopen('${TODO_LIST}.perm', 'a');

for i = ${FIRST_COPY_PERM}:${FIRST_COPY_PERM}+${NB_COPIES_PERM}-1
    XL_r = permute_mat(XL);
    XR_r = permute_mat(XR);

    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_perm' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_perm' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _perm%i $PROC_ID_PLACE_HOLDER\n', i);
    fclose(fid);
    fprintf(fidco, '0\t${RUN_PATH}run.sh $SERIE _perm%i $PROC_ID_PLACE_HOLDER\n', i);
end
fclose(fidco);
"

####### SCRIPT MATLAB RANDOM PERMUTE RIGHT SPARSE SYMMETRIC
SCRIPT_MATLAB_PERM_SSYM="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
XL = load_matrix('${ORG_REP}${FILE_L}${SUFF_ORG}', '${EXT_L}');
XR = load_matrix('${ORG_REP}${FILE_R}${SUFF_ORG}', '${EXT_R}');
fidco = fopen('${TODO_LIST}.permssym', 'a');

for i = ${FIRST_COPY_PERM_SSYM}:${FIRST_COPY_PERM_SSYM}+${NB_COPIES_PERM_SSYM}-1
    XL_r = permute_mat(XL);
    XR_r = permute_ssym(XR);

    save_matrix(XL_r, ['${DATA_REP}${FILE_L}_permssym' num2str(i)], '${EXT_L}');
    save_matrix(XR_r, ['${DATA_REP}${FILE_R}_permssym' num2str(i)], '${EXT_R}');
    fid = fopen('${TODO_LIST}', 'a');
    fprintf(fid, '0\t${RUN_PATH}run.sh $SERIE _permssym%i $PROC_ID_PLACE_HOLDER\n', i);
    fclose(fid);
    fprintf(fidco, '0\t${RUN_PATH}run.sh $SERIE _permssym%i $PROC_ID_PLACE_HOLDER\n', i);
end
fclose(fidco);
"



if [ $NB_COPIES_SWAP -gt 0 ]; then
    echo "Generating ${NB_COPIES_SWAP} (${FIRST_COPY_SWAP}...) swap randomized copies..."
    #echo "${SCRIPT_MATLAB_SWAP}" | $MATLAB_BIN > /dev/null
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
fi
if [ $NB_COPIES_SWAP_DISC -gt 0 ]; then
    echo "Generating ${NB_COPIES_SWAP_DISC} (${FIRST_COPY_SWAP_DISC}...) swap discretize randomized copies..."
    #echo "${SCRIPT_MATLAB_SWAP_DISC}" | $MATLAB_BIN > /dev/null
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 2"  >> $TODO_LIST
fi
if [ $NB_COPIES_PERM -gt 0 ]; then
    echo "Generating ${NB_COPIES_PERM} (${FIRST_COPY_PERM}...) perm randomized copies..."
    #echo "${SCRIPT_MATLAB_PERM}" | $MATLAB_BIN > /dev/null
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 3"  >> $TODO_LIST
fi
if [ $NB_COPIES_PERM_SSYM -gt 0 ]; then
    echo "Generating ${NB_COPIES_PERM_SSYM} (${FIRST_COPY_PERM_SSYM}...) perm sparse sym randomized copies..."
    #echo "${SCRIPT_MATLAB_PERM_SSYM}" | $MATLAB_BIN > /dev/null
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 10" >> $TODO_LIST
    echo -e "0\tsleep 4"  >> $TODO_LIST
fi

#echo ${SCRI_PATH}kill_sclaves.sh $TODO_LIST
${SCRI_PATH}kill_sclaves.sh $TODO_LIST

echo -e "0\tsleep 4"  >> $TODO_LIST
echo -e "0\tsleep 4"  >> $TODO_LIST
echo -e "0\tsleep 4"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST
echo -e "0\texit"  >> $TODO_LIST