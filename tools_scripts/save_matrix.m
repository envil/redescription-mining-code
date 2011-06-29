function [A] = save_matrix(data, filename, ext)
if ( strcmp(ext, '.datbool'))
    [i,j,s] = find(data);
    i = [size(data,1); i];
    j = [size(data,2); j];
    s = [0; s];
    A = [i j s];
    dlmwrite([filename ext], A, 'delimiter', '\t');
elseif ( strcmp(ext, '.datnum'))
    [i,j,s] = find(data);
    i = [size(data,1); i];
    j = [size(data,2); j];
    s = [0; s];
    A = [i j s];
    dlmwrite([filename ext], A, 'delimiter', '\t');
elseif ( strcmp(ext, '.densebool') )
     dlmwrite([filename ext], full(data),'precision',1, 'delimiter', ' '); 
     A = data;
elseif ( strcmp(ext, '.densecat') | strcmp(ext, '.densenum') )
     % WARNING ! CAT and NUM files are stored transposed 
     dlmwrite([filename ext], full(data)', 'delimiter', ' '); 
     A = data';
else
    error(['Unknown extension: ' ext ])
end
