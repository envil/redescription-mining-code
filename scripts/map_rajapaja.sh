
SERIE=rajapaja_bio.T

SUPP_EXT=supp
MAP_EXT=eps
COORDINATES=/fs-1/3/galbrun/redescriptors/sandbox/rajapaja/coordinates.names
SUPPORTS_REP=/fs-1/3/galbrun/redescriptors/sandbox/results/
MAPS_REP=/fs-1/3/galbrun/redescriptors/sandbox/fig/
MATLAB_BIN=/opt/matlab/bin/matlab

echo "Generating maps for $SERIE  ..."
sed 's/\t/;/' ${SUPPORTS_REP}${SERIE}.${SUPP_EXT} > ${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp
echo "display_map('${COORDINATES}', '${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp', '${MAPS_REP}${SERIE}.__RULEID__.${MAP_EXT}', 'psc2' )" | $MATLAB_BIN -nojvm -nosplash > /dev/null
rm ${SUPPORTS_REP}${SERIE}.${SUPP_EXT}.tmp


