%d = calcDist(X,Y)
%
%Calculates the average root mean square distance between two matrices
%divided by the deviation of X. It is equal to |X-Y|_F / sqrt(numel(X)) / std(X)
%
%If the distance is around 1, then X and Y differ significantly.
%
%For permutations the distance is around 1.41.

function d = calcDist(X,Y)
d = full(sqrt(mean((X(:)-Y(:)).^2)) / std(X(:)));
end
