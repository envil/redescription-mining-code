% sed -e 's/pc1//g' -e 's/\([1-9]\)\([AO][AO]\)-\([0-9]*\)/\1 \2 \3/g' -e 's/AA/1/g' -e 's/OA/2/g' -e 's/AO/3/g' -e 's/OO/4/g' -e 's/[0-9]$/ 2/g' -e 's/ *# *\([01]\) *MATCH *$/ \1/g' bool_conservative_queries.accuracies > bool_conservative_queries.stats
% sed -e 's/pc1//g' -e 's/BIOSMALL //g' -e 's/ *# *FULL *$/ 1/g' -e 's/ *# *MISS *$/ 0/g' biosmall_missing_queries.accuracies > biosmall_missing_queries.stats

A =load('bool_conservative_queries.stats'); 

I=find(A(:,9)==2);
B=A(I,:);

P0=(B(:,8)==0);

I10=(B(:,1)==10);
I5=(B(:,1)==5);
I1=(B(:,1)==1);

JAA=(B(:,2)==1);
JOA=(B(:,2)==2);
JAO=(B(:,2)==3);
JOO=(B(:,2)==4);

figure
subplot(1,4,1)
hold on
plot(B(find(I10.*JAA.*P0),5),B(find(I10.*JAA.*P0),7),'b+')
plot(B(find(I5.*JAA.*P0),5),B(find(I5.*JAA.*P0),7),'g+')
plot(B(find(I1.*JAA.*P0),5),B(find(I1.*JAA.*P0),7),'r+')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
xlabel('Jacc with missing data')
ylabel('Jacc original data')
title('AA')
subplot(1,4,2)
hold on
plot(B(find(I10.*JOA.*P0),5),B(find(I10.*JOA.*P0),7),'b+')
plot(B(find(I5.*JOA.*P0),5),B(find(I5.*JOA.*P0),7),'g+')
plot(B(find(I1.*JOA.*P0),5),B(find(I1.*JOA.*P0),7),'r+')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
xlabel('Jacc with missing data')
ylabel('Jacc original data')
title('OA')
subplot(1,4,3)
hold on
plot(B(find(I10.*JAO.*P0),5),B(find(I10.*JAO.*P0),7),'b+')
plot(B(find(I5.*JAO.*P0),5),B(find(I5.*JAO.*P0),7),'g+')
plot(B(find(I1.*JAO.*P0),5),B(find(I1.*JAO.*P0),7),'r+')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
xlabel('Jacc with missing data')
ylabel('Jacc original data')
title('AO')
subplot(1,4,4)
hold on
plot(B(find(I10.*JOO.*P0),5),B(find(I10.*JOO.*P0),7),'b+')
plot(B(find(I5.*JOO.*P0),5),B(find(I5.*JOO.*P0),7),'g+')
plot(B(find(I1.*JOO.*P0),5),B(find(I1.*JOO.*P0),7),'r+')
plot([0 1], [0 1],'k:')
legend('10% missing','5% missing','1% missing', 'location','northwest')
xlabel('Jacc with missing data')
ylabel('Jacc original data')
title('OO')

J=find(A(:,9)==0);
C=A(J,:);

P0=(C(:,8)==0);

IMissLevel=[(C(:,1)==10) (C(:,1)==5) (C(:,1)==1)];
ITypes=[(C(:,2)==1) (C(:,2)==2) (C(:,2)==3) (C(:,2)==4)];

%MISSED=(C(:,5)==-1);

for i=1:size(IMissLevel,2)
	for j=1:size(ITypes,2)
		tI=find(IMissLevel(:,i).*ITypes(:,j));
		if isempty(tI)
			stats{i,j}=[]
		else
			[x,co]=hist(C(tI,7),unique(C(tI,7)))
			stats{i,j}=[x; co];
		endif
	endfor
endfor
