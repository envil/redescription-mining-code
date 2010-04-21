%DX = discretize(X,varargin)
%
%Discretizes the matrix X which can be sparse and contain missing values.
%
%Varargin can contain: type, rowClasses and colClasses.
%
%Different discretization types (adding some new is under work): 
%
% - {'cdf','L1'} = minimizes the L1-cdf error using k-means with cityblock
% - {'equal','length'} = divides the range into n equal lengths
%
%In sparse matrix, the sparse (=zero) elements form their own class. Also 
%missing values, nans, form their own class. Other values are discretized
%separately according to the "type" approach given as parameter.
%
%Varargin may contain discretization type, rowClasses and colClasses.
%If only one number is given, rowClasses = colClasses. If two numbers are 
%given, the first one is rowClasses and the second. The string is mapped to
%the discretization type.
%
%defaults are: 
%type = 'cdf'
%rowClasses = floor(2*sqrt(size(X,2)))
%colClasses = floor(2*sqrt(size(X,1)))
%
%If rowClasses = colClasses, the output contains the discretized matrix
%which is sparse if the original matrix was. If rowClasses != colClasses,
%then the output contains a cell array where the first cell contains the
%row discretization and the second cell the column discretization.
%
%
%Examples:
%
%DX = discretize(X);
%
%DX = discretize(X,30,'equal');

function DX = discretize(X,varargin)

type = [];
rowClasses = [];
colClasses = [];

%parse the arguments
for i = 1:numel(varargin),
    if(ischar(varargin{i}))
        type = varargin{i};
    else
        if(isempty(rowClasses))
            rowClasses = varargin{i};
        else
            colClasses = varargin{i};
        end
    end    
end

%use default values for unassigned parameters

if(isempty(type))
    type = 'equal';
end

if(isempty(rowClasses) && isempty(colClasses))
    rowClasses = floor(2*sqrt(size(X,2)));
    colClasses = floor(2*sqrt(size(X,1)));
end

if(isempty(colClasses))
    colClasses = rowClasses;
end


%perform the discretization
if(rowClasses == colClasses)
    DX = oneDiscretization(X,type,rowClasses);
else
    DX = {oneDiscretization(X,type,rowClasses), oneDiscretization(X,type,colClasses)};
end  

end


function DX = oneDiscretization(X,type,classes)

%if is sparse, then all zero elements form the class 0, others are discretized separately
if(issparse(X))
    [rows,cols,vals] = find(X);
    vals = oneDiscretizationFull(vals,type,classes-1) + 1;
    DX = sparse(rows,cols,vals,size(X,1),size(X,2));    
else
    DX = oneDiscretizationFull(X(:),type,classes);
    DX = reshape(DX,size(X,1),size(X,2));
end

end

%assumes that X is a vector and full (= not sparse)
function DX = oneDiscretizationFull(X,type,classes)

%if contains nans, then all nans form the last class = (classes-1), others are discretized separately
if(any(isnan(X))) 
    DX = zeros(size(X));
    DX(isnan(X)) = classes-1;
    DX(~isnan(X)) = oneDiscretizationFullNoNans(X(~isnan(X)),type,classes-1);
else
    DX = oneDiscretizationFullNoNans(X,type,classes);
end

end


%performs one discretization to the given number of classes without missing
%values, and the X is a full vector
function DX = oneDiscretizationFullNoNans(X,type,classes)

switch(lower(type(1:2)))
    case {'cd','l1','km'} %cdf, L1, k-means
        %do k-means
        [idx,cent]=kmeans(X,classes,'distance','cityblock','emptyaction','singleton','replicates',10); %,'onlinephase','off','options',statset('display','iter'));
        
        %sort the clusters in increasing order
        [cent, order] = sort(cent);
        neworder(order) = 0:(numel(order)-1);
        
        %output the discretized matrix
        DX = neworder(idx);
        
    case {'le','eq'} %equal lengths
        mi = min(X(:));
        ma = max(X(:));
        DX = floor(classes * (X-mi)./(ma-mi));
        DX(DX==classes) = classes-1;
                
    otherwise
        error('unknown discretization type');
end


end
