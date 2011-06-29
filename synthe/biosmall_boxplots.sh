#!/bin/bash
MATLAB_BIN=/opt/matlab/bin/matlab

# for file in $(ls *.accuracies)
# do
#     grep -A 1 'MATCH' $file | grep 'pc[^#]*$' | sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\2/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/2/g' -e 's/OO/3/g' | cut -f 1,2,3,5  -d ' '> ${file}_tmp.stats

head -q -n 40 ../../rajapaja/results/rajapaja_small_nop.queries | cut -f 3 | sed 's/ \([0-9.]*\) .*$/0 0 \1/g' > biosmall_accuracies
#head -q -n 40 ../biosmall_missing/results/small.queries | cut -f 3 | sed 's/ \([0-9.]*\) .*$/0 0 \1/g' > biosmall_accuracies
head -q -n 40 ../biosmall_missing/results_nop/1pc*.compare | cut -f 3 | sed 's/ \([0-9.]*\) .* # \([0-9.]*\) .*$/\1 \2/g' > biosmall_acc1pc
head -q -n 40 ../biosmall_missing/results_nop/5pc*.compare | cut -f 3 | sed 's/ \([0-9.]*\) .* # \([0-9.]*\) .*$/\1 \2/g' > biosmall_acc5pc
awk '{ print FILENAME " 0 " $1; print FILENAME " 1 " $2 }' biosmall_acc*pc | sed 's/^.*acc\([0-5]\)pc /\1 /g' >> biosmall_accuracies

SCRIPT_MATLAB="
noi=[1 5];
figure(1)
clf
Ball =load('biosmall_accuracies'); 

B=Ball(find(Ball(:,1)==0),:);
subplot(1,length(noi)+1,1);

boxplot(B(:,3), 'labels', {''}); %;'OA missing';'OA full';'OO missing';'OO full'});
%h = findobj(gca,'Type','text');
%set(h,'FontSize',14) 
	
ylim([-0.1, 1.1])

set(gca, 'YTickLabels', [0:0.2:1]);
set(gca, 'FontSize', 28 ,'YTick', [0:0.2:1]);


for i=1:length(noi)
	B=Ball(find(Ball(:,1)==noi(i)),:);
	subplot(1,length(noi)+1,i+1);
%        set(gca, 'FontSize', 14 );
	boxplot(B(:,3),B(:,2), 'labels', {'',''}); %;'OA missing';'OA full';'OO missing';'OO full'});
        % h = findobj(gca,'Type','text');
        % set(h,'FontSize',14) 
		
        ylim([-0.1, 1.1])

	set(gca, 'YTickLabels', []);
	set(gca, 'FontSize', 28, 'YTick', [0:0.2:1]);
        % title([ int2str(noi(i)) '% missing values'])
end
saveas(gcf, 'biosmall.eps', 'psc2');
"

echo "${SCRIPT_MATLAB}" | $MATLAB_BIN -nojvm -nosplash > /dev/null

