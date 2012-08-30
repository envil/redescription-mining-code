%Y = undiscretize(DY,X)
%
%Undiscretizes the randomized matrix DY given the original values X.
%
%Permutes the values inside each class, thus undiscretizing the discretized
%original matrix does not likely produce exactly the original matrix.
%
%Assumes that the discretization is increasing in the values of X.
%The method discretize fullfills this assumption.

function Y = undiscretize(DY,X)

%if rowClasses differ from colClasses
if(iscell(DY))
    %Gives a unique class in correct order though the classes may be
    %"uncontinuous", i.e., some class may have zero elements.
    %This works because row and column discretizations are assumed to be
    %increasing.
    DY = DY{1}+DY{2}; 
end

if(issparse(DY))
    [rows,cols,vals] = find(DY);
    [dump,order] = sort(vals + rand(size(vals)));    
    Y = sparse(rows(order),cols(order),sort(nonzeros(X)),size(DY,1),size(DY,2));        
else
    Y = zeros(size(DY));
    [dump,order] = sort(DY(:) + rand(numel(DY),1));
    Y(order) = sort(X(:));
end

end
