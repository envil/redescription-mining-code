function [data_sub, indices, ratio] = filter_data(data, filter_rule)
%
% Select the submatrix of data that verifies the given filtering rule   
% data = {data_one, data_two};
% data_(one|two) = {	matrix (actual data),
% 		idx (selected indices from original matrix),
% 		sym (symetrical matrix ?)}
% filter_rule = { matrix_nb (matrix to wich apply the filtering criterion),
%                  unique (consider data as binary: occurrence/non-occurrence or numerical: nb_occurrences),
%                  dim (dimension whose marginals are thresholded),
%                  thres (minimal values for the marginal to be kept, strict threshold)}
%                  lower (shall value be lower than the threshold)

if filter_rule.matrix_nb ==1
    other_m = 2;
else
    other_m = 1;
end
if filter_rule.dim ==1
    filter_dim = 2;
else
    filter_dim = 1;
end
   
A = data{filter_rule.matrix_nb};
B = data{other_m};
    
if (filter_rule.unique)
    filter_matrix = A.matrix>0;
else
    filter_matrix = A.matrix;
end
if (filter_rule.thres > 0 && filter_rule.thres < 1)
  thres = round(size(filter_matrix,filter_dim)*filter_rule.thres);
else
   thres = filter_rule.thres;
end
sum_f = sum(filter_matrix,filter_dim);
if (filter_rule.lower)
  indices = find(sum_f<thres); 
else
  indices = find(sum_f>thres);
end
ratio = length(indices)/length(sum_f);

if (A.sym)
    tmp = A.matrix(:,indices);
    A.matrix = tmp(indices,:);
    A.idx{1} = A.idx{1}(indices);
elseif (filter_rule.dim == 1)
    A.matrix = A.matrix(indices,:);
    A.idx{1} = A.idx{1}(indices);
else
    A.matrix = A.matrix(:,indices);
    A.idx{2} = A.idx{2}(indices);
end

    
if (filter_rule.dim == 1)
    if (B.sym)
        tmp = B.matrix(:,indices);
        B.matrix = tmp(indices,:);
        B.idx{1} = B.idx{1}(indices);
    else
        B.matrix = B.matrix(indices,:);
        B.idx{1} = B.idx{1}(indices);
    end
end

if (A.sym)
    A.idx_in{1}(A.idx{1}) = A.idx_in{1}(A.idx{1}) +1;
else
    A.idx_in{1}(A.idx{1}) = A.idx_in{1}(A.idx{1}) +1;
    A.idx_in{2}(A.idx{2}) = A.idx_in{2}(A.idx{2}) +1;
end

if (B.sym)
    B.idx_in{1}(B.idx{1}) = B.idx_in{1}(B.idx{1}) +1;
else
    B.idx_in{1}(B.idx{1}) = B.idx_in{1}(B.idx{1}) +1;
    B.idx_in{2}(B.idx{2}) = B.idx_in{2}(B.idx{2}) +1;
end
   
data_sub{filter_rule.matrix_nb} = A;
data_sub{other_m} = B;
    
