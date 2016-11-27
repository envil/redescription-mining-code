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

% figure
% hold on
% plot(B(find(I10.*JAA.*P0),7),B(find(I10.*JAA.*P0),5),'bx')
% plot(B(find(I5.*JAA.*P0),7),B(find(I5.*JAA.*P0),5),'gx')
% plot(B(find(I1.*JAA.*P0),7),B(find(I1.*JAA.*P0),5),'rx')
% plot(B(find(I10.*JOA.*P0),7),B(find(I10.*JOA.*P0),5),'b+')
% plot(B(find(I5.*JOA.*P0),7),B(find(I5.*JOA.*P0),5),'g+')
% plot(B(find(I1.*JOA.*P0),7),B(find(I1.*JOA.*P0),5),'r+')
% plot(B(find(I10.*JAO.*P0),7),B(find(I10.*JAO.*P0),5),'b+')
% plot(B(find(I5.*JAO.*P0),7),B(find(I5.*JAO.*P0),5),'g+')
% plot(B(find(I1.*JAO.*P0),7),B(find(I1.*JAO.*P0),5),'r+')
% plot(B(find(I10.*JOO.*P0),7),B(find(I10.*JOO.*P0),5),'bo')
% plot(B(find(I5.*JOO.*P0),7),B(find(I5.*JOO.*P0),5),'go')
% plot(B(find(I1.*JOO.*P0),7),B(find(I1.*JOO.*P0),5),'ro')
% plot([0 1], [0 1],'k:')
% legend('10% missing','5% missing','1% missing', 'location','northwest')
% ylabel('Jacc with missing data')
% xlabel('Jacc original data')
% title('Redescriptions from synthetic data')

F0=(A(:,9)==0);
F1=(A(:,9)==1);

P0=(A(:,8)==0);

IMissLevel=[(A(:,1)==10) (A(:,1)==5) (A(:,1)==1)];
ITypes=[(A(:,2)==1) (A(:,2)==2) (A(:,2)==3) (A(:,2)==4)];

bins_edges=[0 0.5 0.75:0.05:1 1];

%MISSED=(C(:,5)==-1);
stats=[];
for i=1:size(IMissLevel,2)
	for j=1:size(ITypes,2)
		tI0=find(IMissLevel(:,i).*ITypes(:,j).*F0);
		tI1=find(IMissLevel(:,i).*ITypes(:,j).*F1);
		if isempty(tI0)
			x = zeros(size(bins_edges));
		else
			[x,co]=histc(A(tI0,5),bins_edges); %unique(C(tI,5))
		endif		
		if isempty(tI1)
			y = zeros(size(bins_edges));
		else
			y=histc(A(tI1,5),bins_edges); %unique(C(tI,5))
		endif
		stats= [ stats; x; y];
	endfor
endfor

% G = [ B(:,1) B(:,2) ones(length(B),1); B(:,1) B(:,2) zeros(length(B),1)];
% W =[B(:,5); B(:,7)];
% boxplot(W,G);

