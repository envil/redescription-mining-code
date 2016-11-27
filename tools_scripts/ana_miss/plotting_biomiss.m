% sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\1 \2 \3/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/3/g' -e 's/OO/4/g' -e 's/[0-9]$/ 2/g' -e 's/ *# *\([01]\) *MATCH *$/ \1/g' bool_conservative_queries.accuracies > bool_conservative_queries.stats
% sed -e 's/pc/ /g' -e 's/BIOSMALL //g' -e 's/ *# *FULL *$/ 1/g' -e 's/ *# *MISS *$/ 0/g' biosmall_missing_queries.accuracies > biosmall_missing_queries.stats

B =load('biosmall_missing_queries.stats'); 

FULL=(B(:,7)==1);
MISS=(B(:,7)==0);

P0=(B(:,6)==0);
P1=(B(:,6)>0);

I10=(B(:,1)==10);
I5=(B(:,1)==5);
I1=(B(:,1)==1);


figure
subplot(1,2,1)
hold on
plot(B(find(I10.*FULL.*P0),5),B(find(I10.*FULL.*P0),3),'b+')
plot(B(find(I5.*FULL.*P0),5),B(find(I5.*FULL.*P0),3),'g+')
plot(B(find(I1.*FULL.*P0),5),B(find(I1.*FULL.*P0),3),'r+')
plot(B(find(I10.*FULL.*P1),3),B(find(I10.*FULL.*P1),5),'bo')
plot(B(find(I5.*FULL.*P1),3),B(find(I5.*FULL.*P1),5),'go')
plot(B(find(I1.*FULL.*P1),3),B(find(I1.*FULL.*P1),5),'ro')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
ylabel('Jacc with missing data')
xlabel('Jacc original data')
title('Redescriptions from original data')
subplot(1,2,2)
hold on
plot(B(find(I10.*MISS.*P0),5),B(find(I10.*MISS.*P0),3),'b+')
plot(B(find(I5.*MISS.*P0),5),B(find(I5.*MISS.*P0),3),'g+')
plot(B(find(I1.*MISS.*P0),5),B(find(I1.*MISS.*P0),3),'r+')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
ylabel('Jacc with missing data')
xlabel('Jacc original data')
title('Redescriptions from data with missing values')
