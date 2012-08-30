function [Xr] = permute_mat(X)
% permute_full Random permutation of matrix X
    Xr= X(randperm(size(X,1)), randperm(size(X,2)));
end