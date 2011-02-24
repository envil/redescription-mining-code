function [data, sym] = load_matrix(basename, ext)

if ( strcmp(ext, '.datbool') | strcmp(ext, '.datnum'))
    A = dlmread([basename ext], '\t');
    l = length(A);
    lower_p = length(find(A(:,1) - A(:,2)<0));
    sym = (l-lower_p)*lower_p == 0;
    data = sparse(A(:,1),A(:,2),A(:,3));
    
elseif ( strcmp(ext, '.densebool'))
     data = dlmread([basename ext], ' ');
     sym = false;  
elseif ( strcmp(ext, '.densecat') | strcmp(ext, '.densenum'))
     data = dlmread([basename ext], ' ')';
     sym = false;
else
    error(['Unknown extension: ' ext ])
end
