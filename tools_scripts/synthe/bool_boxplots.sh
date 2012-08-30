#!/bin/bash
MATLAB_BIN=/opt/matlab/bin/matlab

for file in $(ls *.accuracies)
do
    grep -A 1 'MATCH' $file | grep 'pc[^#]*$' | sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\2/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/2/g' -e 's/OO/3/g' | cut -f 1,2,3,5  -d ' '> ${file}_tmp.stats

SCRIPT_MATLAB="
noi=[1 5 10];
figure(1)
clf
Ball =load('${file}_tmp.stats'); 

for i=1:length(noi)
	B=Ball(find(Ball(:,1)==noi(i)),:);
	G = [ zeros(length(B),1); ones(length(B),1)];
	W =[B(:,3); B(:,4)];
	subplot(1,length(noi),i);
	boxplot(W,G,  'labels', {'',''}); %;'OA missing';'OA full';'OO missing';'OO full'});
        % h = findobj(gca,'Type','text');
        % set(h,'FontSize',28) 
	ylim([-0.1, 1.1])
	if (i==1)
		set(gca, 'YTickLabels', [0:0.2:1]);
		set(gca, 'FontSize', 28, 'YTick', [0:0.2:1]);
	else
		set(gca, 'YTickLabels', []);
		set(gca, 'FontSize', 28, 'YTick', [0:0.2:1]);
	end
	% title([ int2str(noi(i)) '% missing values'])
end
saveas(gcf, '${file}_tmp.eps', 'psc2');
"

echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null

done
