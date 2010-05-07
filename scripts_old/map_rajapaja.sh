SUPPORTS_REP=${1}
SERIE=${2}
MAPS_REP=${3}

SUPP_EXT=supp
MAP_EXT=eps
COORDINATES=~/redescriptors/sandbox/rajapaja/coordinates.names
SCRI_PATH=~/redescriptors/sandbox/scripts/
#SUPPORTS_REP=~/redescriptors/sandbox/results/
#MAPS_REP=~/redescriptors/sandbox/fig/
MATLAB_BIN=/opt/matlab/bin/matlab

echo "Generating maps for $SERIE  ..."
sed 's/\t/;/' ${SUPPORTS_REP}${SERIE}.${SUPP_EXT} > ${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp
echo "path(path,'$SCRI_PATH'); display_map('${COORDINATES}', '${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp', '${MAPS_REP}${SERIE}.__RULEID__.${MAP_EXT}', 'psc2' )" | $MATLAB_BIN -nojvm -nosplash > /dev/null
rm ${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp


