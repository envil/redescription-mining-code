%[avE, avRowE, avColE, rowE, colE] = calcErrorDistr(X,Y)
%
%Calculates error in cumulative distribution functions in rows and columns.
%
%Return the total average error, average error in rows, average error in
%columns, errors in rows, and erros in columns.

function [avE, avRowE, avColE, rowE, colE] = calcErrorCdf(X,Y)
colE = calcColumnErrorDistr(X,Y);
rowE = calcColumnErrorDistr(X',Y');

avE = full(mean([rowE colE])); 
avRowE = full(mean(rowE));
avColE = full(mean(colE));
end

function colE = calcColumnErrorDistr(X,Y)
X = sort(X); Y = sort(Y);
colE = sum(abs(X-Y))/size(X,1);
end
