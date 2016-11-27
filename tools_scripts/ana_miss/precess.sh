#!/bin/bash
MATLAB_BIN=/opt/matlab/bin/matlab

for file in $(ls *.accuracies)
do
	grep -A 1 'MATCH' $file | grep 'pc[^#]*$' | sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\2/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/3/g' -e 's/OO/4/g' | cut -f 1,2,3,5  -d ' '> $file.stats

SCRIPT_MATLAB="
figure(1)
clf
B =load('${file}.stats'); 
G = [ B(:,1) B(:,2) ones(length(B),1); B(:,1) B(:,2) zeros(length(B),1)];
W =[B(:,3); B(:,4)];
boxplot(W,G);
saveas(gcf, '${file}.eps', 'eps');
"

echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null

exit
done

#

