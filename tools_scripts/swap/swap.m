%[Y,accRate,realChanges,attempts,P] = swap(D, attempts)
%
%Given a discretized matrix D, produces a random matrix which have the same 
%discretized values in rows and columns as the original matrix D. 
%
%The discretization can be sparse and contain different discretizations 
%for rows and columns, 
%
%The default number of attempts is 2*classes*numel(X) or 2*min(rowClasses,colClasses)*numel(X). 
%The given number of attempts is multiplied with numel(X) or nnz(X). To give an exact number of
%attempts, give it as a negative value.
%
%Example:
%
%X = rand(10,5);
%DX = discretize(X);
%DY = swap(DX)
%Y = undiscretize(DY,X);

function [DY,accRate,realChanges,attempts,P] = swap(DX, attempts)

persistent randGen;

if(all(cellfun(@isempty,regexp(javaclasspath,'Swap.jar'))))
    javaaddpath('Swap.jar');
end

if(isempty(randGen))
    randGen = MersenneTwisterFast;
end

defaultAttempts = 2;

if(~iscell(DX)) %only one discretization
    classes = double(max(DX(:))+1);
    
    if(nargin<2)
        attempts = defaultAttempts * classes;
    end    
else 
    rowClasses = double(max(max(DX{1}))+1);
    colClasses = double(max(max(DX{2}))+1);
    
    if(nargin<2)
        attempts = defaultAttempts * min(rowClasses,colClasses); 
    end  
end

if(attempts < 0)
    attempts = -attempts;
else    
    if(iscell(DX))
        sz = DX{1};
    else
        sz = DX;
    end    
        
    if(issparse(sz))
        sz = nnz(sz); 
    else
        sz = numel(sz);
    end
    
    attempts = sz * attempts;        
end

%randomize matrix and get output values
if(~iscell(DX))
    if(issparse(DX))
        [rows, cols, vals] = find(DX);
        S = SwapParse(rows-1,cols-1,vals,size(DX,1),classes,attempts,randGen);
        rows = double(S.getElem2Row) + 1; cols = double(S.getElem2Col) + 1;
        DY = sparse(rows,cols,vals,size(DX,1),size(DX,2));
        P = [];
    else    
        S = Swap(DX(:),size(DX,1),size(DX,2),classes,attempts,randGen);
        P = S.getPermutationMatrix+1;
        DY = DX(P);
    end
    accRate = S.getAcceptanceRate;
    realChanges = double(S.getRealChanges);
else
    if(rowClasses >= colClasses)
        if(issparse(DX{1}))
            [rows, cols, valsRow] = find(DX{1});
            [rowsC, colsC, valsCol] = find(DX{2});
            
            if(numel(rows)~= numel(rowsC) || any(rows ~= rowsC) || any(cols ~= colsC))
                error('the row and column discretization should have the same sparsity');
            end
            
            S = SwapParse(rows-1,cols-1,valsRow,valsCol,size(DX{1},1),rowClasses,attempts,randGen);
            rows = double(S.getElem2Row) + 1; cols = double(S.getElem2Col) + 1;
            DY = {sparse(rows,cols,valsRow,size(DX{1},1),size(DX{1},2)), sparse(rows,cols,valsCol,size(DX{2},1),size(DX{2},2))};
            P = [];            
        else
            S = Swap(DX{1}(:),DX{2}(:),size(DX{1},1),size(DX{1},2),rowClasses,attempts,randGen);
            P = S.getPermutationMatrix+1;
            DY = {DX{1}(P), DX{2}(P)};
        end
        accRate = S.getAcceptanceRate;
        realChanges = double(S.getRealChanges);
    else %call swap for transpose
        TDX = {DX{2}', DX{1}'};        
        [TDY,accRate,realChanges,attempts,P] = swap(TDX, -attempts);        
        DY = {TDY{2}', TDY{1}'};
        
        if(~isempty(P))
            P = floor((P'-1)/size(P,1)) + mod(P'-1,size(P,1))*size(P,2) + 1;
        end
    end    
end

P = double(P);

end
