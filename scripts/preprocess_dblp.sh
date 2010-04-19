
### DATA
########
DATA_REP="/fs-1/3/galbrun/redescriptors/sandbox/dblp/"
DATA1="coauthor"
SYM1=1
DATA2="conference"
SYM2=0
MAP_EXT="map"
BDAT_EXT="bdat"
NDAT_EXT="ndat"
IDS_EXT="ids"
NAMES_EXT="names"
EN_NAMES_EXT="en.names"
SUFF_FIL="_filtered"
SUFF_SEL="_selected"

### PARAMETERS
##############

FILTER_RULES="{ 
struct('matrix_nb', 2, 'thres', 10, 'dim', 1, 'unique', 0, 'lower', false), 
struct('matrix_nb', 1, 'thres', 10, 'dim', 1, 'unique', 1, 'lower', false), 
struct('matrix_nb', 2, 'thres', 100, 'dim', 2, 'unique',1, 'lower', false) 
}"

METHOD='spqr_cx'
METHOD_PATH="/fs-1/3/galbrun/redescriptors/existing/others/colselect/"
NB_COLS1=100
NB_COLS2=25
SELECT_ADDITIONAL_PARAMS=""

### SCRIPTS
###########
MAT_PATH="/fs-1/3/galbrun/redescriptors/sandbox/scripts/"
MATLAB_BIN="/opt/matlab/bin/matlab"

SCRIPTS_REP="/fs-1/3/galbrun/redescriptors/sandbox/scripts/"
AWK_BINARISE=$SCRIPTS_REP"binarise.awk"
AWK_EXTRACT_NAMES=$SCRIPTS_REP"extract_names.awk"
AWK_DEMAP_INDICES=$SCRIPTS_REP"demap_indices.awk"

### FUNCTIONS
#############

function f_demap {
## takes as input the original mappings return dat files and column names files
## Ex DBLP
## authors -> authors and conferences -> authors where the ids correspond to the line number minus one (i.e. start from 0)
##
	local DATA_MAP=${1}
	local SYM=${2}
	local DATA_DAT=${3}
	local DATA_NAMES=${4}
	echo "Converting map to dat and names ..."
	cut -f 2- $DATA_MAP | awk -f $AWK_DEMAP_INDICES sym=$SYM | sort -n > $DATA_DAT
	cut -f 1 $DATA_MAP > $DATA_NAMES
}

function f_convert_mat {
    local DATA=${1}
    local EXT_IN=${2}
    local EXT_OUT=${3}

    local SCRIPT_MATLAB="
    path(path,'${MAT_PATH}');
    [tmp, sym_tmp] = load_matrix('${DATA}','${EXT_IN}');
    if sym_tmp
       data = tmp+tmp';
    else
       data = tmp;
    end
    save_matrix(data, '${DATA}','${EXT_OUT}');
"

    echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null
}


function f_filter {
    local DATA1=${1}
    local EXT1=${2}
    local DATA2=${3}
    local EXT2=${4}
    local IDS_EXT=${5}
    local SUFF=${6}

    local SCRIPT_MATLAB="
    path(path,'${MAT_PATH}');
    [tmp, sym_tmp] = load_matrix('${DATA1}','${EXT1}');
    if sym_tmp
        data{1}.matrix = tmp+tmp';
        data{1}.sym = 1;
        [n, m] = size(tmp);
        data{1}.idx{1} = [1:n];
        data{1}.idx_in{1} = zeros(1,n);
    else
        [m, n] = size(tmp);
        data{1}.matrix = tmp;
        data{1}.sym = 0;
        data{1}.idx{1} = [1:m];
        data{1}.idx{2} = [1:n];
        data{1}.idx_in{1} = zeros(1,m);
        data{1}.idx_in{2} = zeros(1,n);
    end

    [tmp, sym_tmp] = load_matrix('${DATA2}','${EXT2}');
    if sym_tmp
        data{2}.matrix = tmp+tmp';
        data{2}.sym = 1;
        [n, m] = size(tmp);
        data{2}.idx{1} = [1:n];
        data{2}.idx_in{1} = zeros(1,n);
    else
        [m, n] = size(tmp);
        data{2}.matrix = tmp;
        data{2}.sym = 0;
        data{2}.idx{1} = [1:m];
        data{2}.idx{2} = [1:n];
        data{2}.idx_in{1} = zeros(1,m);
        data{2}.idx_in{2} = zeros(1,n);
    end

    filter_rules=${FILTER_RULES};

    for i =1:length(filter_rules)
        [data, filter_rules{i}.orig_indices, filter_rules{i}.ratio] = filter_data(data, filter_rules{i});
    end

    fid = fopen('${DATA1}${SUFF}.${IDS_EXT}','w');
    fprintf(fid, '%i\n', data{1}.idx{1}-1);
    fclose(fid);
    fid = fopen('${DATA2}${SUFF}.${IDS_EXT}','w');
    fprintf(fid, '%i\n', data{2}.idx{2}-1);
    fclose(fid);

    save_matrix(data{1}.matrix, '${DATA1}${SUFF}','${EXT1}');
    save_matrix(data{2}.matrix, '${DATA2}${SUFF}','${EXT2}');
"

    echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null
}


function f_select_cols {
	local DATA_IN=${1}
	local DATA_OUT=${2}
	local EXT=${3}
	local IDS_EXT=${4}
	local METHOD=${5}
	local METHOD_PATH=${6}
	local NB_COLS=${7}
	local ADDITIONAL_PARAMS=${8}

	local SCRIPT_MATLAB="
path(path,'${MAT_PATH}');
path(path,'${METHOD_PATH}');
[A] = load_matrix('${DATA_IN}','${EXT}');
if issparse(A)
    A = full(A);
end
[idx, X, err] = ${METHOD}(A, ${NB_COLS} ${ADDITIONAL_PARAMS});
[idx, I] = sort(idx);
X = X(I);
fid = fopen('${DATA_OUT}.${IDS_EXT}','w');
fprintf(fid, '%i\n', idx-1);
fclose(fid);
save_matrix(A(:,idx), '${DATA_OUT}','${EXT}');
"

	echo "Selecting ids ..."
	echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null
}


function f_extract_names {
	local IDS_FILE=${1}
	local FULL_NAMES=${2}
	local SUB_NAMES=${3}

	awk -f $AWK_EXTRACT_NAMES $IDS_FILE $FULL_NAMES | sort -n | cut -f 2- > $SUB_NAMES
}


function f_binarise {
	local DATA_IN=${1}
	local DATA_OUT=${2}
	awk -f $AWK_BINARISE $DATA_IN > $DATA_OUT
}


### ACTUAL PROCESSING
#####################

echo "Converting data  from " $MAP_EXT " to " $NDAT_EXT
f_demap $DATA_REP$DATA1.$MAP_EXT $SYM1 $DATA_REP$DATA1.$NDAT_EXT $DATA_REP$DATA1.$NAMES_EXT
f_demap $DATA_REP$DATA2.$MAP_EXT $SYM2 $DATA_REP$DATA2.$NDAT_EXT $DATA_REP$DATA2.$NAMES_EXT 
echo "Filtering data"
if [ ${#FILTER_RULES} -eq 0 ]; then
    echo "No filtering, copying data"
    cp $DATA_REP$DATA1.$NDAT_EXT $DATA_REP$DATA1$SUFF_FIL.$NDAT_EXT
    awk '{ print FNR-1 "\t" $0 } ' $DATA_REP$DATA1.$NAMES_EXT > $DATA_REP$DATA1$SUFF_FIL.$NAMES_EXT
    cp $DATA_REP$DATA2.$NDAT_EXT $DATA_REP$DATA2$SUFF_FIL.$NDAT_EXT
    awk '{ print FNR-1 "\t" $0 } ' $DATA_REP$DATA2.$NAMES_EXT > $DATA_REP$DATA2$SUFF_FIL.$NAMES_EXT
else
    f_filter $DATA_REP$DATA1 $NDAT_EXT $DATA_REP$DATA2 $NDAT_EXT $IDS_EXT $SUFF_FIL $FILTER_RULES
    f_extract_names $DATA_REP$DATA1$SUFF_FIL.$IDS_EXT $DATA_REP$DATA1.$NAMES_EXT  $DATA_REP$DATA1$SUFF_FIL.$NAMES_EXT
    f_extract_names $DATA_REP$DATA2$SUFF_FIL.$IDS_EXT $DATA_REP$DATA2.$NAMES_EXT  $DATA_REP$DATA2$SUFF_FIL.$NAMES_EXT
fi

cut -f 2 $DATA_REP$DATA1$SUFF_FIL.$NAMES_EXT > $DATA_REP$DATA1$SUFF_FIL.$EN_NAMES_EXT
cut -f 2 $DATA_REP$DATA2$SUFF_FIL.$NAMES_EXT > $DATA_REP$DATA2$SUFF_FIL.$EN_NAMES_EXT

echo "Turning $DATA1 to binary"
f_binarise $DATA_REP$DATA1$SUFF_FIL.$NDAT_EXT $DATA_REP$DATA1$SUFF_FIL.$BDAT_EXT
echo "Turning $DATA2 to binary"
f_binarise $DATA_REP$DATA2$SUFF_FIL.$NDAT_EXT $DATA_REP$DATA2$SUFF_FIL.$BDAT_EXT

echo "Selecting columns from data 1"
FILTERED_NBCOLS1=$(wc -l $DATA_REP$DATA2$SUFF_FIL.$IDS_EXT | cut -d ' ' -f 1)
    
if (($FILTERED_NBCOLS1 > $NB_COLS1 && $NB_COLS1 > 0 )); then
    echo "Selecting ${NB_COLS1} columns from $DATA_REP$DATA1$SUFF_FIL"
    f_select_cols $DATA_REP$DATA1$SUFF_FIL $DATA_REP$DATA1$SUFF_SEL $NDAT_EXT $IDS_EXT $METHOD $METHOD_PATH $NB_COLS1 $ADDITIONAL_PARAMS 
    f_extract_names $DATA_REP$DATA1$SUFF_SEL.$IDS_EXT $DATA_REP$DATA1$SUFF_FIL.$NAMES_EXT  $DATA_REP$DATA1$SUFF_SEL.$NAMES_EXT
else
    echo "No selection, copying data"
    cp $DATA_REP$DATA1$SUFF_FIL.$NDAT_EXT $DATA_REP$DATA1$SUFF_SEL.$NDAT_EXT
    awk '{ print FNR-1 "\t" $0 } ' $DATA_REP$DATA1$SUFF_FIL.$NAMES_EXT > $DATA_REP$DATA1$SUFF_SEL.$NAMES_EXT
fi

echo "Selecting columns from data 2"
FILTERED_NBCOLS2=$(wc -l $DATA_REP$DATA2$SUFF_FIL.$IDS_EXT | cut -d ' ' -f 1)
    
if (($FILTERED_NBCOLS2 > $NB_COLS2 && $NB_COLS2 > 0 )); then
    echo "Selecting ${NB_COLS2} columns from $DATA_REP$DATA2$SUFF_FIL"
    f_select_cols $DATA_REP$DATA2$SUFF_FIL $DATA_REP$DATA2$SUFF_SEL $BDAT_EXT $IDS_EXT $METHOD $METHOD_PATH $NB_COLS2 $ADDITIONAL_PARAMS 
    f_extract_names $DATA_REP$DATA2$SUFF_SEL.$IDS_EXT $DATA_REP$DATA2$SUFF_FIL.$NAMES_EXT  $DATA_REP$DATA2$SUFF_SEL.$NAMES_EXT
else
    echo "No selection, copying data"
    cp $DATA_REP$DATA2$SUFF_FIL.$BDAT_EXT $DATA_REP$DATA2$SUFF_SEL.$BDAT_EXT
    awk '{ print FNR-1 "\t" $0 } ' $DATA_REP$DATA2$SUFF_FIL.$NAMES_EXT > $DATA_REP$DATA2$SUFF_SEL.$NAMES_EXT
fi


cut -f 3 $DATA_REP$DATA1$SUFF_SEL.$NAMES_EXT > $DATA_REP$DATA1$SUFF_SEL.$EN_NAMES_EXT
cut -f 3 $DATA_REP$DATA2$SUFF_SEL.$NAMES_EXT > $DATA_REP$DATA2$SUFF_SEL.$EN_NAMES_EXT
 
echo "Converting $DATA1 from $NDAT_EXT to $BDAT_EXT"
f_convert_mat $DATA_REP$DATA1$SUFF_SEL $NDAT_EXT $BDAT_EXT
# f_convert_mat $DATA_REP$DATA2$SUFF_SEL $DAT_EXT $NUM_EXT 
