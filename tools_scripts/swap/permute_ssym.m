function [Xr] = permute_ssym(X)
% permute_ssym Random permutation of sparse symmetric matrix X
    [i,j,v] = find(triu(X));
    pr = randi(size(X,1), length(v), 2);
    Xt = sparse([size(X,1); pr(:,1)], [size(X,2); pr(:,2)], [0; v]);
    Xr = Xt+Xt';
    if (nnz(X) - nnz(Xr))/nnz(X) > 5*10^-3
        warning(['Many values overlapped (' num2str((nnz(X) - nnz(Xr))/nnz(X)) ')!'])
    end
    