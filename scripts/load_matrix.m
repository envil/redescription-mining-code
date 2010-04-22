function [data, sym] = load_matrix(basename, ext)

if ( strcmp(ext, '.bdat') | strcmp(ext, '.ndat'))
    A = dlmread([basename ext], '\t');
    l = length(A);
    lower_p = length(find(A(:,1) - A(:,2)<0));
    sym = (l-lower_p)*lower_p == 0;
    data = sparse(A(:,1),A(:,2),A(:,3));
    [n,m] = size(data);
    if sym & n~=m
        t = max(n,m);
        data(t,t) = 0;
    end
    
elseif ( strcmp(ext, '.dense'))
     data = dlmread([basename ext], ' ');
     sym = false;  
elseif ( strcmp(ext, '.cat') | strcmp(ext, '.num'))
     data = dlmread([basename ext], ' ')';
     sym = false;
else
    error(['Unknown extension: ' ext ])
end
