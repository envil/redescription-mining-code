
ORG_REP=/fs-1/3/galbrun/redescriptors/data/rajapaja/raw/
DATA_MAM=mammals.mat
DATA_WC=worldclim.mat
NAMES_MAM=mammals.mul.names
NAMES_WC=variable_names.txt

OUT_REP=/fs-1/3/galbrun/redescriptors/sandbox/rajapaja/

COOR=coordinates
MAM=mammals
WC_TP=worldclim_tp
WC_BIO=worldclim_bio
MAM_EXT=bdat
WC_EXT=num
NAMES_EXT=names

NB_COOR=2
NB_WC_TP=48
NB_WC_BIO=19
NB_WC_ALT=1

LANG_E='en'
LANG_OFF=2


echo "Preprocessing rajapaja labels ..."
cut -f $LANG_OFF -d ',' ${ORG_REP}${NAMES_MAM} > ${OUT_REP}${MAM}.${LANG_E}.${NAMES_EXT}
head -n ${NB_WC_TP} ${ORG_REP}${NAMES_WC} > ${OUT_REP}${WC_TP}.${NAMES_EXT}
tail -n ${NB_WC_BIO} ${ORG_REP}${NAMES_WC} > ${OUT_REP}${WC_BIO}.${NAMES_EXT}

MATLAB_BIN=/opt/matlab/bin/matlab
SCRIPT_MATLAB="
path(path,'/group/home/hiit_bru/rajapaja/src/')
path(path,'/fs-1/3/galbrun/redescriptors/sandbox/scripts/')

mammals = load('${ORG_REP}${DATA_MAM}');
wc = load('${ORG_REP}${DATA_WC}');

I=find(~isnan(wc.data(:,3)));
data = join(wc.data(I,:), mammals.data(:,:), ...
            wc.utm_id(I), mammals.utm_id);

rows_id_wc=data(:,1:${NB_COOR});
wctp_data=data(:,${NB_COOR}+1:${NB_COOR}+${NB_WC_TP}); 
wcbio_data=data(:,${NB_COOR}+${NB_WC_TP}+1:${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO});  
wc_alt=data(:,${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO}+1:${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO}+${NB_WC_ALT});  

rows_id_mam=data(:,${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO}+${NB_WC_ALT}+1:${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO}+${NB_WC_ALT}+${NB_COOR});
mam_data=data(:,${NB_COOR}+${NB_WC_TP}+${NB_WC_BIO}+${NB_WC_ALT}+${NB_COOR}+1:end);

err = (rows_id_wc-rows_id_mam);
if sum(sum(err'*err)) > 0
    error('Error occured while joining the data !')
end

save_matrix(wctp_data, '${OUT_REP}${WC_TP}', '${WC_EXT}');
save_matrix(wcbio_data, '${OUT_REP}${WC_BIO}', '${WC_EXT}');
save_matrix(mam_data, '${OUT_REP}${MAM}', '${MAM_EXT}');
dlmwrite('${OUT_REP}${COOR}.${NAMES_EXT}', rows_id_mam, 'delimiter', ' ');
"

echo "Preprocessing rajapaja data ..."
echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null



