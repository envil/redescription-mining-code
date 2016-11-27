#!/bin/bash
MATLAB_BIN=/opt/matlab/bin/matlab

for file in $(ls *.accuracies)
do
    grep -A 1 'MATCH' $file | grep 'pc[^#]*$' | sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\2/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/3/g' -e 's/OO/4/g' | cut -f 1,2,3,5  -d ' '> ${file}_tmp.stats

SCRIPT_MATLAB="
noi=[1 5 10];
figure(1)
clf
Ball =load('${file}_tmp.stats'); 

for i=1:length(noi)
	B=Ball(find(Ball(:,1)==noi(i)),:);
	G = [ B(:,2) ones(length(B),1); B(:,2) zeros(length(B),1)];
	W =[B(:,3); B(:,4)];
	subplot(1,length(noi),i);
	boxplot(W,G);
	ylim([-0.1, 1.1])
 	set(gca, 'XTickLabel', {'AA missing';'AA full';'OA missing';'OA full';'AO missing';'AO full';'OO missing';'OO full'});
	set(gca, 'XTick', [1:8]);
	if (i==1)
		set(gca, 'YTick', [0:0.1:1]);
	else
		set(gca, 'YTick', []);
	end
end
saveas(gcf, '${file}_tmp.eps', 'eps');
"

echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null
exit
done
